-- ==========================================================================
-- Script 3 de 3: vistas, funciones y triggers
-- Demuestra logica de negocio residente en el motor (curso de Bases de Datos)
-- ==========================================================================

-- !! IMPORTANTE !!
-- Los TRIGGERS de este script replican en el motor la logica que el backend
-- FastAPI ya aplica (marcar el IMEI como vendido y descontar stock).
-- Estan aqui para sustentar el componente de Bases de Datos. Si va a usar la
-- API contra PostgreSQL, deshabilitelos para no descontar dos veces:
--     ALTER TABLE venta_detalles DISABLE TRIGGER tr_venta_detalle_imei;
--     ALTER TABLE venta_detalles DISABLE TRIGGER tr_venta_detalle_stock;
-- Las VISTAS, la FUNCION fn_imei_valido y el PROCEDIMIENTO si conviven sin problema.

-- --------------------------------------------------------------------------
-- VISTA 1: existencias reales combinando productos serializados y agregados
-- --------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_inventario_disponible AS
SELECT
    p.id                AS producto_id,
    p.sku,
    p.nombre,
    m.nombre            AS marca,
    c.nombre            AS categoria,
    p.requiere_imei,
    CASE
        WHEN p.requiere_imei THEN (
            SELECT COUNT(*) FROM equipos_imei e
            WHERE e.producto_id = p.id AND e.estado = 'DISPONIBLE'
        )
        ELSE p.stock_actual
    END                 AS disponibles,
    p.stock_minimo,
    p.precio_venta,
    p.precio_costo,
    ROUND(p.precio_venta - p.precio_costo, 2)                            AS margen_bruto,
    ROUND((p.precio_venta - p.precio_costo) / NULLIF(p.precio_venta, 0) * 100, 2) AS margen_pct
FROM productos p
LEFT JOIN marcas     m ON m.id = p.marca_id
LEFT JOIN categorias c ON c.id = p.categoria_id
WHERE p.activo;

COMMENT ON VIEW v_inventario_disponible IS 'Unifica el conteo de existencias sin importar el metodo de control del producto.';

-- --------------------------------------------------------------------------
-- VISTA 2: alertas de reabastecimiento
-- --------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_alertas_stock AS
SELECT producto_id, sku, nombre, marca, disponibles, stock_minimo,
       (stock_minimo - disponibles) AS faltante
FROM v_inventario_disponible
WHERE disponibles <= stock_minimo
ORDER BY disponibles ASC;

-- --------------------------------------------------------------------------
-- VISTA 3: ventas diarias consolidadas
-- --------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_ventas_diarias AS
SELECT
    DATE(v.fecha)          AS dia,
    COUNT(*)               AS numero_ventas,
    SUM(v.subtotal)        AS subtotal,
    SUM(v.iva_total)       AS iva,
    SUM(v.total)           AS total,
    ROUND(AVG(v.total), 2) AS ticket_promedio
FROM ventas v
WHERE v.estado = 'COMPLETADA'
GROUP BY DATE(v.fecha)
ORDER BY dia DESC;

-- --------------------------------------------------------------------------
-- VISTA 4: rentabilidad por producto
-- --------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_rentabilidad_producto AS
SELECT
    p.id  AS producto_id,
    p.sku,
    p.nombre,
    SUM(d.cantidad)                                  AS unidades_vendidas,
    SUM(d.base_gravable)                             AS ingreso_sin_iva,
    SUM(d.cantidad * p.precio_costo)                 AS costo_total,
    SUM(d.base_gravable) - SUM(d.cantidad * p.precio_costo) AS utilidad_bruta
FROM venta_detalles d
JOIN ventas    v ON v.id = d.venta_id AND v.estado = 'COMPLETADA'
JOIN productos p ON p.id = d.producto_id
GROUP BY p.id, p.sku, p.nombre
ORDER BY utilidad_bruta DESC;

-- --------------------------------------------------------------------------
-- VISTA 5: trazabilidad completa de un equipo por IMEI
-- --------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_trazabilidad_imei AS
SELECT
    e.imei,
    p.nombre        AS producto,
    e.estado,
    e.fecha_ingreso,
    v.numero_factura,
    v.fecha         AS fecha_venta,
    cl.nombres || ' ' || COALESCE(cl.apellidos, '') AS cliente,
    g.fecha_fin     AS garantia_hasta,
    g.estado        AS estado_garantia
FROM equipos_imei e
JOIN productos p        ON p.id = e.producto_id
LEFT JOIN venta_detalles d ON d.equipo_imei_id = e.id
LEFT JOIN ventas v         ON v.id = d.venta_id
LEFT JOIN clientes cl      ON cl.id = v.cliente_id
LEFT JOIN garantias g      ON g.venta_detalle_id = d.id;

-- --------------------------------------------------------------------------
-- FUNCION: validar el digito verificador del IMEI (algoritmo de Luhn)
-- --------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_imei_valido(p_imei VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    suma     INTEGER := 0;
    digito   INTEGER;
    i        INTEGER;
    posicion INTEGER := 0;
BEGIN
    IF p_imei !~ '^[0-9]{15}$' THEN
        RETURN FALSE;
    END IF;
    FOR i IN REVERSE 15..1 LOOP
        digito := CAST(SUBSTRING(p_imei FROM i FOR 1) AS INTEGER);
        IF posicion % 2 = 1 THEN
            digito := digito * 2;
            IF digito > 9 THEN
                digito := digito - 9;
            END IF;
        END IF;
        suma := suma + digito;
        posicion := posicion + 1;
    END LOOP;
    RETURN suma % 10 = 0;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION fn_imei_valido IS 'Valida el digito verificador del IMEI. Se aplica como restriccion en equipos_imei.';

ALTER TABLE equipos_imei
    ADD CONSTRAINT ck_imei_luhn CHECK (fn_imei_valido(imei));

-- --------------------------------------------------------------------------
-- TRIGGER 1: impedir vender un equipo que no este disponible
-- --------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_valida_imei_disponible()
RETURNS TRIGGER AS $$
DECLARE
    estado_actual estado_imei;
BEGIN
    IF NEW.equipo_imei_id IS NULL THEN
        RETURN NEW;
    END IF;
    SELECT estado INTO estado_actual FROM equipos_imei WHERE id = NEW.equipo_imei_id;
    IF estado_actual <> 'DISPONIBLE' THEN
        RAISE EXCEPTION 'El equipo (id %) no esta disponible. Estado actual: %',
            NEW.equipo_imei_id, estado_actual;
    END IF;
    UPDATE equipos_imei SET estado = 'VENDIDO' WHERE id = NEW.equipo_imei_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_venta_detalle_imei
    BEFORE INSERT ON venta_detalles
    FOR EACH ROW EXECUTE FUNCTION trg_valida_imei_disponible();

-- --------------------------------------------------------------------------
-- TRIGGER 2: descontar stock de accesorios y dejar rastro en el kardex
-- --------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_descuenta_stock()
RETURNS TRIGGER AS $$
DECLARE
    stock_disponible INTEGER;
    es_serializado   BOOLEAN;
BEGIN
    SELECT requiere_imei, stock_actual INTO es_serializado, stock_disponible
    FROM productos WHERE id = NEW.producto_id;

    IF es_serializado THEN
        RETURN NEW;
    END IF;

    IF stock_disponible < NEW.cantidad THEN
        RAISE EXCEPTION 'Stock insuficiente del producto %: disponibles %, solicitadas %',
            NEW.producto_id, stock_disponible, NEW.cantidad;
    END IF;

    UPDATE productos
       SET stock_actual = stock_actual - NEW.cantidad
     WHERE id = NEW.producto_id;

    INSERT INTO movimientos_inventario (producto_id, tipo, cantidad, stock_resultante, motivo, referencia)
    SELECT NEW.producto_id, 'SALIDA', NEW.cantidad, p.stock_actual, 'Venta',
           (SELECT numero_factura FROM ventas WHERE id = NEW.venta_id)
      FROM productos p WHERE p.id = NEW.producto_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_venta_detalle_stock
    AFTER INSERT ON venta_detalles
    FOR EACH ROW EXECUTE FUNCTION trg_descuenta_stock();

-- --------------------------------------------------------------------------
-- PROCEDIMIENTO: marcar garantias vencidas (ejecutable por un job diario)
-- --------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_actualizar_garantias_vencidas()
LANGUAGE plpgsql AS $$
DECLARE
    afectadas INTEGER;
BEGIN
    UPDATE garantias
       SET estado = 'VENCIDA'
     WHERE estado = 'VIGENTE' AND fecha_fin < CURRENT_DATE;
    GET DIAGNOSTICS afectadas = ROW_COUNT;
    RAISE NOTICE 'Garantias marcadas como vencidas: %', afectadas;
END;
$$;

-- --------------------------------------------------------------------------
-- Consultas de verificacion
-- --------------------------------------------------------------------------
-- SELECT * FROM v_inventario_disponible;
-- SELECT * FROM v_alertas_stock;
-- SELECT * FROM v_ventas_diarias;
-- SELECT * FROM v_rentabilidad_producto;
-- SELECT * FROM v_trazabilidad_imei WHERE imei = '356789012345017';
-- SELECT fn_imei_valido('356789012345017');
-- CALL sp_actualizar_garantias_vencidas();

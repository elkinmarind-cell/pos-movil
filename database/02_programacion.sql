-- ==========================================================================================
-- Sistema POS para la gestion y venta de dispositivos moviles
-- Script 2 de 3: programacion de la base de datos
--   funciones, vistas, triggers y procedimientos almacenados
-- Ejecutar despues de 01_esquema.sql
-- ==========================================================================================
SET client_min_messages = WARNING;

-- ------------------------------------------------------------------------------------------
-- FUNCION: validacion del digito verificador del IMEI (algoritmo de Luhn)
-- ------------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_imei_valido(p_imei VARCHAR)
RETURNS BOOLEAN AS $$
DECLARE
    suma     INTEGER := 0;
    digito   INTEGER;
    i        INTEGER;
    posicion INTEGER := 0;
BEGIN
    IF p_imei IS NULL OR p_imei !~ '^[0-9]{15}$' THEN
        RETURN FALSE;
    END IF;
    FOR i IN REVERSE 15..1 LOOP
        digito := CAST(SUBSTRING(p_imei FROM i FOR 1) AS INTEGER);
        IF posicion % 2 = 1 THEN
            digito := digito * 2;
            IF digito > 9 THEN digito := digito - 9; END IF;
        END IF;
        suma := suma + digito;
        posicion := posicion + 1;
    END LOOP;
    RETURN suma % 10 = 0;
END;
$$ LANGUAGE plpgsql IMMUTABLE;
COMMENT ON FUNCTION fn_imei_valido IS 'Valida el digito verificador del IMEI. Se aplica como CHECK en equipos_imei.';

ALTER TABLE equipos_imei ADD CONSTRAINT ck_imei_luhn CHECK (fn_imei_valido(imei));

-- ------------------------------------------------------------------------------------------
-- REGLA: una sola caja abierta por terminal (indice unico parcial)
-- ------------------------------------------------------------------------------------------
CREATE UNIQUE INDEX ux_turno_abierto_por_caja ON turnos_caja (caja_id) WHERE estado = 'ABIERTO';

-- ------------------------------------------------------------------------------------------
-- FUNCION: siguiente numero de factura segun la resolucion vigente de la DIAN
-- ------------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_siguiente_numero(p_resolucion INTEGER)
RETURNS VARCHAR AS $$
DECLARE
    r RECORD;
BEGIN
    SELECT * INTO r FROM resoluciones_dian WHERE id = p_resolucion FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'La resolucion % no existe', p_resolucion;
    END IF;
    IF NOT r.activa OR CURRENT_DATE > r.vigencia_hasta THEN
        RAISE EXCEPTION 'La resolucion % no esta vigente', r.numero_resolucion;
    END IF;
    IF r.consecutivo_actual >= r.rango_hasta THEN
        RAISE EXCEPTION 'Se agoto el rango autorizado de la resolucion %', r.numero_resolucion;
    END IF;
    UPDATE resoluciones_dian SET consecutivo_actual = consecutivo_actual + 1 WHERE id = p_resolucion;
    RETURN r.prefijo || (r.consecutivo_actual + 1)::TEXT;
END;
$$ LANGUAGE plpgsql;

-- ------------------------------------------------------------------------------------------
-- VISTAS
-- ------------------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_inventario_disponible AS
SELECT p.id AS producto_id, p.sku, p.nombre, m.nombre AS marca, c.nombre AS categoria,
       p.requiere_imei,
       CASE WHEN p.requiere_imei
            THEN (SELECT COUNT(*) FROM equipos_imei e
                   WHERE e.producto_id = p.id AND e.estado = 'DISPONIBLE')
            ELSE p.stock_actual END AS disponibles,
       p.stock_minimo, p.precio_costo, p.precio_venta,
       ROUND(p.precio_venta - p.precio_costo, 2) AS margen,
       ROUND((p.precio_venta - p.precio_costo) / NULLIF(p.precio_venta, 0) * 100, 2) AS margen_pct
FROM productos p
LEFT JOIN marcas m     ON m.id = p.marca_id
LEFT JOIN categorias c ON c.id = p.categoria_id
WHERE p.activo;
COMMENT ON VIEW v_inventario_disponible IS 'Existencias unificadas: cuenta IMEI disponibles o stock agregado segun el producto.';

CREATE OR REPLACE VIEW v_alertas_stock AS
SELECT producto_id, sku, nombre, marca, disponibles, stock_minimo,
       (stock_minimo - disponibles) AS faltante
FROM v_inventario_disponible
WHERE disponibles <= stock_minimo
ORDER BY disponibles;

CREATE OR REPLACE VIEW v_ventas_diarias AS
SELECT DATE(v.fecha) AS dia, COUNT(*) AS numero_ventas,
       SUM(v.subtotal) AS subtotal, SUM(v.iva_total) AS iva, SUM(v.total) AS total,
       ROUND(AVG(v.total), 2) AS ticket_promedio
FROM ventas v
WHERE v.estado = 'COMPLETADA'
GROUP BY DATE(v.fecha)
ORDER BY dia DESC;

CREATE OR REPLACE VIEW v_rentabilidad_producto AS
SELECT p.id AS producto_id, p.sku, p.nombre,
       SUM(d.cantidad) AS unidades,
       SUM(d.precio_unitario * d.cantidad - d.descuento) AS ingreso_sin_iva,
       SUM(d.cantidad * p.precio_costo) AS costo,
       SUM(d.precio_unitario * d.cantidad - d.descuento) - SUM(d.cantidad * p.precio_costo) AS utilidad
FROM venta_detalles d
JOIN ventas v    ON v.id = d.venta_id AND v.estado = 'COMPLETADA'
JOIN productos p ON p.id = d.producto_id
GROUP BY p.id, p.sku, p.nombre
ORDER BY utilidad DESC;

CREATE OR REPLACE VIEW v_trazabilidad_imei AS
SELECT e.imei, p.nombre AS producto, e.estado, e.fecha_ingreso,
       v.numero AS factura, v.fecha AS fecha_venta,
       cl.nombres || ' ' || COALESCE(cl.apellidos, '') AS cliente,
       g.fecha_fin AS garantia_hasta, g.estado AS estado_garantia
FROM equipos_imei e
JOIN productos p           ON p.id = e.producto_id
LEFT JOIN venta_detalles d ON d.equipo_imei_id = e.id
LEFT JOIN ventas v         ON v.id = d.venta_id
LEFT JOIN clientes cl      ON cl.id = v.cliente_id
LEFT JOIN garantias g      ON g.venta_detalle_id = d.id;

CREATE OR REPLACE VIEW v_estado_caja AS
SELECT t.id AS turno_id, c.nombre AS caja, u.nombre_completo AS cajero,
       t.apertura, t.estado, t.base_inicial,
       COALESCE((SELECT SUM(pg.valor) FROM pagos pg
                  WHERE pg.turno_caja_id = t.id AND pg.metodo = 'EFECTIVO'), 0) AS efectivo_ventas,
       COALESCE((SELECT SUM(CASE WHEN mc.tipo = 'INGRESO' THEN mc.valor ELSE -mc.valor END)
                   FROM movimientos_caja mc WHERE mc.turno_caja_id = t.id), 0) AS otros_movimientos,
       COALESCE((SELECT SUM(pg.valor) FROM pagos pg WHERE pg.turno_caja_id = t.id), 0) AS recaudo_total
FROM turnos_caja t
JOIN cajas c    ON c.id = t.caja_id
JOIN usuarios u ON u.id = t.usuario_id;

CREATE OR REPLACE VIEW v_garantias_vigentes AS
SELECT g.id, g.estado, g.fecha_inicio, g.fecha_fin,
       (g.fecha_fin - CURRENT_DATE) AS dias_restantes,
       e.imei, p.nombre AS producto, v.numero AS factura,
       cl.nombres || ' ' || COALESCE(cl.apellidos, '') AS cliente, cl.telefono
FROM garantias g
JOIN venta_detalles d      ON d.id = g.venta_detalle_id
JOIN ventas v              ON v.id = d.venta_id
JOIN productos p           ON p.id = d.producto_id
LEFT JOIN equipos_imei e   ON e.id = d.equipo_imei_id
LEFT JOIN clientes cl      ON cl.id = v.cliente_id
WHERE g.estado IN ('VIGENTE', 'EN_RECLAMACION');

CREATE OR REPLACE VIEW v_apartados_pendientes AS
SELECT a.id, cl.nombres || ' ' || COALESCE(cl.apellidos, '') AS cliente, cl.telefono,
       p.nombre AS producto, e.imei, a.valor_total, a.saldo_pendiente,
       (a.valor_total - a.saldo_pendiente) AS abonado, a.fecha_limite,
       (a.fecha_limite - CURRENT_DATE) AS dias_para_vencer, a.estado
FROM apartados a
JOIN clientes cl     ON cl.id = a.cliente_id
JOIN equipos_imei e  ON e.id = a.equipo_imei_id
JOIN productos p     ON p.id = e.producto_id
WHERE a.estado = 'VIGENTE';

-- ------------------------------------------------------------------------------------------
-- TRIGGER 1: auditoria generica (quien cambio que y cuando)
-- ------------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_auditar()
RETURNS TRIGGER AS $$
DECLARE
    v_usuario INTEGER := NULLIF(current_setting('pos.usuario_id', TRUE), '')::INTEGER;
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO auditoria (usuario_id, tabla, registro_id, accion, valores_anteriores)
        VALUES (v_usuario, TG_TABLE_NAME, OLD.id, 'DELETE', to_jsonb(OLD));
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO auditoria (usuario_id, tabla, registro_id, accion, valores_anteriores, valores_nuevos)
        VALUES (v_usuario, TG_TABLE_NAME, NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));
        RETURN NEW;
    ELSE
        INSERT INTO auditoria (usuario_id, tabla, registro_id, accion, valores_nuevos)
        VALUES (v_usuario, TG_TABLE_NAME, NEW.id, 'INSERT', to_jsonb(NEW));
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_auditoria_usuarios  AFTER INSERT OR UPDATE OR DELETE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION trg_auditar();
CREATE TRIGGER tr_auditoria_productos AFTER INSERT OR UPDATE OR DELETE ON productos
    FOR EACH ROW EXECUTE FUNCTION trg_auditar();
CREATE TRIGGER tr_auditoria_equipos   AFTER INSERT OR UPDATE OR DELETE ON equipos_imei
    FOR EACH ROW EXECUTE FUNCTION trg_auditar();
CREATE TRIGGER tr_auditoria_ventas    AFTER INSERT OR UPDATE OR DELETE ON ventas
    FOR EACH ROW EXECUTE FUNCTION trg_auditar();

-- ------------------------------------------------------------------------------------------
-- TRIGGER 2: al vender, el equipo debe estar disponible y queda VENDIDO
-- ------------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_venta_equipo()
RETURNS TRIGGER AS $$
DECLARE
    v_estado estado_imei;
    v_producto INTEGER;
BEGIN
    IF NEW.equipo_imei_id IS NULL THEN RETURN NEW; END IF;
    SELECT estado, producto_id INTO v_estado, v_producto
      FROM equipos_imei WHERE id = NEW.equipo_imei_id FOR UPDATE;
    IF v_producto <> NEW.producto_id THEN
        RAISE EXCEPTION 'El equipo % no corresponde al producto %', NEW.equipo_imei_id, NEW.producto_id;
    END IF;
    IF v_estado NOT IN ('DISPONIBLE', 'APARTADO') THEN
        RAISE EXCEPTION 'El equipo % no esta disponible (estado %)', NEW.equipo_imei_id, v_estado;
    END IF;
    UPDATE equipos_imei SET estado = 'VENDIDO' WHERE id = NEW.equipo_imei_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER tr_venta_equipo BEFORE INSERT ON venta_detalles
    FOR EACH ROW EXECUTE FUNCTION trg_venta_equipo();

-- ------------------------------------------------------------------------------------------
-- TRIGGER 3: descuento de stock, kardex y garantia automatica
-- ------------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_venta_inventario()
RETURNS TRIGGER AS $$
DECLARE
    p RECORD;
    v_stock INTEGER;
    v_usuario INTEGER;
    v_factura VARCHAR;
BEGIN
    SELECT * INTO p FROM productos WHERE id = NEW.producto_id;
    SELECT usuario_id, numero INTO v_usuario, v_factura FROM ventas WHERE id = NEW.venta_id;

    IF NOT p.requiere_imei THEN
        IF p.stock_actual < NEW.cantidad THEN
            RAISE EXCEPTION 'Stock insuficiente de %: disponibles %, solicitadas %',
                p.nombre, p.stock_actual, NEW.cantidad;
        END IF;
        UPDATE productos SET stock_actual = stock_actual - NEW.cantidad
          WHERE id = NEW.producto_id RETURNING stock_actual INTO v_stock;
    END IF;

    INSERT INTO movimientos_inventario
        (producto_id, equipo_imei_id, usuario_id, tipo, cantidad, stock_resultante, motivo, referencia)
    VALUES (NEW.producto_id, NEW.equipo_imei_id, v_usuario, 'SALIDA', NEW.cantidad,
            COALESCE(v_stock, 0), 'Venta', v_factura);

    IF p.meses_garantia > 0 THEN
        INSERT INTO garantias (venta_detalle_id, fecha_inicio, fecha_fin, meses, estado)
        VALUES (NEW.id, CURRENT_DATE,
                CURRENT_DATE + (p.meses_garantia || ' months')::INTERVAL,
                p.meses_garantia, 'VIGENTE');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER tr_venta_inventario AFTER INSERT ON venta_detalles
    FOR EACH ROW EXECUTE FUNCTION trg_venta_inventario();

-- ------------------------------------------------------------------------------------------
-- TRIGGER 4: un apartado reserva el equipo; los abonos bajan el saldo
-- ------------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_apartado_reserva()
RETURNS TRIGGER AS $$
DECLARE
    v_estado estado_imei;
BEGIN
    SELECT estado INTO v_estado FROM equipos_imei WHERE id = NEW.equipo_imei_id FOR UPDATE;
    IF v_estado <> 'DISPONIBLE' THEN
        RAISE EXCEPTION 'El equipo % no se puede apartar (estado %)', NEW.equipo_imei_id, v_estado;
    END IF;
    UPDATE equipos_imei SET estado = 'APARTADO' WHERE id = NEW.equipo_imei_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER tr_apartado_reserva BEFORE INSERT ON apartados
    FOR EACH ROW EXECUTE FUNCTION trg_apartado_reserva();

CREATE OR REPLACE FUNCTION trg_abono_apartado()
RETURNS TRIGGER AS $$
DECLARE
    v_saldo NUMERIC(14,2);
BEGIN
    IF NEW.apartado_id IS NULL THEN RETURN NEW; END IF;
    UPDATE apartados SET saldo_pendiente = GREATEST(saldo_pendiente - NEW.valor, 0)
      WHERE id = NEW.apartado_id RETURNING saldo_pendiente INTO v_saldo;
    IF v_saldo = 0 THEN
        UPDATE apartados SET estado = 'COMPLETADO' WHERE id = NEW.apartado_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER tr_abono_apartado AFTER INSERT ON pagos
    FOR EACH ROW EXECUTE FUNCTION trg_abono_apartado();

-- ------------------------------------------------------------------------------------------
-- TRIGGER 5: alerta automatica cuando un producto baja del minimo
-- ------------------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trg_alerta_stock()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.stock_actual <= NEW.stock_minimo AND NEW.stock_actual < OLD.stock_actual THEN
        INSERT INTO alertas (producto_id, tipo, severidad, mensaje)
        VALUES (NEW.id, 'STOCK_BAJO',
                CASE WHEN NEW.stock_actual = 0 THEN 'ALTA' ELSE 'MEDIA' END,
                'El producto ' || NEW.nombre || ' quedo en ' || NEW.stock_actual ||
                ' unidades (minimo ' || NEW.stock_minimo || ')');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER tr_alerta_stock AFTER UPDATE OF stock_actual ON productos
    FOR EACH ROW EXECUTE FUNCTION trg_alerta_stock();

-- ------------------------------------------------------------------------------------------
-- PROCEDIMIENTOS ALMACENADOS
-- ------------------------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_actualizar_garantias_vencidas()
LANGUAGE plpgsql AS $$
DECLARE afectadas INTEGER;
BEGIN
    UPDATE garantias SET estado = 'VENCIDA'
      WHERE estado = 'VIGENTE' AND fecha_fin < CURRENT_DATE;
    GET DIAGNOSTICS afectadas = ROW_COUNT;
    RAISE NOTICE 'Garantias marcadas como vencidas: %', afectadas;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_vencer_apartados()
LANGUAGE plpgsql AS $$
DECLARE r RECORD;
BEGIN
    FOR r IN SELECT id, equipo_imei_id FROM apartados
              WHERE estado = 'VIGENTE' AND fecha_limite < CURRENT_DATE LOOP
        UPDATE apartados SET estado = 'VENCIDO' WHERE id = r.id;
        UPDATE equipos_imei SET estado = 'DISPONIBLE' WHERE id = r.equipo_imei_id;
    END LOOP;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_cerrar_turno(p_turno INTEGER, p_contado NUMERIC)
LANGUAGE plpgsql AS $$
DECLARE
    v_esperado NUMERIC(14,2);
    v_base     NUMERIC(14,2);
BEGIN
    SELECT base_inicial INTO v_base FROM turnos_caja WHERE id = p_turno AND estado = 'ABIERTO';
    IF NOT FOUND THEN
        RAISE EXCEPTION 'El turno % no existe o ya fue cerrado', p_turno;
    END IF;
    SELECT v_base
         + COALESCE((SELECT SUM(valor) FROM pagos
                      WHERE turno_caja_id = p_turno AND metodo = 'EFECTIVO'), 0)
         + COALESCE((SELECT SUM(CASE WHEN tipo = 'INGRESO' THEN valor ELSE -valor END)
                       FROM movimientos_caja WHERE turno_caja_id = p_turno), 0)
      INTO v_esperado;
    UPDATE turnos_caja
       SET cierre = NOW(), estado = 'CERRADO',
           efectivo_esperado = v_esperado, efectivo_contado = p_contado,
           diferencia = p_contado - v_esperado
     WHERE id = p_turno;
    RAISE NOTICE 'Turno % cerrado. Esperado %, contado %, diferencia %',
        p_turno, v_esperado, p_contado, p_contado - v_esperado;
END;
$$;

CREATE OR REPLACE FUNCTION fn_anular_venta(p_venta INTEGER, p_motivo VARCHAR, p_usuario INTEGER)
RETURNS VOID AS $$
DECLARE d RECORD;
BEGIN
    IF (SELECT estado FROM ventas WHERE id = p_venta) = 'ANULADA' THEN
        RAISE EXCEPTION 'La venta % ya estaba anulada', p_venta;
    END IF;
    FOR d IN SELECT * FROM venta_detalles WHERE venta_id = p_venta LOOP
        IF d.equipo_imei_id IS NOT NULL THEN
            UPDATE equipos_imei SET estado = 'DISPONIBLE' WHERE id = d.equipo_imei_id;
        ELSE
            UPDATE productos SET stock_actual = stock_actual + d.cantidad WHERE id = d.producto_id;
        END IF;
        INSERT INTO movimientos_inventario
            (producto_id, equipo_imei_id, usuario_id, tipo, cantidad, stock_resultante, motivo, referencia)
        SELECT d.producto_id, d.equipo_imei_id, p_usuario, 'DEVOLUCION', d.cantidad, p.stock_actual,
               'Anulacion: ' || p_motivo, (SELECT numero FROM ventas WHERE id = p_venta)
          FROM productos p WHERE p.id = d.producto_id;
        DELETE FROM garantias WHERE venta_detalle_id = d.id;
    END LOOP;
    UPDATE ventas SET estado = 'ANULADA', motivo_anulacion = p_motivo WHERE id = p_venta;
    RAISE NOTICE 'Venta % anulada por el usuario %: %', p_venta, p_usuario, p_motivo;
END;
$$ LANGUAGE plpgsql;

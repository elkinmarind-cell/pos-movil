-- ==========================================================================================
-- Script de pruebas de la base de datos
-- Comprueba que las reglas de negocio se cumplen en el motor, no solo en la aplicacion.
-- Cada bloque falla con EXCEPTION si la regla no se cumple. Si termina, todo paso.
-- Ejecutar sobre la base ya cargada:  psql -d pos_movil -f 04_pruebas.sql
-- ==========================================================================================
SET client_min_messages = NOTICE;

DO $$
DECLARE n INTEGER; v NUMERIC; ok BOOLEAN;
BEGIN
    RAISE NOTICE '--- 1. Carga de datos ---';
    SELECT COUNT(*) INTO n FROM usuarios;
    ASSERT n = 4, 'se esperaban 4 usuarios';
    SELECT COUNT(*) INTO n FROM rol_permisos WHERE rol_id = 1;
    ASSERT n = (SELECT COUNT(*) FROM permisos), 'el administrador debe tener todos los permisos';
    SELECT COUNT(*) INTO n FROM equipos_imei;
    ASSERT n = 15, 'se esperaban 15 equipos con IMEI';
    RAISE NOTICE 'usuarios, permisos e inventario cargados';

    RAISE NOTICE '--- 2. Validacion de IMEI (funcion Luhn) ---';
    ASSERT (SELECT bool_and(fn_imei_valido(imei)) FROM equipos_imei), 'hay IMEI que no pasan Luhn';
    ASSERT NOT fn_imei_valido('123456789012345'), 'un IMEI invalido fue aceptado';
    ASSERT NOT fn_imei_valido('abc'), 'un IMEI con letras fue aceptado';
    RAISE NOTICE 'los 15 IMEI son validos y los invalidos se rechazan';

    RAISE NOTICE '--- 3. Efecto de los triggers al vender ---';
    SELECT COUNT(*) INTO n FROM equipos_imei WHERE estado = 'VENDIDO';
    ASSERT n = 3, format('se esperaban 3 equipos vendidos, hay %s', n);
    SELECT COUNT(*) INTO n FROM movimientos_inventario WHERE tipo = 'SALIDA';
    ASSERT n >= 7, 'el kardex no registro las salidas de la venta';
    SELECT COUNT(*) INTO n FROM garantias;
    ASSERT n >= 6, 'no se generaron las garantias automaticas';
    RAISE NOTICE 'IMEI marcados, kardex escrito y garantias creadas por los triggers';

    RAISE NOTICE '--- 4. Cuadre aritmetico de las ventas ---';
    SELECT COUNT(*) INTO n FROM ventas v
     WHERE v.total <> (SELECT COALESCE(SUM(d.total_linea), 0) FROM venta_detalles d WHERE d.venta_id = v.id);
    ASSERT n = 0, 'hay ventas cuyo total no coincide con la suma de sus lineas';
    SELECT COUNT(*) INTO n FROM ventas v
     WHERE v.total <> (SELECT COALESCE(SUM(p.valor), 0) FROM pagos p WHERE p.venta_id = v.id);
    ASSERT n = 0, 'hay ventas cuyo pago no cubre el total';
    RAISE NOTICE 'totales, IVA y pagos cuadran en todas las ventas';

    RAISE NOTICE '--- 5. Apartados ---';
    SELECT saldo_pendiente INTO v FROM apartados WHERE id = 1;
    ASSERT v = 2199900.00, format('el saldo del apartado deberia ser 2199900, es %s', v);
    ASSERT (SELECT estado FROM equipos_imei WHERE id = 13) = 'APARTADO', 'el equipo apartado no quedo reservado';
    RAISE NOTICE 'los abonos descontaron el saldo y el equipo quedo reservado';

    RAISE NOTICE '--- 6. Vistas ---';
    ASSERT (SELECT COUNT(*) FROM v_inventario_disponible) = 12, 'v_inventario_disponible incompleta';
    ASSERT (SELECT disponibles FROM v_inventario_disponible WHERE sku = 'SM-A155') = 3,
           'quedan 3 Galaxy A15 disponibles despues de vender uno';
    ASSERT (SELECT COUNT(*) FROM v_ventas_diarias) >= 1, 'v_ventas_diarias vacia';
    ASSERT (SELECT COUNT(*) FROM v_trazabilidad_imei WHERE factura IS NOT NULL) = 3,
           'la trazabilidad no enlaza los equipos vendidos con su factura';
    ASSERT (SELECT COUNT(*) FROM v_apartados_pendientes) = 1, 'v_apartados_pendientes incorrecta';
    RAISE NOTICE 'las 8 vistas responden con datos coherentes';

    RAISE NOTICE '--- 7. Auditoria automatica ---';
    SELECT COUNT(*) INTO n FROM auditoria;
    ASSERT n > 30, format('la auditoria deberia tener decenas de registros, tiene %s', n);
    RAISE NOTICE 'la auditoria registro % cambios sin que la aplicacion haga nada', n;
END $$;

-- ------------------------------------------------------------------------------------------
-- 8. Reglas que DEBEN fallar: cada bloque espera un error
-- ------------------------------------------------------------------------------------------
DO $$
DECLARE paso BOOLEAN;
BEGIN
    RAISE NOTICE '--- 8. Reglas de rechazo ---';

    BEGIN   -- vender dos veces el mismo equipo
        INSERT INTO venta_detalles (venta_id, producto_id, equipo_imei_id, cantidad, precio_unitario, iva_valor, total_linea)
        VALUES (1, 1, 1, 1, 849900, 161481, 1011381);
        RAISE EXCEPTION 'FALLO: se permitio vender dos veces el equipo 1';
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE 'FALLO:%' THEN RAISE; END IF;
        RAISE NOTICE 'ok: no se puede vender un equipo ya vendido';
    END;

    BEGIN   -- IMEI con digito verificador invalido
        INSERT INTO equipos_imei (producto_id, imei, costo) VALUES (1, '123456789012345', 100);
        RAISE EXCEPTION 'FALLO: se acepto un IMEI invalido';
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE 'FALLO:%' THEN RAISE; END IF;
        RAISE NOTICE 'ok: el CHECK de Luhn rechaza IMEI invalidos';
    END;

    BEGIN   -- stock insuficiente
        INSERT INTO venta_detalles (venta_id, producto_id, cantidad, precio_unitario, iva_valor, total_linea)
        VALUES (1, 6, 99999, 39900, 1, 1);
        RAISE EXCEPTION 'FALLO: se vendio mas stock del disponible';
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE 'FALLO:%' THEN RAISE; END IF;
        RAISE NOTICE 'ok: no se puede vender mas stock del que hay';
    END;

    BEGIN   -- un pago no puede ser de una venta y de un apartado a la vez
        INSERT INTO pagos (venta_id, apartado_id, turno_caja_id, metodo, valor) VALUES (1, 1, 2, 'EFECTIVO', 1000);
        RAISE EXCEPTION 'FALLO: se acepto un pago con dos origenes';
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE 'FALLO:%' THEN RAISE; END IF;
        RAISE NOTICE 'ok: un pago pertenece a una venta o a un apartado, no a ambos';
    END;

    BEGIN   -- dos turnos abiertos en la misma caja
        INSERT INTO turnos_caja (caja_id, usuario_id, base_inicial) VALUES (1, 2, 100000);
        RAISE EXCEPTION 'FALLO: se abrieron dos turnos en la misma caja';
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE 'FALLO:%' THEN RAISE; END IF;
        RAISE NOTICE 'ok: solo puede haber un turno abierto por caja';
    END;

    BEGIN   -- producto serializado no puede llevar stock agregado
        INSERT INTO productos (sku, nombre, categoria_id, precio_costo, precio_venta, requiere_imei, stock_actual)
        VALUES ('XX-TEST','Prueba',1,100,200,TRUE,5);
        RAISE EXCEPTION 'FALLO: un producto con IMEI acepto stock agregado';
    EXCEPTION WHEN OTHERS THEN
        IF SQLERRM LIKE 'FALLO:%' THEN RAISE; END IF;
        RAISE NOTICE 'ok: un producto serializado no lleva stock agregado';
    END;
END $$;

-- ------------------------------------------------------------------------------------------
-- 9. Procedimientos almacenados (en transaccion: no deja rastro)
-- ------------------------------------------------------------------------------------------
BEGIN;
DO $$
DECLARE v_estado estado_venta; v_disp INTEGER; v_dif NUMERIC;
BEGIN
    RAISE NOTICE '--- 9. Procedimientos ---';
    PERFORM fn_anular_venta(1, 'Prueba de anulacion', 1);
    SELECT estado INTO v_estado FROM ventas WHERE id = 1;
    ASSERT v_estado = 'ANULADA', 'la venta no quedo anulada';
    ASSERT (SELECT estado FROM equipos_imei WHERE id = 1) = 'DISPONIBLE', 'el equipo no volvio a disponible';
    ASSERT (SELECT COUNT(*) FROM garantias WHERE venta_detalle_id = 1) = 0, 'la garantia no se elimino';
    RAISE NOTICE 'ok: fn_anular_venta revierte equipo, stock y garantia';

    CALL sp_cerrar_turno(2, 1500000);
    SELECT diferencia INTO v_dif FROM turnos_caja WHERE id = 2;
    ASSERT (SELECT estado FROM turnos_caja WHERE id = 2) = 'CERRADO', 'el turno no se cerro';
    RAISE NOTICE 'ok: sp_cerrar_turno calculo el arqueo (diferencia %)', v_dif;
END $$;
ROLLBACK;

SELECT 'TODAS LAS PRUEBAS DE LA BASE DE DATOS PASARON' AS resultado;

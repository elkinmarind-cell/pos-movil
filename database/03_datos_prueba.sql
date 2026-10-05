-- ======================================================================================
-- Sistema POS para la gestion y venta de dispositivos moviles
-- Script 3 de 3: datos de prueba
-- Ejecutar despues de 01_esquema.sql y 02_programacion.sql
-- Los IMEI cumplen el digito verificador de Luhn; los triggers generan kardex y garantias.
-- ======================================================================================
SET client_min_messages = WARNING;

-- --------------------------------------------------------------------------------------
-- Seguridad: roles, permisos y usuarios
-- --------------------------------------------------------------------------------------
INSERT INTO roles (nombre, descripcion) VALUES
    ('ADMINISTRADOR', 'Control total del sistema'),
    ('CAJERO',        'Vende, cobra y consulta'),
    ('BODEGA',        'Administra inventario y compras'),
    ('TECNICO',       'Atiende el servicio tecnico');
INSERT INTO permisos (codigo, modulo, descripcion) VALUES
    ('ventas.ver', 'ventas', 'Permite ver en ventas'),
    ('ventas.crear', 'ventas', 'Permite crear en ventas'),
    ('ventas.anular', 'ventas', 'Permite anular en ventas'),
    ('inventario.ver', 'inventario', 'Permite ver en inventario'),
    ('inventario.crear', 'inventario', 'Permite crear en inventario'),
    ('inventario.ajustar', 'inventario', 'Permite ajustar en inventario'),
    ('clientes.ver', 'clientes', 'Permite ver en clientes'),
    ('clientes.crear', 'clientes', 'Permite crear en clientes'),
    ('clientes.editar', 'clientes', 'Permite editar en clientes'),
    ('compras.ver', 'compras', 'Permite ver en compras'),
    ('compras.crear', 'compras', 'Permite crear en compras'),
    ('compras.recibir', 'compras', 'Permite recibir en compras'),
    ('caja.abrir', 'caja', 'Permite abrir en caja'),
    ('caja.cerrar', 'caja', 'Permite cerrar en caja'),
    ('caja.movimiento', 'caja', 'Permite movimiento en caja'),
    ('usuarios.ver', 'usuarios', 'Permite ver en usuarios'),
    ('usuarios.crear', 'usuarios', 'Permite crear en usuarios'),
    ('usuarios.editar', 'usuarios', 'Permite editar en usuarios'),
    ('reportes.ver', 'reportes', 'Permite ver en reportes'),
    ('reportes.exportar', 'reportes', 'Permite exportar en reportes'),
    ('garantias.ver', 'garantias', 'Permite ver en garantias'),
    ('garantias.reclamar', 'garantias', 'Permite reclamar en garantias'),
    ('garantias.cerrar', 'garantias', 'Permite cerrar en garantias'),
    ('servicio.ver', 'servicio', 'Permite ver en servicio'),
    ('servicio.crear', 'servicio', 'Permite crear en servicio'),
    ('servicio.cerrar', 'servicio', 'Permite cerrar en servicio'),
    ('configuracion.ver', 'configuracion', 'Permite ver en configuracion'),
    ('configuracion.editar', 'configuracion', 'Permite editar en configuracion');

-- El administrador recibe todos los permisos; los demas roles, los de su funcion
INSERT INTO rol_permisos (rol_id, permiso_id) SELECT 1, id FROM permisos;
INSERT INTO rol_permisos (rol_id, permiso_id) SELECT 2, id FROM permisos
    WHERE modulo IN ('ventas','clientes','caja','garantias') AND codigo <> 'ventas.anular';
INSERT INTO rol_permisos (rol_id, permiso_id) SELECT 3, id FROM permisos
    WHERE modulo IN ('inventario','compras') OR codigo IN ('reportes.ver','clientes.ver');
INSERT INTO rol_permisos (rol_id, permiso_id) SELECT 4, id FROM permisos
    WHERE modulo IN ('servicio','garantias') OR codigo IN ('clientes.ver','inventario.ver');

-- Contrasenas de prueba: admin123, cajero123, bodega123, tecnico123
-- Se guardan como hash PBKDF2-SHA256 con sal aleatoria; la base nunca ve el texto plano.
INSERT INTO usuarios (rol_id, username, nombre_completo, email, password_hash) VALUES
    (1, 'admin', 'Elkin Santiago Marin Duarte', 'admin@posmovil.co', 'pbkdf2_sha256$260000$f2eb6e8452a0c552f28eeae727cb2f0c$5cb3d01cefd2694979d492dd392aedf4715c1dc14f5693ad009d1d6bfabcccb2'),
    (2, 'cajero', 'Juan David Zabala Plata', 'cajero@posmovil.co', 'pbkdf2_sha256$260000$ae42f79bd13e85bc6423158a8fccb6b9$ef7ea0d1104e80f4b4a944b6ae111b0ce031a77c83cad0f1c2f5fb7cd3ce369a'),
    (3, 'bodega', 'Sandra Milena Rojas', 'bodega@posmovil.co', 'pbkdf2_sha256$260000$cd08f41bf7f78ffea76d939fb51e2ecd$359925273e84b0269b6e06ef10da4e3d72bc8d68eae81b7476992fddc7bf639f'),
    (4, 'tecnico', 'Andres Felipe Castro', 'tecnico@posmovil.co', 'pbkdf2_sha256$260000$ee00a7cbb19e3e7d7045ddfc6bda704e$face6a2a0e1dfae9a58c5839f3b2d293728e053c1f87933f4d12df40037fd089');

-- --------------------------------------------------------------------------------------
-- Catalogo
-- --------------------------------------------------------------------------------------
INSERT INTO categorias (nombre, descripcion) VALUES
    ('Smartphones',    'Equipos moviles con control por IMEI'),
    ('Accesorios',     'Cargadores, forros y vidrios'),
    ('Audio',          'Audifonos y parlantes'),
    ('SIM y recargas', 'Lineas nuevas y recargas'),
    ('Repuestos',      'Partes para servicio tecnico');
INSERT INTO categorias (categoria_padre_id, nombre, descripcion) VALUES
    (2, 'Proteccion',  'Forros y vidrios templados'),
    (2, 'Energia',     'Cargadores y baterias externas');

INSERT INTO marcas (nombre, pais_origen) VALUES
    ('Samsung','Corea del Sur'), ('Xiaomi','China'), ('Motorola','Estados Unidos'),
    ('Apple','Estados Unidos'), ('Honor','China'), ('Genericos','Varios');

INSERT INTO proveedores (nit, razon_social, contacto, telefono, email) VALUES
    ('900123456-7','Distribuidora Movil Andina S.A.S.','Carolina Ruiz','3105558877','ventas@movilandina.co'),
    ('901789654-2','Accesorios y Mas Ltda.','Hernan Diaz','3147779900','compras@accesoriosymas.co');

INSERT INTO productos (sku, nombre, descripcion, marca_id, categoria_id, precio_costo, precio_venta, requiere_imei, meses_garantia, stock_actual, stock_minimo) VALUES
    ('SM-A155','Samsung Galaxy A15 128GB','Equipo nuevo, sellado, con garantia de fabrica.',1,1,620000.00,849900.00,TRUE,12,0,2),
    ('XM-RN13','Xiaomi Redmi Note 13 256GB','Equipo nuevo, sellado, con garantia de fabrica.',2,1,680000.00,929900.00,TRUE,12,0,2),
    ('MT-G24','Motorola Moto G24 128GB','Equipo nuevo, sellado, con garantia de fabrica.',3,1,410000.00,599900.00,TRUE,12,0,2),
    ('AP-IP13','Apple iPhone 13 128GB','Equipo nuevo, sellado, con garantia de fabrica.',4,1,2350000.00,2999900.00,TRUE,12,0,1),
    ('HN-X8B','Honor X8b 256GB','Equipo nuevo, sellado, con garantia de fabrica.',5,1,720000.00,999900.00,TRUE,12,0,2),
    ('AC-CAR20','Cargador rapido 20W USB-C',NULL,6,7,18000.00,39900.00,FALSE,3,40,10),
    ('AC-VID01','Vidrio templado universal',NULL,6,6,3500.00,15000.00,FALSE,3,120,20),
    ('AC-FOR01','Forro antichoque',NULL,6,6,6000.00,25000.00,FALSE,3,80,15),
    ('AU-BT500','Audifonos Bluetooth TWS',NULL,6,3,45000.00,89900.00,FALSE,6,25,8),
    ('SM-SIM01','SIM card prepago',NULL,6,4,1000.00,5000.00,FALSE,0,200,50),
    ('RP-PAN15','Pantalla generica compatible',NULL,6,5,85000.00,180000.00,FALSE,3,12,4),
    ('RP-BAT20','Bateria de repuesto',NULL,6,5,30000.00,75000.00,FALSE,3,18,5);

INSERT INTO promociones (nombre, tipo_descuento, valor, fecha_inicio, fecha_fin) VALUES
    ('Combo proteccion',  'VALOR_FIJO',  5000.00, CURRENT_DATE - 10, CURRENT_DATE + 30),
    ('Octubre tecnologia','PORCENTAJE',     10.00, CURRENT_DATE - 5,  CURRENT_DATE + 20);
INSERT INTO promocion_productos (promocion_id, producto_id) VALUES (1,7),(1,8),(2,1),(2,3);

-- --------------------------------------------------------------------------------------
-- Compras y entrada de inventario
-- --------------------------------------------------------------------------------------
INSERT INTO ordenes_compra (proveedor_id, usuario_id, numero, fecha, fecha_recepcion, estado, total) VALUES
    (1, 3, 'OC-2026-0001', CURRENT_DATE - 20, CURRENT_DATE - 18, 'RECIBIDA', 11180000.00),
    (2, 3, 'OC-2026-0002', CURRENT_DATE - 12, CURRENT_DATE - 10, 'RECIBIDA',  2370000.00),
    (1, 3, 'OC-2026-0003', CURRENT_DATE - 2,  NULL,              'ENVIADA',   3720000.00);

INSERT INTO orden_compra_detalles (orden_compra_id, producto_id, cantidad_pedida, cantidad_recibida, costo_unitario) VALUES
    (1, 1, 4, 4,  620000.00), (1, 2, 3, 3,  680000.00), (1, 3, 4, 4,  410000.00),
    (1, 4, 2, 2, 2350000.00), (1, 5, 2, 2,  720000.00),
    (2, 6, 40, 40, 18000.00), (2, 7, 120, 120, 3500.00), (2, 8, 80, 80, 6000.00),
    (2, 9, 25, 25, 45000.00), (2,10, 200, 200, 1000.00),
    (3, 1, 6, 0, 620000.00);

INSERT INTO equipos_imei (producto_id, orden_compra_detalle_id, imei, color, almacenamiento_gb, costo, codigo_rfid) VALUES
    (1, 1, '356789012345011', 'Negro', 128, 620000.00, 'RFID01000'),
    (1, 1, '356789012345029', 'Azul', 128, 620000.00, 'RFID01001'),
    (1, 1, '356789012345037', 'Plata', 128, 620000.00, 'RFID01002'),
    (1, 1, '356789012345045', 'Verde', 128, 620000.00, 'RFID01003'),
    (2, 2, '359123456780110', 'Negro', 256, 680000.00, 'RFID02000'),
    (2, 2, '359123456780128', 'Azul', 256, 680000.00, 'RFID02001'),
    (2, 2, '359123456780136', 'Plata', 256, 680000.00, 'RFID02002'),
    (3, 3, '354555666777011', 'Negro', 128, 410000.00, 'RFID03000'),
    (3, 3, '354555666777029', 'Azul', 128, 410000.00, 'RFID03001'),
    (3, 3, '354555666777037', 'Plata', 128, 410000.00, 'RFID03002'),
    (3, 3, '354555666777045', 'Verde', 128, 410000.00, 'RFID03003'),
    (4, 4, '353333444555013', 'Negro', 128, 2350000.00, 'RFID04000'),
    (4, 4, '353333444555021', 'Azul', 128, 2350000.00, 'RFID04001'),
    (5, 5, '357777888999010', 'Negro', 256, 720000.00, 'RFID05000'),
    (5, 5, '357777888999028', 'Azul', 256, 720000.00, 'RFID05001');

-- Kardex de la carga inicial (las salidas las escribe el trigger al vender)
INSERT INTO movimientos_inventario (producto_id, equipo_imei_id, usuario_id, tipo, cantidad, stock_resultante, motivo, referencia)
    SELECT producto_id, id, 3, 'ENTRADA', 1, 0, 'Ingreso por orden de compra', 'OC-2026-0001' FROM equipos_imei;
INSERT INTO movimientos_inventario (producto_id, usuario_id, tipo, cantidad, stock_resultante, motivo, referencia)
    SELECT id, 3, 'ENTRADA', stock_actual, stock_actual, 'Ingreso por orden de compra', 'OC-2026-0002'
      FROM productos WHERE NOT requiere_imei AND stock_actual > 0;

-- --------------------------------------------------------------------------------------
-- Clientes
-- --------------------------------------------------------------------------------------
INSERT INTO clientes (tipo_documento, numero_documento, nombres, apellidos, telefono, email, direccion, ciudad, autoriza_datos) VALUES
    ('CC','1012345678','Laura','Gomez Rivera','3001234567','laura.gomez@example.com','Calle 45 #12-30','Bogota',TRUE),
    ('CC','79654321','Carlos','Perez Nino','3129876543','carlos.perez@example.com','Carrera 7 #98-15','Bogota',TRUE),
    ('CC','52998877','Diana','Martinez Soto','3201122334','diana.martinez@example.com','Calle 80 #20-11','Bogota',TRUE),
    ('CC','80123456','Miguel','Herrera Lopez','3015566778','miguel.herrera@example.com','Av. Suba #110-25','Bogota',FALSE),
    ('CE','E0456789','Ana','Quispe Mamani','3186677889','ana.quispe@example.com','Calle 13 #50-04','Bogota',TRUE),
    ('NIT','901456789','Papeleria La 80',NULL,'6014567890','compras@papeleria80.co','Av 80 #45-10','Bogota',TRUE);

-- --------------------------------------------------------------------------------------
-- Caja y resolucion de facturacion
-- --------------------------------------------------------------------------------------
INSERT INTO cajas (nombre, ubicacion) VALUES
    ('Caja 1','Mostrador principal'), ('Caja 2','Mostrador servicio tecnico');

INSERT INTO turnos_caja (caja_id, usuario_id, apertura, cierre, base_inicial, efectivo_esperado, efectivo_contado, diferencia, estado) VALUES
    (1, 2, NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days' + INTERVAL '8 hours', 200000.00, 1289812.00, 1289812.00, 0.00, 'CERRADO'),
    (1, 2, NOW() - INTERVAL '2 hours', NULL, 200000.00, NULL, NULL, NULL, 'ABIERTO');

INSERT INTO movimientos_caja (turno_caja_id, tipo, concepto, valor) VALUES
    (1, 'EGRESO',  'Compra de papel para facturas', 25000.00),
    (2, 'INGRESO', 'Base adicional entregada por el administrador', 100000.00);

INSERT INTO resoluciones_dian (numero_resolucion, prefijo, rango_desde, rango_hasta, consecutivo_actual, vigencia_desde, vigencia_hasta) VALUES
    ('18764000012345','FV', 1, 5000, 0, CURRENT_DATE - 60, CURRENT_DATE + 305);

-- --------------------------------------------------------------------------------------
-- Ventas (los triggers descuentan inventario y crean las garantias)
-- --------------------------------------------------------------------------------------
INSERT INTO ventas (cliente_id, usuario_id, turno_caja_id, numero, fecha, subtotal, descuento_total, iva_total, total) VALUES
    (1, 2, 1, 'FV1', NOW() - INTERVAL '3 days', 889800.00, 0.00, 169062.00, 1058862.00),
    (2, 2, 1, 'FV2', NOW() - INTERVAL '3 days', 644900.00, 5000.00, 122531.00, 767431.00),
    (3, 2, 2, 'FV3', NOW() - INTERVAL '2 hours', 929900.00, 0.00, 176681.00, 1106581.00),
    (4, 2, 2, 'FV4', NOW() - INTERVAL '1 hour', 134900.00, 0.00, 25631.00, 160531.00),
    (NULL, 2, 2, 'FV5', NOW() - INTERVAL '30 minutes', 10000.00, 0.00, 1900.00, 11900.00);

INSERT INTO venta_detalles (venta_id, producto_id, equipo_imei_id, cantidad, precio_unitario, descuento, iva_porcentaje, iva_valor, total_linea) VALUES
    (1, 1, 1, 1, 849900, 0.00, 19.00, 161481.00, 1011381.00),
    (1, 6, NULL, 1, 39900, 0.00, 19.00, 7581.00, 47481.00),
    (2, 3, 10, 1, 599900, 0.00, 19.00, 113981.00, 713881.00),
    (2, 8, NULL, 2, 25000, 5000.00, 19.00, 8550.00, 53550.00),
    (3, 2, 5, 1, 929900, 0.00, 19.00, 176681.00, 1106581.00),
    (4, 9, NULL, 1, 89900, 0.00, 19.00, 17081.00, 106981.00),
    (4, 7, NULL, 3, 15000, 0.00, 19.00, 8550.00, 53550.00),
    (5, 10, NULL, 2, 5000, 0.00, 19.00, 1900.00, 11900.00);

INSERT INTO pagos (venta_id, turno_caja_id, metodo, valor, fecha)
    SELECT id, turno_caja_id, 'EFECTIVO', total, fecha FROM ventas;

-- La factura lleva el mismo consecutivo autorizado que la venta
INSERT INTO facturas_electronicas (venta_id, resolucion_id, numero, cufe, fecha_emision, xml_firmado, estado_dian)
    SELECT v.id, 1, v.numero,
           MD5(v.id::TEXT || v.total::TEXT || 'cufe')::VARCHAR || MD5(v.numero)::VARCHAR,
           v.fecha, '<?xml version="1.0"?><Invoice>...</Invoice>', 'ACEPTADA'
      FROM ventas v;

-- El consecutivo de la resolucion queda donde lo dejaron estas ventas
UPDATE resoluciones_dian SET consecutivo_actual = (SELECT COUNT(*) FROM ventas) WHERE id = 1;

-- --------------------------------------------------------------------------------------
-- Apartados, devoluciones, garantias y servicio tecnico
-- --------------------------------------------------------------------------------------
INSERT INTO apartados (cliente_id, equipo_imei_id, fecha, fecha_limite, valor_total, saldo_pendiente) VALUES
    (3, 13, NOW() - INTERVAL '5 days', CURRENT_DATE + 10, 2999900.00, 2999900.00);
INSERT INTO pagos (apartado_id, turno_caja_id, metodo, valor, referencia) VALUES
    (1, 1, 'EFECTIVO', 500000.00, 'Abono inicial'),
    (1, 2, 'NEQUI',    300000.00, 'Abono por Nequi');

INSERT INTO devoluciones (venta_id, usuario_id, fecha, motivo, tipo_reembolso, total) VALUES
    (4, 1, NOW() - INTERVAL '20 minutes', 'El cliente se arrepintio del accesorio', 'NOTA_CREDITO', 106981.00);
INSERT INTO devolucion_detalles (devolucion_id, venta_detalle_id, cantidad, valor, reingresa_inventario)
    SELECT 1, d.id, d.cantidad, d.total_linea, TRUE
      FROM venta_detalles d WHERE d.venta_id = 4 AND d.producto_id = 9;
INSERT INTO notas_credito (factura_id, devolucion_id, numero, cude, valor, estado_dian)
    VALUES (4, 1, 'NC000001', MD5('nc1')::VARCHAR || MD5('nc1b')::VARCHAR, 106981.00, 'ACEPTADA');

-- Una garantia en reclamacion y su orden de servicio
-- La reclamacion vive en la orden de servicio; la garantia solo cambia de estado
UPDATE garantias SET estado = 'EN_RECLAMACION' WHERE venta_detalle_id = 1;
INSERT INTO ordenes_servicio (cliente_id, equipo_imei_id, equipo_externo, garantia_id, tecnico_id, numero,
                              falla_reportada, diagnostico, costo_mano_obra, estado, fecha_ingreso) VALUES
    (1, 1, NULL, 1, 4, 'OS-2026-0001', 'No enciende despues de una actualizacion',
     'Falla de software; se reinstala firmware', 0.00, 'REPARACION', NOW() - INTERVAL '1 day'),
    (2, NULL, 'Samsung Galaxy A34 que el cliente trajo de otro lado', NULL, 4, 'OS-2026-0002',
     'Pantalla rota por caida', 'Cambio de pantalla completa', 60000.00, 'LISTO', NOW() - INTERVAL '4 days');
INSERT INTO orden_servicio_repuestos (orden_servicio_id, producto_id, cantidad, precio_unitario) VALUES
    (2, 11, 1, 180000.00);

-- --------------------------------------------------------------------------------------
-- Activacion de lineas
-- --------------------------------------------------------------------------------------
INSERT INTO operadores (nombre, nit) VALUES
    ('Claro','800153993-7'), ('Movistar','830122566-1'), ('Tigo','830114921-1'), ('WOM','901273315-5');

INSERT INTO planes (operador_id, nombre, modalidad, cargo_mensual, datos_gb, comision) VALUES
    (1,'Claro Max 30GB','POSPAGO', 54900.00, 30.0, 25000.00),
    (1,'Claro Prepago','PREPAGO',       0.00, NULL,  5000.00),
    (2,'Movistar Ilimitado','POSPAGO',69900.00, 50.0, 32000.00),
    (3,'Tigo 20GB','POSPAGO',        44900.00, 20.0, 21000.00),
    (4,'WOM 40GB','POSPAGO',         39900.00, 40.0, 28000.00);

INSERT INTO activaciones_linea (plan_id, cliente_id, venta_id, numero_linea, iccid_sim, tipo, estado, fecha) VALUES
    (1, 1, 1, '3001234567', '8957010000000000001', 'NUEVA',        'ACTIVA',    NOW() - INTERVAL '3 days'),
    (3, 2, 2, '3129876543', '8957010000000000002', 'PORTABILIDAD', 'ACTIVA',    NOW() - INTERVAL '3 days'),
    (5, 3, NULL,'3201122334','8957010000000000003', 'NUEVA',       'PENDIENTE', NOW() - INTERVAL '1 hour');

-- --------------------------------------------------------------------------------------
-- IoT: dispositivos, eventos y alertas
-- --------------------------------------------------------------------------------------
INSERT INTO dispositivos_iot (caja_id, nombre, tipo, direccion_mac, direccion_ip, protocolo, ubicacion) VALUES
    (1, 'Lector de barras caja 1','LECTOR_BARRAS','a4:5e:60:11:22:33','192.168.1.21','WIFI','Mostrador principal'),
    (1, 'Impresora termica caja 1','IMPRESORA_TERMICA','a4:5e:60:11:22:34','192.168.1.22','WIFI','Mostrador principal'),
    (NULL,'Arco RFID puerta','ARCO_RFID','a4:5e:60:11:22:35','192.168.1.23','WIFI','Entrada del local'),
    (NULL,'Sensor de puerta bodega','SENSOR_PUERTA','a4:5e:60:11:22:36',NULL,'ZIGBEE','Bodega'),
    (2, 'Lector RFID servicio','LECTOR_RFID','a4:5e:60:11:22:37','192.168.1.25','BLE','Servicio tecnico');

INSERT INTO eventos_iot (dispositivo_id, equipo_imei_id, tipo_evento, payload, fecha) VALUES
    (3, 1, 'LECTURA_RFID', '{"rssi": -52, "antena": 1, "direccion": "salida"}', NOW() - INTERVAL '3 days'),
    (1, NULL,'ESCANEO_BARRAS','{"codigo": "7701234567890", "producto": "AC-CAR20"}', NOW() - INTERVAL '2 hours'),
    (3, 6, 'LECTURA_RFID', '{"rssi": -61, "antena": 2, "direccion": "salida"}', NOW() - INTERVAL '45 minutes'),
    (4, NULL,'PUERTA_ABIERTA','{"duracion_s": 42}', NOW() - INTERVAL '6 hours'),
    (5, 1, 'LECTURA_RFID', '{"rssi": -48, "antena": 1, "direccion": "ingreso_servicio"}', NOW() - INTERVAL '1 day');

INSERT INTO alertas (evento_iot_id, producto_id, atendida_por, tipo, severidad, mensaje, fecha, fecha_atencion) VALUES
    (3, NULL, NULL, 'SALIDA_NO_AUTORIZADA', 'CRITICA',
     'El arco RFID detecto un equipo sin venta registrada saliendo del local', NOW() - INTERVAL '45 minutes', NULL),
    (NULL, NULL, 1, 'DISPOSITIVO_OFFLINE', 'MEDIA',
     'El sensor de puerta de bodega no reporta desde hace 6 horas', NOW() - INTERVAL '30 minutes', NOW());

-- --------------------------------------------------------------------------------------
-- Cierre: estados derivados
-- --------------------------------------------------------------------------------------
CALL sp_actualizar_garantias_vencidas();
CALL sp_vencer_apartados();

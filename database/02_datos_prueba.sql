-- ==========================================================================
-- Script 2 de 3: datos de prueba
-- Ejecutar despues de 01_schema_postgres.sql
-- Los IMEI incluidos superan la validacion Luhn (digito verificador correcto).
-- ==========================================================================

-- Contrasenas (hash PBKDF2-SHA256 generado por la aplicacion):
--   admin / admin123 | cajero / cajero123 | bodega / bodega123
-- Para regenerar los hashes:  python -m app.seed  desde la carpeta backend.
INSERT INTO usuarios (username, nombre_completo, email, password_hash, rol) VALUES
    ('admin',  'Elkin Santiago Marin Duarte', 'admin@posmovil.co',  'GENERAR_CON_SEED', 'ADMIN'),
    ('cajero', 'Juan David Zabala Plata',     'cajero@posmovil.co', 'GENERAR_CON_SEED', 'CAJERO'),
    ('bodega', 'Operario de Bodega',          'bodega@posmovil.co', 'GENERAR_CON_SEED', 'BODEGA');

INSERT INTO categorias (nombre, descripcion) VALUES
    ('Smartphones',     'Equipos moviles con control por IMEI'),
    ('Accesorios',      'Cargadores, forros, vidrios templados'),
    ('Audio',           'Audifonos y parlantes'),
    ('SIM y recargas',  'Lineas nuevas y recargas');

INSERT INTO marcas (nombre, pais_origen) VALUES
    ('Samsung',   'Corea del Sur'),
    ('Xiaomi',    'China'),
    ('Motorola',  'Estados Unidos'),
    ('Apple',     'Estados Unidos'),
    ('Genericos', 'Varios');

INSERT INTO proveedores (nit, razon_social, contacto, telefono, email) VALUES
    ('900123456-7', 'Distribuidora Movil Andina S.A.S.', 'Carolina Ruiz', '3105558877', 'ventas@movilandina.co');

-- Equipos (serializados por IMEI): stock_actual = 0 por la restriccion del esquema
INSERT INTO productos (sku, nombre, descripcion, marca_id, categoria_id, precio_costo, precio_venta, iva_porcentaje, requiere_imei, meses_garantia, stock_actual, stock_minimo) VALUES
    ('SM-A155', 'Samsung Galaxy A15 128GB',    'Equipo nuevo, sellado, con garantia de fabrica.', 1, 1,  620000.00,  849900.00, 19, TRUE, 12, 0, 2),
    ('XM-RN13', 'Xiaomi Redmi Note 13 256GB',  'Equipo nuevo, sellado, con garantia de fabrica.', 2, 1,  680000.00,  929900.00, 19, TRUE, 12, 0, 2),
    ('MT-G24',  'Motorola Moto G24 128GB',     'Equipo nuevo, sellado, con garantia de fabrica.', 3, 1,  410000.00,  599900.00, 19, TRUE, 12, 0, 2),
    ('AP-IP13', 'Apple iPhone 13 128GB',       'Equipo nuevo, sellado, con garantia de fabrica.', 4, 1, 2350000.00, 2999900.00, 19, TRUE, 12, 0, 2);

-- Accesorios (control por stock agregado)
INSERT INTO productos (sku, nombre, marca_id, categoria_id, precio_costo, precio_venta, iva_porcentaje, requiere_imei, meses_garantia, stock_actual, stock_minimo) VALUES
    ('AC-CAR20',  'Cargador rapido 20W USB-C', 5, 2, 18000.00, 39900.00, 19, FALSE, 3,  40, 10),
    ('AC-VID01',  'Vidrio templado universal', 5, 2,  3500.00, 15000.00, 19, FALSE, 3, 120, 10),
    ('AC-FOR01',  'Forro antichoque',          5, 2,  6000.00, 25000.00, 19, FALSE, 3,  80, 10),
    ('AU-BT500',  'Audifonos Bluetooth TWS',   5, 3, 45000.00, 89900.00, 19, FALSE, 3,  25, 10),
    ('SM-SIM01',  'SIM card prepago',          5, 4,  1000.00,  5000.00, 19, FALSE, 3, 200, 10);

INSERT INTO equipos_imei (producto_id, imei, color, almacenamiento_gb, precio_costo) VALUES
    (1, '356789012345011', 'Negro', 128, 620000),
    (1, '356789012345029', 'Azul', 128, 620000),
    (1, '356789012345037', 'Plata', 128, 620000),
    (1, '356789012345045', 'Verde', 128, 620000),
    (2, '359123456780110', 'Negro', 256, 680000),
    (2, '359123456780128', 'Azul', 256, 680000),
    (2, '359123456780136', 'Plata', 256, 680000),
    (3, '354555666777011', 'Negro', 128, 410000),
    (3, '354555666777029', 'Azul', 128, 410000),
    (3, '354555666777037', 'Plata', 128, 410000),
    (3, '354555666777045', 'Verde', 128, 410000),
    (4, '353333444555013', 'Negro', 128, 2350000),
    (4, '353333444555021', 'Azul', 128, 2350000);

UPDATE equipos_imei SET proveedor_id = 1;

INSERT INTO clientes (tipo_documento, numero_documento, nombres, apellidos, telefono, email, direccion, ciudad) VALUES
    ('CC',  '1012345678', 'Laura',            'Gomez Rivera', '3001234567', 'laura.gomez@example.com',   'Calle 45 #12-30',  'Bogota'),
    ('CC',  '79654321',   'Carlos',           'Perez Nino',   '3129876543', 'carlos.perez@example.com',  'Carrera 7 #98-15', 'Bogota'),
    ('NIT', '901456789',  'Papeleria La 80',  NULL,           '6014567890', 'compras@papeleria80.co',    'Av 80 #45-10',     'Bogota');

-- Movimientos de entrada por la carga inicial del inventario
INSERT INTO movimientos_inventario (producto_id, equipo_imei_id, tipo, cantidad, motivo, usuario_id)
SELECT producto_id, id, 'ENTRADA', 1, 'Carga inicial de inventario', 3 FROM equipos_imei;

INSERT INTO movimientos_inventario (producto_id, tipo, cantidad, stock_resultante, motivo, usuario_id)
SELECT id, 'ENTRADA', stock_actual, stock_actual, 'Carga inicial de inventario', 3
FROM productos WHERE requiere_imei = FALSE;

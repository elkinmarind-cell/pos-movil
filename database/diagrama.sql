-- ==========================================================================
-- Sistema POS para dispositivos moviles — estructura para diagramar
--
-- Solo tipos, tablas, claves primarias, foraneas y unicas. Es el mismo
-- modelo de 01_esquema.sql sin funciones, triggers ni indices parciales,
-- que son los objetos que hacen fallar a los importadores de diagramas.
--
-- Generado con  python gen_dbml.py
-- ==========================================================================

CREATE TYPE accion_auditoria AS ENUM ('INSERT', 'UPDATE', 'DELETE');
CREATE TYPE tipo_descuento AS ENUM ('PORCENTAJE', 'VALOR_FIJO');
CREATE TYPE estado_orden_compra AS ENUM ('BORRADOR', 'ENVIADA', 'RECIBIDA_PARCIAL', 'RECIBIDA', 'ANULADA');
CREATE TYPE estado_imei AS ENUM ('DISPONIBLE', 'APARTADO', 'VENDIDO', 'DEVUELTO', 'EN_SERVICIO', 'DADO_DE_BAJA');
CREATE TYPE tipo_movimiento AS ENUM ('ENTRADA', 'SALIDA', 'AJUSTE', 'DEVOLUCION');
CREATE TYPE tipo_documento AS ENUM ('CC', 'CE', 'TI', 'NIT', 'PASAPORTE');
CREATE TYPE estado_venta AS ENUM ('COMPLETADA', 'ANULADA');
CREATE TYPE metodo_pago AS ENUM ('EFECTIVO', 'DEBITO', 'CREDITO', 'TRANSFERENCIA', 'NEQUI', 'DAVIPLATA');
CREATE TYPE estado_apartado AS ENUM ('VIGENTE', 'COMPLETADO', 'VENCIDO', 'CANCELADO');
CREATE TYPE estado_turno AS ENUM ('ABIERTO', 'CERRADO');
CREATE TYPE tipo_mov_caja AS ENUM ('INGRESO', 'EGRESO');
CREATE TYPE estado_dian AS ENUM ('PENDIENTE', 'ACEPTADA', 'RECHAZADA');
CREATE TYPE tipo_reembolso AS ENUM ('EFECTIVO', 'CAMBIO', 'NOTA_CREDITO');
CREATE TYPE estado_garantia AS ENUM ('VIGENTE', 'VENCIDA', 'EN_RECLAMACION', 'ATENDIDA');
CREATE TYPE estado_servicio AS ENUM ('RECIBIDO', 'DIAGNOSTICO', 'REPARACION', 'LISTO', 'ENTREGADO');
CREATE TYPE modalidad_plan AS ENUM ('PREPAGO', 'POSPAGO');
CREATE TYPE tipo_activacion AS ENUM ('NUEVA', 'PORTABILIDAD', 'REPOSICION');
CREATE TYPE estado_activacion AS ENUM ('PENDIENTE', 'ACTIVA', 'RECHAZADA');
CREATE TYPE tipo_dispositivo AS ENUM ('LECTOR_BARRAS', 'LECTOR_RFID', 'ARCO_RFID', 'SENSOR_PUERTA', 'IMPRESORA_TERMICA');
CREATE TYPE protocolo_iot AS ENUM ('WIFI', 'BLE', 'ZIGBEE', 'MQTT');
CREATE TYPE tipo_alerta AS ENUM ('SALIDA_NO_AUTORIZADA', 'STOCK_BAJO', 'DISPOSITIVO_OFFLINE', 'GARANTIA_POR_VENCER');
CREATE TYPE severidad AS ENUM ('BAJA', 'MEDIA', 'ALTA', 'CRITICA');

-- Caja
CREATE TABLE cajas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(40) NOT NULL UNIQUE,
    ubicacion VARCHAR(80),
    activa BOOLEAN NOT NULL DEFAULT TRUE
);

-- Catalogo
CREATE TABLE categorias (
    id SERIAL PRIMARY KEY,
    categoria_padre_id INTEGER REFERENCES categorias(id) ON DELETE SET NULL,
    nombre VARCHAR(80) NOT NULL UNIQUE,
    descripcion VARCHAR(255)
);

-- Clientes
CREATE TABLE clientes (
    id SERIAL PRIMARY KEY,
    tipo_documento tipo_documento NOT NULL DEFAULT 'CC',
    numero_documento VARCHAR(20) NOT NULL,
    nombres VARCHAR(80) NOT NULL,
    apellidos VARCHAR(80),
    telefono VARCHAR(30),
    email VARCHAR(120),
    direccion VARCHAR(180),
    ciudad VARCHAR(80),
    autoriza_datos BOOLEAN NOT NULL DEFAULT FALSE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tipo_documento, numero_documento)
);

-- Catalogo
CREATE TABLE marcas (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(80) NOT NULL UNIQUE,
    pais_origen VARCHAR(80)
);

-- Activacion de lineas
CREATE TABLE operadores (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(40) NOT NULL UNIQUE,
    nit VARCHAR(20) NOT NULL UNIQUE,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- Seguridad y auditoria
CREATE TABLE permisos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(60) NOT NULL UNIQUE,
    modulo VARCHAR(40) NOT NULL,
    descripcion VARCHAR(200)
);

-- Catalogo
CREATE TABLE promociones (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    tipo_descuento tipo_descuento NOT NULL,
    valor NUMERIC(14,2) NOT NULL DEFAULT 0,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE
);

-- Compras
CREATE TABLE proveedores (
    id SERIAL PRIMARY KEY,
    nit VARCHAR(20) NOT NULL UNIQUE,
    razon_social VARCHAR(150) NOT NULL,
    contacto VARCHAR(120),
    telefono VARCHAR(30),
    email VARCHAR(120),
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- Facturacion electronica DIAN
CREATE TABLE resoluciones_dian (
    id SERIAL PRIMARY KEY,
    numero_resolucion VARCHAR(30) NOT NULL UNIQUE,
    prefijo VARCHAR(10) NOT NULL,
    rango_desde INTEGER NOT NULL,
    rango_hasta INTEGER NOT NULL,
    consecutivo_actual INTEGER NOT NULL DEFAULT 0,
    vigencia_desde DATE NOT NULL,
    vigencia_hasta DATE NOT NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE
);

-- Seguridad y auditoria
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(40) NOT NULL UNIQUE,
    descripcion VARCHAR(200)
);

-- IoT
CREATE TABLE dispositivos_iot (
    id SERIAL PRIMARY KEY,
    caja_id INTEGER REFERENCES cajas(id) ON DELETE SET NULL,
    nombre VARCHAR(80) NOT NULL,
    tipo tipo_dispositivo NOT NULL,
    direccion_mac MACADDR NOT NULL UNIQUE,
    direccion_ip INET,
    protocolo protocolo_iot NOT NULL,
    ubicacion VARCHAR(80) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    ultima_conexion TIMESTAMPTZ
);

-- Activacion de lineas
CREATE TABLE planes (
    id SERIAL PRIMARY KEY,
    operador_id INTEGER NOT NULL REFERENCES operadores(id) ON DELETE RESTRICT,
    nombre VARCHAR(80) NOT NULL,
    modalidad modalidad_plan NOT NULL,
    cargo_mensual NUMERIC(14,2) NOT NULL DEFAULT 0,
    datos_gb NUMERIC(6,1),
    comision NUMERIC(14,2) NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- Catalogo
CREATE TABLE productos (
    id SERIAL PRIMARY KEY,
    categoria_id INTEGER NOT NULL REFERENCES categorias(id) ON DELETE RESTRICT,
    marca_id INTEGER REFERENCES marcas(id) ON DELETE SET NULL,
    sku VARCHAR(40) NOT NULL UNIQUE,
    codigo_barras VARCHAR(20) UNIQUE,
    nombre VARCHAR(150) NOT NULL,
    descripcion TEXT,
    precio_costo NUMERIC(14,2) NOT NULL DEFAULT 0,
    precio_venta NUMERIC(14,2) NOT NULL DEFAULT 0,
    iva_porcentaje NUMERIC(5,2) NOT NULL DEFAULT 19,
    requiere_imei BOOLEAN NOT NULL DEFAULT FALSE,
    meses_garantia SMALLINT NOT NULL DEFAULT 12,
    stock_actual INTEGER NOT NULL DEFAULT 0,
    stock_minimo INTEGER NOT NULL DEFAULT 5,
    activo BOOLEAN NOT NULL DEFAULT TRUE
);

-- Seguridad y auditoria
CREATE TABLE rol_permisos (
    rol_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permiso_id INTEGER NOT NULL REFERENCES permisos(id) ON DELETE RESTRICT,
    PRIMARY KEY (rol_id, permiso_id)
);

-- Seguridad y auditoria
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    rol_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    username VARCHAR(50) NOT NULL UNIQUE,
    nombre_completo VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    ultimo_acceso TIMESTAMPTZ,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Seguridad y auditoria
CREATE TABLE auditoria (
    id BIGSERIAL PRIMARY KEY,
    usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    tabla VARCHAR(60) NOT NULL,
    registro_id BIGINT NOT NULL,
    accion accion_auditoria NOT NULL,
    valores_anteriores JSONB,
    valores_nuevos JSONB,
    direccion_ip INET,
    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Compras
CREATE TABLE ordenes_compra (
    id SERIAL PRIMARY KEY,
    proveedor_id INTEGER NOT NULL REFERENCES proveedores(id) ON DELETE RESTRICT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    numero VARCHAR(20) NOT NULL UNIQUE,
    fecha DATE NOT NULL,
    fecha_recepcion DATE,
    estado estado_orden_compra NOT NULL DEFAULT 'BORRADOR',
    total NUMERIC(14,2) NOT NULL DEFAULT 0
);

-- Catalogo
CREATE TABLE promocion_productos (
    promocion_id INTEGER NOT NULL REFERENCES promociones(id) ON DELETE CASCADE,
    producto_id INTEGER NOT NULL REFERENCES productos(id) ON DELETE RESTRICT,
    PRIMARY KEY (promocion_id, producto_id)
);

-- Caja
CREATE TABLE turnos_caja (
    id SERIAL PRIMARY KEY,
    caja_id INTEGER NOT NULL REFERENCES cajas(id) ON DELETE RESTRICT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    apertura TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cierre TIMESTAMPTZ,
    base_inicial NUMERIC(14,2) NOT NULL DEFAULT 0,
    efectivo_esperado NUMERIC(14,2),
    efectivo_contado NUMERIC(14,2),
    diferencia NUMERIC(14,2),
    estado estado_turno NOT NULL DEFAULT 'ABIERTO'
);

-- Caja
CREATE TABLE movimientos_caja (
    id SERIAL PRIMARY KEY,
    turno_caja_id INTEGER NOT NULL REFERENCES turnos_caja(id) ON DELETE CASCADE,
    tipo tipo_mov_caja NOT NULL,
    concepto VARCHAR(150) NOT NULL,
    valor NUMERIC(14,2) NOT NULL DEFAULT 0,
    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Compras
CREATE TABLE orden_compra_detalles (
    id SERIAL PRIMARY KEY,
    orden_compra_id INTEGER NOT NULL REFERENCES ordenes_compra(id) ON DELETE CASCADE,
    producto_id INTEGER NOT NULL REFERENCES productos(id) ON DELETE RESTRICT,
    cantidad_pedida INTEGER NOT NULL DEFAULT 0,
    cantidad_recibida INTEGER NOT NULL DEFAULT 0,
    costo_unitario NUMERIC(14,2) NOT NULL DEFAULT 0
);

-- Ventas
CREATE TABLE ventas (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER REFERENCES clientes(id) ON DELETE SET NULL,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    turno_caja_id INTEGER NOT NULL REFERENCES turnos_caja(id) ON DELETE RESTRICT,
    numero VARCHAR(20) NOT NULL UNIQUE,
    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    subtotal NUMERIC(14,2) NOT NULL DEFAULT 0,
    descuento_total NUMERIC(14,2) NOT NULL DEFAULT 0,
    iva_total NUMERIC(14,2) NOT NULL DEFAULT 0,
    total NUMERIC(14,2) NOT NULL DEFAULT 0,
    estado estado_venta NOT NULL DEFAULT 'COMPLETADA',
    observaciones TEXT,
    motivo_anulacion VARCHAR(255)
);

-- Activacion de lineas
CREATE TABLE activaciones_linea (
    id SERIAL PRIMARY KEY,
    plan_id INTEGER NOT NULL REFERENCES planes(id) ON DELETE RESTRICT,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE RESTRICT,
    venta_id INTEGER REFERENCES ventas(id) ON DELETE SET NULL,
    numero_linea VARCHAR(10) NOT NULL,
    iccid_sim VARCHAR(22) NOT NULL UNIQUE,
    tipo tipo_activacion NOT NULL,
    estado estado_activacion NOT NULL DEFAULT 'PENDIENTE',
    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Posventa y servicio tecnico
CREATE TABLE devoluciones (
    id SERIAL PRIMARY KEY,
    venta_id INTEGER NOT NULL REFERENCES ventas(id) ON DELETE RESTRICT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    motivo VARCHAR(255) NOT NULL,
    tipo_reembolso tipo_reembolso NOT NULL,
    total NUMERIC(14,2) NOT NULL DEFAULT 0
);

-- Inventario serializado
CREATE TABLE equipos_imei (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER NOT NULL REFERENCES productos(id) ON DELETE RESTRICT,
    orden_compra_detalle_id INTEGER REFERENCES orden_compra_detalles(id) ON DELETE SET NULL,
    imei VARCHAR(15) NOT NULL UNIQUE,
    imei2 VARCHAR(15),
    codigo_rfid VARCHAR(24) UNIQUE,
    color VARCHAR(40),
    almacenamiento_gb SMALLINT,
    costo NUMERIC(14,2) NOT NULL DEFAULT 0,
    estado estado_imei NOT NULL DEFAULT 'DISPONIBLE',
    fecha_ingreso TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Facturacion electronica DIAN
CREATE TABLE facturas_electronicas (
    id SERIAL PRIMARY KEY,
    venta_id INTEGER NOT NULL UNIQUE REFERENCES ventas(id) ON DELETE RESTRICT,
    resolucion_id INTEGER NOT NULL REFERENCES resoluciones_dian(id) ON DELETE RESTRICT,
    numero VARCHAR(20) NOT NULL UNIQUE,
    cufe VARCHAR(96) NOT NULL UNIQUE,
    fecha_emision TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    xml_firmado TEXT NOT NULL,
    estado_dian estado_dian NOT NULL DEFAULT 'PENDIENTE',
    respuesta_dian JSONB
);

-- Ventas
CREATE TABLE apartados (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE RESTRICT,
    equipo_imei_id INTEGER NOT NULL REFERENCES equipos_imei(id) ON DELETE RESTRICT,
    venta_id INTEGER UNIQUE REFERENCES ventas(id) ON DELETE SET NULL,
    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_limite DATE NOT NULL,
    valor_total NUMERIC(14,2) NOT NULL DEFAULT 0,
    saldo_pendiente NUMERIC(14,2) NOT NULL DEFAULT 0,
    estado estado_apartado NOT NULL DEFAULT 'VIGENTE'
);

-- IoT
CREATE TABLE eventos_iot (
    id BIGSERIAL PRIMARY KEY,
    dispositivo_id INTEGER NOT NULL REFERENCES dispositivos_iot(id) ON DELETE CASCADE,
    equipo_imei_id INTEGER REFERENCES equipos_imei(id) ON DELETE SET NULL,
    tipo_evento VARCHAR(40) NOT NULL,
    payload JSONB NOT NULL,
    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Inventario serializado
CREATE TABLE movimientos_inventario (
    id BIGSERIAL PRIMARY KEY,
    producto_id INTEGER NOT NULL REFERENCES productos(id) ON DELETE RESTRICT,
    equipo_imei_id INTEGER REFERENCES equipos_imei(id) ON DELETE SET NULL,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    tipo tipo_movimiento NOT NULL,
    cantidad INTEGER NOT NULL DEFAULT 1,
    stock_resultante INTEGER NOT NULL DEFAULT 0,
    motivo VARCHAR(255),
    referencia VARCHAR(60),
    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Facturacion electronica DIAN
CREATE TABLE notas_credito (
    id SERIAL PRIMARY KEY,
    factura_id INTEGER NOT NULL REFERENCES facturas_electronicas(id) ON DELETE RESTRICT,
    devolucion_id INTEGER NOT NULL UNIQUE REFERENCES devoluciones(id) ON DELETE RESTRICT,
    numero VARCHAR(20) NOT NULL UNIQUE,
    cude VARCHAR(96) NOT NULL UNIQUE,
    valor NUMERIC(14,2) NOT NULL DEFAULT 0,
    fecha_emision TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    estado_dian estado_dian NOT NULL DEFAULT 'PENDIENTE'
);

-- Ventas
CREATE TABLE venta_detalles (
    id SERIAL PRIMARY KEY,
    venta_id INTEGER NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
    producto_id INTEGER NOT NULL REFERENCES productos(id) ON DELETE RESTRICT,
    equipo_imei_id INTEGER REFERENCES equipos_imei(id) ON DELETE SET NULL,
    promocion_id INTEGER REFERENCES promociones(id) ON DELETE SET NULL,
    cantidad INTEGER NOT NULL DEFAULT 1,
    precio_unitario NUMERIC(14,2) NOT NULL DEFAULT 0,
    descuento NUMERIC(14,2) NOT NULL DEFAULT 0,
    iva_porcentaje NUMERIC(5,2) NOT NULL DEFAULT 19,
    iva_valor NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_linea NUMERIC(14,2) NOT NULL DEFAULT 0,
    UNIQUE (venta_id, equipo_imei_id)
);

-- IoT
CREATE TABLE alertas (
    id SERIAL PRIMARY KEY,
    evento_iot_id BIGINT UNIQUE REFERENCES eventos_iot(id) ON DELETE SET NULL,
    producto_id INTEGER REFERENCES productos(id) ON DELETE SET NULL,
    atendida_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    tipo tipo_alerta NOT NULL,
    severidad severidad NOT NULL DEFAULT 'MEDIA',
    mensaje VARCHAR(255) NOT NULL,
    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_atencion TIMESTAMPTZ
);

-- Posventa y servicio tecnico
CREATE TABLE devolucion_detalles (
    id SERIAL PRIMARY KEY,
    devolucion_id INTEGER NOT NULL REFERENCES devoluciones(id) ON DELETE CASCADE,
    venta_detalle_id INTEGER NOT NULL REFERENCES venta_detalles(id) ON DELETE RESTRICT,
    cantidad INTEGER NOT NULL DEFAULT 0,
    valor NUMERIC(14,2) NOT NULL DEFAULT 0,
    reingresa_inventario BOOLEAN NOT NULL DEFAULT TRUE
);

-- Posventa y servicio tecnico
CREATE TABLE garantias (
    id SERIAL PRIMARY KEY,
    venta_detalle_id INTEGER NOT NULL UNIQUE REFERENCES venta_detalles(id) ON DELETE RESTRICT,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    meses SMALLINT NOT NULL DEFAULT 12,
    estado estado_garantia NOT NULL DEFAULT 'VIGENTE'
);

-- Ventas
CREATE TABLE pagos (
    id SERIAL PRIMARY KEY,
    venta_id INTEGER REFERENCES ventas(id) ON DELETE SET NULL,
    apartado_id INTEGER REFERENCES apartados(id) ON DELETE SET NULL,
    turno_caja_id INTEGER NOT NULL REFERENCES turnos_caja(id) ON DELETE RESTRICT,
    metodo metodo_pago NOT NULL,
    valor NUMERIC(14,2) NOT NULL DEFAULT 0,
    referencia VARCHAR(60),
    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Posventa y servicio tecnico
CREATE TABLE ordenes_servicio (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER NOT NULL REFERENCES clientes(id) ON DELETE RESTRICT,
    equipo_imei_id INTEGER REFERENCES equipos_imei(id) ON DELETE SET NULL,
    garantia_id INTEGER REFERENCES garantias(id) ON DELETE SET NULL,
    tecnico_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    numero VARCHAR(20) NOT NULL UNIQUE,
    equipo_externo VARCHAR(150),
    falla_reportada TEXT NOT NULL,
    diagnostico TEXT,
    costo_mano_obra NUMERIC(14,2) NOT NULL DEFAULT 0,
    estado estado_servicio NOT NULL DEFAULT 'RECIBIDO',
    fecha_ingreso TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_entrega TIMESTAMPTZ
);

-- Posventa y servicio tecnico
CREATE TABLE orden_servicio_repuestos (
    id SERIAL PRIMARY KEY,
    orden_servicio_id INTEGER NOT NULL REFERENCES ordenes_servicio(id) ON DELETE CASCADE,
    producto_id INTEGER NOT NULL REFERENCES productos(id) ON DELETE RESTRICT,
    cantidad INTEGER NOT NULL DEFAULT 0,
    precio_unitario NUMERIC(14,2) NOT NULL DEFAULT 0
);

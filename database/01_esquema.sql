-- ========================================================================================
-- Sistema POS para la gestion y venta de dispositivos moviles
-- Script 1 de 3: esquema (DDL)   ·   PostgreSQL 14+
-- Generado desde la misma definicion que produjo el diagrama UML: 37 tablas, 11 modulos.
-- ========================================================================================

DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;

SET client_min_messages = WARNING;

-- ----------------------------------------------------------------------------------------
-- Dominios: tipos enumerados
-- ----------------------------------------------------------------------------------------
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

-- ----------------------------------------------------------------------------------------
-- Modulo: Seguridad y auditoria
-- ----------------------------------------------------------------------------------------
CREATE TABLE roles (
    id            SERIAL PRIMARY KEY,
    nombre        VARCHAR(40) NOT NULL,
    descripcion   VARCHAR(200),
    CONSTRAINT uq_roles_nombre UNIQUE (nombre)
);

CREATE TABLE permisos (
    id            SERIAL PRIMARY KEY,
    codigo        VARCHAR(60) NOT NULL,
    modulo        VARCHAR(40) NOT NULL,
    descripcion   VARCHAR(200),
    CONSTRAINT uq_permisos_codigo UNIQUE (codigo)
);

CREATE TABLE rol_permisos (
    rol_id       INTEGER NOT NULL,
    permiso_id   INTEGER NOT NULL,
    CONSTRAINT pk_rol_permisos PRIMARY KEY (rol_id, permiso_id),
    CONSTRAINT fk_rol_permisos_rol_id FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE CASCADE,
    CONSTRAINT fk_rol_permisos_permiso_id FOREIGN KEY (permiso_id) REFERENCES permisos(id) ON DELETE RESTRICT
);
CREATE INDEX ix_rol_permisos_rol_id ON rol_permisos (rol_id);
CREATE INDEX ix_rol_permisos_permiso_id ON rol_permisos (permiso_id);

CREATE TABLE usuarios (
    id                SERIAL PRIMARY KEY,
    rol_id            INTEGER NOT NULL,
    username          VARCHAR(50) NOT NULL,
    nombre_completo   VARCHAR(120) NOT NULL,
    email             VARCHAR(120) NOT NULL,
    password_hash     VARCHAR(255) NOT NULL,
    activo            BOOLEAN NOT NULL DEFAULT TRUE,
    ultimo_acceso     TIMESTAMPTZ,
    creado_en         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_usuarios_rol_id FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE RESTRICT,
    CONSTRAINT uq_usuarios_username UNIQUE (username),
    CONSTRAINT uq_usuarios_email UNIQUE (email)
);
COMMENT ON TABLE usuarios IS 'Operadores del sistema. La contrasena se guarda como hash PBKDF2-SHA256.';
CREATE INDEX ix_usuarios_rol_id ON usuarios (rol_id);

CREATE TABLE auditoria (
    id                   BIGSERIAL PRIMARY KEY,
    usuario_id           INTEGER,
    tabla                VARCHAR(60) NOT NULL,
    registro_id          BIGINT NOT NULL,
    accion               accion_auditoria NOT NULL,
    valores_anteriores   JSONB,
    valores_nuevos       JSONB,
    direccion_ip         INET,
    fecha                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_auditoria_usuario_id FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
);
COMMENT ON TABLE auditoria IS 'Bitacora append-only de cambios: quien, que, cuando y desde que IP.';
CREATE INDEX ix_auditoria_usuario_id ON auditoria (usuario_id);
CREATE INDEX ix_auditoria_fecha ON auditoria (fecha);
CREATE INDEX ix_auditoria_tabla ON auditoria (tabla);

-- ----------------------------------------------------------------------------------------
-- Modulo: Catalogo
-- ----------------------------------------------------------------------------------------
CREATE TABLE categorias (
    id                   SERIAL PRIMARY KEY,
    categoria_padre_id   INTEGER,
    nombre               VARCHAR(80) NOT NULL,
    descripcion          VARCHAR(255),
    CONSTRAINT fk_categorias_categoria_padre_id FOREIGN KEY (categoria_padre_id) REFERENCES categorias(id) ON DELETE SET NULL,
    CONSTRAINT uq_categorias_nombre UNIQUE (nombre),
    CONSTRAINT ck_categoria_no_self CHECK (categoria_padre_id IS NULL OR categoria_padre_id <> id)
);
CREATE INDEX ix_categorias_categoria_padre_id ON categorias (categoria_padre_id);

CREATE TABLE marcas (
    id            SERIAL PRIMARY KEY,
    nombre        VARCHAR(80) NOT NULL,
    pais_origen   VARCHAR(80),
    CONSTRAINT uq_marcas_nombre UNIQUE (nombre)
);

CREATE TABLE productos (
    id               SERIAL PRIMARY KEY,
    categoria_id     INTEGER NOT NULL,
    marca_id         INTEGER,
    sku              VARCHAR(40) NOT NULL,
    codigo_barras    VARCHAR(20),
    nombre           VARCHAR(150) NOT NULL,
    descripcion      TEXT,
    precio_costo     NUMERIC(14,2) NOT NULL DEFAULT 0,
    precio_venta     NUMERIC(14,2) NOT NULL DEFAULT 0,
    iva_porcentaje   NUMERIC(5,2) NOT NULL DEFAULT 19,
    requiere_imei    BOOLEAN NOT NULL DEFAULT FALSE,
    meses_garantia   SMALLINT NOT NULL DEFAULT 12,
    stock_actual     INTEGER NOT NULL DEFAULT 0,
    stock_minimo     INTEGER NOT NULL DEFAULT 5,
    activo           BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_productos_categoria_id FOREIGN KEY (categoria_id) REFERENCES categorias(id) ON DELETE RESTRICT,
    CONSTRAINT fk_productos_marca_id FOREIGN KEY (marca_id) REFERENCES marcas(id) ON DELETE SET NULL,
    CONSTRAINT uq_productos_sku UNIQUE (sku),
    CONSTRAINT uq_productos_codigo_barras UNIQUE (codigo_barras),
    CONSTRAINT ck_producto_precios CHECK (precio_costo >= 0 AND precio_venta >= 0),
    CONSTRAINT ck_producto_iva CHECK (iva_porcentaje BETWEEN 0 AND 100),
    CONSTRAINT ck_producto_stock CHECK (stock_actual >= 0 AND stock_minimo >= 0),
    CONSTRAINT ck_producto_serializado CHECK (NOT requiere_imei OR stock_actual = 0),
    CONSTRAINT ck_producto_margen CHECK (precio_venta >= precio_costo)
);
COMMENT ON TABLE productos IS 'Modelo comercial. Si requiere_imei el stock se lleva por serie en equipos_imei.';
CREATE INDEX ix_productos_categoria_id ON productos (categoria_id);
CREATE INDEX ix_productos_marca_id ON productos (marca_id);
CREATE INDEX ix_productos_nombre ON productos (nombre);
CREATE INDEX ix_productos_requiere_imei ON productos (requiere_imei);

CREATE TABLE promociones (
    id               SERIAL PRIMARY KEY,
    nombre           VARCHAR(120) NOT NULL,
    tipo_descuento   tipo_descuento NOT NULL,
    valor            NUMERIC(14,2) NOT NULL DEFAULT 0,
    fecha_inicio     DATE NOT NULL,
    fecha_fin        DATE NOT NULL,
    activa           BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT ck_promocion_fechas CHECK (fecha_fin >= fecha_inicio),
    CONSTRAINT ck_promocion_valor CHECK (valor > 0)
);

CREATE TABLE promocion_productos (
    promocion_id   INTEGER NOT NULL,
    producto_id    INTEGER NOT NULL,
    CONSTRAINT pk_promocion_productos PRIMARY KEY (promocion_id, producto_id),
    CONSTRAINT fk_promocion_productos_promocion_id FOREIGN KEY (promocion_id) REFERENCES promociones(id) ON DELETE CASCADE,
    CONSTRAINT fk_promocion_productos_producto_id FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT
);
CREATE INDEX ix_promocion_productos_promocion_id ON promocion_productos (promocion_id);
CREATE INDEX ix_promocion_productos_producto_id ON promocion_productos (producto_id);

-- ----------------------------------------------------------------------------------------
-- Modulo: Compras
-- ----------------------------------------------------------------------------------------
CREATE TABLE proveedores (
    id             SERIAL PRIMARY KEY,
    nit            VARCHAR(20) NOT NULL,
    razon_social   VARCHAR(150) NOT NULL,
    contacto       VARCHAR(120),
    telefono       VARCHAR(30),
    email          VARCHAR(120),
    activo         BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_proveedores_nit UNIQUE (nit)
);

CREATE TABLE ordenes_compra (
    id                SERIAL PRIMARY KEY,
    proveedor_id      INTEGER NOT NULL,
    usuario_id        INTEGER NOT NULL,
    numero            VARCHAR(20) NOT NULL,
    fecha             DATE NOT NULL,
    fecha_recepcion   DATE,
    estado            estado_orden_compra NOT NULL DEFAULT 'BORRADOR',
    total             NUMERIC(14,2) NOT NULL DEFAULT 0,
    CONSTRAINT fk_ordenes_compra_proveedor_id FOREIGN KEY (proveedor_id) REFERENCES proveedores(id) ON DELETE RESTRICT,
    CONSTRAINT fk_ordenes_compra_usuario_id FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    CONSTRAINT uq_ordenes_compra_numero UNIQUE (numero)
);
CREATE INDEX ix_ordenes_compra_proveedor_id ON ordenes_compra (proveedor_id);
CREATE INDEX ix_ordenes_compra_usuario_id ON ordenes_compra (usuario_id);

CREATE TABLE orden_compra_detalles (
    id                  SERIAL PRIMARY KEY,
    orden_compra_id     INTEGER NOT NULL,
    producto_id         INTEGER NOT NULL,
    cantidad_pedida     INTEGER NOT NULL DEFAULT 0,
    cantidad_recibida   INTEGER NOT NULL DEFAULT 0,
    costo_unitario      NUMERIC(14,2) NOT NULL DEFAULT 0,
    CONSTRAINT fk_orden_compra_detalles_orden_compra_id FOREIGN KEY (orden_compra_id) REFERENCES ordenes_compra(id) ON DELETE CASCADE,
    CONSTRAINT fk_orden_compra_detalles_producto_id FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT,
    CONSTRAINT ck_ocd_cantidades CHECK (cantidad_pedida > 0 AND cantidad_recibida >= 0),
    CONSTRAINT ck_ocd_recibida CHECK (cantidad_recibida <= cantidad_pedida)
);
CREATE INDEX ix_orden_compra_detalles_orden_compra_id ON orden_compra_detalles (orden_compra_id);
CREATE INDEX ix_orden_compra_detalles_producto_id ON orden_compra_detalles (producto_id);

-- ----------------------------------------------------------------------------------------
-- Modulo: Inventario serializado
-- ----------------------------------------------------------------------------------------
CREATE TABLE equipos_imei (
    id                        SERIAL PRIMARY KEY,
    producto_id               INTEGER NOT NULL,
    orden_compra_detalle_id   INTEGER,
    imei                      VARCHAR(15) NOT NULL,
    imei2                     VARCHAR(15),
    codigo_rfid               VARCHAR(24),
    color                     VARCHAR(40),
    almacenamiento_gb         SMALLINT,
    costo                     NUMERIC(14,2) NOT NULL DEFAULT 0,
    estado                    estado_imei NOT NULL DEFAULT 'DISPONIBLE',
    fecha_ingreso             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_equipos_imei_producto_id FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT,
    CONSTRAINT fk_equipos_imei_orden_compra_detalle_id FOREIGN KEY (orden_compra_detalle_id) REFERENCES orden_compra_detalles(id) ON DELETE SET NULL,
    CONSTRAINT uq_equipos_imei_imei UNIQUE (imei),
    CONSTRAINT uq_equipos_imei_codigo_rfid UNIQUE (codigo_rfid),
    CONSTRAINT ck_imei_formato CHECK (imei ~ '^[0-9]{15}$'),
    CONSTRAINT ck_imei2_formato CHECK (imei2 IS NULL OR imei2 ~ '^[0-9]{15}$')
);
COMMENT ON TABLE equipos_imei IS 'Unidad fisica trazable. En Colombia el IMEI se reporta a la base positiva de la CRC.';
CREATE INDEX ix_equipos_imei_producto_id ON equipos_imei (producto_id);
CREATE INDEX ix_equipos_imei_orden_compra_detalle_id ON equipos_imei (orden_compra_detalle_id);
CREATE INDEX ix_equipos_imei_estado ON equipos_imei (estado);

CREATE TABLE movimientos_inventario (
    id                 BIGSERIAL PRIMARY KEY,
    producto_id        INTEGER NOT NULL,
    equipo_imei_id     INTEGER,
    usuario_id         INTEGER NOT NULL,
    tipo               tipo_movimiento NOT NULL,
    cantidad           INTEGER NOT NULL DEFAULT 1,
    stock_resultante   INTEGER NOT NULL DEFAULT 0,
    motivo             VARCHAR(255),
    referencia         VARCHAR(60),
    fecha              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_movimientos_inventario_producto_id FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT,
    CONSTRAINT fk_movimientos_inventario_equipo_imei_id FOREIGN KEY (equipo_imei_id) REFERENCES equipos_imei(id) ON DELETE SET NULL,
    CONSTRAINT fk_movimientos_inventario_usuario_id FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    CONSTRAINT ck_movimiento_cantidad CHECK (cantidad > 0)
);
COMMENT ON TABLE movimientos_inventario IS 'Kardex append-only: soporta la auditoria de existencias.';
CREATE INDEX ix_movimientos_inventario_producto_id ON movimientos_inventario (producto_id);
CREATE INDEX ix_movimientos_inventario_equipo_imei_id ON movimientos_inventario (equipo_imei_id);
CREATE INDEX ix_movimientos_inventario_usuario_id ON movimientos_inventario (usuario_id);
CREATE INDEX ix_movimientos_inventario_fecha ON movimientos_inventario (fecha);

-- ----------------------------------------------------------------------------------------
-- Modulo: Clientes
-- ----------------------------------------------------------------------------------------
CREATE TABLE clientes (
    id                 SERIAL PRIMARY KEY,
    tipo_documento     tipo_documento NOT NULL DEFAULT 'CC',
    numero_documento   VARCHAR(20) NOT NULL,
    nombres            VARCHAR(80) NOT NULL,
    apellidos          VARCHAR(80),
    telefono           VARCHAR(30),
    email              VARCHAR(120),
    direccion          VARCHAR(180),
    ciudad             VARCHAR(80),
    autoriza_datos     BOOLEAN NOT NULL DEFAULT FALSE,
    activo             BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_cliente_documento UNIQUE (tipo_documento, numero_documento)
);
COMMENT ON TABLE clientes IS 'autoriza_datos cubre el tratamiento de datos de la Ley 1581 de 2012.';
CREATE INDEX ix_clientes_numero_documento ON clientes (numero_documento);

-- ----------------------------------------------------------------------------------------
-- Modulo: Caja
-- ----------------------------------------------------------------------------------------
CREATE TABLE cajas (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(40) NOT NULL,
    ubicacion   VARCHAR(80),
    activa      BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_cajas_nombre UNIQUE (nombre)
);

CREATE TABLE turnos_caja (
    id                  SERIAL PRIMARY KEY,
    caja_id             INTEGER NOT NULL,
    usuario_id          INTEGER NOT NULL,
    apertura            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cierre              TIMESTAMPTZ,
    base_inicial        NUMERIC(14,2) NOT NULL DEFAULT 0,
    efectivo_esperado   NUMERIC(14,2),
    efectivo_contado    NUMERIC(14,2),
    diferencia          NUMERIC(14,2),
    estado              estado_turno NOT NULL DEFAULT 'ABIERTO',
    CONSTRAINT fk_turnos_caja_caja_id FOREIGN KEY (caja_id) REFERENCES cajas(id) ON DELETE RESTRICT,
    CONSTRAINT fk_turnos_caja_usuario_id FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    CONSTRAINT ck_turno_fechas CHECK (cierre IS NULL OR cierre >= apertura),
    CONSTRAINT ck_turno_base CHECK (base_inicial >= 0)
);
COMMENT ON TABLE turnos_caja IS 'Apertura, cierre y arqueo por caja y cajero.';
CREATE INDEX ix_turnos_caja_caja_id ON turnos_caja (caja_id);
CREATE INDEX ix_turnos_caja_usuario_id ON turnos_caja (usuario_id);

CREATE TABLE movimientos_caja (
    id              SERIAL PRIMARY KEY,
    turno_caja_id   INTEGER NOT NULL,
    tipo            tipo_mov_caja NOT NULL,
    concepto        VARCHAR(150) NOT NULL,
    valor           NUMERIC(14,2) NOT NULL DEFAULT 0,
    fecha           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_movimientos_caja_turno_caja_id FOREIGN KEY (turno_caja_id) REFERENCES turnos_caja(id) ON DELETE CASCADE,
    CONSTRAINT ck_movcaja_valor CHECK (valor > 0)
);
CREATE INDEX ix_movimientos_caja_turno_caja_id ON movimientos_caja (turno_caja_id);

-- ----------------------------------------------------------------------------------------
-- Modulo: Ventas
-- ----------------------------------------------------------------------------------------
CREATE TABLE ventas (
    id                 SERIAL PRIMARY KEY,
    cliente_id         INTEGER,
    usuario_id         INTEGER NOT NULL,
    turno_caja_id      INTEGER NOT NULL,
    numero             VARCHAR(20) NOT NULL,
    fecha              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    subtotal           NUMERIC(14,2) NOT NULL DEFAULT 0,
    descuento_total    NUMERIC(14,2) NOT NULL DEFAULT 0,
    iva_total          NUMERIC(14,2) NOT NULL DEFAULT 0,
    total              NUMERIC(14,2) NOT NULL DEFAULT 0,
    estado             estado_venta NOT NULL DEFAULT 'COMPLETADA',
    observaciones      TEXT,
    motivo_anulacion   VARCHAR(255),
    CONSTRAINT fk_ventas_cliente_id FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL,
    CONSTRAINT fk_ventas_usuario_id FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    CONSTRAINT fk_ventas_turno_caja_id FOREIGN KEY (turno_caja_id) REFERENCES turnos_caja(id) ON DELETE RESTRICT,
    CONSTRAINT uq_ventas_numero UNIQUE (numero),
    CONSTRAINT ck_venta_total CHECK (total = subtotal + iva_total),
    CONSTRAINT ck_venta_anulada CHECK (estado <> 'ANULADA' OR motivo_anulacion IS NOT NULL),
    CONSTRAINT ck_venta_montos CHECK (subtotal >= 0 AND iva_total >= 0 AND descuento_total >= 0)
);
CREATE INDEX ix_ventas_cliente_id ON ventas (cliente_id);
CREATE INDEX ix_ventas_usuario_id ON ventas (usuario_id);
CREATE INDEX ix_ventas_turno_caja_id ON ventas (turno_caja_id);
CREATE INDEX ix_ventas_fecha ON ventas (fecha);
CREATE INDEX ix_ventas_estado ON ventas (estado);

CREATE TABLE venta_detalles (
    id                SERIAL PRIMARY KEY,
    venta_id          INTEGER NOT NULL,
    producto_id       INTEGER NOT NULL,
    equipo_imei_id    INTEGER,
    promocion_id      INTEGER,
    cantidad          INTEGER NOT NULL DEFAULT 1,
    precio_unitario   NUMERIC(14,2) NOT NULL DEFAULT 0,
    descuento         NUMERIC(14,2) NOT NULL DEFAULT 0,
    iva_porcentaje    NUMERIC(5,2) NOT NULL DEFAULT 19,
    iva_valor         NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_linea       NUMERIC(14,2) NOT NULL DEFAULT 0,
    CONSTRAINT fk_venta_detalles_venta_id FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
    CONSTRAINT fk_venta_detalles_producto_id FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT,
    CONSTRAINT fk_venta_detalles_equipo_imei_id FOREIGN KEY (equipo_imei_id) REFERENCES equipos_imei(id) ON DELETE SET NULL,
    CONSTRAINT fk_venta_detalles_promocion_id FOREIGN KEY (promocion_id) REFERENCES promociones(id) ON DELETE SET NULL,
    CONSTRAINT uq_detalle_equipo_venta UNIQUE (venta_id, equipo_imei_id),
    CONSTRAINT ck_detalle_cantidad CHECK (cantidad > 0),
    CONSTRAINT ck_detalle_serializado CHECK (equipo_imei_id IS NULL OR cantidad = 1),
    CONSTRAINT ck_detalle_total CHECK (total_linea = (precio_unitario * cantidad - descuento) + iva_valor),
    CONSTRAINT ck_detalle_descuento CHECK (descuento >= 0)
);
CREATE INDEX ix_venta_detalles_venta_id ON venta_detalles (venta_id);
CREATE INDEX ix_venta_detalles_producto_id ON venta_detalles (producto_id);
CREATE INDEX ix_venta_detalles_equipo_imei_id ON venta_detalles (equipo_imei_id);
CREATE INDEX ix_venta_detalles_promocion_id ON venta_detalles (promocion_id);

CREATE TABLE apartados (
    id                SERIAL PRIMARY KEY,
    cliente_id        INTEGER NOT NULL,
    equipo_imei_id    INTEGER NOT NULL,
    venta_id          INTEGER,
    fecha             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_limite      DATE NOT NULL,
    valor_total       NUMERIC(14,2) NOT NULL DEFAULT 0,
    saldo_pendiente   NUMERIC(14,2) NOT NULL DEFAULT 0,
    estado            estado_apartado NOT NULL DEFAULT 'VIGENTE',
    CONSTRAINT fk_apartados_cliente_id FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE RESTRICT,
    CONSTRAINT fk_apartados_equipo_imei_id FOREIGN KEY (equipo_imei_id) REFERENCES equipos_imei(id) ON DELETE RESTRICT,
    CONSTRAINT uq_apartados_venta_id UNIQUE (venta_id),
    CONSTRAINT fk_apartados_venta_id FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE SET NULL,
    CONSTRAINT ck_apartado_saldo CHECK (saldo_pendiente >= 0 AND saldo_pendiente <= valor_total),
    CONSTRAINT ck_apartado_valor CHECK (valor_total > 0)
);
CREATE INDEX ix_apartados_cliente_id ON apartados (cliente_id);
CREATE INDEX ix_apartados_equipo_imei_id ON apartados (equipo_imei_id);
CREATE INDEX ix_apartados_venta_id ON apartados (venta_id);

CREATE TABLE pagos (
    id              SERIAL PRIMARY KEY,
    venta_id        INTEGER,
    apartado_id     INTEGER,
    turno_caja_id   INTEGER NOT NULL,
    metodo          metodo_pago NOT NULL,
    valor           NUMERIC(14,2) NOT NULL DEFAULT 0,
    referencia      VARCHAR(60),
    fecha           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_pagos_venta_id FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE SET NULL,
    CONSTRAINT fk_pagos_apartado_id FOREIGN KEY (apartado_id) REFERENCES apartados(id) ON DELETE SET NULL,
    CONSTRAINT fk_pagos_turno_caja_id FOREIGN KEY (turno_caja_id) REFERENCES turnos_caja(id) ON DELETE RESTRICT,
    CONSTRAINT ck_pago_origen CHECK ((venta_id IS NOT NULL)::int + (apartado_id IS NOT NULL)::int = 1),
    CONSTRAINT ck_pago_valor CHECK (valor > 0)
);
COMMENT ON TABLE pagos IS 'Un pago pertenece a una venta o al abono de un apartado, nunca a los dos.';
CREATE INDEX ix_pagos_venta_id ON pagos (venta_id);
CREATE INDEX ix_pagos_apartado_id ON pagos (apartado_id);
CREATE INDEX ix_pagos_turno_caja_id ON pagos (turno_caja_id);

-- ----------------------------------------------------------------------------------------
-- Modulo: Posventa y servicio tecnico
-- ----------------------------------------------------------------------------------------
CREATE TABLE devoluciones (
    id               SERIAL PRIMARY KEY,
    venta_id         INTEGER NOT NULL,
    usuario_id       INTEGER NOT NULL,
    fecha            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    motivo           VARCHAR(255) NOT NULL,
    tipo_reembolso   tipo_reembolso NOT NULL,
    total            NUMERIC(14,2) NOT NULL DEFAULT 0,
    CONSTRAINT fk_devoluciones_venta_id FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE RESTRICT,
    CONSTRAINT fk_devoluciones_usuario_id FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE RESTRICT,
    CONSTRAINT ck_devolucion_total CHECK (total >= 0)
);
CREATE INDEX ix_devoluciones_venta_id ON devoluciones (venta_id);
CREATE INDEX ix_devoluciones_usuario_id ON devoluciones (usuario_id);

CREATE TABLE devolucion_detalles (
    id                     SERIAL PRIMARY KEY,
    devolucion_id          INTEGER NOT NULL,
    venta_detalle_id       INTEGER NOT NULL,
    cantidad               INTEGER NOT NULL DEFAULT 0,
    valor                  NUMERIC(14,2) NOT NULL DEFAULT 0,
    reingresa_inventario   BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_devolucion_detalles_devolucion_id FOREIGN KEY (devolucion_id) REFERENCES devoluciones(id) ON DELETE CASCADE,
    CONSTRAINT fk_devolucion_detalles_venta_detalle_id FOREIGN KEY (venta_detalle_id) REFERENCES venta_detalles(id) ON DELETE RESTRICT,
    CONSTRAINT ck_devdet_cantidad CHECK (cantidad > 0)
);
CREATE INDEX ix_devolucion_detalles_devolucion_id ON devolucion_detalles (devolucion_id);
CREATE INDEX ix_devolucion_detalles_venta_detalle_id ON devolucion_detalles (venta_detalle_id);

CREATE TABLE garantias (
    id                 SERIAL PRIMARY KEY,
    venta_detalle_id   INTEGER NOT NULL,
    fecha_inicio       DATE NOT NULL,
    fecha_fin          DATE NOT NULL,
    meses              SMALLINT NOT NULL DEFAULT 12,
    estado             estado_garantia NOT NULL DEFAULT 'VIGENTE',
    CONSTRAINT uq_garantias_venta_detalle_id UNIQUE (venta_detalle_id),
    CONSTRAINT fk_garantias_venta_detalle_id FOREIGN KEY (venta_detalle_id) REFERENCES venta_detalles(id) ON DELETE RESTRICT,
    CONSTRAINT ck_garantia_fechas CHECK (fecha_fin > fecha_inicio),
    CONSTRAINT ck_garantia_meses CHECK (meses > 0)
);
COMMENT ON TABLE garantias IS 'Garantia legal del Estatuto del Consumidor (Ley 1480 de 2011).';
CREATE INDEX ix_garantias_venta_detalle_id ON garantias (venta_detalle_id);
CREATE INDEX ix_garantias_estado ON garantias (estado);
CREATE INDEX ix_garantias_fecha_fin ON garantias (fecha_fin);

CREATE TABLE ordenes_servicio (
    id                SERIAL PRIMARY KEY,
    cliente_id        INTEGER NOT NULL,
    equipo_imei_id    INTEGER,
    garantia_id       INTEGER,
    tecnico_id        INTEGER,
    numero            VARCHAR(20) NOT NULL,
    equipo_externo    VARCHAR(150),
    falla_reportada   TEXT NOT NULL,
    diagnostico       TEXT,
    costo_mano_obra   NUMERIC(14,2) NOT NULL DEFAULT 0,
    estado            estado_servicio NOT NULL DEFAULT 'RECIBIDO',
    fecha_ingreso     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_entrega     TIMESTAMPTZ,
    CONSTRAINT fk_ordenes_servicio_cliente_id FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE RESTRICT,
    CONSTRAINT fk_ordenes_servicio_equipo_imei_id FOREIGN KEY (equipo_imei_id) REFERENCES equipos_imei(id) ON DELETE SET NULL,
    CONSTRAINT fk_ordenes_servicio_garantia_id FOREIGN KEY (garantia_id) REFERENCES garantias(id) ON DELETE SET NULL,
    CONSTRAINT fk_ordenes_servicio_tecnico_id FOREIGN KEY (tecnico_id) REFERENCES usuarios(id) ON DELETE SET NULL,
    CONSTRAINT uq_ordenes_servicio_numero UNIQUE (numero),
    CONSTRAINT ck_os_equipo CHECK (equipo_imei_id IS NOT NULL OR equipo_externo IS NOT NULL),
    CONSTRAINT ck_os_entrega CHECK (fecha_entrega IS NULL OR fecha_entrega >= fecha_ingreso),
    CONSTRAINT ck_os_costo CHECK (costo_mano_obra >= 0)
);
COMMENT ON TABLE ordenes_servicio IS 'Servicio tecnico; si viene de garantia se enlaza con garantia_id.';
CREATE INDEX ix_ordenes_servicio_cliente_id ON ordenes_servicio (cliente_id);
CREATE INDEX ix_ordenes_servicio_equipo_imei_id ON ordenes_servicio (equipo_imei_id);
CREATE INDEX ix_ordenes_servicio_garantia_id ON ordenes_servicio (garantia_id);
CREATE INDEX ix_ordenes_servicio_tecnico_id ON ordenes_servicio (tecnico_id);
CREATE INDEX ix_ordenes_servicio_estado ON ordenes_servicio (estado);

CREATE TABLE orden_servicio_repuestos (
    id                  SERIAL PRIMARY KEY,
    orden_servicio_id   INTEGER NOT NULL,
    producto_id         INTEGER NOT NULL,
    cantidad            INTEGER NOT NULL DEFAULT 0,
    precio_unitario     NUMERIC(14,2) NOT NULL DEFAULT 0,
    CONSTRAINT fk_orden_servicio_repuestos_orden_servicio_id FOREIGN KEY (orden_servicio_id) REFERENCES ordenes_servicio(id) ON DELETE CASCADE,
    CONSTRAINT fk_orden_servicio_repuestos_producto_id FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT,
    CONSTRAINT ck_osr_cantidad CHECK (cantidad > 0)
);
CREATE INDEX ix_orden_servicio_repuestos_orden_servicio_id ON orden_servicio_repuestos (orden_servicio_id);
CREATE INDEX ix_orden_servicio_repuestos_producto_id ON orden_servicio_repuestos (producto_id);

-- ----------------------------------------------------------------------------------------
-- Modulo: Facturacion electronica DIAN
-- ----------------------------------------------------------------------------------------
CREATE TABLE resoluciones_dian (
    id                   SERIAL PRIMARY KEY,
    numero_resolucion    VARCHAR(30) NOT NULL,
    prefijo              VARCHAR(10) NOT NULL,
    rango_desde          INTEGER NOT NULL,
    rango_hasta          INTEGER NOT NULL,
    consecutivo_actual   INTEGER NOT NULL DEFAULT 0,
    vigencia_desde       DATE NOT NULL,
    vigencia_hasta       DATE NOT NULL,
    activa               BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_resoluciones_dian_numero_resolucion UNIQUE (numero_resolucion),
    CONSTRAINT ck_resolucion_rango CHECK (rango_desde <= rango_hasta),
    CONSTRAINT ck_resolucion_consecutivo CHECK (consecutivo_actual BETWEEN rango_desde - 1 AND rango_hasta),
    CONSTRAINT ck_resolucion_vigencia CHECK (vigencia_hasta > vigencia_desde)
);
COMMENT ON TABLE resoluciones_dian IS 'Resolucion de numeracion autorizada por la DIAN.';

CREATE TABLE facturas_electronicas (
    id               SERIAL PRIMARY KEY,
    venta_id         INTEGER NOT NULL,
    resolucion_id    INTEGER NOT NULL,
    numero           VARCHAR(20) NOT NULL,
    cufe             VARCHAR(96) NOT NULL,
    fecha_emision    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    xml_firmado      TEXT NOT NULL,
    estado_dian      estado_dian NOT NULL DEFAULT 'PENDIENTE',
    respuesta_dian   JSONB,
    CONSTRAINT uq_facturas_electronicas_venta_id UNIQUE (venta_id),
    CONSTRAINT fk_facturas_electronicas_venta_id FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE RESTRICT,
    CONSTRAINT fk_facturas_electronicas_resolucion_id FOREIGN KEY (resolucion_id) REFERENCES resoluciones_dian(id) ON DELETE RESTRICT,
    CONSTRAINT uq_facturas_electronicas_numero UNIQUE (numero),
    CONSTRAINT uq_facturas_electronicas_cufe UNIQUE (cufe)
);
COMMENT ON TABLE facturas_electronicas IS 'Factura electronica con CUFE y respuesta de la DIAN.';
CREATE INDEX ix_facturas_electronicas_venta_id ON facturas_electronicas (venta_id);
CREATE INDEX ix_facturas_electronicas_resolucion_id ON facturas_electronicas (resolucion_id);

CREATE TABLE notas_credito (
    id              SERIAL PRIMARY KEY,
    factura_id      INTEGER NOT NULL,
    devolucion_id   INTEGER NOT NULL,
    numero          VARCHAR(20) NOT NULL,
    cude            VARCHAR(96) NOT NULL,
    valor           NUMERIC(14,2) NOT NULL DEFAULT 0,
    fecha_emision   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    estado_dian     estado_dian NOT NULL DEFAULT 'PENDIENTE',
    CONSTRAINT fk_notas_credito_factura_id FOREIGN KEY (factura_id) REFERENCES facturas_electronicas(id) ON DELETE RESTRICT,
    CONSTRAINT uq_notas_credito_devolucion_id UNIQUE (devolucion_id),
    CONSTRAINT fk_notas_credito_devolucion_id FOREIGN KEY (devolucion_id) REFERENCES devoluciones(id) ON DELETE RESTRICT,
    CONSTRAINT uq_notas_credito_numero UNIQUE (numero),
    CONSTRAINT uq_notas_credito_cude UNIQUE (cude),
    CONSTRAINT ck_nota_valor CHECK (valor > 0)
);
CREATE INDEX ix_notas_credito_factura_id ON notas_credito (factura_id);
CREATE INDEX ix_notas_credito_devolucion_id ON notas_credito (devolucion_id);

-- ----------------------------------------------------------------------------------------
-- Modulo: Activacion de lineas
-- ----------------------------------------------------------------------------------------
CREATE TABLE operadores (
    id       SERIAL PRIMARY KEY,
    nombre   VARCHAR(40) NOT NULL,
    nit      VARCHAR(20) NOT NULL,
    activo   BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_operadores_nombre UNIQUE (nombre),
    CONSTRAINT uq_operadores_nit UNIQUE (nit)
);

CREATE TABLE planes (
    id              SERIAL PRIMARY KEY,
    operador_id     INTEGER NOT NULL,
    nombre          VARCHAR(80) NOT NULL,
    modalidad       modalidad_plan NOT NULL,
    cargo_mensual   NUMERIC(14,2) NOT NULL DEFAULT 0,
    datos_gb        NUMERIC(6,1),
    comision        NUMERIC(14,2) NOT NULL DEFAULT 0,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_planes_operador_id FOREIGN KEY (operador_id) REFERENCES operadores(id) ON DELETE RESTRICT,
    CONSTRAINT ck_plan_valores CHECK (cargo_mensual >= 0 AND comision >= 0)
);
CREATE INDEX ix_planes_operador_id ON planes (operador_id);

CREATE TABLE activaciones_linea (
    id             SERIAL PRIMARY KEY,
    plan_id        INTEGER NOT NULL,
    cliente_id     INTEGER NOT NULL,
    venta_id       INTEGER,
    numero_linea   VARCHAR(10) NOT NULL,
    iccid_sim      VARCHAR(22) NOT NULL,
    tipo           tipo_activacion NOT NULL,
    estado         estado_activacion NOT NULL DEFAULT 'PENDIENTE',
    fecha          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_activaciones_linea_plan_id FOREIGN KEY (plan_id) REFERENCES planes(id) ON DELETE RESTRICT,
    CONSTRAINT fk_activaciones_linea_cliente_id FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE RESTRICT,
    CONSTRAINT fk_activaciones_linea_venta_id FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE SET NULL,
    CONSTRAINT uq_activaciones_linea_iccid_sim UNIQUE (iccid_sim),
    CONSTRAINT ck_linea_formato CHECK (numero_linea ~ '^3[0-9]{9}$')
);
CREATE INDEX ix_activaciones_linea_plan_id ON activaciones_linea (plan_id);
CREATE INDEX ix_activaciones_linea_cliente_id ON activaciones_linea (cliente_id);
CREATE INDEX ix_activaciones_linea_venta_id ON activaciones_linea (venta_id);

-- ----------------------------------------------------------------------------------------
-- Modulo: IoT
-- ----------------------------------------------------------------------------------------
CREATE TABLE dispositivos_iot (
    id                SERIAL PRIMARY KEY,
    caja_id           INTEGER,
    nombre            VARCHAR(80) NOT NULL,
    tipo              tipo_dispositivo NOT NULL,
    direccion_mac     MACADDR NOT NULL,
    direccion_ip      INET,
    protocolo         protocolo_iot NOT NULL,
    ubicacion         VARCHAR(80) NOT NULL,
    activo            BOOLEAN NOT NULL DEFAULT TRUE,
    ultima_conexion   TIMESTAMPTZ,
    CONSTRAINT fk_dispositivos_iot_caja_id FOREIGN KEY (caja_id) REFERENCES cajas(id) ON DELETE SET NULL,
    CONSTRAINT uq_dispositivos_iot_direccion_mac UNIQUE (direccion_mac)
);
COMMENT ON TABLE dispositivos_iot IS 'Lectores de codigo de barras, arcos RFID y sensores de la tienda.';
CREATE INDEX ix_dispositivos_iot_caja_id ON dispositivos_iot (caja_id);

CREATE TABLE eventos_iot (
    id               BIGSERIAL PRIMARY KEY,
    dispositivo_id   INTEGER NOT NULL,
    equipo_imei_id   INTEGER,
    tipo_evento      VARCHAR(40) NOT NULL,
    payload          JSONB NOT NULL,
    fecha            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT fk_eventos_iot_dispositivo_id FOREIGN KEY (dispositivo_id) REFERENCES dispositivos_iot(id) ON DELETE CASCADE,
    CONSTRAINT fk_eventos_iot_equipo_imei_id FOREIGN KEY (equipo_imei_id) REFERENCES equipos_imei(id) ON DELETE SET NULL
);
COMMENT ON TABLE eventos_iot IS 'Telemetria cruda de los dispositivos.';
CREATE INDEX ix_eventos_iot_dispositivo_id ON eventos_iot (dispositivo_id);
CREATE INDEX ix_eventos_iot_equipo_imei_id ON eventos_iot (equipo_imei_id);
CREATE INDEX ix_eventos_iot_fecha ON eventos_iot (fecha);

CREATE TABLE alertas (
    id               SERIAL PRIMARY KEY,
    evento_iot_id    BIGINT,
    producto_id      INTEGER,
    atendida_por     INTEGER,
    tipo             tipo_alerta NOT NULL,
    severidad        severidad NOT NULL DEFAULT 'MEDIA',
    mensaje          VARCHAR(255) NOT NULL,
    fecha            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fecha_atencion   TIMESTAMPTZ,
    CONSTRAINT uq_alertas_evento_iot_id UNIQUE (evento_iot_id),
    CONSTRAINT fk_alertas_evento_iot_id FOREIGN KEY (evento_iot_id) REFERENCES eventos_iot(id) ON DELETE SET NULL,
    CONSTRAINT fk_alertas_producto_id FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE SET NULL,
    CONSTRAINT fk_alertas_atendida_por FOREIGN KEY (atendida_por) REFERENCES usuarios(id) ON DELETE SET NULL
);
COMMENT ON TABLE alertas IS 'Alertas operativas derivadas de eventos IoT o de reglas de negocio.';
CREATE INDEX ix_alertas_evento_iot_id ON alertas (evento_iot_id);
CREATE INDEX ix_alertas_producto_id ON alertas (producto_id);
CREATE INDEX ix_alertas_atendida_por ON alertas (atendida_por);
CREATE INDEX ix_alertas_fecha ON alertas (fecha);


-- ==========================================================================
-- Sistema POS para la Gestion y Venta de Dispositivos Moviles
-- Script 1 de 3: creacion del esquema (DDL)
-- Motor: PostgreSQL 14+
-- ==========================================================================

DROP TABLE IF EXISTS garantias CASCADE;
DROP TABLE IF EXISTS venta_detalles CASCADE;
DROP TABLE IF EXISTS ventas CASCADE;
DROP TABLE IF EXISTS movimientos_inventario CASCADE;
DROP TABLE IF EXISTS equipos_imei CASCADE;
DROP TABLE IF EXISTS productos CASCADE;
DROP TABLE IF EXISTS proveedores CASCADE;
DROP TABLE IF EXISTS marcas CASCADE;
DROP TABLE IF EXISTS categorias CASCADE;
DROP TABLE IF EXISTS clientes CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;

DROP TYPE IF EXISTS rol_usuario CASCADE;
DROP TYPE IF EXISTS estado_imei CASCADE;
DROP TYPE IF EXISTS tipo_movimiento CASCADE;
DROP TYPE IF EXISTS estado_venta CASCADE;
DROP TYPE IF EXISTS metodo_pago CASCADE;
DROP TYPE IF EXISTS estado_garantia CASCADE;
DROP TYPE IF EXISTS tipo_documento CASCADE;

-- --------------------------------------------------------------------------
-- Tipos enumerados: el dominio queda restringido en la propia base de datos
-- --------------------------------------------------------------------------
CREATE TYPE rol_usuario      AS ENUM ('ADMIN', 'CAJERO', 'BODEGA');
CREATE TYPE estado_imei      AS ENUM ('DISPONIBLE', 'RESERVADO', 'VENDIDO', 'DEVUELTO', 'EN_GARANTIA', 'DADO_DE_BAJA');
CREATE TYPE tipo_movimiento  AS ENUM ('ENTRADA', 'SALIDA', 'AJUSTE', 'DEVOLUCION');
CREATE TYPE estado_venta     AS ENUM ('COMPLETADA', 'ANULADA');
CREATE TYPE metodo_pago      AS ENUM ('EFECTIVO', 'TARJETA_DEBITO', 'TARJETA_CREDITO', 'TRANSFERENCIA', 'NEQUI', 'DAVIPLATA');
CREATE TYPE estado_garantia  AS ENUM ('VIGENTE', 'VENCIDA', 'EN_RECLAMACION', 'ATENDIDA');
CREATE TYPE tipo_documento   AS ENUM ('CC', 'CE', 'TI', 'NIT', 'PASAPORTE');

-- --------------------------------------------------------------------------
-- Seguridad
-- --------------------------------------------------------------------------
CREATE TABLE usuarios (
    id              SERIAL PRIMARY KEY,
    username        VARCHAR(50)  NOT NULL UNIQUE,
    nombre_completo VARCHAR(120) NOT NULL,
    email           VARCHAR(120) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    rol             rol_usuario  NOT NULL DEFAULT 'CAJERO',
    activo          BOOLEAN      NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
COMMENT ON TABLE usuarios IS 'Operadores del sistema. La contrasena se guarda como hash PBKDF2-SHA256, nunca en texto plano.';

-- --------------------------------------------------------------------------
-- Catalogo
-- --------------------------------------------------------------------------
CREATE TABLE categorias (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(80) NOT NULL UNIQUE,
    descripcion VARCHAR(255)
);

CREATE TABLE marcas (
    id           SERIAL PRIMARY KEY,
    nombre       VARCHAR(80) NOT NULL UNIQUE,
    pais_origen  VARCHAR(80)
);

CREATE TABLE proveedores (
    id           SERIAL PRIMARY KEY,
    nit          VARCHAR(30)  NOT NULL UNIQUE,
    razon_social VARCHAR(150) NOT NULL,
    contacto     VARCHAR(120),
    telefono     VARCHAR(30),
    email        VARCHAR(120),
    activo       BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE productos (
    id              SERIAL PRIMARY KEY,
    sku             VARCHAR(40)  NOT NULL UNIQUE,
    nombre          VARCHAR(150) NOT NULL,
    descripcion     TEXT,
    marca_id        INTEGER REFERENCES marcas(id)     ON DELETE SET NULL,
    categoria_id    INTEGER REFERENCES categorias(id) ON DELETE SET NULL,
    precio_costo    NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (precio_costo  >= 0),
    precio_venta    NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (precio_venta  >= 0),
    iva_porcentaje  NUMERIC(5,2)  NOT NULL DEFAULT 19 CHECK (iva_porcentaje BETWEEN 0 AND 100),
    requiere_imei   BOOLEAN NOT NULL DEFAULT FALSE,
    meses_garantia  INTEGER NOT NULL DEFAULT 12 CHECK (meses_garantia >= 0),
    stock_actual    INTEGER NOT NULL DEFAULT 0 CHECK (stock_actual >= 0),
    stock_minimo    INTEGER NOT NULL DEFAULT 5 CHECK (stock_minimo >= 0),
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- Un producto serializado no lleva stock agregado: su existencia son los IMEI
    CONSTRAINT ck_producto_stock_serializado
        CHECK (NOT requiere_imei OR stock_actual = 0)
);
CREATE INDEX idx_productos_nombre    ON productos (nombre);
CREATE INDEX idx_productos_categoria ON productos (categoria_id);
COMMENT ON COLUMN productos.stock_actual IS 'Solo aplica a productos NO serializados (accesorios). Los equipos se cuentan en equipos_imei.';

CREATE TABLE equipos_imei (
    id                SERIAL PRIMARY KEY,
    imei              VARCHAR(15) NOT NULL UNIQUE,
    imei2             VARCHAR(15),
    producto_id       INTEGER NOT NULL REFERENCES productos(id)   ON DELETE RESTRICT,
    proveedor_id      INTEGER          REFERENCES proveedores(id) ON DELETE SET NULL,
    color             VARCHAR(40),
    almacenamiento_gb INTEGER CHECK (almacenamiento_gb > 0),
    precio_costo      NUMERIC(14,2) NOT NULL DEFAULT 0,
    estado            estado_imei   NOT NULL DEFAULT 'DISPONIBLE',
    fecha_ingreso     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    observaciones     TEXT,
    CONSTRAINT ck_imei_longitud CHECK (imei ~ '^[0-9]{15}$')
);
CREATE INDEX idx_imei_estado   ON equipos_imei (estado);
CREATE INDEX idx_imei_producto ON equipos_imei (producto_id);
COMMENT ON TABLE equipos_imei IS 'Trazabilidad unitaria. En Colombia el IMEI debe reportarse a la base positiva de la CRC.';

CREATE TABLE movimientos_inventario (
    id               SERIAL PRIMARY KEY,
    producto_id      INTEGER NOT NULL REFERENCES productos(id)    ON DELETE RESTRICT,
    equipo_imei_id   INTEGER          REFERENCES equipos_imei(id) ON DELETE SET NULL,
    tipo             tipo_movimiento NOT NULL,
    cantidad         INTEGER NOT NULL CHECK (cantidad > 0),
    stock_resultante INTEGER,
    motivo           VARCHAR(255),
    referencia       VARCHAR(60),
    usuario_id       INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    fecha            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_movimientos_producto ON movimientos_inventario (producto_id);
CREATE INDEX idx_movimientos_fecha    ON movimientos_inventario (fecha);
COMMENT ON TABLE movimientos_inventario IS 'Kardex append-only: soporta la auditoria de existencias.';

-- --------------------------------------------------------------------------
-- Clientes y ventas
-- --------------------------------------------------------------------------
CREATE TABLE clientes (
    id               SERIAL PRIMARY KEY,
    tipo_documento   tipo_documento NOT NULL DEFAULT 'CC',
    numero_documento VARCHAR(20) NOT NULL,
    nombres          VARCHAR(80) NOT NULL,
    apellidos        VARCHAR(80),
    telefono         VARCHAR(30),
    email            VARCHAR(120),
    direccion        VARCHAR(180),
    ciudad           VARCHAR(80) DEFAULT 'Bogota',
    activo           BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_cliente_documento UNIQUE (tipo_documento, numero_documento)
);
CREATE INDEX idx_clientes_documento ON clientes (numero_documento);

CREATE TABLE ventas (
    id               SERIAL PRIMARY KEY,
    numero_factura   VARCHAR(30) NOT NULL UNIQUE,
    cliente_id       INTEGER          REFERENCES clientes(id) ON DELETE SET NULL,
    usuario_id       INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    fecha            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    subtotal         NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
    descuento_total  NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (descuento_total >= 0),
    iva_total        NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (iva_total >= 0),
    total            NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (total >= 0),
    metodo_pago      metodo_pago  NOT NULL DEFAULT 'EFECTIVO',
    estado           estado_venta NOT NULL DEFAULT 'COMPLETADA',
    observaciones    TEXT,
    motivo_anulacion VARCHAR(255),
    CONSTRAINT ck_venta_anulada_con_motivo
        CHECK (estado <> 'ANULADA' OR motivo_anulacion IS NOT NULL)
);
CREATE INDEX idx_ventas_fecha  ON ventas (fecha);
CREATE INDEX idx_ventas_estado ON ventas (estado);

CREATE TABLE venta_detalles (
    id              SERIAL PRIMARY KEY,
    venta_id        INTEGER NOT NULL REFERENCES ventas(id)       ON DELETE CASCADE,
    producto_id     INTEGER NOT NULL REFERENCES productos(id)    ON DELETE RESTRICT,
    equipo_imei_id  INTEGER          REFERENCES equipos_imei(id) ON DELETE SET NULL,
    descripcion     VARCHAR(180) NOT NULL,
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(14,2) NOT NULL CHECK (precio_unitario >= 0),
    descuento       NUMERIC(14,2) NOT NULL DEFAULT 0 CHECK (descuento >= 0),
    iva_porcentaje  NUMERIC(5,2)  NOT NULL DEFAULT 19,
    base_gravable   NUMERIC(14,2) NOT NULL DEFAULT 0,
    iva_valor       NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_linea     NUMERIC(14,2) NOT NULL DEFAULT 0,
    -- Un equipo serializado se vende de a una unidad por linea
    CONSTRAINT ck_detalle_serializado CHECK (equipo_imei_id IS NULL OR cantidad = 1),
    CONSTRAINT uq_detalle_equipo UNIQUE (equipo_imei_id, venta_id)
);
CREATE INDEX idx_detalles_venta    ON venta_detalles (venta_id);
CREATE INDEX idx_detalles_producto ON venta_detalles (producto_id);

CREATE TABLE garantias (
    id                SERIAL PRIMARY KEY,
    venta_detalle_id  INTEGER NOT NULL UNIQUE REFERENCES venta_detalles(id) ON DELETE CASCADE,
    cliente_id        INTEGER REFERENCES clientes(id)     ON DELETE SET NULL,
    equipo_imei_id    INTEGER REFERENCES equipos_imei(id) ON DELETE SET NULL,
    fecha_inicio      DATE NOT NULL,
    fecha_fin         DATE NOT NULL,
    meses             INTEGER NOT NULL DEFAULT 12 CHECK (meses > 0),
    estado            estado_garantia NOT NULL DEFAULT 'VIGENTE',
    descripcion_falla TEXT,
    fecha_reclamacion DATE,
    solucion          TEXT,
    CONSTRAINT ck_garantia_fechas CHECK (fecha_fin > fecha_inicio)
);
CREATE INDEX idx_garantias_estado ON garantias (estado);
CREATE INDEX idx_garantias_fin    ON garantias (fecha_fin);
COMMENT ON TABLE garantias IS 'Estatuto del Consumidor (Ley 1480 de 2011): la garantia legal minima debe quedar registrada.';

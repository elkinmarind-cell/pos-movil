"""Modelo ORM del POS. Generado desde la misma definicion que el DDL:
si el esquema cambia, este archivo se regenera y la prueba de consistencia lo verifica."""
from __future__ import annotations

import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (BigInteger, Boolean, Date, DateTime, Enum, ForeignKey, Integer,
                        Numeric, SmallInteger, String, Text)
from sqlalchemy.dialects.postgresql import INET, JSONB, MACADDR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import FetchedValue

from .database import Base


# --------------------------------------------------------------------------------------
# Dominios (deben coincidir con los tipos ENUM de PostgreSQL)
# --------------------------------------------------------------------------------------
class AccionAuditoria(str, enum.Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"

class TipoDescuento(str, enum.Enum):
    PORCENTAJE = "PORCENTAJE"
    VALOR_FIJO = "VALOR_FIJO"

class EstadoOrdenCompra(str, enum.Enum):
    BORRADOR = "BORRADOR"
    ENVIADA = "ENVIADA"
    RECIBIDA_PARCIAL = "RECIBIDA_PARCIAL"
    RECIBIDA = "RECIBIDA"
    ANULADA = "ANULADA"

class EstadoImei(str, enum.Enum):
    DISPONIBLE = "DISPONIBLE"
    APARTADO = "APARTADO"
    VENDIDO = "VENDIDO"
    DEVUELTO = "DEVUELTO"
    EN_SERVICIO = "EN_SERVICIO"
    DADO_DE_BAJA = "DADO_DE_BAJA"

class TipoMovimiento(str, enum.Enum):
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"
    AJUSTE = "AJUSTE"
    DEVOLUCION = "DEVOLUCION"

class TipoDocumento(str, enum.Enum):
    CC = "CC"
    CE = "CE"
    TI = "TI"
    NIT = "NIT"
    PASAPORTE = "PASAPORTE"

class EstadoVenta(str, enum.Enum):
    COMPLETADA = "COMPLETADA"
    ANULADA = "ANULADA"

class MetodoPago(str, enum.Enum):
    EFECTIVO = "EFECTIVO"
    DEBITO = "DEBITO"
    CREDITO = "CREDITO"
    TRANSFERENCIA = "TRANSFERENCIA"
    NEQUI = "NEQUI"
    DAVIPLATA = "DAVIPLATA"

class EstadoApartado(str, enum.Enum):
    VIGENTE = "VIGENTE"
    COMPLETADO = "COMPLETADO"
    VENCIDO = "VENCIDO"
    CANCELADO = "CANCELADO"

class EstadoTurno(str, enum.Enum):
    ABIERTO = "ABIERTO"
    CERRADO = "CERRADO"

class TipoMovCaja(str, enum.Enum):
    INGRESO = "INGRESO"
    EGRESO = "EGRESO"

class EstadoDian(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    ACEPTADA = "ACEPTADA"
    RECHAZADA = "RECHAZADA"

class TipoReembolso(str, enum.Enum):
    EFECTIVO = "EFECTIVO"
    CAMBIO = "CAMBIO"
    NOTA_CREDITO = "NOTA_CREDITO"

class EstadoGarantia(str, enum.Enum):
    VIGENTE = "VIGENTE"
    VENCIDA = "VENCIDA"
    EN_RECLAMACION = "EN_RECLAMACION"
    ATENDIDA = "ATENDIDA"

class EstadoServicio(str, enum.Enum):
    RECIBIDO = "RECIBIDO"
    DIAGNOSTICO = "DIAGNOSTICO"
    REPARACION = "REPARACION"
    LISTO = "LISTO"
    ENTREGADO = "ENTREGADO"

class ModalidadPlan(str, enum.Enum):
    PREPAGO = "PREPAGO"
    POSPAGO = "POSPAGO"

class TipoActivacion(str, enum.Enum):
    NUEVA = "NUEVA"
    PORTABILIDAD = "PORTABILIDAD"
    REPOSICION = "REPOSICION"

class EstadoActivacion(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    ACTIVA = "ACTIVA"
    RECHAZADA = "RECHAZADA"

class TipoDispositivo(str, enum.Enum):
    LECTOR_BARRAS = "LECTOR_BARRAS"
    LECTOR_RFID = "LECTOR_RFID"
    ARCO_RFID = "ARCO_RFID"
    SENSOR_PUERTA = "SENSOR_PUERTA"
    IMPRESORA_TERMICA = "IMPRESORA_TERMICA"

class ProtocoloIot(str, enum.Enum):
    WIFI = "WIFI"
    BLE = "BLE"
    ZIGBEE = "ZIGBEE"
    MQTT = "MQTT"

class TipoAlerta(str, enum.Enum):
    SALIDA_NO_AUTORIZADA = "SALIDA_NO_AUTORIZADA"
    STOCK_BAJO = "STOCK_BAJO"
    DISPOSITIVO_OFFLINE = "DISPOSITIVO_OFFLINE"
    GARANTIA_POR_VENCER = "GARANTIA_POR_VENCER"

class Severidad(str, enum.Enum):
    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    CRITICA = "CRITICA"


# --------------------------------------------------------------------------------------
# Tablas
# --------------------------------------------------------------------------------------
class Rol(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(40))
    descripcion: Mapped[str | None] = mapped_column(String(200), nullable=True)
    permisos_asignados: Mapped[list["RolPermiso"]] = relationship(foreign_keys="RolPermiso.rol_id", back_populates="rol", cascade="all, delete-orphan")


class Permiso(Base):
    __tablename__ = "permisos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    codigo: Mapped[str] = mapped_column(String(60))
    modulo: Mapped[str] = mapped_column(String(40))
    descripcion: Mapped[str | None] = mapped_column(String(200), nullable=True)


class RolPermiso(Base):
    __tablename__ = "rol_permisos"

    rol_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"), primary_key=True)
    permiso_id: Mapped[int] = mapped_column(Integer, ForeignKey("permisos.id"), primary_key=True)
    rol: Mapped["Rol"] = relationship(foreign_keys=[rol_id], back_populates="permisos_asignados")
    permiso: Mapped["Permiso"] = relationship(foreign_keys=[permiso_id])


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rol_id: Mapped[int] = mapped_column(Integer, ForeignKey("roles.id"))
    username: Mapped[str] = mapped_column(String(50))
    nombre_completo: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    activo: Mapped[bool] = mapped_column(Boolean, server_default=FetchedValue())
    ultimo_acceso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=FetchedValue())
    rol: Mapped["Rol"] = relationship(foreign_keys=[rol_id])


class Auditoria(Base):
    __tablename__ = "auditoria"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    usuario_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    tabla: Mapped[str] = mapped_column(String(60))
    registro_id: Mapped[int] = mapped_column(BigInteger)
    accion: Mapped[AccionAuditoria] = mapped_column(Enum(AccionAuditoria, name="accion_auditoria"))
    valores_anteriores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    valores_nuevos: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    direccion_ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=FetchedValue())
    usuario: Mapped["Usuario | None"] = relationship(foreign_keys=[usuario_id])


class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    categoria_padre_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("categorias.id"), nullable=True)
    nombre: Mapped[str] = mapped_column(String(80))
    descripcion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    categoria_padre: Mapped["Categoria | None"] = relationship(foreign_keys=[categoria_padre_id])


class Marca(Base):
    __tablename__ = "marcas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80))
    pais_origen: Mapped[str | None] = mapped_column(String(80), nullable=True)


class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    categoria_id: Mapped[int] = mapped_column(Integer, ForeignKey("categorias.id"))
    marca_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("marcas.id"), nullable=True)
    sku: Mapped[str] = mapped_column(String(40))
    codigo_barras: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nombre: Mapped[str] = mapped_column(String(150))
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    precio_costo: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    precio_venta: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    iva_porcentaje: Mapped[Decimal] = mapped_column(Numeric(5, 2), server_default=FetchedValue())
    requiere_imei: Mapped[bool] = mapped_column(Boolean, server_default=FetchedValue())
    meses_garantia: Mapped[int] = mapped_column(SmallInteger, server_default=FetchedValue())
    stock_actual: Mapped[int] = mapped_column(Integer, server_default=FetchedValue())
    stock_minimo: Mapped[int] = mapped_column(Integer, server_default=FetchedValue())
    activo: Mapped[bool] = mapped_column(Boolean, server_default=FetchedValue())
    categoria: Mapped["Categoria"] = relationship(foreign_keys=[categoria_id])
    marca: Mapped["Marca | None"] = relationship(foreign_keys=[marca_id])
    equipos: Mapped[list["EquipoImei"]] = relationship(foreign_keys="EquipoImei.producto_id", back_populates="producto", cascade="all, delete-orphan")


class Promocion(Base):
    __tablename__ = "promociones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120))
    tipo_descuento: Mapped[TipoDescuento] = mapped_column(Enum(TipoDescuento, name="tipo_descuento"))
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date] = mapped_column(Date)
    activa: Mapped[bool] = mapped_column(Boolean, server_default=FetchedValue())


class PromocionProducto(Base):
    __tablename__ = "promocion_productos"

    promocion_id: Mapped[int] = mapped_column(Integer, ForeignKey("promociones.id"), primary_key=True)
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey("productos.id"), primary_key=True)
    promocion: Mapped["Promocion"] = relationship(foreign_keys=[promocion_id])
    producto: Mapped["Producto"] = relationship(foreign_keys=[producto_id])


class Proveedor(Base):
    __tablename__ = "proveedores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nit: Mapped[str] = mapped_column(String(20))
    razon_social: Mapped[str] = mapped_column(String(150))
    contacto: Mapped[str | None] = mapped_column(String(120), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, server_default=FetchedValue())


class OrdenCompra(Base):
    __tablename__ = "ordenes_compra"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proveedor_id: Mapped[int] = mapped_column(Integer, ForeignKey("proveedores.id"))
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"))
    numero: Mapped[str] = mapped_column(String(20))
    fecha: Mapped[date] = mapped_column(Date)
    fecha_recepcion: Mapped[date | None] = mapped_column(Date, nullable=True)
    estado: Mapped[EstadoOrdenCompra] = mapped_column(Enum(EstadoOrdenCompra, name="estado_orden_compra"), server_default=FetchedValue())
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    proveedor: Mapped["Proveedor"] = relationship(foreign_keys=[proveedor_id])
    usuario: Mapped["Usuario"] = relationship(foreign_keys=[usuario_id])
    detalles: Mapped[list["OrdenCompraDetalle"]] = relationship(foreign_keys="OrdenCompraDetalle.orden_compra_id", back_populates="orden_compra", cascade="all, delete-orphan")


class OrdenCompraDetalle(Base):
    __tablename__ = "orden_compra_detalles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    orden_compra_id: Mapped[int] = mapped_column(Integer, ForeignKey("ordenes_compra.id"))
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey("productos.id"))
    cantidad_pedida: Mapped[int] = mapped_column(Integer, server_default=FetchedValue())
    cantidad_recibida: Mapped[int] = mapped_column(Integer, server_default=FetchedValue())
    costo_unitario: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    orden_compra: Mapped["OrdenCompra"] = relationship(foreign_keys=[orden_compra_id], back_populates="detalles")
    producto: Mapped["Producto"] = relationship(foreign_keys=[producto_id])


class EquipoImei(Base):
    __tablename__ = "equipos_imei"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey("productos.id"))
    orden_compra_detalle_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("orden_compra_detalles.id"), nullable=True)
    imei: Mapped[str] = mapped_column(String(15))
    imei2: Mapped[str | None] = mapped_column(String(15), nullable=True)
    codigo_rfid: Mapped[str | None] = mapped_column(String(24), nullable=True)
    color: Mapped[str | None] = mapped_column(String(40), nullable=True)
    almacenamiento_gb: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    costo: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    estado: Mapped[EstadoImei] = mapped_column(Enum(EstadoImei, name="estado_imei"), server_default=FetchedValue())
    fecha_ingreso: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=FetchedValue())
    producto: Mapped["Producto"] = relationship(foreign_keys=[producto_id], back_populates="equipos")
    orden_compra_detalle: Mapped["OrdenCompraDetalle | None"] = relationship(foreign_keys=[orden_compra_detalle_id])


class MovimientoInventario(Base):
    __tablename__ = "movimientos_inventario"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey("productos.id"))
    equipo_imei_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("equipos_imei.id"), nullable=True)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"))
    tipo: Mapped[TipoMovimiento] = mapped_column(Enum(TipoMovimiento, name="tipo_movimiento"))
    cantidad: Mapped[int] = mapped_column(Integer, server_default=FetchedValue())
    stock_resultante: Mapped[int] = mapped_column(Integer, server_default=FetchedValue())
    motivo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    referencia: Mapped[str | None] = mapped_column(String(60), nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=FetchedValue())
    producto: Mapped["Producto"] = relationship(foreign_keys=[producto_id])
    equipo_imei: Mapped["EquipoImei | None"] = relationship(foreign_keys=[equipo_imei_id])
    usuario: Mapped["Usuario"] = relationship(foreign_keys=[usuario_id])


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo_documento: Mapped[TipoDocumento] = mapped_column(Enum(TipoDocumento, name="tipo_documento"), server_default=FetchedValue())
    numero_documento: Mapped[str] = mapped_column(String(20))
    nombres: Mapped[str] = mapped_column(String(80))
    apellidos: Mapped[str | None] = mapped_column(String(80), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    direccion: Mapped[str | None] = mapped_column(String(180), nullable=True)
    ciudad: Mapped[str | None] = mapped_column(String(80), nullable=True)
    autoriza_datos: Mapped[bool] = mapped_column(Boolean, server_default=FetchedValue())
    activo: Mapped[bool] = mapped_column(Boolean, server_default=FetchedValue())
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=FetchedValue())


class Caja(Base):
    __tablename__ = "cajas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(40))
    ubicacion: Mapped[str | None] = mapped_column(String(80), nullable=True)
    activa: Mapped[bool] = mapped_column(Boolean, server_default=FetchedValue())


class TurnoCaja(Base):
    __tablename__ = "turnos_caja"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    caja_id: Mapped[int] = mapped_column(Integer, ForeignKey("cajas.id"))
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"))
    apertura: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=FetchedValue())
    cierre: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    base_inicial: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    efectivo_esperado: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    efectivo_contado: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    diferencia: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    estado: Mapped[EstadoTurno] = mapped_column(Enum(EstadoTurno, name="estado_turno"), server_default=FetchedValue())
    caja: Mapped["Caja"] = relationship(foreign_keys=[caja_id])
    usuario: Mapped["Usuario"] = relationship(foreign_keys=[usuario_id])
    movimientos: Mapped[list["MovimientoCaja"]] = relationship(foreign_keys="MovimientoCaja.turno_caja_id", back_populates="turno_caja", cascade="all, delete-orphan")


class MovimientoCaja(Base):
    __tablename__ = "movimientos_caja"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    turno_caja_id: Mapped[int] = mapped_column(Integer, ForeignKey("turnos_caja.id"))
    tipo: Mapped[TipoMovCaja] = mapped_column(Enum(TipoMovCaja, name="tipo_mov_caja"))
    concepto: Mapped[str] = mapped_column(String(150))
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=FetchedValue())
    turno_caja: Mapped["TurnoCaja"] = relationship(foreign_keys=[turno_caja_id], back_populates="movimientos")


class Venta(Base):
    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("clientes.id"), nullable=True)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"))
    turno_caja_id: Mapped[int] = mapped_column(Integer, ForeignKey("turnos_caja.id"))
    numero: Mapped[str] = mapped_column(String(20))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=FetchedValue())
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    descuento_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    iva_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    estado: Mapped[EstadoVenta] = mapped_column(Enum(EstadoVenta, name="estado_venta"), server_default=FetchedValue())
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    motivo_anulacion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cliente: Mapped["Cliente | None"] = relationship(foreign_keys=[cliente_id])
    usuario: Mapped["Usuario"] = relationship(foreign_keys=[usuario_id])
    turno_caja: Mapped["TurnoCaja"] = relationship(foreign_keys=[turno_caja_id])
    detalles: Mapped[list["VentaDetalle"]] = relationship(foreign_keys="VentaDetalle.venta_id", back_populates="venta", cascade="all, delete-orphan")
    pagos: Mapped[list["Pago"]] = relationship(foreign_keys="Pago.venta_id", back_populates="venta", cascade="all, delete-orphan")


class VentaDetalle(Base):
    __tablename__ = "venta_detalles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venta_id: Mapped[int] = mapped_column(Integer, ForeignKey("ventas.id"))
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey("productos.id"))
    equipo_imei_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("equipos_imei.id"), nullable=True)
    promocion_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("promociones.id"), nullable=True)
    cantidad: Mapped[int] = mapped_column(Integer, server_default=FetchedValue())
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    descuento: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    iva_porcentaje: Mapped[Decimal] = mapped_column(Numeric(5, 2), server_default=FetchedValue())
    iva_valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    total_linea: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    venta: Mapped["Venta"] = relationship(foreign_keys=[venta_id], back_populates="detalles")
    producto: Mapped["Producto"] = relationship(foreign_keys=[producto_id])
    equipo_imei: Mapped["EquipoImei | None"] = relationship(foreign_keys=[equipo_imei_id])
    promocion: Mapped["Promocion | None"] = relationship(foreign_keys=[promocion_id])


class Pago(Base):
    __tablename__ = "pagos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venta_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("ventas.id"), nullable=True)
    apartado_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("apartados.id"), nullable=True)
    turno_caja_id: Mapped[int] = mapped_column(Integer, ForeignKey("turnos_caja.id"))
    metodo: Mapped[MetodoPago] = mapped_column(Enum(MetodoPago, name="metodo_pago"))
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    referencia: Mapped[str | None] = mapped_column(String(60), nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=FetchedValue())
    venta: Mapped["Venta | None"] = relationship(foreign_keys=[venta_id], back_populates="pagos")
    apartado: Mapped["Apartado | None"] = relationship(foreign_keys=[apartado_id])
    turno_caja: Mapped["TurnoCaja"] = relationship(foreign_keys=[turno_caja_id])


class Apartado(Base):
    __tablename__ = "apartados"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.id"))
    equipo_imei_id: Mapped[int] = mapped_column(Integer, ForeignKey("equipos_imei.id"))
    venta_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("ventas.id"), nullable=True)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=FetchedValue())
    fecha_limite: Mapped[date] = mapped_column(Date)
    valor_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    saldo_pendiente: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    estado: Mapped[EstadoApartado] = mapped_column(Enum(EstadoApartado, name="estado_apartado"), server_default=FetchedValue())
    cliente: Mapped["Cliente"] = relationship(foreign_keys=[cliente_id])
    equipo_imei: Mapped["EquipoImei"] = relationship(foreign_keys=[equipo_imei_id])
    venta: Mapped["Venta | None"] = relationship(foreign_keys=[venta_id])


class ResolucionDian(Base):
    __tablename__ = "resoluciones_dian"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero_resolucion: Mapped[str] = mapped_column(String(30))
    prefijo: Mapped[str] = mapped_column(String(10))
    rango_desde: Mapped[int] = mapped_column(Integer)
    rango_hasta: Mapped[int] = mapped_column(Integer)
    consecutivo_actual: Mapped[int] = mapped_column(Integer, server_default=FetchedValue())
    vigencia_desde: Mapped[date] = mapped_column(Date)
    vigencia_hasta: Mapped[date] = mapped_column(Date)
    activa: Mapped[bool] = mapped_column(Boolean, server_default=FetchedValue())


class FacturaElectronica(Base):
    __tablename__ = "facturas_electronicas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venta_id: Mapped[int] = mapped_column(Integer, ForeignKey("ventas.id"))
    resolucion_id: Mapped[int] = mapped_column(Integer, ForeignKey("resoluciones_dian.id"))
    numero: Mapped[str] = mapped_column(String(20))
    cufe: Mapped[str] = mapped_column(String(96))
    fecha_emision: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=FetchedValue())
    xml_firmado: Mapped[str] = mapped_column(Text)
    estado_dian: Mapped[EstadoDian] = mapped_column(Enum(EstadoDian, name="estado_dian"), server_default=FetchedValue())
    respuesta_dian: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    venta: Mapped["Venta"] = relationship(foreign_keys=[venta_id])
    resolucion: Mapped["ResolucionDian"] = relationship(foreign_keys=[resolucion_id])


class NotaCredito(Base):
    __tablename__ = "notas_credito"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    factura_id: Mapped[int] = mapped_column(Integer, ForeignKey("facturas_electronicas.id"))
    devolucion_id: Mapped[int] = mapped_column(Integer, ForeignKey("devoluciones.id"))
    numero: Mapped[str] = mapped_column(String(20))
    cude: Mapped[str] = mapped_column(String(96))
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    fecha_emision: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=FetchedValue())
    estado_dian: Mapped[EstadoDian] = mapped_column(Enum(EstadoDian, name="estado_dian"), server_default=FetchedValue())
    factura: Mapped["FacturaElectronica"] = relationship(foreign_keys=[factura_id])
    devolucion: Mapped["Devolucion"] = relationship(foreign_keys=[devolucion_id])


class Devolucion(Base):
    __tablename__ = "devoluciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venta_id: Mapped[int] = mapped_column(Integer, ForeignKey("ventas.id"))
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=FetchedValue())
    motivo: Mapped[str] = mapped_column(String(255))
    tipo_reembolso: Mapped[TipoReembolso] = mapped_column(Enum(TipoReembolso, name="tipo_reembolso"))
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    venta: Mapped["Venta"] = relationship(foreign_keys=[venta_id])
    usuario: Mapped["Usuario"] = relationship(foreign_keys=[usuario_id])
    detalles: Mapped[list["DevolucionDetalle"]] = relationship(foreign_keys="DevolucionDetalle.devolucion_id", back_populates="devolucion", cascade="all, delete-orphan")


class DevolucionDetalle(Base):
    __tablename__ = "devolucion_detalles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    devolucion_id: Mapped[int] = mapped_column(Integer, ForeignKey("devoluciones.id"))
    venta_detalle_id: Mapped[int] = mapped_column(Integer, ForeignKey("venta_detalles.id"))
    cantidad: Mapped[int] = mapped_column(Integer, server_default=FetchedValue())
    valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    reingresa_inventario: Mapped[bool] = mapped_column(Boolean, server_default=FetchedValue())
    devolucion: Mapped["Devolucion"] = relationship(foreign_keys=[devolucion_id], back_populates="detalles")
    venta_detalle: Mapped["VentaDetalle"] = relationship(foreign_keys=[venta_detalle_id])


class Garantia(Base):
    __tablename__ = "garantias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    venta_detalle_id: Mapped[int] = mapped_column(Integer, ForeignKey("venta_detalles.id"))
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date] = mapped_column(Date)
    meses: Mapped[int] = mapped_column(SmallInteger, server_default=FetchedValue())
    estado: Mapped[EstadoGarantia] = mapped_column(Enum(EstadoGarantia, name="estado_garantia"), server_default=FetchedValue())
    venta_detalle: Mapped["VentaDetalle"] = relationship(foreign_keys=[venta_detalle_id])


class OrdenServicio(Base):
    __tablename__ = "ordenes_servicio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.id"))
    equipo_imei_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("equipos_imei.id"), nullable=True)
    garantia_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("garantias.id"), nullable=True)
    tecnico_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    numero: Mapped[str] = mapped_column(String(20))
    equipo_externo: Mapped[str | None] = mapped_column(String(150), nullable=True)
    falla_reportada: Mapped[str] = mapped_column(Text)
    diagnostico: Mapped[str | None] = mapped_column(Text, nullable=True)
    costo_mano_obra: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    estado: Mapped[EstadoServicio] = mapped_column(Enum(EstadoServicio, name="estado_servicio"), server_default=FetchedValue())
    fecha_ingreso: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=FetchedValue())
    fecha_entrega: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cliente: Mapped["Cliente"] = relationship(foreign_keys=[cliente_id])
    equipo_imei: Mapped["EquipoImei | None"] = relationship(foreign_keys=[equipo_imei_id])
    garantia: Mapped["Garantia | None"] = relationship(foreign_keys=[garantia_id])
    tecnico: Mapped["Usuario | None"] = relationship(foreign_keys=[tecnico_id])
    repuestos: Mapped[list["OrdenServicioRepuesto"]] = relationship(foreign_keys="OrdenServicioRepuesto.orden_servicio_id", back_populates="orden_servicio", cascade="all, delete-orphan")


class OrdenServicioRepuesto(Base):
    __tablename__ = "orden_servicio_repuestos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    orden_servicio_id: Mapped[int] = mapped_column(Integer, ForeignKey("ordenes_servicio.id"))
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey("productos.id"))
    cantidad: Mapped[int] = mapped_column(Integer, server_default=FetchedValue())
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    orden_servicio: Mapped["OrdenServicio"] = relationship(foreign_keys=[orden_servicio_id], back_populates="repuestos")
    producto: Mapped["Producto"] = relationship(foreign_keys=[producto_id])


class Operador(Base):
    __tablename__ = "operadores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(40))
    nit: Mapped[str] = mapped_column(String(20))
    activo: Mapped[bool] = mapped_column(Boolean, server_default=FetchedValue())


class Plan(Base):
    __tablename__ = "planes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operador_id: Mapped[int] = mapped_column(Integer, ForeignKey("operadores.id"))
    nombre: Mapped[str] = mapped_column(String(80))
    modalidad: Mapped[ModalidadPlan] = mapped_column(Enum(ModalidadPlan, name="modalidad_plan"))
    cargo_mensual: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    datos_gb: Mapped[Decimal | None] = mapped_column(Numeric(6, 1), nullable=True)
    comision: Mapped[Decimal] = mapped_column(Numeric(14, 2), server_default=FetchedValue())
    activo: Mapped[bool] = mapped_column(Boolean, server_default=FetchedValue())
    operador: Mapped["Operador"] = relationship(foreign_keys=[operador_id])


class ActivacionLinea(Base):
    __tablename__ = "activaciones_linea"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(Integer, ForeignKey("planes.id"))
    cliente_id: Mapped[int] = mapped_column(Integer, ForeignKey("clientes.id"))
    venta_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("ventas.id"), nullable=True)
    numero_linea: Mapped[str] = mapped_column(String(10))
    iccid_sim: Mapped[str] = mapped_column(String(22))
    tipo: Mapped[TipoActivacion] = mapped_column(Enum(TipoActivacion, name="tipo_activacion"))
    estado: Mapped[EstadoActivacion] = mapped_column(Enum(EstadoActivacion, name="estado_activacion"), server_default=FetchedValue())
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=FetchedValue())
    plan: Mapped["Plan"] = relationship(foreign_keys=[plan_id])
    cliente: Mapped["Cliente"] = relationship(foreign_keys=[cliente_id])
    venta: Mapped["Venta | None"] = relationship(foreign_keys=[venta_id])


class DispositivoIot(Base):
    __tablename__ = "dispositivos_iot"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    caja_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("cajas.id"), nullable=True)
    nombre: Mapped[str] = mapped_column(String(80))
    tipo: Mapped[TipoDispositivo] = mapped_column(Enum(TipoDispositivo, name="tipo_dispositivo"))
    direccion_mac: Mapped[str] = mapped_column(MACADDR)
    direccion_ip: Mapped[str | None] = mapped_column(INET, nullable=True)
    protocolo: Mapped[ProtocoloIot] = mapped_column(Enum(ProtocoloIot, name="protocolo_iot"))
    ubicacion: Mapped[str] = mapped_column(String(80))
    activo: Mapped[bool] = mapped_column(Boolean, server_default=FetchedValue())
    ultima_conexion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    caja: Mapped["Caja | None"] = relationship(foreign_keys=[caja_id])


class EventoIot(Base):
    __tablename__ = "eventos_iot"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    dispositivo_id: Mapped[int] = mapped_column(Integer, ForeignKey("dispositivos_iot.id"))
    equipo_imei_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("equipos_imei.id"), nullable=True)
    tipo_evento: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict] = mapped_column(JSONB)
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=FetchedValue())
    dispositivo: Mapped["DispositivoIot"] = relationship(foreign_keys=[dispositivo_id])
    equipo_imei: Mapped["EquipoImei | None"] = relationship(foreign_keys=[equipo_imei_id])


class Alerta(Base):
    __tablename__ = "alertas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    evento_iot_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("eventos_iot.id"), nullable=True)
    producto_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("productos.id"), nullable=True)
    atendida_por: Mapped[int | None] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    tipo: Mapped[TipoAlerta] = mapped_column(Enum(TipoAlerta, name="tipo_alerta"))
    severidad: Mapped[Severidad] = mapped_column(Enum(Severidad, name="severidad"), server_default=FetchedValue())
    mensaje: Mapped[str] = mapped_column(String(255))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=FetchedValue())
    fecha_atencion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evento_iot: Mapped["EventoIot | None"] = relationship(foreign_keys=[evento_iot_id])
    producto: Mapped["Producto | None"] = relationship(foreign_keys=[producto_id])
    atendida_por_rel: Mapped["Usuario | None"] = relationship(foreign_keys=[atendida_por])


# Nombre de tabla -> clase, util para la auditoria y las pruebas
CLASES = {
    "roles": Rol,
    "permisos": Permiso,
    "rol_permisos": RolPermiso,
    "usuarios": Usuario,
    "auditoria": Auditoria,
    "categorias": Categoria,
    "marcas": Marca,
    "productos": Producto,
    "promociones": Promocion,
    "promocion_productos": PromocionProducto,
    "proveedores": Proveedor,
    "ordenes_compra": OrdenCompra,
    "orden_compra_detalles": OrdenCompraDetalle,
    "equipos_imei": EquipoImei,
    "movimientos_inventario": MovimientoInventario,
    "clientes": Cliente,
    "cajas": Caja,
    "turnos_caja": TurnoCaja,
    "movimientos_caja": MovimientoCaja,
    "ventas": Venta,
    "venta_detalles": VentaDetalle,
    "pagos": Pago,
    "apartados": Apartado,
    "resoluciones_dian": ResolucionDian,
    "facturas_electronicas": FacturaElectronica,
    "notas_credito": NotaCredito,
    "devoluciones": Devolucion,
    "devolucion_detalles": DevolucionDetalle,
    "garantias": Garantia,
    "ordenes_servicio": OrdenServicio,
    "orden_servicio_repuestos": OrdenServicioRepuesto,
    "operadores": Operador,
    "planes": Plan,
    "activaciones_linea": ActivacionLinea,
    "dispositivos_iot": DispositivoIot,
    "eventos_iot": EventoIot,
    "alertas": Alerta,
}

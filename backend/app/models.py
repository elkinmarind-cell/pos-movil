"""Modelo de datos del POS de dispositivos moviles."""
from __future__ import annotations

import enum
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, Enum, ForeignKey,
    Integer, Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def ahora() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------
# Enumeraciones de dominio
# --------------------------------------------------------------------------
class RolUsuario(str, enum.Enum):
    ADMIN = "admin"
    CAJERO = "cajero"
    BODEGA = "bodega"


class EstadoImei(str, enum.Enum):
    DISPONIBLE = "disponible"
    RESERVADO = "reservado"
    VENDIDO = "vendido"
    DEVUELTO = "devuelto"
    EN_GARANTIA = "en_garantia"
    DADO_DE_BAJA = "dado_de_baja"


class TipoMovimiento(str, enum.Enum):
    ENTRADA = "entrada"
    SALIDA = "salida"
    AJUSTE = "ajuste"
    DEVOLUCION = "devolucion"


class EstadoVenta(str, enum.Enum):
    COMPLETADA = "completada"
    ANULADA = "anulada"


class MetodoPago(str, enum.Enum):
    EFECTIVO = "efectivo"
    TARJETA_DEBITO = "tarjeta_debito"
    TARJETA_CREDITO = "tarjeta_credito"
    TRANSFERENCIA = "transferencia"
    NEQUI = "nequi"
    DAVIPLATA = "daviplata"


class EstadoGarantia(str, enum.Enum):
    VIGENTE = "vigente"
    VENCIDA = "vencida"
    EN_RECLAMACION = "en_reclamacion"
    ATENDIDA = "atendida"


class TipoDocumento(str, enum.Enum):
    CC = "CC"
    CE = "CE"
    TI = "TI"
    NIT = "NIT"
    PASAPORTE = "PASAPORTE"


# --------------------------------------------------------------------------
# Seguridad / usuarios
# --------------------------------------------------------------------------
class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    nombre_completo: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(120), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    rol: Mapped[RolUsuario] = mapped_column(Enum(RolUsuario), default=RolUsuario.CAJERO)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

    ventas: Mapped[list["Venta"]] = relationship(back_populates="usuario")


# --------------------------------------------------------------------------
# Catalogo
# --------------------------------------------------------------------------
class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(255))

    productos: Mapped[list["Producto"]] = relationship(back_populates="categoria")


class Marca(Base):
    __tablename__ = "marcas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)
    pais_origen: Mapped[str | None] = mapped_column(String(80))

    productos: Mapped[list["Producto"]] = relationship(back_populates="marca")


class Proveedor(Base):
    __tablename__ = "proveedores"

    id: Mapped[int] = mapped_column(primary_key=True)
    nit: Mapped[str] = mapped_column(String(30), unique=True)
    razon_social: Mapped[str] = mapped_column(String(150))
    contacto: Mapped[str | None] = mapped_column(String(120))
    telefono: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(120))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class Producto(Base):
    """Un modelo comercial. Si requiere_imei=True el stock se lleva por serie."""
    __tablename__ = "productos"
    __table_args__ = (
        CheckConstraint("precio_venta >= 0", name="ck_producto_precio_venta"),
        CheckConstraint("precio_costo >= 0", name="ck_producto_precio_costo"),
        CheckConstraint("stock_actual >= 0", name="ck_producto_stock"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(150), index=True)
    descripcion: Mapped[str | None] = mapped_column(Text)
    marca_id: Mapped[int | None] = mapped_column(ForeignKey("marcas.id"))
    categoria_id: Mapped[int | None] = mapped_column(ForeignKey("categorias.id"))

    precio_costo: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    precio_venta: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    iva_porcentaje: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("19"))

    requiere_imei: Mapped[bool] = mapped_column(Boolean, default=False)
    meses_garantia: Mapped[int] = mapped_column(Integer, default=12)

    # Solo aplica a productos sin IMEI (accesorios, SIM, etc.)
    stock_actual: Mapped[int] = mapped_column(Integer, default=0)
    stock_minimo: Mapped[int] = mapped_column(Integer, default=5)

    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

    marca: Mapped[Marca | None] = relationship(back_populates="productos")
    categoria: Mapped[Categoria | None] = relationship(back_populates="productos")
    equipos: Mapped[list["EquipoImei"]] = relationship(back_populates="producto")


class EquipoImei(Base):
    """Unidad fisica trazable por IMEI. Es el corazon del control de un POS de celulares."""
    __tablename__ = "equipos_imei"
    __table_args__ = (
        UniqueConstraint("imei", name="uq_equipo_imei"),
        CheckConstraint("length(imei) = 15", name="ck_imei_longitud"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    imei: Mapped[str] = mapped_column(String(15), index=True)
    imei2: Mapped[str | None] = mapped_column(String(15))
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    proveedor_id: Mapped[int | None] = mapped_column(ForeignKey("proveedores.id"))

    color: Mapped[str | None] = mapped_column(String(40))
    almacenamiento_gb: Mapped[int | None] = mapped_column(Integer)
    precio_costo: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    estado: Mapped[EstadoImei] = mapped_column(Enum(EstadoImei), default=EstadoImei.DISPONIBLE, index=True)
    fecha_ingreso: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)
    observaciones: Mapped[str | None] = mapped_column(Text)

    producto: Mapped[Producto] = relationship(back_populates="equipos")
    proveedor: Mapped[Proveedor | None] = relationship()


class MovimientoInventario(Base):
    """Kardex: toda alteracion de existencias queda registrada y es auditable."""
    __tablename__ = "movimientos_inventario"

    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), index=True)
    equipo_imei_id: Mapped[int | None] = mapped_column(ForeignKey("equipos_imei.id"))
    tipo: Mapped[TipoMovimiento] = mapped_column(Enum(TipoMovimiento))
    cantidad: Mapped[int] = mapped_column(Integer, default=1)
    stock_resultante: Mapped[int | None] = mapped_column(Integer)
    motivo: Mapped[str | None] = mapped_column(String(255))
    referencia: Mapped[str | None] = mapped_column(String(60))
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuarios.id"))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora, index=True)

    producto: Mapped[Producto] = relationship()
    equipo: Mapped[EquipoImei | None] = relationship()
    usuario: Mapped[Usuario | None] = relationship()


# --------------------------------------------------------------------------
# Clientes y ventas
# --------------------------------------------------------------------------
class Cliente(Base):
    __tablename__ = "clientes"
    __table_args__ = (
        UniqueConstraint("tipo_documento", "numero_documento", name="uq_cliente_documento"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    tipo_documento: Mapped[TipoDocumento] = mapped_column(Enum(TipoDocumento), default=TipoDocumento.CC)
    numero_documento: Mapped[str] = mapped_column(String(20), index=True)
    nombres: Mapped[str] = mapped_column(String(80))
    apellidos: Mapped[str | None] = mapped_column(String(80))
    telefono: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(120))
    direccion: Mapped[str | None] = mapped_column(String(180))
    ciudad: Mapped[str | None] = mapped_column(String(80), default="Bogota")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora)

    ventas: Mapped[list["Venta"]] = relationship(back_populates="cliente")

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombres} {self.apellidos or ''}".strip()


class Venta(Base):
    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero_factura: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=ahora, index=True)

    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    descuento_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    iva_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))

    metodo_pago: Mapped[MetodoPago] = mapped_column(Enum(MetodoPago), default=MetodoPago.EFECTIVO)
    estado: Mapped[EstadoVenta] = mapped_column(Enum(EstadoVenta), default=EstadoVenta.COMPLETADA, index=True)
    observaciones: Mapped[str | None] = mapped_column(Text)
    motivo_anulacion: Mapped[str | None] = mapped_column(String(255))

    cliente: Mapped[Cliente | None] = relationship(back_populates="ventas")
    usuario: Mapped[Usuario] = relationship(back_populates="ventas")
    detalles: Mapped[list["VentaDetalle"]] = relationship(
        back_populates="venta", cascade="all, delete-orphan"
    )


class VentaDetalle(Base):
    __tablename__ = "venta_detalles"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_detalle_cantidad"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id", ondelete="CASCADE"), index=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"))
    equipo_imei_id: Mapped[int | None] = mapped_column(ForeignKey("equipos_imei.id"))

    descripcion: Mapped[str] = mapped_column(String(180))
    cantidad: Mapped[int] = mapped_column(Integer, default=1)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    descuento: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    iva_porcentaje: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("19"))
    base_gravable: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    iva_valor: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))
    total_linea: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"))

    venta: Mapped[Venta] = relationship(back_populates="detalles")
    producto: Mapped[Producto] = relationship()
    equipo: Mapped[EquipoImei | None] = relationship()
    garantia: Mapped["Garantia | None"] = relationship(back_populates="detalle", uselist=False)


class Garantia(Base):
    __tablename__ = "garantias"

    id: Mapped[int] = mapped_column(primary_key=True)
    venta_detalle_id: Mapped[int] = mapped_column(ForeignKey("venta_detalles.id", ondelete="CASCADE"), unique=True)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.id"))
    equipo_imei_id: Mapped[int | None] = mapped_column(ForeignKey("equipos_imei.id"))

    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date] = mapped_column(Date, index=True)
    meses: Mapped[int] = mapped_column(Integer, default=12)
    estado: Mapped[EstadoGarantia] = mapped_column(Enum(EstadoGarantia), default=EstadoGarantia.VIGENTE, index=True)

    descripcion_falla: Mapped[str | None] = mapped_column(Text)
    fecha_reclamacion: Mapped[date | None] = mapped_column(Date)
    solucion: Mapped[str | None] = mapped_column(Text)

    detalle: Mapped[VentaDetalle] = relationship(back_populates="garantia")
    cliente: Mapped[Cliente | None] = relationship()
    equipo: Mapped[EquipoImei | None] = relationship()

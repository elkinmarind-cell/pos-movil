"""Contratos de entrada/salida de la API (validacion con Pydantic v2)."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .models import (
    EstadoGarantia, EstadoImei, EstadoVenta, MetodoPago,
    RolUsuario, TipoDocumento, TipoMovimiento,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ----------------------------- Autenticacion -----------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: "UsuarioOut"


class UsuarioCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    nombre_completo: str
    email: EmailStr
    password: str = Field(min_length=6)
    rol: RolUsuario = RolUsuario.CAJERO


class UsuarioOut(ORMModel):
    id: int
    username: str
    nombre_completo: str
    email: str
    rol: RolUsuario
    activo: bool


# ------------------------------- Catalogo --------------------------------
class CategoriaOut(ORMModel):
    id: int
    nombre: str
    descripcion: str | None = None


class MarcaOut(ORMModel):
    id: int
    nombre: str
    pais_origen: str | None = None


class ProductoBase(BaseModel):
    sku: str = Field(min_length=2, max_length=40)
    nombre: str
    descripcion: str | None = None
    marca_id: int | None = None
    categoria_id: int | None = None
    precio_costo: Decimal = Decimal("0")
    precio_venta: Decimal = Decimal("0")
    iva_porcentaje: Decimal = Decimal("19")
    requiere_imei: bool = False
    meses_garantia: int = 12
    stock_minimo: int = 5

    @field_validator("precio_venta", "precio_costo")
    @classmethod
    def no_negativo(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("El precio no puede ser negativo")
        return v


class ProductoCreate(ProductoBase):
    stock_actual: int = 0


class ProductoUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    precio_costo: Decimal | None = None
    precio_venta: Decimal | None = None
    iva_porcentaje: Decimal | None = None
    stock_minimo: int | None = None
    meses_garantia: int | None = None
    activo: bool | None = None


class ProductoOut(ORMModel):
    id: int
    sku: str
    nombre: str
    descripcion: str | None = None
    marca: MarcaOut | None = None
    categoria: CategoriaOut | None = None
    precio_costo: Decimal
    precio_venta: Decimal
    iva_porcentaje: Decimal
    requiere_imei: bool
    meses_garantia: int
    stock_actual: int
    stock_minimo: int
    activo: bool
    disponibles: int = 0  # unidades vendibles (IMEI disponibles o stock_actual)


# --------------------------------- IMEI ----------------------------------
class EquipoImeiCreate(BaseModel):
    imei: str = Field(min_length=15, max_length=15)
    imei2: str | None = None
    producto_id: int
    proveedor_id: int | None = None
    color: str | None = None
    almacenamiento_gb: int | None = None
    precio_costo: Decimal = Decimal("0")
    observaciones: str | None = None

    @field_validator("imei")
    @classmethod
    def imei_valido(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit():
            raise ValueError("El IMEI debe contener solo digitos")
        if not luhn_valido(v):
            raise ValueError("El IMEI no supera la validacion Luhn (digito verificador incorrecto)")
        return v


class EquipoImeiOut(ORMModel):
    id: int
    imei: str
    imei2: str | None = None
    producto_id: int
    color: str | None = None
    almacenamiento_gb: int | None = None
    precio_costo: Decimal
    estado: EstadoImei
    fecha_ingreso: datetime
    observaciones: str | None = None


class MovimientoOut(ORMModel):
    id: int
    producto_id: int
    equipo_imei_id: int | None = None
    tipo: TipoMovimiento
    cantidad: int
    stock_resultante: int | None = None
    motivo: str | None = None
    referencia: str | None = None
    fecha: datetime


class AjusteStock(BaseModel):
    cantidad: int = Field(description="Positivo suma, negativo resta")
    motivo: str


# -------------------------------- Clientes -------------------------------
class ClienteCreate(BaseModel):
    tipo_documento: TipoDocumento = TipoDocumento.CC
    numero_documento: str = Field(min_length=5, max_length=20)
    nombres: str
    apellidos: str | None = None
    telefono: str | None = None
    email: EmailStr | None = None
    direccion: str | None = None
    ciudad: str | None = "Bogota"


class ClienteUpdate(BaseModel):
    nombres: str | None = None
    apellidos: str | None = None
    telefono: str | None = None
    email: EmailStr | None = None
    direccion: str | None = None
    ciudad: str | None = None
    activo: bool | None = None


class ClienteOut(ORMModel):
    id: int
    tipo_documento: TipoDocumento
    numero_documento: str
    nombres: str
    apellidos: str | None = None
    telefono: str | None = None
    email: str | None = None
    direccion: str | None = None
    ciudad: str | None = None
    activo: bool
    creado_en: datetime


# --------------------------------- Ventas --------------------------------
class ItemVenta(BaseModel):
    producto_id: int
    cantidad: int = Field(default=1, ge=1)
    imei: str | None = Field(default=None, description="Obligatorio si el producto requiere IMEI")
    descuento: Decimal = Decimal("0")


class VentaCreate(BaseModel):
    cliente_id: int | None = None
    metodo_pago: MetodoPago = MetodoPago.EFECTIVO
    observaciones: str | None = None
    items: list[ItemVenta] = Field(min_length=1)


class AnularVenta(BaseModel):
    motivo: str = Field(min_length=5)


class VentaDetalleOut(ORMModel):
    id: int
    producto_id: int
    equipo_imei_id: int | None = None
    descripcion: str
    cantidad: int
    precio_unitario: Decimal
    descuento: Decimal
    iva_porcentaje: Decimal
    base_gravable: Decimal
    iva_valor: Decimal
    total_linea: Decimal


class VentaOut(ORMModel):
    id: int
    numero_factura: str
    fecha: datetime
    cliente: ClienteOut | None = None
    usuario: UsuarioOut
    subtotal: Decimal
    descuento_total: Decimal
    iva_total: Decimal
    total: Decimal
    metodo_pago: MetodoPago
    estado: EstadoVenta
    observaciones: str | None = None
    motivo_anulacion: str | None = None
    detalles: list[VentaDetalleOut] = []


# ------------------------------- Garantias -------------------------------
class GarantiaOut(ORMModel):
    id: int
    venta_detalle_id: int
    cliente_id: int | None = None
    equipo_imei_id: int | None = None
    fecha_inicio: date
    fecha_fin: date
    meses: int
    estado: EstadoGarantia
    descripcion_falla: str | None = None
    fecha_reclamacion: date | None = None
    solucion: str | None = None
    dias_restantes: int = 0


class ReclamacionGarantia(BaseModel):
    descripcion_falla: str = Field(min_length=5)


class CierreGarantia(BaseModel):
    solucion: str = Field(min_length=5)


# -------------------------------- Reportes -------------------------------
class ResumenDashboard(BaseModel):
    ventas_hoy: Decimal
    numero_ventas_hoy: int
    ventas_mes: Decimal
    numero_ventas_mes: int
    ticket_promedio_mes: Decimal
    equipos_disponibles: int
    productos_bajo_stock: int
    garantias_vigentes: int
    garantias_en_reclamacion: int


class VentaPorDia(BaseModel):
    fecha: str
    total: Decimal
    cantidad: int


class ProductoMasVendido(BaseModel):
    producto_id: int
    nombre: str
    unidades: int
    total_vendido: Decimal


class AlertaStock(BaseModel):
    producto_id: int
    sku: str
    nombre: str
    disponibles: int
    stock_minimo: int


def luhn_valido(numero: str) -> bool:
    """Validacion del digito verificador del IMEI (algoritmo de Luhn)."""
    suma = 0
    invertido = numero[::-1]
    for i, caracter in enumerate(invertido):
        digito = int(caracter)
        if i % 2 == 1:
            digito *= 2
            if digito > 9:
                digito -= 9
        suma += digito
    return suma % 10 == 0


Token.model_rebuild()

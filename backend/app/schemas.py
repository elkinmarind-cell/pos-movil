"""Contratos de entrada y salida de la API (Pydantic v2)."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .models import (EstadoActivacion, EstadoApartado, EstadoDian, EstadoGarantia, EstadoImei,
                     EstadoOrdenCompra, EstadoServicio, EstadoTurno, EstadoVenta, MetodoPago,
                     ModalidadPlan, Severidad, TipoActivacion, TipoAlerta, TipoDescuento,
                     TipoDispositivo, TipoDocumento, TipoMovCaja, TipoMovimiento, TipoReembolso)


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------ seguridad
class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut
    permisos: list[str]


class RolOut(ORM):
    id: int
    nombre: str
    descripcion: str | None = None


class PermisoOut(ORM):
    id: int
    codigo: str
    modulo: str
    descripcion: str | None = None


class UsuarioOut(ORM):
    id: int
    rol_id: int
    username: str
    nombre_completo: str
    email: str
    activo: bool
    ultimo_acceso: datetime | None = None
    rol: RolOut | None = None


class UsuarioCreate(BaseModel):
    rol_id: int
    username: str = Field(min_length=3, max_length=50)
    nombre_completo: str = Field(min_length=3, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6)


class UsuarioUpdate(BaseModel):
    rol_id: int | None = None
    nombre_completo: str | None = None
    email: EmailStr | None = None
    activo: bool | None = None


class CambioClave(BaseModel):
    password: str = Field(min_length=6)


class RolPermisosUpdate(BaseModel):
    permisos: list[int]


# ------------------------------------------------------------------ catalogo
class CategoriaOut(ORM):
    id: int
    nombre: str
    categoria_padre_id: int | None = None
    descripcion: str | None = None


class MarcaOut(ORM):
    id: int
    nombre: str
    pais_origen: str | None = None


class ProductoBase(BaseModel):
    sku: str = Field(min_length=2, max_length=40)
    nombre: str = Field(min_length=2, max_length=150)
    descripcion: str | None = None
    categoria_id: int
    marca_id: int | None = None
    codigo_barras: str | None = None
    precio_costo: Decimal = Decimal("0")
    precio_venta: Decimal = Decimal("0")
    iva_porcentaje: Decimal = Decimal("19")
    requiere_imei: bool = False
    meses_garantia: int = 12
    stock_minimo: int = 5

    @field_validator("precio_costo", "precio_venta")
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
    categoria_id: int | None = None
    marca_id: int | None = None
    codigo_barras: str | None = None
    precio_costo: Decimal | None = None
    precio_venta: Decimal | None = None
    meses_garantia: int | None = None
    stock_minimo: int | None = None
    activo: bool | None = None


class ProductoOut(ORM):
    id: int
    sku: str
    nombre: str
    descripcion: str | None = None
    categoria: CategoriaOut | None = None
    marca: MarcaOut | None = None
    codigo_barras: str | None = None
    precio_costo: Decimal
    precio_venta: Decimal
    iva_porcentaje: Decimal
    requiere_imei: bool
    meses_garantia: int
    stock_actual: int
    stock_minimo: int
    activo: bool
    disponibles: int = 0


class AjusteStock(BaseModel):
    cantidad: int = Field(description="Positivo suma, negativo resta")
    motivo: str = Field(min_length=3, max_length=255)


# ------------------------------------------------------------------ inventario
def luhn_valido(numero: str) -> bool:
    suma = 0
    for i, c in enumerate(numero[::-1]):
        d = int(c)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        suma += d
    return suma % 10 == 0


class EquipoCreate(BaseModel):
    producto_id: int
    imei: str = Field(min_length=15, max_length=15)
    imei2: str | None = None
    codigo_rfid: str | None = None
    color: str | None = None
    almacenamiento_gb: int | None = None
    costo: Decimal = Decimal("0")
    orden_compra_detalle_id: int | None = None

    @field_validator("imei")
    @classmethod
    def imei_valido(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit():
            raise ValueError("El IMEI debe tener solo digitos")
        if not luhn_valido(v):
            raise ValueError("El IMEI no supera la validacion Luhn (digito verificador incorrecto)")
        return v


class EquipoOut(ORM):
    id: int
    producto_id: int
    imei: str
    imei2: str | None = None
    codigo_rfid: str | None = None
    color: str | None = None
    almacenamiento_gb: int | None = None
    costo: Decimal
    estado: EstadoImei
    fecha_ingreso: datetime
    producto: ProductoOut | None = None


class CambioEstadoEquipo(BaseModel):
    estado: EstadoImei
    motivo: str = Field(min_length=3)


class MovimientoOut(ORM):
    id: int
    producto_id: int
    equipo_imei_id: int | None = None
    tipo: TipoMovimiento
    cantidad: int
    stock_resultante: int
    motivo: str | None = None
    referencia: str | None = None
    fecha: datetime


# ------------------------------------------------------------------ clientes
class ClienteCreate(BaseModel):
    tipo_documento: TipoDocumento = TipoDocumento.CC
    numero_documento: str = Field(min_length=5, max_length=20)
    nombres: str = Field(min_length=2, max_length=80)
    apellidos: str | None = None
    telefono: str | None = None
    email: EmailStr | None = None
    direccion: str | None = None
    ciudad: str | None = "Bogota"
    autoriza_datos: bool = False


class ClienteUpdate(BaseModel):
    nombres: str | None = None
    apellidos: str | None = None
    telefono: str | None = None
    email: EmailStr | None = None
    direccion: str | None = None
    ciudad: str | None = None
    autoriza_datos: bool | None = None
    activo: bool | None = None


class ClienteOut(ORM):
    id: int
    tipo_documento: TipoDocumento
    numero_documento: str
    nombres: str
    apellidos: str | None = None
    telefono: str | None = None
    email: str | None = None
    direccion: str | None = None
    ciudad: str | None = None
    autoriza_datos: bool
    activo: bool
    creado_en: datetime


# ------------------------------------------------------------------ compras
class OrdenCompraItem(BaseModel):
    producto_id: int
    cantidad: int = Field(gt=0)
    costo_unitario: Decimal = Field(gt=0)


class OrdenCompraCreate(BaseModel):
    proveedor_id: int
    items: list[OrdenCompraItem] = Field(min_length=1)


class OrdenCompraDetalleOut(ORM):
    id: int
    producto_id: int
    cantidad_pedida: int
    cantidad_recibida: int
    costo_unitario: Decimal
    producto: ProductoOut | None = None


class OrdenCompraOut(ORM):
    id: int
    numero: str
    proveedor_id: int
    usuario_id: int
    fecha: date
    fecha_recepcion: date | None = None
    estado: EstadoOrdenCompra
    total: Decimal
    detalles: list[OrdenCompraDetalleOut] = []


class RecepcionItem(BaseModel):
    detalle_id: int
    cantidad: int = Field(ge=0)
    imeis: list[str] = []


class Recepcion(BaseModel):
    items: list[RecepcionItem] = Field(min_length=1)


# ------------------------------------------------------------------ caja
class AperturaCaja(BaseModel):
    caja_id: int
    base_inicial: Decimal = Field(ge=0)


class CierreCaja(BaseModel):
    efectivo_contado: Decimal = Field(ge=0)


class MovimientoCajaCreate(BaseModel):
    tipo: TipoMovCaja
    concepto: str = Field(min_length=3, max_length=150)
    valor: Decimal = Field(gt=0)


class TurnoOut(ORM):
    id: int
    caja_id: int
    usuario_id: int
    apertura: datetime
    cierre: datetime | None = None
    base_inicial: Decimal
    efectivo_esperado: Decimal | None = None
    efectivo_contado: Decimal | None = None
    diferencia: Decimal | None = None
    estado: EstadoTurno


class ArqueoOut(BaseModel):
    turno_id: int
    caja: str
    cajero: str
    apertura: datetime
    base_inicial: Decimal
    efectivo_ventas: Decimal
    otros_movimientos: Decimal
    recaudo_total: Decimal
    efectivo_esperado: Decimal


# ------------------------------------------------------------------ ventas
class ItemVenta(BaseModel):
    producto_id: int
    cantidad: int = Field(default=1, ge=1)
    imei: str | None = None
    descuento: Decimal = Decimal("0")
    promocion_id: int | None = None


class PagoEntrada(BaseModel):
    metodo: MetodoPago
    valor: Decimal = Field(gt=0)
    referencia: str | None = None


class VentaCreate(BaseModel):
    cliente_id: int | None = None
    observaciones: str | None = None
    items: list[ItemVenta] = Field(min_length=1)
    pagos: list[PagoEntrada] = Field(min_length=1)


class AnularVenta(BaseModel):
    motivo: str = Field(min_length=5, max_length=255)


class VentaDetalleOut(ORM):
    id: int
    producto_id: int
    equipo_imei_id: int | None = None
    cantidad: int
    precio_unitario: Decimal
    descuento: Decimal
    iva_porcentaje: Decimal
    iva_valor: Decimal
    total_linea: Decimal
    producto: ProductoOut | None = None
    equipo_imei: EquipoOut | None = None


class PagoOut(ORM):
    id: int
    metodo: MetodoPago
    valor: Decimal
    referencia: str | None = None
    fecha: datetime


class VentaOut(ORM):
    id: int
    numero: str
    fecha: datetime
    cliente_id: int | None = None
    usuario_id: int
    turno_caja_id: int
    subtotal: Decimal
    descuento_total: Decimal
    iva_total: Decimal
    total: Decimal
    estado: EstadoVenta
    observaciones: str | None = None
    motivo_anulacion: str | None = None
    cliente: ClienteOut | None = None
    usuario: UsuarioOut | None = None
    detalles: list[VentaDetalleOut] = []
    pagos: list[PagoOut] = []


# ------------------------------------------------------------------ apartados
class ApartadoCreate(BaseModel):
    cliente_id: int
    imei: str
    dias_plazo: int = Field(default=30, ge=1, le=180)
    abono_inicial: Decimal = Field(default=Decimal("0"), ge=0)
    metodo: MetodoPago = MetodoPago.EFECTIVO


class AbonoCreate(BaseModel):
    valor: Decimal = Field(gt=0)
    metodo: MetodoPago = MetodoPago.EFECTIVO
    referencia: str | None = None


class ApartadoOut(ORM):
    id: int
    cliente_id: int
    equipo_imei_id: int
    venta_id: int | None = None
    fecha: datetime
    fecha_limite: date
    valor_total: Decimal
    saldo_pendiente: Decimal
    estado: EstadoApartado
    cliente: ClienteOut | None = None
    equipo_imei: EquipoOut | None = None


# ------------------------------------------------------------------ posventa
class GarantiaOut(ORM):
    id: int
    venta_detalle_id: int
    fecha_inicio: date
    fecha_fin: date
    meses: int
    estado: EstadoGarantia
    dias_restantes: int = 0


class DevolucionItem(BaseModel):
    venta_detalle_id: int
    cantidad: int = Field(ge=1)
    reingresa_inventario: bool = True


class DevolucionCreate(BaseModel):
    venta_id: int
    motivo: str = Field(min_length=5, max_length=255)
    tipo_reembolso: TipoReembolso = TipoReembolso.NOTA_CREDITO
    items: list[DevolucionItem] = Field(min_length=1)


class DevolucionOut(ORM):
    id: int
    venta_id: int
    fecha: datetime
    motivo: str
    tipo_reembolso: TipoReembolso
    total: Decimal


class OrdenServicioCreate(BaseModel):
    cliente_id: int
    imei: str | None = None
    equipo_externo: str | None = None
    garantia_id: int | None = None
    falla_reportada: str = Field(min_length=5)
    costo_mano_obra: Decimal = Decimal("0")


class OrdenServicioUpdate(BaseModel):
    estado: EstadoServicio | None = None
    diagnostico: str | None = None
    costo_mano_obra: Decimal | None = None
    tecnico_id: int | None = None


class OrdenServicioOut(ORM):
    id: int
    numero: str
    cliente_id: int
    equipo_imei_id: int | None = None
    equipo_externo: str | None = None
    garantia_id: int | None = None
    tecnico_id: int | None = None
    falla_reportada: str
    diagnostico: str | None = None
    costo_mano_obra: Decimal
    estado: EstadoServicio
    fecha_ingreso: datetime
    fecha_entrega: datetime | None = None
    cliente: ClienteOut | None = None


# ------------------------------------------------------------------ telefonia
class OperadorOut(ORM):
    id: int
    nombre: str
    nit: str
    activo: bool


class PlanOut(ORM):
    id: int
    operador_id: int
    nombre: str
    modalidad: ModalidadPlan
    cargo_mensual: Decimal
    datos_gb: Decimal | None = None
    comision: Decimal
    activo: bool
    operador: OperadorOut | None = None


class ActivacionCreate(BaseModel):
    plan_id: int
    cliente_id: int
    venta_id: int | None = None
    numero_linea: str = Field(pattern=r"^3\d{9}$")
    iccid_sim: str = Field(min_length=18, max_length=22)
    tipo: TipoActivacion = TipoActivacion.NUEVA


class ActivacionOut(ORM):
    id: int
    plan_id: int
    cliente_id: int
    venta_id: int | None = None
    numero_linea: str
    iccid_sim: str
    tipo: TipoActivacion
    estado: EstadoActivacion
    fecha: datetime
    plan: PlanOut | None = None


# ------------------------------------------------------------------ IoT
class DispositivoOut(ORM):
    id: int
    nombre: str
    tipo: TipoDispositivo
    direccion_mac: str
    direccion_ip: str | None = None

    @field_validator("direccion_ip", "direccion_mac", mode="before")
    @classmethod
    def a_texto(cls, v):
        """psycopg devuelve INET y MACADDR como objetos; la API los expone como texto."""
        return None if v is None else str(v)
    protocolo: str
    ubicacion: str
    activo: bool
    ultima_conexion: datetime | None = None


class EventoOut(ORM):
    id: int
    dispositivo_id: int
    equipo_imei_id: int | None = None
    tipo_evento: str
    payload: dict
    fecha: datetime


class AlertaOut(ORM):
    id: int
    tipo: TipoAlerta
    severidad: Severidad
    mensaje: str
    fecha: datetime
    fecha_atencion: datetime | None = None
    producto_id: int | None = None
    evento_iot_id: int | None = None


# ------------------------------------------------------------------ reportes
class Dashboard(BaseModel):
    ventas_hoy: Decimal
    numero_ventas_hoy: int
    ventas_mes: Decimal
    numero_ventas_mes: int
    ticket_promedio_mes: Decimal
    equipos_disponibles: int
    productos_bajo_stock: int
    garantias_vigentes: int
    ordenes_servicio_abiertas: int
    apartados_vigentes: int
    alertas_sin_atender: int
    turno_abierto: bool


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


class Rentabilidad(BaseModel):
    producto_id: int
    sku: str
    nombre: str
    unidades: int
    ingreso_sin_iva: Decimal
    costo: Decimal
    utilidad: Decimal


class TrazabilidadImei(BaseModel):
    imei: str
    producto: str
    estado: str
    fecha_ingreso: datetime
    factura: str | None = None
    fecha_venta: datetime | None = None
    cliente: str | None = None
    garantia_hasta: date | None = None
    estado_garantia: str | None = None


LoginOut.model_rebuild()

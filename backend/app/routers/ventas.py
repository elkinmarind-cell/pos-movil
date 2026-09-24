from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import requiere_roles, usuario_actual
from ..models import EstadoVenta, RolUsuario, Usuario, Venta
from ..schemas import AnularVenta, VentaCreate, VentaOut
from ..services import anular_venta, procesar_venta

router = APIRouter(prefix="/api/ventas", tags=["Ventas"])


@router.post("", response_model=VentaOut, status_code=201, summary="Registrar venta")
def crear(
    datos: VentaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_actual),
):
    return procesar_venta(db, datos, usuario)


@router.get("", response_model=list[VentaOut], summary="Listar ventas")
def listar(
    desde: str | None = Query(None, description="YYYY-MM-DD"),
    hasta: str | None = Query(None, description="YYYY-MM-DD"),
    estado: EstadoVenta | None = None,
    cliente_id: int | None = None,
    limite: int = Query(100, le=500),
    db: Session = Depends(get_db),
    _: Usuario = Depends(usuario_actual),
):
    consulta = db.query(Venta)
    if desde:
        consulta = consulta.filter(Venta.fecha >= datetime.combine(
            datetime.strptime(desde, "%Y-%m-%d").date(), time.min, tzinfo=timezone.utc))
    if hasta:
        consulta = consulta.filter(Venta.fecha <= datetime.combine(
            datetime.strptime(hasta, "%Y-%m-%d").date(), time.max, tzinfo=timezone.utc))
    if estado:
        consulta = consulta.filter(Venta.estado == estado)
    if cliente_id:
        consulta = consulta.filter(Venta.cliente_id == cliente_id)
    return consulta.order_by(Venta.fecha.desc()).limit(limite).all()


@router.get("/{venta_id}", response_model=VentaOut, summary="Detalle de venta (factura)")
def detalle(venta_id: int, db: Session = Depends(get_db), _: Usuario = Depends(usuario_actual)):
    venta = db.get(Venta, venta_id)
    if not venta:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Venta no encontrada")
    return venta


@router.post("/{venta_id}/anular", response_model=VentaOut, summary="Anular venta (reversa inventario)")
def anular(
    venta_id: int,
    datos: AnularVenta,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_roles(RolUsuario.ADMIN)),
):
    venta = db.get(Venta, venta_id)
    if not venta:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Venta no encontrada")
    return anular_venta(db, venta, datos.motivo, usuario)

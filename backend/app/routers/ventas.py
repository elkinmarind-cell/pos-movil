from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import requiere, usuario_actual
from ..models import EstadoVenta, FacturaElectronica, Usuario, Venta
from ..schemas import AnularVenta, VentaCreate, VentaOut
from ..servicios import ventas as svc

router = APIRouter(prefix="/api/ventas", tags=["Ventas"], dependencies=[Depends(usuario_actual)])


@router.post("", response_model=VentaOut, status_code=201, summary="Registrar venta")
def crear(datos: VentaCreate, db: Session = Depends(get_db),
          usuario: Usuario = Depends(requiere("ventas.crear"))):
    return svc.procesar_venta(db, datos, usuario)


@router.get("", response_model=list[VentaOut], summary="Listar ventas")
def listar(desde: str | None = Query(None, description="YYYY-MM-DD"),
           hasta: str | None = Query(None, description="YYYY-MM-DD"),
           estado: EstadoVenta | None = None, cliente_id: int | None = None,
           limite: int = Query(100, le=500), db: Session = Depends(get_db)):
    consulta = select(Venta)
    if desde:
        consulta = consulta.where(Venta.fecha >= datetime.combine(
            datetime.strptime(desde, "%Y-%m-%d").date(), time.min, tzinfo=timezone.utc))
    if hasta:
        consulta = consulta.where(Venta.fecha <= datetime.combine(
            datetime.strptime(hasta, "%Y-%m-%d").date(), time.max, tzinfo=timezone.utc))
    if estado:
        consulta = consulta.where(Venta.estado == estado)
    if cliente_id:
        consulta = consulta.where(Venta.cliente_id == cliente_id)
    return db.scalars(consulta.order_by(Venta.fecha.desc()).limit(limite)).all()


@router.get("/{venta_id}", response_model=VentaOut, summary="Detalle de venta")
def detalle(venta_id: int, db: Session = Depends(get_db)):
    venta = db.get(Venta, venta_id)
    if venta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La venta no existe")
    return venta


@router.get("/{venta_id}/factura", summary="Factura electronica de la venta")
def factura(venta_id: int, db: Session = Depends(get_db)):
    f = db.scalars(select(FacturaElectronica).where(FacturaElectronica.venta_id == venta_id)).first()
    if f is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Esa venta no tiene factura electronica")
    return {"numero": f.numero, "cufe": f.cufe, "fecha_emision": f.fecha_emision,
            "estado_dian": f.estado_dian, "xml": f.xml_firmado}


@router.post("/{venta_id}/anular", response_model=VentaOut, summary="Anular venta")
def anular(venta_id: int, datos: AnularVenta, db: Session = Depends(get_db),
           usuario: Usuario = Depends(requiere("ventas.anular"))):
    venta = db.get(Venta, venta_id)
    if venta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La venta no existe")
    return svc.anular_venta(db, venta, datos.motivo, usuario)

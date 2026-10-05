from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import requiere, usuario_actual
from ..models import OrdenCompra, Proveedor, Usuario
from ..schemas import OrdenCompraCreate, OrdenCompraOut, Recepcion
from ..servicios import compras as svc

router = APIRouter(prefix="/api/compras", tags=["Compras"], dependencies=[Depends(usuario_actual)])


@router.get("/proveedores", summary="Proveedores")
def proveedores(db: Session = Depends(get_db)):
    return db.scalars(select(Proveedor).where(Proveedor.activo.is_(True))
                      .order_by(Proveedor.razon_social)).all()


@router.get("", response_model=list[OrdenCompraOut], summary="Ordenes de compra")
def listar(limite: int = 100, db: Session = Depends(get_db)):
    return db.scalars(select(OrdenCompra).order_by(OrdenCompra.fecha.desc()).limit(limite)).all()


@router.post("", response_model=OrdenCompraOut, status_code=201, summary="Crear orden de compra")
def crear(datos: OrdenCompraCreate, db: Session = Depends(get_db),
          usuario: Usuario = Depends(requiere("compras.crear"))):
    return svc.crear_orden(db, datos, usuario)


@router.get("/{orden_id}", response_model=OrdenCompraOut, summary="Detalle de orden")
def detalle(orden_id: int, db: Session = Depends(get_db)):
    orden = db.get(OrdenCompra, orden_id)
    if orden is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La orden no existe")
    return orden


@router.post("/{orden_id}/recibir", response_model=OrdenCompraOut, summary="Recibir mercancia")
def recibir(orden_id: int, datos: Recepcion, db: Session = Depends(get_db),
            usuario: Usuario = Depends(requiere("compras.recibir"))):
    orden = db.get(OrdenCompra, orden_id)
    if orden is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La orden no existe")
    return svc.recibir(db, orden, datos, usuario)

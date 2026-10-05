from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import requiere, usuario_actual
from ..models import (Apartado, Devolucion, EstadoApartado, EstadoGarantia, EstadoServicio,
                      Garantia, OrdenServicio, Usuario)
from ..schemas import (AbonoCreate, ApartadoCreate, ApartadoOut, DevolucionCreate, DevolucionOut,
                       GarantiaOut, OrdenServicioCreate, OrdenServicioOut, OrdenServicioUpdate)
from ..servicios import posventa as svc

router = APIRouter(prefix="/api", tags=["Posventa"], dependencies=[Depends(usuario_actual)])


# --------------------------------------------------------------- garantias
@router.get("/garantias", response_model=list[GarantiaOut], summary="Garantias")
def garantias(estado: EstadoGarantia | None = None, db: Session = Depends(get_db)):
    svc.actualizar_vencidas(db)
    consulta = select(Garantia)
    if estado:
        consulta = consulta.where(Garantia.estado == estado)
    salida = []
    for g in db.scalars(consulta.order_by(Garantia.fecha_fin)).all():
        dto = GarantiaOut.model_validate(g)
        dto.dias_restantes = svc.dias_restantes(g)
        salida.append(dto)
    return salida


@router.post("/garantias/{garantia_id}/reclamar", response_model=OrdenServicioOut,
             status_code=201, summary="Abrir reclamacion de garantia")
def reclamar(garantia_id: int, falla: str = Body(..., embed=True, min_length=5),
             db: Session = Depends(get_db), usuario: Usuario = Depends(requiere("garantias.reclamar"))):
    garantia = db.get(Garantia, garantia_id)
    if garantia is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La garantia no existe")
    return svc.reclamar_garantia(db, garantia, falla, usuario)


# --------------------------------------------------------------- devoluciones
@router.get("/devoluciones", response_model=list[DevolucionOut], summary="Devoluciones")
def devoluciones(limite: int = 100, db: Session = Depends(get_db)):
    return db.scalars(select(Devolucion).order_by(Devolucion.fecha.desc()).limit(limite)).all()


@router.post("/devoluciones", response_model=DevolucionOut, status_code=201, summary="Registrar devolucion")
def crear_devolucion(datos: DevolucionCreate, db: Session = Depends(get_db),
                     usuario: Usuario = Depends(requiere("ventas.anular", "ventas.crear"))):
    return svc.crear_devolucion(db, datos, usuario)


# --------------------------------------------------------------- servicio tecnico
@router.get("/servicio", response_model=list[OrdenServicioOut], summary="Ordenes de servicio")
def ordenes(estado: EstadoServicio | None = None, db: Session = Depends(get_db)):
    consulta = select(OrdenServicio)
    if estado:
        consulta = consulta.where(OrdenServicio.estado == estado)
    return db.scalars(consulta.order_by(OrdenServicio.fecha_ingreso.desc())).all()


@router.post("/servicio", response_model=OrdenServicioOut, status_code=201, summary="Recibir equipo")
def crear_servicio(datos: OrdenServicioCreate, db: Session = Depends(get_db),
                   usuario: Usuario = Depends(requiere("servicio.crear"))):
    return svc.crear_orden_servicio(db, datos, usuario)


@router.put("/servicio/{orden_id}", response_model=OrdenServicioOut, summary="Actualizar orden")
def actualizar_servicio(orden_id: int, datos: OrdenServicioUpdate, db: Session = Depends(get_db),
                        usuario: Usuario = Depends(requiere("servicio.cerrar", "servicio.crear"))):
    orden = db.get(OrdenServicio, orden_id)
    if orden is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La orden no existe")
    return svc.actualizar_orden_servicio(db, orden, datos, usuario)


# --------------------------------------------------------------- apartados
@router.get("/apartados", response_model=list[ApartadoOut], summary="Apartados")
def apartados(estado: EstadoApartado | None = None, db: Session = Depends(get_db)):
    consulta = select(Apartado)
    if estado:
        consulta = consulta.where(Apartado.estado == estado)
    return db.scalars(consulta.order_by(Apartado.fecha_limite)).all()


@router.post("/apartados", response_model=ApartadoOut, status_code=201, summary="Apartar un equipo")
def crear_apartado(datos: ApartadoCreate, db: Session = Depends(get_db),
                   usuario: Usuario = Depends(requiere("ventas.crear"))):
    return svc.crear_apartado(db, datos, usuario)


@router.post("/apartados/{apartado_id}/abono", response_model=ApartadoOut, summary="Registrar abono")
def abonar(apartado_id: int, datos: AbonoCreate, db: Session = Depends(get_db),
           usuario: Usuario = Depends(requiere("ventas.crear"))):
    apartado = db.get(Apartado, apartado_id)
    if apartado is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El apartado no existe")
    return svc.abonar(db, apartado, datos, usuario)

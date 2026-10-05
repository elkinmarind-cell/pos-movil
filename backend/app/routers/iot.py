from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import usuario_actual
from ..models import Alerta, DispositivoIot, EventoIot, Usuario
from ..schemas import AlertaOut, DispositivoOut, EventoOut

router = APIRouter(prefix="/api/iot", tags=["IoT"], dependencies=[Depends(usuario_actual)])


@router.get("/dispositivos", response_model=list[DispositivoOut], summary="Dispositivos de la tienda")
def dispositivos(db: Session = Depends(get_db)):
    return db.scalars(select(DispositivoIot).order_by(DispositivoIot.nombre)).all()


@router.get("/eventos", response_model=list[EventoOut], summary="Eventos recientes")
def eventos(limite: int = Query(100, le=500), db: Session = Depends(get_db)):
    return db.scalars(select(EventoIot).order_by(EventoIot.fecha.desc()).limit(limite)).all()


@router.get("/alertas", response_model=list[AlertaOut], summary="Alertas")
def alertas(sin_atender: bool = False, limite: int = Query(100, le=500), db: Session = Depends(get_db)):
    consulta = select(Alerta)
    if sin_atender:
        consulta = consulta.where(Alerta.fecha_atencion.is_(None))
    return db.scalars(consulta.order_by(Alerta.fecha.desc()).limit(limite)).all()


@router.post("/alertas/{alerta_id}/atender", response_model=AlertaOut, summary="Marcar alerta atendida")
def atender(alerta_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    alerta = db.get(Alerta, alerta_id)
    if alerta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La alerta no existe")
    if alerta.fecha_atencion is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esa alerta ya fue atendida")
    alerta.fecha_atencion = datetime.now(timezone.utc)
    alerta.atendida_por = usuario.id
    db.commit()
    db.refresh(alerta)
    return alerta

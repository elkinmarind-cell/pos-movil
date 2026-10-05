from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import requiere, usuario_actual
from ..models import ActivacionLinea, Cliente, Operador, Plan, Usuario
from ..schemas import ActivacionCreate, ActivacionOut, OperadorOut, PlanOut

router = APIRouter(prefix="/api/telefonia", tags=["Activacion de lineas"],
                   dependencies=[Depends(usuario_actual)])


@router.get("/operadores", response_model=list[OperadorOut], summary="Operadores")
def operadores(db: Session = Depends(get_db)):
    return db.scalars(select(Operador).where(Operador.activo.is_(True)).order_by(Operador.nombre)).all()


@router.get("/planes", response_model=list[PlanOut], summary="Planes")
def planes(operador_id: int | None = None, db: Session = Depends(get_db)):
    consulta = select(Plan).where(Plan.activo.is_(True))
    if operador_id:
        consulta = consulta.where(Plan.operador_id == operador_id)
    return db.scalars(consulta.order_by(Plan.nombre)).all()


@router.get("/activaciones", response_model=list[ActivacionOut], summary="Lineas activadas")
def activaciones(limite: int = 100, db: Session = Depends(get_db)):
    return db.scalars(select(ActivacionLinea).order_by(ActivacionLinea.fecha.desc()).limit(limite)).all()


@router.post("/activaciones", response_model=ActivacionOut, status_code=201, summary="Activar linea")
def activar(datos: ActivacionCreate, db: Session = Depends(get_db),
            _: Usuario = Depends(requiere("ventas.crear"))):
    if db.get(Plan, datos.plan_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El plan no existe")
    if db.get(Cliente, datos.cliente_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El cliente no existe")
    if db.scalars(select(ActivacionLinea).where(ActivacionLinea.iccid_sim == datos.iccid_sim)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Esa SIM ya fue activada")
    activacion = ActivacionLinea(**datos.model_dump())
    db.add(activacion)
    db.commit()
    db.refresh(activacion)
    return activacion

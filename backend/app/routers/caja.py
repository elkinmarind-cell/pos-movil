from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import requiere, usuario_actual
from ..models import Caja, EstadoTurno, TurnoCaja, Usuario
from ..schemas import (AperturaCaja, ArqueoOut, CierreCaja, MovimientoCajaCreate, TurnoOut)
from ..servicios import caja as svc

router = APIRouter(prefix="/api/caja", tags=["Caja"], dependencies=[Depends(usuario_actual)])


@router.get("/cajas", summary="Terminales de caja")
def cajas(db: Session = Depends(get_db)):
    return [{"id": c.id, "nombre": c.nombre, "ubicacion": c.ubicacion, "activa": c.activa,
             "ocupada": bool(db.scalars(select(TurnoCaja).where(
                 TurnoCaja.caja_id == c.id, TurnoCaja.estado == EstadoTurno.ABIERTO)).first())}
            for c in db.scalars(select(Caja).order_by(Caja.id)).all()]


@router.get("/turno", response_model=TurnoOut | None, summary="Mi turno abierto")
def mi_turno(db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    return svc.turno_abierto(db, usuario)


@router.get("/turnos", response_model=list[TurnoOut], summary="Historial de turnos")
def turnos(limite: int = 50, db: Session = Depends(get_db)):
    return db.scalars(select(TurnoCaja).order_by(TurnoCaja.apertura.desc()).limit(limite)).all()


@router.post("/abrir", response_model=TurnoOut, status_code=201, summary="Abrir caja")
def abrir(datos: AperturaCaja, db: Session = Depends(get_db),
          usuario: Usuario = Depends(requiere("caja.abrir"))):
    return svc.abrir(db, usuario, datos.caja_id, datos.base_inicial)


@router.get("/arqueo", response_model=ArqueoOut, summary="Arqueo del turno abierto")
def arqueo(db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    return svc.arqueo(db, svc.exigir_turno(db, usuario).id)


@router.post("/cerrar", response_model=TurnoOut, summary="Cerrar caja con arqueo")
def cerrar(datos: CierreCaja, db: Session = Depends(get_db),
           usuario: Usuario = Depends(requiere("caja.cerrar"))):
    return svc.cerrar(db, svc.exigir_turno(db, usuario), datos.efectivo_contado)


@router.post("/movimiento", status_code=201, summary="Ingreso o egreso de efectivo")
def movimiento(datos: MovimientoCajaCreate, db: Session = Depends(get_db),
               usuario: Usuario = Depends(requiere("caja.movimiento"))):
    turno = svc.exigir_turno(db, usuario)
    mov = svc.registrar_movimiento(db, turno, datos.tipo, datos.concepto, datos.valor)
    return {"id": mov.id, "tipo": mov.tipo, "concepto": mov.concepto, "valor": mov.valor}

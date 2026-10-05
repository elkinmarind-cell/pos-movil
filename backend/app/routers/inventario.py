from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import requiere, usuario_actual
from ..models import EquipoImei, EstadoImei, Usuario
from ..schemas import CambioEstadoEquipo, EquipoCreate, EquipoOut
from ..servicios import inventario

router = APIRouter(prefix="/api/inventario", tags=["Inventario e IMEI"],
                   dependencies=[Depends(usuario_actual)])


@router.get("/imei", response_model=list[EquipoOut], summary="Equipos por IMEI")
def listar(producto_id: int | None = None, estado: EstadoImei | None = None,
           q: str | None = Query(None, description="Busqueda parcial por IMEI o RFID"),
           limite: int = Query(200, le=1000), db: Session = Depends(get_db)):
    consulta = select(EquipoImei)
    if producto_id:
        consulta = consulta.where(EquipoImei.producto_id == producto_id)
    if estado:
        consulta = consulta.where(EquipoImei.estado == estado)
    if q:
        consulta = consulta.where(EquipoImei.imei.ilike(f"%{q}%"))
    return db.scalars(consulta.order_by(EquipoImei.fecha_ingreso.desc()).limit(limite)).all()


@router.get("/imei/{imei}", response_model=EquipoOut, summary="Consultar un IMEI")
def consultar(imei: str, db: Session = Depends(get_db)):
    equipo = db.scalars(select(EquipoImei).where(EquipoImei.imei == imei)).first()
    if equipo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ese IMEI no esta en el inventario")
    return equipo


@router.post("/imei", response_model=EquipoOut, status_code=201, summary="Ingresar equipo")
def ingresar(datos: EquipoCreate, db: Session = Depends(get_db),
             usuario: Usuario = Depends(requiere("inventario.crear"))):
    return inventario.ingresar_equipo(db, datos, usuario)


@router.post("/imei/lote", response_model=list[EquipoOut], status_code=201, summary="Ingresar lote")
def ingresar_lote(equipos: list[EquipoCreate], db: Session = Depends(get_db),
                  usuario: Usuario = Depends(requiere("inventario.crear"))):
    vistos: set[str] = set()
    creados = []
    for datos in equipos:
        if datos.imei in vistos:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"IMEI {datos.imei} repetido en el lote")
        vistos.add(datos.imei)
        creados.append(inventario.ingresar_equipo(db, datos, usuario))
    return creados


@router.patch("/imei/{imei}/estado", response_model=EquipoOut, summary="Cambiar estado de un equipo")
def cambiar_estado(imei: str, datos: CambioEstadoEquipo, db: Session = Depends(get_db),
                   usuario: Usuario = Depends(requiere("inventario.ajustar"))):
    equipo = db.scalars(select(EquipoImei).where(EquipoImei.imei == imei)).first()
    if equipo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ese IMEI no esta registrado")
    return inventario.cambiar_estado(db, equipo, datos.estado, datos.motivo, usuario)

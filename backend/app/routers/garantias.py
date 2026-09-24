from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import usuario_actual
from ..models import EquipoImei, EstadoGarantia, EstadoImei, Garantia
from ..schemas import CierreGarantia, GarantiaOut, ReclamacionGarantia
from ..services import actualizar_garantias_vencidas

router = APIRouter(prefix="/api/garantias", tags=["Garantias"], dependencies=[Depends(usuario_actual)])


def _salida(garantia: Garantia) -> GarantiaOut:
    dto = GarantiaOut.model_validate(garantia)
    dto.dias_restantes = max((garantia.fecha_fin - datetime.now(timezone.utc).date()).days, 0)
    return dto


@router.get("", response_model=list[GarantiaOut], summary="Listar garantias")
def listar(
    estado: EstadoGarantia | None = None,
    cliente_id: int | None = None,
    imei: str | None = Query(None, description="Consulta la garantia de un equipo"),
    db: Session = Depends(get_db),
):
    actualizar_garantias_vencidas(db)
    consulta = db.query(Garantia)
    if estado:
        consulta = consulta.filter(Garantia.estado == estado)
    if cliente_id:
        consulta = consulta.filter(Garantia.cliente_id == cliente_id)
    if imei:
        equipo = db.query(EquipoImei).filter(EquipoImei.imei == imei).first()
        if not equipo:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "IMEI no registrado")
        consulta = consulta.filter(Garantia.equipo_imei_id == equipo.id)
    return [_salida(g) for g in consulta.order_by(Garantia.fecha_fin).all()]


@router.post("/{garantia_id}/reclamar", response_model=GarantiaOut, summary="Abrir reclamacion de garantia")
def reclamar(garantia_id: int, datos: ReclamacionGarantia, db: Session = Depends(get_db)):
    garantia = db.get(Garantia, garantia_id)
    if not garantia:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Garantia no encontrada")
    hoy = datetime.now(timezone.utc).date()
    if garantia.fecha_fin < hoy:
        garantia.estado = EstadoGarantia.VENCIDA
        db.commit()
        raise HTTPException(status.HTTP_409_CONFLICT, f"La garantia vencio el {garantia.fecha_fin}")
    if garantia.estado == EstadoGarantia.EN_RECLAMACION:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una reclamacion abierta para esta garantia")

    garantia.estado = EstadoGarantia.EN_RECLAMACION
    garantia.descripcion_falla = datos.descripcion_falla
    garantia.fecha_reclamacion = hoy
    if garantia.equipo_imei_id:
        equipo = db.get(EquipoImei, garantia.equipo_imei_id)
        if equipo:
            equipo.estado = EstadoImei.EN_GARANTIA
    db.commit()
    db.refresh(garantia)
    return _salida(garantia)


@router.post("/{garantia_id}/cerrar", response_model=GarantiaOut, summary="Cerrar reclamacion")
def cerrar(garantia_id: int, datos: CierreGarantia, db: Session = Depends(get_db)):
    garantia = db.get(Garantia, garantia_id)
    if not garantia:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Garantia no encontrada")
    if garantia.estado != EstadoGarantia.EN_RECLAMACION:
        raise HTTPException(status.HTTP_409_CONFLICT, "La garantia no tiene una reclamacion abierta")
    garantia.estado = EstadoGarantia.ATENDIDA
    garantia.solucion = datos.solucion
    if garantia.equipo_imei_id:
        equipo = db.get(EquipoImei, garantia.equipo_imei_id)
        if equipo and equipo.estado == EstadoImei.EN_GARANTIA:
            equipo.estado = EstadoImei.VENDIDO
    db.commit()
    db.refresh(garantia)
    return _salida(garantia)

"""Turnos de caja: apertura, movimientos y cierre con arqueo."""
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ..models import Caja, EstadoTurno, MovimientoCaja, TipoMovCaja, TurnoCaja, Usuario


def turno_abierto(db: Session, usuario: Usuario) -> TurnoCaja | None:
    return db.scalars(
        select(TurnoCaja).where(TurnoCaja.usuario_id == usuario.id,
                                TurnoCaja.estado == EstadoTurno.ABIERTO)
    ).first()


def exigir_turno(db: Session, usuario: Usuario) -> TurnoCaja:
    turno = turno_abierto(db, usuario)
    if turno is None:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Debe abrir la caja antes de registrar movimientos de dinero")
    return turno


def abrir(db: Session, usuario: Usuario, caja_id: int, base_inicial: Decimal) -> TurnoCaja:
    if db.get(Caja, caja_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La caja no existe")
    if turno_abierto(db, usuario):
        raise HTTPException(status.HTTP_409_CONFLICT, "Usted ya tiene un turno abierto")
    ocupada = db.scalars(select(TurnoCaja).where(TurnoCaja.caja_id == caja_id,
                                                 TurnoCaja.estado == EstadoTurno.ABIERTO)).first()
    if ocupada:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esa caja ya tiene un turno abierto")
    turno = TurnoCaja(caja_id=caja_id, usuario_id=usuario.id, base_inicial=base_inicial)
    db.add(turno)
    db.commit()
    db.refresh(turno)
    return turno


def cerrar(db: Session, turno: TurnoCaja, efectivo_contado: Decimal) -> TurnoCaja:
    """El calculo del arqueo lo hace el procedimiento almacenado sp_cerrar_turno."""
    if turno.estado != EstadoTurno.ABIERTO:
        raise HTTPException(status.HTTP_409_CONFLICT, "El turno ya estaba cerrado")
    db.execute(text("CALL sp_cerrar_turno(:t, :c)"), {"t": turno.id, "c": efectivo_contado})
    db.commit()
    db.refresh(turno)
    return turno


def registrar_movimiento(db: Session, turno: TurnoCaja, tipo: TipoMovCaja,
                         concepto: str, valor: Decimal) -> MovimientoCaja:
    mov = MovimientoCaja(turno_caja_id=turno.id, tipo=tipo, concepto=concepto, valor=valor)
    db.add(mov)
    db.commit()
    db.refresh(mov)
    return mov


def arqueo(db: Session, turno_id: int) -> dict:
    fila = db.execute(text("SELECT * FROM v_estado_caja WHERE turno_id = :t"), {"t": turno_id}).mappings().first()
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El turno no existe")
    d = dict(fila)
    d["efectivo_esperado"] = d["base_inicial"] + d["efectivo_ventas"] + d["otros_movimientos"]
    return d

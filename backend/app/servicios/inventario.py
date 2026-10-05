"""Inventario: existencias, ingreso de equipos y kardex."""
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import (EquipoImei, EstadoImei, MovimientoInventario, Producto, TipoMovimiento, Usuario)


def disponibles(db: Session, producto: Producto) -> int:
    if producto.requiere_imei:
        return db.scalar(select(func.count(EquipoImei.id)).where(
            EquipoImei.producto_id == producto.id, EquipoImei.estado == EstadoImei.DISPONIBLE)) or 0
    return producto.stock_actual


def registrar_movimiento(db: Session, producto: Producto, tipo: TipoMovimiento, cantidad: int,
                         usuario: Usuario, equipo: EquipoImei | None = None,
                         motivo: str | None = None, referencia: str | None = None) -> MovimientoInventario:
    mov = MovimientoInventario(
        producto_id=producto.id, equipo_imei_id=equipo.id if equipo else None,
        usuario_id=usuario.id, tipo=tipo, cantidad=cantidad,
        stock_resultante=disponibles(db, producto), motivo=motivo, referencia=referencia,
    )
    db.add(mov)
    return mov


def ingresar_equipo(db: Session, datos, usuario: Usuario) -> EquipoImei:
    producto = db.get(Producto, datos.producto_id)
    if producto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El producto no existe")
    if not producto.requiere_imei:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Este producto no se controla por IMEI; use el ajuste de stock")
    if db.scalars(select(EquipoImei).where(EquipoImei.imei == datos.imei)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, f"El IMEI {datos.imei} ya esta registrado")
    equipo = EquipoImei(**datos.model_dump())
    db.add(equipo)
    db.flush()
    registrar_movimiento(db, producto, TipoMovimiento.ENTRADA, 1, usuario, equipo,
                         motivo="Ingreso de equipo a bodega")
    db.commit()
    db.refresh(equipo)
    return equipo


def ajustar_stock(db: Session, producto: Producto, cantidad: int, motivo: str, usuario: Usuario) -> Producto:
    if producto.requiere_imei:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Este producto se controla por IMEI: ingrese o de de baja equipos")
    nuevo = producto.stock_actual + cantidad
    if nuevo < 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El ajuste dejaria el stock en negativo")
    producto.stock_actual = nuevo
    db.flush()
    registrar_movimiento(db, producto,
                         TipoMovimiento.ENTRADA if cantidad > 0 else TipoMovimiento.SALIDA,
                         abs(cantidad), usuario, motivo=motivo)
    db.commit()
    db.refresh(producto)
    return producto


def cambiar_estado(db: Session, equipo: EquipoImei, estado: EstadoImei, motivo: str, usuario: Usuario) -> EquipoImei:
    if equipo.estado == EstadoImei.VENDIDO and estado == EstadoImei.DISPONIBLE:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "Un equipo vendido solo vuelve a disponible anulando la venta")
    anterior = equipo.estado.value
    equipo.estado = estado
    db.flush()
    registrar_movimiento(db, equipo.producto, TipoMovimiento.AJUSTE, 1, usuario, equipo,
                         motivo=f"{anterior} -> {estado.value}: {motivo}")
    db.commit()
    db.refresh(equipo)
    return equipo

"""Compras a proveedores y recepcion de mercancia."""
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..dinero import dinero
from ..models import (EquipoImei, EstadoOrdenCompra, OrdenCompra, OrdenCompraDetalle, Producto,
                      Proveedor, TipoMovimiento, Usuario)
from .inventario import registrar_movimiento


def _siguiente_numero(db: Session) -> str:
    anio = datetime.now(timezone.utc).year
    n = db.scalar(select(func.count(OrdenCompra.id)).where(
        OrdenCompra.numero.like(f"OC-{anio}-%"))) or 0
    return f"OC-{anio}-{n + 1:04d}"


def crear_orden(db: Session, datos, usuario: Usuario) -> OrdenCompra:
    if db.get(Proveedor, datos.proveedor_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El proveedor no existe")
    total = Decimal("0")
    orden = OrdenCompra(proveedor_id=datos.proveedor_id, usuario_id=usuario.id,
                        numero=_siguiente_numero(db), fecha=datetime.now(timezone.utc).date(),
                        estado=EstadoOrdenCompra.ENVIADA, total=0)
    db.add(orden)
    db.flush()
    for item in datos.items:
        if db.get(Producto, item.producto_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"El producto {item.producto_id} no existe")
        db.add(OrdenCompraDetalle(orden_compra_id=orden.id, producto_id=item.producto_id,
                                  cantidad_pedida=item.cantidad, cantidad_recibida=0,
                                  costo_unitario=dinero(item.costo_unitario)))
        total += dinero(item.costo_unitario) * item.cantidad
    orden.total = dinero(total)
    db.commit()
    db.refresh(orden)
    return orden


def recibir(db: Session, orden: OrdenCompra, datos, usuario: Usuario) -> OrdenCompra:
    if orden.estado in (EstadoOrdenCompra.RECIBIDA, EstadoOrdenCompra.ANULADA):
        raise HTTPException(status.HTTP_409_CONFLICT, f"La orden ya esta {orden.estado.value}")

    for item in datos.items:
        detalle = db.get(OrdenCompraDetalle, item.detalle_id)
        if detalle is None or detalle.orden_compra_id != orden.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Ese renglon no pertenece a la orden")
        pendiente = detalle.cantidad_pedida - detalle.cantidad_recibida
        if item.cantidad > pendiente:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"Solo quedan {pendiente} unidades pendientes en ese renglon")
        producto = db.get(Producto, detalle.producto_id)

        if producto.requiere_imei:
            if len(item.imeis) != item.cantidad:
                raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                    f"'{producto.nombre}' exige un IMEI por unidad: "
                                    f"recibe {item.cantidad} y envio {len(item.imeis)} IMEI")
            for imei in item.imeis:
                if db.scalars(select(EquipoImei).where(EquipoImei.imei == imei)).first():
                    raise HTTPException(status.HTTP_409_CONFLICT, f"El IMEI {imei} ya esta registrado")
                equipo = EquipoImei(producto_id=producto.id, orden_compra_detalle_id=detalle.id,
                                    imei=imei, costo=detalle.costo_unitario)
                db.add(equipo)
                db.flush()
                registrar_movimiento(db, producto, TipoMovimiento.ENTRADA, 1, usuario, equipo,
                                     motivo="Recepcion de compra", referencia=orden.numero)
        else:
            producto.stock_actual += item.cantidad
            db.flush()
            registrar_movimiento(db, producto, TipoMovimiento.ENTRADA, item.cantidad, usuario,
                                 motivo="Recepcion de compra", referencia=orden.numero)
        detalle.cantidad_recibida += item.cantidad

    db.flush()
    completa = all(d.cantidad_recibida >= d.cantidad_pedida for d in orden.detalles)
    orden.estado = EstadoOrdenCompra.RECIBIDA if completa else EstadoOrdenCompra.RECIBIDA_PARCIAL
    if completa:
        orden.fecha_recepcion = datetime.now(timezone.utc).date()
    db.commit()
    db.refresh(orden)
    return orden

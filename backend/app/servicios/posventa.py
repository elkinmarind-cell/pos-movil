"""Devoluciones, garantias, apartados y servicio tecnico."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from ..dinero import dinero
from ..models import (Apartado, Devolucion, DevolucionDetalle, EquipoImei, EstadoApartado,
                      EstadoGarantia, EstadoImei, EstadoServicio, EstadoVenta, Garantia, NotaCredito,
                      OrdenServicio, Pago, Producto, TipoMovimiento, TipoReembolso, Usuario, Venta,
                      VentaDetalle, FacturaElectronica)
from .inventario import registrar_movimiento
from . import caja


# ----------------------------------------------------------------- devoluciones
def crear_devolucion(db: Session, datos, usuario: Usuario) -> Devolucion:
    venta = db.get(Venta, datos.venta_id)
    if venta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La venta no existe")
    if venta.estado == EstadoVenta.ANULADA:
        raise HTTPException(status.HTTP_409_CONFLICT, "No se puede devolver sobre una venta anulada")

    devolucion = Devolucion(venta_id=venta.id, usuario_id=usuario.id, motivo=datos.motivo,
                            tipo_reembolso=datos.tipo_reembolso, total=0)
    db.add(devolucion)
    db.flush()

    total = Decimal("0")
    for item in datos.items:
        detalle = db.get(VentaDetalle, item.venta_detalle_id)
        if detalle is None or detalle.venta_id != venta.id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Ese renglon no pertenece a la venta")
        devueltas = db.scalar(select(func.coalesce(func.sum(DevolucionDetalle.cantidad), 0))
                              .where(DevolucionDetalle.venta_detalle_id == detalle.id)) or 0
        if item.cantidad > detalle.cantidad - devueltas:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"Solo quedan {detalle.cantidad - devueltas} unidades por devolver")
        valor = dinero(detalle.total_linea / detalle.cantidad * item.cantidad)
        db.add(DevolucionDetalle(devolucion_id=devolucion.id, venta_detalle_id=detalle.id,
                                 cantidad=item.cantidad, valor=valor,
                                 reingresa_inventario=item.reingresa_inventario))
        total += valor

        if item.reingresa_inventario:
            producto = db.get(Producto, detalle.producto_id)
            if detalle.equipo_imei_id:
                equipo = db.get(EquipoImei, detalle.equipo_imei_id)
                equipo.estado = EstadoImei.DEVUELTO
                db.flush()
                registrar_movimiento(db, producto, TipoMovimiento.DEVOLUCION, 1, usuario, equipo,
                                     motivo=f"Devolucion: {datos.motivo}", referencia=venta.numero)
            else:
                producto.stock_actual += item.cantidad
                db.flush()
                registrar_movimiento(db, producto, TipoMovimiento.DEVOLUCION, item.cantidad, usuario,
                                     motivo=f"Devolucion: {datos.motivo}", referencia=venta.numero)
        # la garantia de lo devuelto deja de tener sentido
        g = db.scalars(select(Garantia).where(Garantia.venta_detalle_id == detalle.id)).first()
        if g is not None and item.cantidad == detalle.cantidad:
            db.delete(g)

    devolucion.total = dinero(total)
    db.flush()

    if datos.tipo_reembolso == TipoReembolso.NOTA_CREDITO:
        factura = db.scalars(select(FacturaElectronica)
                             .where(FacturaElectronica.venta_id == venta.id)).first()
        if factura is not None:
            import hashlib
            n = (db.scalar(select(func.count(NotaCredito.id))) or 0) + 1
            db.add(NotaCredito(
                factura_id=factura.id, devolucion_id=devolucion.id, numero=f"NC{n:06d}",
                cude=hashlib.sha384(f"{factura.numero}{devolucion.id}{total}".encode()).hexdigest(),
                valor=dinero(total)))
    db.commit()
    db.refresh(devolucion)
    return devolucion


# ----------------------------------------------------------------- garantias
def dias_restantes(g: Garantia) -> int:
    return max((g.fecha_fin - datetime.now(timezone.utc).date()).days, 0)


def actualizar_vencidas(db: Session) -> None:
    db.execute(text("CALL sp_actualizar_garantias_vencidas()"))
    db.commit()


def reclamar_garantia(db: Session, garantia: Garantia, falla: str, usuario: Usuario) -> OrdenServicio:
    hoy = datetime.now(timezone.utc).date()
    if garantia.fecha_fin < hoy:
        garantia.estado = EstadoGarantia.VENCIDA
        db.commit()
        raise HTTPException(status.HTTP_409_CONFLICT, f"La garantia vencio el {garantia.fecha_fin}")
    if garantia.estado == EstadoGarantia.EN_RECLAMACION:
        raise HTTPException(status.HTTP_409_CONFLICT, "Esa garantia ya tiene una reclamacion abierta")

    detalle = db.get(VentaDetalle, garantia.venta_detalle_id)
    venta = db.get(Venta, detalle.venta_id)
    if venta.cliente_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "La venta fue a consumidor final: registre el cliente antes de reclamar")
    garantia.estado = EstadoGarantia.EN_RECLAMACION
    if detalle.equipo_imei_id:
        equipo = db.get(EquipoImei, detalle.equipo_imei_id)
        equipo.estado = EstadoImei.EN_SERVICIO
    orden = OrdenServicio(cliente_id=venta.cliente_id, equipo_imei_id=detalle.equipo_imei_id,
                          equipo_externo=None if detalle.equipo_imei_id else "Producto sin IMEI",
                          garantia_id=garantia.id, numero=_numero_servicio(db),
                          falla_reportada=falla, costo_mano_obra=0,
                          estado=EstadoServicio.RECIBIDO)
    db.add(orden)
    db.commit()
    db.refresh(orden)
    return orden


# ----------------------------------------------------------------- servicio tecnico
def _numero_servicio(db: Session) -> str:
    anio = datetime.now(timezone.utc).year
    n = db.scalar(select(func.count(OrdenServicio.id)).where(
        OrdenServicio.numero.like(f"OS-{anio}-%"))) or 0
    return f"OS-{anio}-{n + 1:04d}"


def crear_orden_servicio(db: Session, datos, usuario: Usuario) -> OrdenServicio:
    equipo = None
    if datos.imei:
        equipo = db.scalars(select(EquipoImei).where(EquipoImei.imei == datos.imei)).first()
        if equipo is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND,
                                f"El IMEI {datos.imei} no esta en el sistema; "
                                f"registrelo como equipo externo")
        equipo.estado = EstadoImei.EN_SERVICIO
    elif not datos.equipo_externo:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Indique el IMEI del equipo o una descripcion del equipo externo")
    orden = OrdenServicio(cliente_id=datos.cliente_id, equipo_imei_id=equipo.id if equipo else None,
                          equipo_externo=datos.equipo_externo, garantia_id=datos.garantia_id,
                          numero=_numero_servicio(db), falla_reportada=datos.falla_reportada,
                          costo_mano_obra=dinero(datos.costo_mano_obra),
                          estado=EstadoServicio.RECIBIDO)
    db.add(orden)
    db.commit()
    db.refresh(orden)
    return orden


def actualizar_orden_servicio(db: Session, orden: OrdenServicio, datos, usuario: Usuario) -> OrdenServicio:
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(orden, campo, valor)
    if datos.estado == EstadoServicio.ENTREGADO:
        orden.fecha_entrega = datetime.now(timezone.utc)
        if orden.equipo_imei_id:
            equipo = db.get(EquipoImei, orden.equipo_imei_id)
            if equipo.estado == EstadoImei.EN_SERVICIO:
                equipo.estado = EstadoImei.VENDIDO
        if orden.garantia_id:
            g = db.get(Garantia, orden.garantia_id)
            if g and g.estado == EstadoGarantia.EN_RECLAMACION:
                g.estado = EstadoGarantia.ATENDIDA
    db.commit()
    db.refresh(orden)
    return orden


# ----------------------------------------------------------------- apartados
def crear_apartado(db: Session, datos, usuario: Usuario) -> Apartado:
    equipo = db.scalars(select(EquipoImei).where(EquipoImei.imei == datos.imei)).first()
    if equipo is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"El IMEI {datos.imei} no esta en inventario")
    if equipo.estado != EstadoImei.DISPONIBLE:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            f"El equipo no esta disponible (estado {equipo.estado.value})")
    producto = db.get(Producto, equipo.producto_id)
    valor = dinero(producto.precio_venta * (1 + dinero(producto.iva_porcentaje) / 100))
    if datos.abono_inicial > valor:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El abono inicial supera el valor del equipo")

    turno = caja.exigir_turno(db, usuario) if datos.abono_inicial > 0 else None
    apartado = Apartado(cliente_id=datos.cliente_id, equipo_imei_id=equipo.id,
                        fecha_limite=date.today() + timedelta(days=datos.dias_plazo),
                        valor_total=valor, saldo_pendiente=valor)
    db.add(apartado)
    db.flush()
    if datos.abono_inicial > 0:
        db.add(Pago(apartado_id=apartado.id, turno_caja_id=turno.id, metodo=datos.metodo,
                    valor=dinero(datos.abono_inicial), referencia="Abono inicial"))
    db.commit()
    db.refresh(apartado)
    return apartado


def abonar(db: Session, apartado: Apartado, datos, usuario: Usuario) -> Apartado:
    if apartado.estado != EstadoApartado.VIGENTE:
        raise HTTPException(status.HTTP_409_CONFLICT, f"El apartado esta {apartado.estado.value}")
    if dinero(datos.valor) > apartado.saldo_pendiente:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"El abono supera el saldo pendiente ({apartado.saldo_pendiente})")
    turno = caja.exigir_turno(db, usuario)
    db.add(Pago(apartado_id=apartado.id, turno_caja_id=turno.id, metodo=datos.metodo,
                valor=dinero(datos.valor), referencia=datos.referencia))
    db.commit()
    db.refresh(apartado)
    return apartado

"""Reglas de negocio del POS. Aisladas de la capa HTTP para poder probarlas."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from .config import settings
from .models import (
    EquipoImei, EstadoGarantia, EstadoImei, EstadoVenta, Garantia,
    MovimientoInventario, Producto, TipoMovimiento, Usuario, Venta, VentaDetalle,
)
from .schemas import VentaCreate

CENTAVO = Decimal("0.01")


def dinero(valor: Decimal | float | int) -> Decimal:
    """Redondeo monetario consistente en todo el sistema (2 decimales, mitad arriba)."""
    return Decimal(str(valor)).quantize(CENTAVO, rounding=ROUND_HALF_UP)


# --------------------------------------------------------------------------
# Inventario
# --------------------------------------------------------------------------
def disponibles_de(db: Session, producto: Producto) -> int:
    """Unidades vendibles: IMEI en estado disponible, o stock_actual para accesorios."""
    if producto.requiere_imei:
        return (
            db.query(func.count(EquipoImei.id))
            .filter(
                EquipoImei.producto_id == producto.id,
                EquipoImei.estado == EstadoImei.DISPONIBLE,
            )
            .scalar()
            or 0
        )
    return producto.stock_actual


def registrar_movimiento(
    db: Session,
    producto: Producto,
    tipo: TipoMovimiento,
    cantidad: int,
    usuario: Usuario | None = None,
    equipo: EquipoImei | None = None,
    motivo: str | None = None,
    referencia: str | None = None,
) -> MovimientoInventario:
    movimiento = MovimientoInventario(
        producto_id=producto.id,
        equipo_imei_id=equipo.id if equipo else None,
        tipo=tipo,
        cantidad=cantidad,
        stock_resultante=disponibles_de(db, producto),
        motivo=motivo,
        referencia=referencia,
        usuario_id=usuario.id if usuario else None,
    )
    db.add(movimiento)
    return movimiento


# --------------------------------------------------------------------------
# Facturacion
# --------------------------------------------------------------------------
def siguiente_numero_factura(db: Session) -> str:
    """Consecutivo tipo FV-2026-000123. En produccion lo asignaria la DIAN."""
    anio = datetime.now(timezone.utc).year
    prefijo = f"FV-{anio}-"
    ultimo = (
        db.query(Venta.numero_factura)
        .filter(Venta.numero_factura.like(f"{prefijo}%"))
        .order_by(Venta.numero_factura.desc())
        .first()
    )
    consecutivo = int(ultimo[0].split("-")[-1]) + 1 if ultimo else 1
    return f"{prefijo}{consecutivo:06d}"


def _sumar_meses(inicio: date, meses: int) -> date:
    mes = inicio.month - 1 + meses
    anio = inicio.year + mes // 12
    mes = mes % 12 + 1
    dias_mes = [31, 29 if (anio % 4 == 0 and anio % 100 != 0) or anio % 400 == 0 else 28,
                31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mes - 1]
    return date(anio, mes, min(inicio.day, dias_mes))


def procesar_venta(db: Session, datos: VentaCreate, usuario: Usuario) -> Venta:
    """Valida stock/IMEI, calcula impuestos, descuenta inventario y genera garantias.

    Todo ocurre dentro de una sola transaccion: si una linea falla, no se vende nada.
    """
    venta = Venta(
        numero_factura=siguiente_numero_factura(db),
        cliente_id=datos.cliente_id,
        usuario_id=usuario.id,
        metodo_pago=datos.metodo_pago,
        observaciones=datos.observaciones,
        estado=EstadoVenta.COMPLETADA,
    )
    db.add(venta)
    db.flush()

    subtotal = Decimal("0")
    descuento_total = Decimal("0")
    iva_total = Decimal("0")
    imeis_usados: set[str] = set()

    for item in datos.items:
        producto = db.get(Producto, item.producto_id)
        if not producto or not producto.activo:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Producto {item.producto_id} no existe o esta inactivo")

        equipo: EquipoImei | None = None

        if producto.requiere_imei:
            if item.cantidad != 1:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"'{producto.nombre}' se vende por unidad serializada: una linea por IMEI",
                )
            if not item.imei:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"'{producto.nombre}' requiere IMEI y no se envio ninguno",
                )
            if item.imei in imeis_usados:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, f"El IMEI {item.imei} esta repetido en la factura")
            equipo = db.query(EquipoImei).filter(EquipoImei.imei == item.imei).with_for_update(nowait=False).first() \
                if settings.es_postgres else db.query(EquipoImei).filter(EquipoImei.imei == item.imei).first()
            if not equipo:
                raise HTTPException(status.HTTP_404_NOT_FOUND, f"El IMEI {item.imei} no existe en inventario")
            if equipo.producto_id != producto.id:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    f"El IMEI {item.imei} no corresponde al producto '{producto.nombre}'",
                )
            if equipo.estado != EstadoImei.DISPONIBLE:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    f"El IMEI {item.imei} no esta disponible (estado actual: {equipo.estado.value})",
                )
            imeis_usados.add(item.imei)
        else:
            if producto.stock_actual < item.cantidad:
                raise HTTPException(
                    status.HTTP_409_CONFLICT,
                    f"Stock insuficiente de '{producto.nombre}': disponibles {producto.stock_actual}, "
                    f"solicitadas {item.cantidad}",
                )

        precio = dinero(producto.precio_venta)
        descuento = dinero(item.descuento)
        bruto = dinero(precio * item.cantidad)
        if descuento > bruto:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "El descuento no puede superar el valor de la linea")

        base = dinero(bruto - descuento)
        iva_pct = dinero(producto.iva_porcentaje)
        iva = dinero(base * iva_pct / Decimal("100"))
        total_linea = dinero(base + iva)

        descripcion = producto.nombre
        if equipo:
            descripcion = f"{producto.nombre} - IMEI {equipo.imei}"

        detalle = VentaDetalle(
            venta_id=venta.id,
            producto_id=producto.id,
            equipo_imei_id=equipo.id if equipo else None,
            descripcion=descripcion,
            cantidad=item.cantidad,
            precio_unitario=precio,
            descuento=descuento,
            iva_porcentaje=iva_pct,
            base_gravable=base,
            iva_valor=iva,
            total_linea=total_linea,
        )
        db.add(detalle)
        db.flush()

        # Descuento de inventario
        if equipo:
            equipo.estado = EstadoImei.VENDIDO
            registrar_movimiento(
                db, producto, TipoMovimiento.SALIDA, 1, usuario, equipo,
                motivo="Venta", referencia=venta.numero_factura,
            )
        else:
            producto.stock_actual -= item.cantidad
            registrar_movimiento(
                db, producto, TipoMovimiento.SALIDA, item.cantidad, usuario,
                motivo="Venta", referencia=venta.numero_factura,
            )

        # Garantia automatica
        meses = producto.meses_garantia or settings.meses_garantia_default
        if meses > 0:
            inicio = datetime.now(timezone.utc).date()
            db.add(
                Garantia(
                    venta_detalle_id=detalle.id,
                    cliente_id=datos.cliente_id,
                    equipo_imei_id=equipo.id if equipo else None,
                    fecha_inicio=inicio,
                    fecha_fin=_sumar_meses(inicio, meses),
                    meses=meses,
                    estado=EstadoGarantia.VIGENTE,
                )
            )

        subtotal += base
        descuento_total += descuento
        iva_total += iva

    venta.subtotal = dinero(subtotal)
    venta.descuento_total = dinero(descuento_total)
    venta.iva_total = dinero(iva_total)
    venta.total = dinero(subtotal + iva_total)

    db.commit()
    db.refresh(venta)
    return venta


def anular_venta(db: Session, venta: Venta, motivo: str, usuario: Usuario) -> Venta:
    """Reversa completa: devuelve IMEI a disponible, repone stock y anula garantias."""
    if venta.estado == EstadoVenta.ANULADA:
        raise HTTPException(status.HTTP_409_CONFLICT, "La venta ya estaba anulada")

    for detalle in venta.detalles:
        producto = db.get(Producto, detalle.producto_id)
        if detalle.equipo_imei_id:
            equipo = db.get(EquipoImei, detalle.equipo_imei_id)
            if equipo:
                equipo.estado = EstadoImei.DISPONIBLE
                registrar_movimiento(
                    db, producto, TipoMovimiento.DEVOLUCION, 1, usuario, equipo,
                    motivo=f"Anulacion: {motivo}", referencia=venta.numero_factura,
                )
        else:
            producto.stock_actual += detalle.cantidad
            registrar_movimiento(
                db, producto, TipoMovimiento.DEVOLUCION, detalle.cantidad, usuario,
                motivo=f"Anulacion: {motivo}", referencia=venta.numero_factura,
            )
        if detalle.garantia:
            db.delete(detalle.garantia)

    venta.estado = EstadoVenta.ANULADA
    venta.motivo_anulacion = motivo
    db.commit()
    db.refresh(venta)
    return venta


def actualizar_garantias_vencidas(db: Session) -> int:
    """Marca como vencidas las garantias cuya fecha_fin ya paso."""
    hoy = datetime.now(timezone.utc).date()
    afectadas = (
        db.query(Garantia)
        .filter(Garantia.estado == EstadoGarantia.VIGENTE, Garantia.fecha_fin < hoy)
        .update({Garantia.estado: EstadoGarantia.VENCIDA}, synchronize_session=False)
    )
    db.commit()
    return afectadas

"""Proceso de venta.

Reparto de responsabilidades: la aplicacion valida, calcula el dinero y arma la factura;
la base de datos (triggers) descuenta inventario, escribe el kardex y crea la garantia.
Asi la regla vale aunque alguien inserte por fuera de la API.
"""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib

from fastapi import HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from ..config import settings
from ..dinero import dinero
from ..models import (EquipoImei, EstadoImei, EstadoVenta, FacturaElectronica, Pago, Producto,
                      Promocion, TipoDescuento, Usuario, Venta, VentaDetalle)
from . import caja


def _error_bd(exc: DBAPIError) -> HTTPException:
    """Convierte el mensaje de un RAISE EXCEPTION de PostgreSQL en un 409 legible."""
    original = getattr(exc, "orig", None)
    mensaje = str(getattr(original, "diag", None) and original.diag.message_primary or original or exc)
    return HTTPException(status.HTTP_409_CONFLICT, mensaje.strip())


def _precio_con_promocion(db: Session, producto: Producto, promocion_id: int | None) -> Decimal:
    precio = dinero(producto.precio_venta)
    if not promocion_id:
        return precio
    promo = db.get(Promocion, promocion_id)
    if promo is None or not promo.activa:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La promocion no existe o no esta activa")
    hoy = datetime.now(timezone.utc).date()
    if not (promo.fecha_inicio <= hoy <= promo.fecha_fin):
        raise HTTPException(status.HTTP_409_CONFLICT, "La promocion no esta vigente")
    if promo.tipo_descuento == TipoDescuento.PORCENTAJE:
        return dinero(precio - precio * dinero(promo.valor) / 100)
    return dinero(max(precio - dinero(promo.valor), Decimal("0")))


def procesar_venta(db: Session, datos, usuario: Usuario) -> Venta:
    turno = caja.exigir_turno(db, usuario)

    lineas, subtotal, iva_total, descuento_total = [], Decimal("0"), Decimal("0"), Decimal("0")
    imeis_usados: set[str] = set()

    for item in datos.items:
        producto = db.get(Producto, item.producto_id)
        if producto is None or not producto.activo:
            raise HTTPException(status.HTTP_404_NOT_FOUND,
                                f"El producto {item.producto_id} no existe o esta inactivo")
        equipo = None
        if producto.requiere_imei:
            if item.cantidad != 1:
                raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                    f"'{producto.nombre}' se vende por unidad: una linea por IMEI")
            if not item.imei:
                raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                    f"'{producto.nombre}' requiere IMEI y no se envio ninguno")
            if item.imei in imeis_usados:
                raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                    f"El IMEI {item.imei} esta repetido en la factura")
            equipo = db.scalars(select(EquipoImei).where(EquipoImei.imei == item.imei)).first()
            if equipo is None:
                raise HTTPException(status.HTTP_404_NOT_FOUND, f"El IMEI {item.imei} no esta en inventario")
            if equipo.producto_id != producto.id:
                raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                    f"El IMEI {item.imei} no corresponde a '{producto.nombre}'")
            if equipo.estado not in (EstadoImei.DISPONIBLE, EstadoImei.APARTADO):
                raise HTTPException(status.HTTP_409_CONFLICT,
                                    f"El IMEI {item.imei} no esta disponible (estado {equipo.estado.value})")
            imeis_usados.add(item.imei)
        elif producto.stock_actual < item.cantidad:
            raise HTTPException(status.HTTP_409_CONFLICT,
                                f"Stock insuficiente de '{producto.nombre}': hay {producto.stock_actual}, "
                                f"piden {item.cantidad}")

        precio = _precio_con_promocion(db, producto, item.promocion_id)
        bruto = dinero(precio * item.cantidad)
        desc = dinero(item.descuento)
        if desc > bruto:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                "El descuento no puede superar el valor de la linea")
        base = dinero(bruto - desc)
        iva_pct = dinero(producto.iva_porcentaje)
        iva = dinero(base * iva_pct / 100)
        lineas.append(dict(producto_id=producto.id, equipo_imei_id=equipo.id if equipo else None,
                           promocion_id=item.promocion_id, cantidad=item.cantidad,
                           precio_unitario=precio, descuento=desc, iva_porcentaje=iva_pct,
                           iva_valor=iva, total_linea=dinero(base + iva)))
        subtotal += base
        iva_total += iva
        descuento_total += desc

    total = dinero(subtotal + iva_total)
    pagado = dinero(sum(dinero(p.valor) for p in datos.pagos))
    if pagado != total:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            f"Los pagos suman {pagado} y el total es {total}")

    try:
        numero = db.scalar(text("SELECT fn_siguiente_numero(:r)"), {"r": settings.resolucion_dian_id})
        venta = Venta(cliente_id=datos.cliente_id, usuario_id=usuario.id, turno_caja_id=turno.id,
                      numero=numero, subtotal=dinero(subtotal), descuento_total=dinero(descuento_total),
                      iva_total=dinero(iva_total), total=total, observaciones=datos.observaciones)
        db.add(venta)
        db.flush()
        for linea in lineas:
            db.add(VentaDetalle(venta_id=venta.id, **linea))
        db.flush()
        for p in datos.pagos:
            db.add(Pago(venta_id=venta.id, turno_caja_id=turno.id, metodo=p.metodo,
                        valor=dinero(p.valor), referencia=p.referencia))
        cufe = hashlib.sha384(f"{numero}{total}{datos.cliente_id}{venta.id}".encode()).hexdigest()
        db.add(FacturaElectronica(
            venta_id=venta.id, resolucion_id=settings.resolucion_dian_id, numero=numero, cufe=cufe,
            xml_firmado=f"<?xml version='1.0'?><Invoice><ID>{numero}</ID><Total>{total}</Total></Invoice>"))
        db.commit()
    except DBAPIError as exc:
        db.rollback()
        raise _error_bd(exc) from exc
    db.refresh(venta)
    return venta


def anular_venta(db: Session, venta: Venta, motivo: str, usuario: Usuario) -> Venta:
    """La reversa completa la hace la funcion fn_anular_venta en PostgreSQL."""
    if venta.estado == EstadoVenta.ANULADA:
        raise HTTPException(status.HTTP_409_CONFLICT, "La venta ya estaba anulada")
    try:
        db.execute(text("SELECT fn_anular_venta(:v, :m, :u)"),
                   {"v": venta.id, "m": motivo, "u": usuario.id})
        db.commit()
    except DBAPIError as exc:
        db.rollback()
        raise _error_bd(exc) from exc
    db.refresh(venta)
    return venta

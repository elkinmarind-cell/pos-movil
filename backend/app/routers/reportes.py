"""Reportes. Se apoyan en las vistas de PostgreSQL: la logica de consulta vive en la base."""
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import requiere, usuario_actual
from ..dinero import dinero
from ..models import (Alerta, Apartado, EquipoImei, EstadoApartado, EstadoGarantia, EstadoImei,
                      EstadoServicio, EstadoVenta, Garantia, OrdenServicio, Usuario, Venta)
from ..schemas import (AlertaStock, Dashboard, ProductoMasVendido, Rentabilidad, TrazabilidadImei,
                       VentaPorDia)
from ..servicios import caja as svc_caja

router = APIRouter(prefix="/api/reportes", tags=["Reportes"],
                   dependencies=[Depends(requiere("reportes.ver"))])


def _inicio_dia(dias_atras: int = 0) -> datetime:
    dia = datetime.now(timezone.utc).date() - timedelta(days=dias_atras)
    return datetime.combine(dia, time.min, tzinfo=timezone.utc)


@router.get("/dashboard", response_model=Dashboard, summary="Indicadores principales")
def dashboard(db: Session = Depends(get_db), usuario: Usuario = Depends(usuario_actual)):
    db.execute(text("CALL sp_actualizar_garantias_vencidas()"))
    db.execute(text("CALL sp_vencer_apartados()"))
    db.commit()

    hoy = _inicio_dia()
    inicio_mes = datetime.combine(datetime.now(timezone.utc).date().replace(day=1),
                                  time.min, tzinfo=timezone.utc)
    completadas = select(Venta).where(Venta.estado == EstadoVenta.COMPLETADA)

    total_hoy = db.scalar(select(func.coalesce(func.sum(Venta.total), 0))
                          .where(Venta.estado == EstadoVenta.COMPLETADA, Venta.fecha >= hoy))
    num_hoy = db.scalar(select(func.count()).select_from(completadas.where(Venta.fecha >= hoy).subquery()))
    total_mes = db.scalar(select(func.coalesce(func.sum(Venta.total), 0))
                          .where(Venta.estado == EstadoVenta.COMPLETADA, Venta.fecha >= inicio_mes))
    num_mes = db.scalar(select(func.count()).select_from(completadas.where(Venta.fecha >= inicio_mes).subquery()))

    bajo_stock = db.execute(text("SELECT COUNT(*) FROM v_alertas_stock")).scalar() or 0

    return Dashboard(
        ventas_hoy=dinero(total_hoy), numero_ventas_hoy=num_hoy or 0,
        ventas_mes=dinero(total_mes), numero_ventas_mes=num_mes or 0,
        ticket_promedio_mes=dinero(Decimal(str(total_mes)) / num_mes) if num_mes else Decimal("0.00"),
        equipos_disponibles=db.scalar(select(func.count(EquipoImei.id))
                                      .where(EquipoImei.estado == EstadoImei.DISPONIBLE)) or 0,
        productos_bajo_stock=bajo_stock,
        garantias_vigentes=db.scalar(select(func.count(Garantia.id))
                                     .where(Garantia.estado == EstadoGarantia.VIGENTE)) or 0,
        ordenes_servicio_abiertas=db.scalar(select(func.count(OrdenServicio.id)).where(
            OrdenServicio.estado.notin_([EstadoServicio.ENTREGADO]))) or 0,
        apartados_vigentes=db.scalar(select(func.count(Apartado.id))
                                     .where(Apartado.estado == EstadoApartado.VIGENTE)) or 0,
        alertas_sin_atender=db.scalar(select(func.count(Alerta.id))
                                      .where(Alerta.fecha_atencion.is_(None))) or 0,
        turno_abierto=svc_caja.turno_abierto(db, usuario) is not None,
    )


@router.get("/ventas-por-dia", response_model=list[VentaPorDia], summary="Serie diaria")
def ventas_por_dia(dias: int = Query(14, ge=1, le=90), db: Session = Depends(get_db)):
    filas = {r["dia"].isoformat(): r for r in db.execute(text(
        "SELECT dia, total, numero_ventas FROM v_ventas_diarias WHERE dia >= :d"),
        {"d": _inicio_dia(dias - 1).date()}).mappings()}
    salida = []
    for i in range(dias):
        clave = (datetime.now(timezone.utc).date() - timedelta(days=dias - 1 - i)).isoformat()
        fila = filas.get(clave)
        salida.append(VentaPorDia(fecha=clave,
                                  total=dinero(fila["total"]) if fila else Decimal("0.00"),
                                  cantidad=fila["numero_ventas"] if fila else 0))
    return salida


@router.get("/mas-vendidos", response_model=list[ProductoMasVendido], summary="Productos mas vendidos")
def mas_vendidos(limite: int = Query(10, le=50), db: Session = Depends(get_db)):
    filas = db.execute(text("SELECT producto_id, nombre, unidades, ingreso_sin_iva "
                            "FROM v_rentabilidad_producto ORDER BY unidades DESC LIMIT :l"),
                       {"l": limite}).mappings()
    return [ProductoMasVendido(producto_id=f["producto_id"], nombre=f["nombre"],
                               unidades=int(f["unidades"]), total_vendido=dinero(f["ingreso_sin_iva"]))
            for f in filas]


@router.get("/rentabilidad", response_model=list[Rentabilidad], summary="Rentabilidad por producto")
def rentabilidad(db: Session = Depends(get_db)):
    return [Rentabilidad(producto_id=f["producto_id"], sku=f["sku"], nombre=f["nombre"],
                         unidades=int(f["unidades"]), ingreso_sin_iva=dinero(f["ingreso_sin_iva"]),
                         costo=dinero(f["costo"]), utilidad=dinero(f["utilidad"]))
            for f in db.execute(text("SELECT * FROM v_rentabilidad_producto")).mappings()]


@router.get("/alertas-stock", response_model=list[AlertaStock], summary="Productos bajo el minimo")
def alertas_stock(db: Session = Depends(get_db)):
    return [AlertaStock(producto_id=f["producto_id"], sku=f["sku"], nombre=f["nombre"],
                        disponibles=int(f["disponibles"]), stock_minimo=int(f["stock_minimo"]))
            for f in db.execute(text("SELECT * FROM v_alertas_stock")).mappings()]


@router.get("/trazabilidad/{imei}", response_model=TrazabilidadImei, summary="Historia de un equipo")
def trazabilidad(imei: str, db: Session = Depends(get_db)):
    from fastapi import HTTPException, status
    fila = db.execute(text("SELECT * FROM v_trazabilidad_imei WHERE imei = :i"), {"i": imei}).mappings().first()
    if fila is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Ese IMEI no esta en el sistema")
    return TrazabilidadImei(**dict(fila))

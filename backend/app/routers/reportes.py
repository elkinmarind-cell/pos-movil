from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import usuario_actual
from ..models import (
    EquipoImei, EstadoGarantia, EstadoImei, EstadoVenta,
    Garantia, Producto, Venta, VentaDetalle,
)
from ..schemas import AlertaStock, ProductoMasVendido, ResumenDashboard, VentaPorDia
from ..services import actualizar_garantias_vencidas, disponibles_de, dinero

router = APIRouter(prefix="/api/reportes", tags=["Reportes"], dependencies=[Depends(usuario_actual)])


def _inicio_dia(dias_atras: int = 0) -> datetime:
    dia = datetime.now(timezone.utc).date() - timedelta(days=dias_atras)
    return datetime.combine(dia, time.min, tzinfo=timezone.utc)


@router.get("/dashboard", response_model=ResumenDashboard, summary="Indicadores principales")
def dashboard(db: Session = Depends(get_db)):
    actualizar_garantias_vencidas(db)
    hoy = _inicio_dia()
    inicio_mes = datetime.combine(
        datetime.now(timezone.utc).date().replace(day=1), time.min, tzinfo=timezone.utc
    )

    base = db.query(Venta).filter(Venta.estado == EstadoVenta.COMPLETADA)

    total_hoy = base.filter(Venta.fecha >= hoy).with_entities(func.coalesce(func.sum(Venta.total), 0)).scalar()
    num_hoy = base.filter(Venta.fecha >= hoy).count()
    total_mes = base.filter(Venta.fecha >= inicio_mes).with_entities(func.coalesce(func.sum(Venta.total), 0)).scalar()
    num_mes = base.filter(Venta.fecha >= inicio_mes).count()

    equipos = db.query(func.count(EquipoImei.id)).filter(EquipoImei.estado == EstadoImei.DISPONIBLE).scalar() or 0

    bajo_stock = 0
    for producto in db.query(Producto).filter(Producto.activo.is_(True)).all():
        if disponibles_de(db, producto) <= producto.stock_minimo:
            bajo_stock += 1

    vigentes = db.query(func.count(Garantia.id)).filter(Garantia.estado == EstadoGarantia.VIGENTE).scalar() or 0
    reclamos = db.query(func.count(Garantia.id)).filter(
        Garantia.estado == EstadoGarantia.EN_RECLAMACION).scalar() or 0

    return ResumenDashboard(
        ventas_hoy=dinero(total_hoy),
        numero_ventas_hoy=num_hoy,
        ventas_mes=dinero(total_mes),
        numero_ventas_mes=num_mes,
        ticket_promedio_mes=dinero(Decimal(str(total_mes)) / num_mes) if num_mes else Decimal("0.00"),
        equipos_disponibles=equipos,
        productos_bajo_stock=bajo_stock,
        garantias_vigentes=vigentes,
        garantias_en_reclamacion=reclamos,
    )


@router.get("/ventas-por-dia", response_model=list[VentaPorDia], summary="Serie diaria de ventas")
def ventas_por_dia(dias: int = Query(14, ge=1, le=90), db: Session = Depends(get_db)):
    desde = _inicio_dia(dias - 1)
    ventas = (
        db.query(Venta)
        .filter(Venta.estado == EstadoVenta.COMPLETADA, Venta.fecha >= desde)
        .all()
    )
    acumulado: dict[str, dict] = {}
    for i in range(dias):
        clave = (datetime.now(timezone.utc).date() - timedelta(days=dias - 1 - i)).isoformat()
        acumulado[clave] = {"total": Decimal("0"), "cantidad": 0}
    for venta in ventas:
        clave = venta.fecha.date().isoformat()
        if clave in acumulado:
            acumulado[clave]["total"] += Decimal(str(venta.total))
            acumulado[clave]["cantidad"] += 1
    return [
        VentaPorDia(fecha=fecha, total=dinero(datos["total"]), cantidad=datos["cantidad"])
        for fecha, datos in acumulado.items()
    ]


@router.get("/mas-vendidos", response_model=list[ProductoMasVendido], summary="Productos mas vendidos")
def mas_vendidos(limite: int = Query(10, le=50), dias: int = Query(30, ge=1, le=365),
                 db: Session = Depends(get_db)):
    desde = _inicio_dia(dias - 1)
    filas = (
        db.query(
            VentaDetalle.producto_id,
            Producto.nombre,
            func.sum(VentaDetalle.cantidad).label("unidades"),
            func.sum(VentaDetalle.total_linea).label("total"),
        )
        .join(Venta, Venta.id == VentaDetalle.venta_id)
        .join(Producto, Producto.id == VentaDetalle.producto_id)
        .filter(Venta.estado == EstadoVenta.COMPLETADA, Venta.fecha >= desde)
        .group_by(VentaDetalle.producto_id, Producto.nombre)
        .order_by(func.sum(VentaDetalle.cantidad).desc())
        .limit(limite)
        .all()
    )
    return [
        ProductoMasVendido(producto_id=f[0], nombre=f[1], unidades=int(f[2]), total_vendido=dinero(f[3]))
        for f in filas
    ]


@router.get("/alertas-stock", response_model=list[AlertaStock], summary="Productos en o bajo el minimo")
def alertas_stock(db: Session = Depends(get_db)):
    alertas: list[AlertaStock] = []
    for producto in db.query(Producto).filter(Producto.activo.is_(True)).all():
        disponibles = disponibles_de(db, producto)
        if disponibles <= producto.stock_minimo:
            alertas.append(
                AlertaStock(
                    producto_id=producto.id,
                    sku=producto.sku,
                    nombre=producto.nombre,
                    disponibles=disponibles,
                    stock_minimo=producto.stock_minimo,
                )
            )
    return sorted(alertas, key=lambda a: a.disponibles)

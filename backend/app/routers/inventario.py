from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import requiere_roles, usuario_actual
from ..models import EquipoImei, EstadoImei, Producto, RolUsuario, TipoMovimiento, Usuario
from ..schemas import EquipoImeiCreate, EquipoImeiOut
from ..services import registrar_movimiento

router = APIRouter(prefix="/api/inventario", tags=["Inventario / IMEI"], dependencies=[Depends(usuario_actual)])


@router.get("/imei", response_model=list[EquipoImeiOut], summary="Listar equipos por IMEI")
def listar(
    producto_id: int | None = None,
    estado: EstadoImei | None = None,
    q: str | None = Query(None, description="Busqueda parcial por IMEI"),
    limite: int = Query(100, le=500),
    db: Session = Depends(get_db),
):
    consulta = db.query(EquipoImei)
    if producto_id:
        consulta = consulta.filter(EquipoImei.producto_id == producto_id)
    if estado:
        consulta = consulta.filter(EquipoImei.estado == estado)
    if q:
        consulta = consulta.filter(EquipoImei.imei.ilike(f"%{q}%"))
    return consulta.order_by(EquipoImei.fecha_ingreso.desc()).limit(limite).all()


@router.get("/imei/{imei}", response_model=EquipoImeiOut, summary="Consultar un IMEI (trazabilidad)")
def consultar(imei: str, db: Session = Depends(get_db)):
    equipo = db.query(EquipoImei).filter(EquipoImei.imei == imei).first()
    if not equipo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "IMEI no registrado en el inventario")
    return equipo


@router.post("/imei", response_model=EquipoImeiOut, status_code=201, summary="Ingresar equipo al inventario")
def ingresar(
    datos: EquipoImeiCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_roles(RolUsuario.ADMIN, RolUsuario.BODEGA)),
):
    producto = db.get(Producto, datos.producto_id)
    if not producto:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    if not producto.requiere_imei:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Este producto no se controla por IMEI")
    if db.query(EquipoImei).filter(EquipoImei.imei == datos.imei).first():
        raise HTTPException(status.HTTP_409_CONFLICT, f"El IMEI {datos.imei} ya esta registrado")

    equipo = EquipoImei(**datos.model_dump(), estado=EstadoImei.DISPONIBLE)
    db.add(equipo)
    db.flush()
    registrar_movimiento(db, producto, TipoMovimiento.ENTRADA, 1, usuario, equipo,
                         motivo="Ingreso de equipo a bodega")
    db.commit()
    db.refresh(equipo)
    return equipo


@router.post("/imei/lote", response_model=list[EquipoImeiOut], status_code=201, summary="Ingresar lote de equipos")
def ingresar_lote(
    equipos: list[EquipoImeiCreate],
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_roles(RolUsuario.ADMIN, RolUsuario.BODEGA)),
):
    creados: list[EquipoImei] = []
    vistos: set[str] = set()
    for datos in equipos:
        if datos.imei in vistos:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"IMEI {datos.imei} repetido en el lote")
        vistos.add(datos.imei)
        producto = db.get(Producto, datos.producto_id)
        if not producto or not producto.requiere_imei:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                f"Producto {datos.producto_id} invalido para control por IMEI")
        if db.query(EquipoImei).filter(EquipoImei.imei == datos.imei).first():
            raise HTTPException(status.HTTP_409_CONFLICT, f"El IMEI {datos.imei} ya esta registrado")
        equipo = EquipoImei(**datos.model_dump(), estado=EstadoImei.DISPONIBLE)
        db.add(equipo)
        db.flush()
        registrar_movimiento(db, producto, TipoMovimiento.ENTRADA, 1, usuario, equipo, motivo="Ingreso por lote")
        creados.append(equipo)
    db.commit()
    for equipo in creados:
        db.refresh(equipo)
    return creados


@router.patch("/imei/{imei}/estado", response_model=EquipoImeiOut, summary="Cambiar estado de un equipo")
def cambiar_estado(
    imei: str,
    nuevo_estado: EstadoImei,
    motivo: str = Query(..., min_length=3),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_roles(RolUsuario.ADMIN, RolUsuario.BODEGA)),
):
    equipo = db.query(EquipoImei).filter(EquipoImei.imei == imei).first()
    if not equipo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "IMEI no registrado")
    if equipo.estado == EstadoImei.VENDIDO and nuevo_estado == EstadoImei.DISPONIBLE:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Un equipo vendido solo vuelve a disponible anulando la venta correspondiente",
        )
    anterior = equipo.estado.value
    equipo.estado = nuevo_estado
    registrar_movimiento(
        db, equipo.producto, TipoMovimiento.AJUSTE, 1, usuario, equipo,
        motivo=f"{anterior} -> {nuevo_estado.value}: {motivo}",
    )
    db.commit()
    db.refresh(equipo)
    return equipo

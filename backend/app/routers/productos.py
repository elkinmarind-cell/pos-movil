from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import requiere_roles, usuario_actual
from ..models import Categoria, Marca, Producto, RolUsuario, TipoMovimiento, Usuario
from ..schemas import (
    AjusteStock, CategoriaOut, MarcaOut, MovimientoOut,
    ProductoCreate, ProductoOut, ProductoUpdate,
)
from ..services import disponibles_de, registrar_movimiento

router = APIRouter(prefix="/api/productos", tags=["Productos"], dependencies=[Depends(usuario_actual)])


def _salida(db: Session, producto: Producto) -> ProductoOut:
    dto = ProductoOut.model_validate(producto)
    dto.disponibles = disponibles_de(db, producto)
    return dto


@router.get("", response_model=list[ProductoOut], summary="Catalogo de productos")
def listar(
    q: str | None = Query(None, description="Busca por SKU o nombre"),
    categoria_id: int | None = None,
    solo_disponibles: bool = False,
    db: Session = Depends(get_db),
):
    consulta = db.query(Producto).filter(Producto.activo.is_(True))
    if q:
        patron = f"%{q}%"
        consulta = consulta.filter(or_(Producto.sku.ilike(patron), Producto.nombre.ilike(patron)))
    if categoria_id:
        consulta = consulta.filter(Producto.categoria_id == categoria_id)

    productos = [_salida(db, p) for p in consulta.order_by(Producto.nombre).all()]
    if solo_disponibles:
        productos = [p for p in productos if p.disponibles > 0]
    return productos


@router.get("/categorias", response_model=list[CategoriaOut], summary="Categorias")
def categorias(db: Session = Depends(get_db)):
    return db.query(Categoria).order_by(Categoria.nombre).all()


@router.get("/marcas", response_model=list[MarcaOut], summary="Marcas")
def marcas(db: Session = Depends(get_db)):
    return db.query(Marca).order_by(Marca.nombre).all()


@router.post("", response_model=ProductoOut, status_code=201, summary="Crear producto")
def crear(
    datos: ProductoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_roles(RolUsuario.ADMIN, RolUsuario.BODEGA)),
):
    if db.query(Producto).filter(Producto.sku == datos.sku).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un producto con ese SKU")
    producto = Producto(**datos.model_dump())
    db.add(producto)
    db.flush()
    if producto.stock_actual and not producto.requiere_imei:
        registrar_movimiento(db, producto, TipoMovimiento.ENTRADA, producto.stock_actual,
                             usuario, motivo="Carga inicial")
    db.commit()
    db.refresh(producto)
    return _salida(db, producto)


@router.get("/{producto_id}", response_model=ProductoOut, summary="Detalle de producto")
def detalle(producto_id: int, db: Session = Depends(get_db)):
    producto = db.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    return _salida(db, producto)


@router.put("/{producto_id}", response_model=ProductoOut, summary="Actualizar producto")
def actualizar(
    producto_id: int,
    datos: ProductoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_roles(RolUsuario.ADMIN, RolUsuario.BODEGA)),
):
    producto = db.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(producto, campo, valor)
    db.commit()
    db.refresh(producto)
    return _salida(db, producto)


@router.post("/{producto_id}/ajuste-stock", response_model=ProductoOut, summary="Ajustar stock (sin IMEI)")
def ajustar_stock(
    producto_id: int,
    datos: AjusteStock,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(requiere_roles(RolUsuario.ADMIN, RolUsuario.BODEGA)),
):
    producto = db.get(Producto, producto_id)
    if not producto:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    if producto.requiere_imei:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Este producto se controla por IMEI: use /api/inventario/imei para ingresar equipos",
        )
    nuevo = producto.stock_actual + datos.cantidad
    if nuevo < 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El ajuste dejaria el stock en negativo")
    producto.stock_actual = nuevo
    tipo = TipoMovimiento.ENTRADA if datos.cantidad > 0 else TipoMovimiento.SALIDA
    registrar_movimiento(db, producto, tipo, abs(datos.cantidad), usuario, motivo=datos.motivo)
    db.commit()
    db.refresh(producto)
    return _salida(db, producto)


@router.get("/{producto_id}/kardex", response_model=list[MovimientoOut], summary="Kardex del producto")
def kardex(producto_id: int, limite: int = Query(100, le=500), db: Session = Depends(get_db)):
    from ..models import MovimientoInventario
    if not db.get(Producto, producto_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    return (
        db.query(MovimientoInventario)
        .filter(MovimientoInventario.producto_id == producto_id)
        .order_by(MovimientoInventario.fecha.desc())
        .limit(limite)
        .all()
    )

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import requiere, usuario_actual
from ..models import Categoria, Marca, MovimientoInventario, Producto, Usuario
from ..schemas import (AjusteStock, CategoriaOut, MarcaOut, MovimientoOut, ProductoCreate,
                       ProductoOut, ProductoUpdate)
from ..servicios import inventario

router = APIRouter(prefix="/api", tags=["Catalogo"], dependencies=[Depends(usuario_actual)])


def salida(db: Session, p: Producto) -> ProductoOut:
    dto = ProductoOut.model_validate(p)
    dto.disponibles = inventario.disponibles(db, p)
    return dto


@router.get("/categorias", response_model=list[CategoriaOut], summary="Categorias")
def categorias(db: Session = Depends(get_db)):
    return db.scalars(select(Categoria).order_by(Categoria.nombre)).all()


@router.get("/marcas", response_model=list[MarcaOut], summary="Marcas")
def marcas(db: Session = Depends(get_db)):
    return db.scalars(select(Marca).order_by(Marca.nombre)).all()


@router.get("/productos", response_model=list[ProductoOut], summary="Catalogo de productos")
def listar(q: str | None = Query(None, description="SKU, nombre o codigo de barras"),
           categoria_id: int | None = None, solo_disponibles: bool = False,
           incluir_inactivos: bool = False, db: Session = Depends(get_db)):
    consulta = select(Producto)
    if not incluir_inactivos:
        consulta = consulta.where(Producto.activo.is_(True))
    if q:
        patron = f"%{q}%"
        consulta = consulta.where(or_(Producto.sku.ilike(patron), Producto.nombre.ilike(patron),
                                      Producto.codigo_barras.ilike(patron)))
    if categoria_id:
        consulta = consulta.where(Producto.categoria_id == categoria_id)
    productos = [salida(db, p) for p in db.scalars(consulta.order_by(Producto.nombre)).all()]
    return [p for p in productos if p.disponibles > 0] if solo_disponibles else productos


@router.post("/productos", response_model=ProductoOut, status_code=201, summary="Crear producto")
def crear(datos: ProductoCreate, db: Session = Depends(get_db),
          usuario: Usuario = Depends(requiere("inventario.crear"))):
    if db.scalars(select(Producto).where(Producto.sku == datos.sku)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un producto con ese SKU")
    if datos.requiere_imei and datos.stock_actual:
        raise HTTPException(status.HTTP_400_BAD_REQUEST,
                            "Un producto con IMEI no lleva stock agregado: ingrese los equipos")
    producto = Producto(**datos.model_dump())
    db.add(producto)
    db.flush()
    if producto.stock_actual:
        from ..models import TipoMovimiento
        inventario.registrar_movimiento(db, producto, TipoMovimiento.ENTRADA, producto.stock_actual,
                                        usuario, motivo="Carga inicial")
    db.commit()
    db.refresh(producto)
    return salida(db, producto)


@router.get("/productos/{producto_id}", response_model=ProductoOut, summary="Detalle de producto")
def detalle(producto_id: int, db: Session = Depends(get_db)):
    producto = db.get(Producto, producto_id)
    if producto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El producto no existe")
    return salida(db, producto)


@router.put("/productos/{producto_id}", response_model=ProductoOut, summary="Actualizar producto")
def actualizar(producto_id: int, datos: ProductoUpdate, db: Session = Depends(get_db),
               _: Usuario = Depends(requiere("inventario.crear"))):
    producto = db.get(Producto, producto_id)
    if producto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El producto no existe")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(producto, campo, valor)
    db.commit()
    db.refresh(producto)
    return salida(db, producto)


@router.post("/productos/{producto_id}/ajuste-stock", response_model=ProductoOut,
             summary="Ajustar stock de un accesorio")
def ajustar(producto_id: int, datos: AjusteStock, db: Session = Depends(get_db),
            usuario: Usuario = Depends(requiere("inventario.ajustar"))):
    producto = db.get(Producto, producto_id)
    if producto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El producto no existe")
    return salida(db, inventario.ajustar_stock(db, producto, datos.cantidad, datos.motivo, usuario))


@router.get("/productos/{producto_id}/kardex", response_model=list[MovimientoOut], summary="Kardex")
def kardex(producto_id: int, limite: int = Query(100, le=500), db: Session = Depends(get_db)):
    return db.scalars(select(MovimientoInventario)
                      .where(MovimientoInventario.producto_id == producto_id)
                      .order_by(MovimientoInventario.fecha.desc()).limit(limite)).all()

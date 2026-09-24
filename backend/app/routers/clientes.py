from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import usuario_actual
from ..models import Cliente, Usuario, Venta
from ..schemas import ClienteCreate, ClienteOut, ClienteUpdate, VentaOut

router = APIRouter(prefix="/api/clientes", tags=["Clientes"], dependencies=[Depends(usuario_actual)])


@router.get("", response_model=list[ClienteOut], summary="Listar / buscar clientes")
def listar(
    q: str | None = Query(None, description="Busca por documento, nombre o telefono"),
    limite: int = Query(50, le=200),
    db: Session = Depends(get_db),
):
    consulta = db.query(Cliente).filter(Cliente.activo.is_(True))
    if q:
        patron = f"%{q}%"
        consulta = consulta.filter(
            or_(
                Cliente.numero_documento.ilike(patron),
                Cliente.nombres.ilike(patron),
                Cliente.apellidos.ilike(patron),
                Cliente.telefono.ilike(patron),
            )
        )
    return consulta.order_by(Cliente.nombres).limit(limite).all()


@router.post("", response_model=ClienteOut, status_code=201, summary="Registrar cliente")
def crear(datos: ClienteCreate, db: Session = Depends(get_db)):
    existente = (
        db.query(Cliente)
        .filter(
            Cliente.tipo_documento == datos.tipo_documento,
            Cliente.numero_documento == datos.numero_documento,
        )
        .first()
    )
    if existente:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un cliente con ese documento")
    cliente = Cliente(**datos.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.get("/{cliente_id}", response_model=ClienteOut, summary="Detalle de cliente")
def detalle(cliente_id: int, db: Session = Depends(get_db)):
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado")
    return cliente


@router.put("/{cliente_id}", response_model=ClienteOut, summary="Actualizar cliente")
def actualizar(cliente_id: int, datos: ClienteUpdate, db: Session = Depends(get_db)):
    cliente = db.get(Cliente, cliente_id)
    if not cliente:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(cliente, campo, valor)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.get("/{cliente_id}/compras", response_model=list[VentaOut], summary="Historial de compras")
def compras(cliente_id: int, db: Session = Depends(get_db)):
    if not db.get(Cliente, cliente_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cliente no encontrado")
    return db.query(Venta).filter(Venta.cliente_id == cliente_id).order_by(Venta.fecha.desc()).all()

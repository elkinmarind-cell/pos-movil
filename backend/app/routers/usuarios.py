from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import requiere, usuario_actual
from ..models import Permiso, Rol, RolPermiso, Usuario
from ..schemas import (CambioClave, PermisoOut, RolOut, RolPermisosUpdate, UsuarioCreate,
                       UsuarioOut, UsuarioUpdate)
from ..security import hash_password

router = APIRouter(prefix="/api", tags=["Usuarios y roles"])


@router.get("/roles", response_model=list[RolOut], summary="Roles del sistema")
def roles(db: Session = Depends(get_db), _: Usuario = Depends(usuario_actual)):
    return db.scalars(select(Rol).order_by(Rol.id)).all()


@router.get("/permisos", response_model=list[PermisoOut], summary="Catalogo de permisos")
def permisos(db: Session = Depends(get_db), _: Usuario = Depends(requiere("usuarios.ver"))):
    return db.scalars(select(Permiso).order_by(Permiso.modulo, Permiso.codigo)).all()


@router.get("/roles/{rol_id}/permisos", response_model=list[int], summary="Permisos de un rol")
def permisos_rol(rol_id: int, db: Session = Depends(get_db), _: Usuario = Depends(requiere("usuarios.ver"))):
    return list(db.scalars(select(RolPermiso.permiso_id).where(RolPermiso.rol_id == rol_id)).all())


@router.put("/roles/{rol_id}/permisos", response_model=list[int], summary="Reasignar permisos de un rol")
def actualizar_permisos(rol_id: int, datos: RolPermisosUpdate, db: Session = Depends(get_db),
                        _: Usuario = Depends(requiere("usuarios.editar"))):
    if db.get(Rol, rol_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El rol no existe")
    db.query(RolPermiso).filter(RolPermiso.rol_id == rol_id).delete()
    for pid in sorted(set(datos.permisos)):
        if db.get(Permiso, pid) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"El permiso {pid} no existe")
        db.add(RolPermiso(rol_id=rol_id, permiso_id=pid))
    db.commit()
    return sorted(set(datos.permisos))


@router.get("/usuarios", response_model=list[UsuarioOut], summary="Listar usuarios")
def listar(db: Session = Depends(get_db), _: Usuario = Depends(requiere("usuarios.ver"))):
    return db.scalars(select(Usuario).order_by(Usuario.id)).all()


@router.post("/usuarios", response_model=UsuarioOut, status_code=201, summary="Crear usuario")
def crear(datos: UsuarioCreate, db: Session = Depends(get_db),
          _: Usuario = Depends(requiere("usuarios.crear"))):
    if db.scalars(select(Usuario).where(Usuario.username == datos.username)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Ese nombre de usuario ya existe")
    if db.scalars(select(Usuario).where(Usuario.email == datos.email)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Ese correo ya esta registrado")
    if db.get(Rol, datos.rol_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El rol no existe")
    usuario = Usuario(rol_id=datos.rol_id, username=datos.username,
                      nombre_completo=datos.nombre_completo, email=datos.email,
                      password_hash=hash_password(datos.password))
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.put("/usuarios/{usuario_id}", response_model=UsuarioOut, summary="Actualizar usuario")
def actualizar(usuario_id: int, datos: UsuarioUpdate, db: Session = Depends(get_db),
               actor: Usuario = Depends(requiere("usuarios.editar"))):
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El usuario no existe")
    if datos.activo is False and usuario.id == actor.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No puede desactivar su propio usuario")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(usuario, campo, valor)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.put("/usuarios/{usuario_id}/clave", status_code=204, summary="Cambiar contrasena")
def cambiar_clave(usuario_id: int, datos: CambioClave, db: Session = Depends(get_db),
                  actor: Usuario = Depends(usuario_actual)):
    if usuario_id != actor.id:
        requiere("usuarios.editar")(actor, db)
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "El usuario no existe")
    usuario.password_hash = hash_password(datos.password)
    db.commit()

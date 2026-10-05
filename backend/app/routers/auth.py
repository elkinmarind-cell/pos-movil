from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import permisos_de, usuario_actual
from ..models import Usuario
from ..schemas import LoginOut, UsuarioOut
from ..security import crear_access_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["Autenticacion"])


@router.post("/login", response_model=LoginOut, summary="Iniciar sesion")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.scalars(select(Usuario).where(Usuario.username == form.username)).first()
    if not usuario or not verify_password(form.password, usuario.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario o contrasena incorrectos")
    if not usuario.activo:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "El usuario esta inactivo")
    usuario.ultimo_acceso = datetime.now(timezone.utc)
    db.commit()
    db.refresh(usuario)
    return LoginOut(
        access_token=crear_access_token(usuario.id, usuario.username, usuario.rol.nombre),
        usuario=UsuarioOut.model_validate(usuario),
        permisos=sorted(permisos_de(db, usuario.rol_id)),
    )


@router.get("/yo", response_model=LoginOut, summary="Sesion actual")
def yo(usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)):
    return LoginOut(access_token="", usuario=UsuarioOut.model_validate(usuario),
                    permisos=sorted(permisos_de(db, usuario.rol_id)))

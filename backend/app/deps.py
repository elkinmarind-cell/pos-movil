"""Dependencias compartidas: sesion de BD, usuario autenticado y control de roles."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import RolUsuario, Usuario
from .security import decodificar_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

CREDENCIALES_INVALIDAS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciales invalidas o token expirado",
    headers={"WWW-Authenticate": "Bearer"},
)


def usuario_actual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    payload = decodificar_token(token)
    if payload is None or "sub" not in payload:
        raise CREDENCIALES_INVALIDAS
    usuario = db.query(Usuario).filter(Usuario.username == payload["sub"]).first()
    if usuario is None or not usuario.activo:
        raise CREDENCIALES_INVALIDAS
    return usuario


def requiere_roles(*roles: RolUsuario):
    """Uso: Depends(requiere_roles(RolUsuario.ADMIN, RolUsuario.BODEGA))"""
    def verificador(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
        if usuario.rol not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"El rol '{usuario.rol.value}' no tiene permiso para esta operacion",
            )
        return usuario
    return verificador

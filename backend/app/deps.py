"""Dependencias compartidas: sesion, usuario autenticado y permisos."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_db, marcar_usuario
from .models import Permiso, RolPermiso, Usuario

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

NO_AUTORIZADO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciales invalidas o sesion expirada",
    headers={"WWW-Authenticate": "Bearer"},
)


def usuario_actual(token: str = Depends(oauth2), db: Session = Depends(get_db)) -> Usuario:
    from .security import decodificar_token
    payload = decodificar_token(token)
    if not payload or "sub" not in payload:
        raise NO_AUTORIZADO
    usuario = db.get(Usuario, int(payload["sub"]))
    if usuario is None or not usuario.activo:
        raise NO_AUTORIZADO
    # el trigger de auditoria usara este valor para saber quien hizo cada cambio
    marcar_usuario(db, usuario.id)
    return usuario


def permisos_de(db: Session, rol_id: int) -> set[str]:
    return set(db.scalars(
        select(Permiso.codigo).join(RolPermiso, RolPermiso.permiso_id == Permiso.id)
        .where(RolPermiso.rol_id == rol_id)
    ).all())


def requiere(*codigos: str):
    """Exige que el rol del usuario tenga al menos uno de los permisos indicados."""
    def verificador(usuario: Usuario = Depends(usuario_actual), db: Session = Depends(get_db)) -> Usuario:
        suyos = permisos_de(db, usuario.rol_id)
        if not set(codigos) & suyos:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Su rol no tiene permiso para esta operacion (se requiere {' o '.join(codigos)})",
            )
        return usuario
    return verificador

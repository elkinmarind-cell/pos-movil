from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import requiere_roles, usuario_actual
from ..models import RolUsuario, Usuario
from ..schemas import Token, UsuarioCreate, UsuarioOut
from ..security import crear_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["Autenticacion"])


@router.post("/login", response_model=Token, summary="Iniciar sesion")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.username == form.username).first()
    if not usuario or not verify_password(form.password, usuario.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario o contrasena incorrectos")
    if not usuario.activo:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "El usuario esta inactivo")
    token = crear_access_token(usuario.username, usuario.rol.value)
    return Token(access_token=token, usuario=UsuarioOut.model_validate(usuario))


@router.get("/yo", response_model=UsuarioOut, summary="Datos del usuario autenticado")
def yo(usuario: Usuario = Depends(usuario_actual)):
    return usuario


@router.post("/usuarios", response_model=UsuarioOut, status_code=201, summary="Crear usuario (solo admin)")
def crear_usuario(
    datos: UsuarioCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(requiere_roles(RolUsuario.ADMIN)),
):
    if db.query(Usuario).filter(Usuario.username == datos.username).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "El nombre de usuario ya existe")
    if db.query(Usuario).filter(Usuario.email == datos.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "El correo ya esta registrado")
    usuario = Usuario(
        username=datos.username,
        nombre_completo=datos.nombre_completo,
        email=datos.email,
        password_hash=hash_password(datos.password),
        rol=datos.rol,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@router.get("/usuarios", response_model=list[UsuarioOut], summary="Listar usuarios (solo admin)")
def listar_usuarios(db: Session = Depends(get_db), _: Usuario = Depends(requiere_roles(RolUsuario.ADMIN))):
    return db.query(Usuario).order_by(Usuario.id).all()

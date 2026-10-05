"""Conexion a PostgreSQL.

El esquema NO lo crea la aplicacion: lo crean los scripts de database/. La aplicacion
solo se conecta, y la prueba de consistencia verifica que ambos coincidan.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def marcar_usuario(db: Session, usuario_id: int | None) -> None:
    """Deja el usuario en la sesion de PostgreSQL para que el trigger de auditoria
    registre quien hizo cada cambio."""
    db.execute(
        __import__("sqlalchemy").text("SELECT set_config('pos.usuario_id', :v, true)"),
        {"v": str(usuario_id or "")},
    )

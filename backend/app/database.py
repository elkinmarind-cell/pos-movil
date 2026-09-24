"""Conexion a la base de datos. Soporta SQLite (demo) y PostgreSQL (entrega)."""
import warnings

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

# SQLite no maneja Decimal nativamente; SQLAlchemy lo convierte y avisa.
warnings.filterwarnings("ignore", message=r".*does \*not\* support Decimal objects natively.*")

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    future=True,
)

if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _activar_foreign_keys(dbapi_connection, connection_record):
        """SQLite ignora las FK salvo que se activen por conexion."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

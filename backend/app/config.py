"""Configuracion de la aplicacion. Todo por variables de entorno (12-factor)."""
from decimal import Decimal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "POS Movil"
    descripcion: str = "Sistema de gestion y venta de dispositivos moviles"
    version: str = "1.0.0"

    # PostgreSQL es el motor del sistema: el esquema, las vistas y los triggers viven ahi.
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/pos_movil"

    secret_key: str = "clave-de-desarrollo-cambiar-en-produccion"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    iva_porcentaje: Decimal = Decimal("19")
    moneda: str = "COP"
    resolucion_dian_id: int = 1

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()

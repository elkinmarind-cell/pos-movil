"""Configuracion central de la aplicacion (12-factor: todo por variables de entorno)."""
from decimal import Decimal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "POS Movil - Gestion y Venta de Dispositivos Moviles"
    version: str = "0.1.0"

    # SQLite por defecto => el prototipo arranca sin instalar motor alguno.
    # En produccion/entrega academica se usa PostgreSQL via DATABASE_URL.
    database_url: str = "sqlite:///./pos_movil.db"

    secret_key: str = "clave-de-desarrollo-no-usar-en-produccion"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    iva_porcentaje: Decimal = Decimal("19")
    meses_garantia_default: int = 12
    moneda: str = "COP"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def es_postgres(self) -> bool:
        return self.database_url.startswith("postgresql")


settings = Settings()

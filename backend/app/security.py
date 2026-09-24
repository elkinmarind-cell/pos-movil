"""Hash de contrasenas (PBKDF2-SHA256) y emision/validacion de JWT."""
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

from .config import settings

_ITERACIONES = 260_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERACIONES)
    return f"pbkdf2_sha256${_ITERACIONES}${salt.hex()}${dk.hex()}"


def verify_password(password: str, almacenado: str) -> bool:
    try:
        algoritmo, iteraciones, salt_hex, hash_hex = almacenado.split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), int(iteraciones))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def crear_access_token(subject: str, rol: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "rol": rol, "exp": expira}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decodificar_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None

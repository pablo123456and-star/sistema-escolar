"""
Contraseñas y tokens.

- Contraseñas: hash bcrypt (compatible con los hashes de pgcrypto de 08_datos_prueba.sql).
- Token de sesión: JWT propio firmado con HS256 (JWT_SECRETO) que expira en JWT_MINUTOS
  (o JWT_DIAS_RECORDAR si el usuario marcó "Recordar sesión").
"""
import secrets
import string
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.nucleo.config import obtener_config

ALGORITMO = "HS256"
# Hash de relleno: se usa cuando el usuario no existe para que la respuesta tarde
# lo mismo y no revele qué usuarios existen.
_HASH_RELLENO = bcrypt.hashpw(b"relleno", bcrypt.gensalt(rounds=10))


def hash_contrasena(contrasena: str) -> str:
    return bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")


def verificar_contrasena(contrasena: str, hash_guardado: str | None) -> bool:
    if not hash_guardado:
        bcrypt.checkpw(contrasena.encode("utf-8")[:72], _HASH_RELLENO)
        return False
    try:
        return bcrypt.checkpw(contrasena.encode("utf-8"), hash_guardado.encode("ascii"))
    except ValueError:
        return False


def contrasena_temporal(largo: int = 10) -> str:
    """Contraseña aleatoria para restablecer una cuenta (se entrega una sola vez)."""
    alfabeto = string.ascii_letters + string.digits
    while True:
        c = "".join(secrets.choice(alfabeto) for _ in range(largo))
        if any(x.isdigit() for x in c) and any(x.isupper() for x in c) and any(x.islower() for x in c):
            return c


def _secreto() -> str:
    secreto = obtener_config().JWT_SECRETO
    if not secreto:
        raise RuntimeError("Falta JWT_SECRETO en el archivo .env del backend")
    return secreto


def crear_token(id_usuario: int, rol: str, recordar: bool = False) -> tuple[str, datetime]:
    cfg = obtener_config()
    ahora = datetime.now(UTC)
    expira = ahora + (timedelta(days=cfg.JWT_DIAS_RECORDAR) if recordar else timedelta(minutes=cfg.JWT_MINUTOS))
    datos = {"sub": str(id_usuario), "rol": rol, "iat": ahora, "exp": expira}
    return jwt.encode(datos, _secreto(), algorithm=ALGORITMO), expira


def leer_token(token: str) -> dict:
    """Devuelve el contenido del token o lanza jwt.InvalidTokenError."""
    return jwt.decode(token, _secreto(), algorithms=[ALGORITMO], options={"require": ["sub", "exp"]})

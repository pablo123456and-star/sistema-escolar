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


# ---- Bloqueo progresivo y recuperación de contraseña ------------------------
MINUTOS_BLOQUEO = {
    1: 5,   # 1er bloqueo (tras 3 intentos fallidos)
    2: 15,  # 2do bloqueo
    3: 30,  # 3er bloqueo
}


def duracion_bloqueo_minutos(nivel_bloqueo: int) -> int:
    """Duración en minutos según el nivel de bloqueo progresivo (máx 60)."""
    return MINUTOS_BLOQUEO.get(nivel_bloqueo, 60)


def formatear_tiempo_restante(segundos_totales: int) -> str:
    """Devuelve un texto legible para el usuario con el tiempo que debe esperar."""
    if segundos_totales <= 0:
        return "unos segundos"
    minutos = segundos_totales // 60
    segundos = segundos_totales % 60
    if minutos > 0 and segundos > 0:
        return f"{minutos} min y {segundos} s"
    if minutos > 0:
        return f"{minutos} minuto{'s' if minutos != 1 else ''}"
    return f"{segundos} segundo{'s' if segundos != 1 else ''}"


def hashear_token(token_plano: str) -> str:
    """Calcula el hash SHA-256 de un token para guardarlo de forma segura en BD."""
    import hashlib
    return hashlib.sha256(token_plano.encode("utf-8")).hexdigest()


def generar_token_recuperacion() -> tuple[str, str]:
    """Genera un token criptográficamente seguro y devuelve (token_plano, token_hash)."""
    token_plano = secrets.token_urlsafe(32)
    return token_plano, hashear_token(token_plano)

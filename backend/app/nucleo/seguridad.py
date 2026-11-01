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
INTENTOS_PARA_BLOQUEAR = 3
MINUTOS_BLOQUEO = {
    1: 15,   # 1er bloqueo (tras 3 intentos fallidos seguidos)
    2: 30,   # 2do bloqueo
    3: 60,   # 3er bloqueo
    4: 120,  # 4to bloqueo
}
MINUTOS_BLOQUEO_MAXIMO = 24 * 60  # 5to bloqueo en adelante: 24 horas
# Dos fallos son "seguidos" si entre uno y otro pasan menos de 15 minutos
VENTANA_FALLOS_SEGUIDOS = timedelta(minutes=15)
# Tras 24 horas sin fallos (contadas desde que terminó el último bloqueo) se vuelve al primer nivel
REINICIO_NIVEL_BLOQUEO = timedelta(hours=24)


def duracion_bloqueo_minutos(nivel_bloqueo: int) -> int:
    """Duración en minutos según el nivel de bloqueo progresivo (15 min, 30 min, 1 h, 2 h y luego 24 h)."""
    return MINUTOS_BLOQUEO.get(nivel_bloqueo, MINUTOS_BLOQUEO_MAXIMO)


def _con_zona(momento: datetime | None) -> datetime | None:
    if momento is not None and momento.tzinfo is None:
        return momento.replace(tzinfo=UTC)
    return momento


def registrar_fallo(
    ahora: datetime,
    intentos_previos: int,
    nivel_previo: int,
    ultimo_fallo: datetime | None,
    bloqueado_hasta: datetime | None,
) -> tuple[int, int, datetime | None]:
    """Aplica un intento fallido y devuelve (intentos, nivel, bloqueado_hasta) para guardar en la cuenta.

    - Solo se suman los fallos seguidos (menos de 15 minutos entre uno y otro): los de días
      anteriores no cuentan.
    - Al tercer fallo seguido se bloquea con el siguiente nivel y el contador vuelve a 0, así
      después de cada bloqueo hay otra vez 3 intentos.
    - Si pasaron 24 horas sin fallos desde el último fallo o desde que terminó el último bloqueo
      (lo que sea más tarde), el nivel vuelve a empezar.
    """
    ultimo_fallo, bloqueado_hasta = _con_zona(ultimo_fallo), _con_zona(bloqueado_hasta)
    intentos, nivel = intentos_previos or 0, nivel_previo or 0
    if ultimo_fallo is None:
        intentos, nivel = 0, 0
    else:
        referencia = max(ultimo_fallo, bloqueado_hasta or ultimo_fallo)
        if ahora - referencia >= REINICIO_NIVEL_BLOQUEO:
            intentos, nivel = 0, 0
        elif ahora - ultimo_fallo >= VENTANA_FALLOS_SEGUIDOS:
            intentos = 0

    intentos += 1
    if intentos < INTENTOS_PARA_BLOQUEAR:
        return intentos, nivel, None
    nivel += 1
    return 0, nivel, ahora + timedelta(minutes=duracion_bloqueo_minutos(nivel))


def formatear_tiempo_restante(segundos_totales: int) -> str:
    """Devuelve un texto legible para el usuario con el tiempo que debe esperar."""
    if segundos_totales <= 0:
        return "unos segundos"
    minutos = segundos_totales // 60
    segundos = segundos_totales % 60
    if minutos >= 60:
        horas, minutos = divmod(minutos + (1 if segundos else 0), 60)
        texto = f"{horas} hora{'s' if horas != 1 else ''}"
        return f"{texto} y {minutos} min" if minutos else texto
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

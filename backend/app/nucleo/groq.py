"""
Cliente de Groq para el asistente por voz (CU28): voz a texto (Whisper) y chat con herramientas.

Se usa la API REST de Groq (compatible con OpenAI) con urllib, igual que Brevo (correo.py) y
Stripe (pasarela_pago.py): no requiere instalar paquetes nuevos. La clave va en GROQ_API_KEY
(.env o variables del servidor), nunca en el repositorio ni en el frontend.
El plan gratuito de Groq limita los tokens por minuto: si Groq pide esperar hasta 30 segundos,
se espera y se reintenta (máximo 2 veces).
"""
import asyncio
import json
import logging
import time
import urllib.error
import urllib.request
import uuid

from app.nucleo.config import obtener_config
from app.nucleo.errores import ErrorNegocio

logger = logging.getLogger("app.groq")

# Límite de tokens por minuto: una pregunta hace varias vueltas de chat; si Groq pide esperar
# unos segundos, se espera y se reintenta (hasta 2 veces) en lugar de fallar a mitad de la respuesta.
MAX_INTENTOS = 3
MAX_ESPERA_SEGUNDOS = 30


class AsistenteNoDisponible(ErrorNegocio):
    estado = 503
    codigo = "asistente_no_disponible"


def habilitado() -> bool:
    return obtener_config().GROQ_API_KEY.startswith("gsk_")


def _segundos_espera(valor: str | None) -> float | None:
    try:
        return float(valor) if valor else None
    except ValueError:
        return None


def _peticion(ruta: str, cuerpo: bytes, tipo: str, segundos: int = 60) -> dict:
    cfg = obtener_config()
    if not habilitado():
        raise AsistenteNoDisponible("El asistente por voz no está configurado en el servidor.")
    for intento in range(1, MAX_INTENTOS + 1):
        peticion = urllib.request.Request(
            f"{cfg.GROQ_URL}{ruta}", data=cuerpo, method="POST",
            headers={"Authorization": f"Bearer {cfg.GROQ_API_KEY}", "Content-Type": tipo,
                     "Accept": "application/json", "User-Agent": "escuela-backend"},
        )
        try:
            with urllib.request.urlopen(peticion, timeout=segundos) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            espera = _segundos_espera(e.headers.get("retry-after"))
            if e.code == 429 and intento < MAX_INTENTOS and espera is not None and espera <= MAX_ESPERA_SEGUNDOS:
                time.sleep(espera + 0.5)
                continue
            logger.warning("Groq respondió %s: %s", e.code, e.read()[:300].decode(errors="replace"))
            if e.code == 429:
                raise AsistenteNoDisponible("El asistente recibió demasiadas consultas. Intente en un minuto.") from e
            raise AsistenteNoDisponible("El asistente no pudo responder en este momento.") from e
        except (urllib.error.URLError, TimeoutError) as e:
            logger.warning("No se pudo conectar con Groq: %s", e)
            raise AsistenteNoDisponible("No se pudo conectar con el servicio del asistente.") from e
    raise AsistenteNoDisponible("El asistente recibió demasiadas consultas. Intente en un minuto.")


async def chat(mensajes: list[dict], herramientas: list[dict]) -> dict:
    """Una vuelta de chat; devuelve el mensaje del modelo (texto o pedidos de herramientas)."""
    modelo = obtener_config().GROQ_MODELO
    pedido = {"model": modelo, "messages": mensajes, "tools": herramientas, "tool_choice": "auto",
              "temperature": 0.2, "max_completion_tokens": 1000}
    if modelo.startswith("openai/gpt-oss"):
        pedido["reasoning_effort"] = "low"   # menos tokens de razonamiento
    datos = await asyncio.to_thread(_peticion, "/chat/completions", json.dumps(pedido).encode(), "application/json")
    return datos["choices"][0]["message"]


async def transcribir(audio: bytes, tipo_audio: str) -> str:
    """Audio grabado en el navegador -> texto en español."""
    tipo = tipo_audio.split(";")[0].strip() or "audio/webm"
    extension = {"audio/webm": "webm", "audio/ogg": "ogg", "audio/mp4": "mp4", "audio/mpeg": "mp3",
                 "audio/wav": "wav", "audio/x-wav": "wav"}.get(tipo, "webm")
    limite = uuid.uuid4().hex
    partes = []
    for nombre, valor in (("model", obtener_config().GROQ_MODELO_VOZ), ("language", "es"),
                          ("response_format", "json"), ("temperature", "0")):
        partes.append(f'--{limite}\r\nContent-Disposition: form-data; name="{nombre}"\r\n\r\n{valor}\r\n'.encode())
    partes.append(f'--{limite}\r\nContent-Disposition: form-data; name="file"; filename="pregunta.{extension}"\r\n'
                  f"Content-Type: {tipo}\r\n\r\n".encode() + audio + b"\r\n")
    partes.append(f"--{limite}--\r\n".encode())
    datos = await asyncio.to_thread(_peticion, "/audio/transcriptions", b"".join(partes),
                                    f"multipart/form-data; boundary={limite}")
    return (datos.get("text") or "").strip()

"""
Endpoints del paquete asistente: /api/v1/asistente/...

  GET  /asistente/estado    ¿Está configurado el asistente? (para mostrar u ocultar el botón)
  POST /asistente/consulta  Pregunta escrita
  POST /asistente/voz       Pregunta grabada: el cuerpo es el audio (audio/webm, audio/ogg, audio/mp4...).
                            Los turnos anteriores van en la cabecera X-Historial (JSON en UTF-8 y base64).
"""
import base64
import json

from fastapi import APIRouter, Request
from pydantic import ValidationError

from app.nucleo import groq
from app.nucleo.dependencias import Sesion, Usuario, ip_cliente
from app.paquetes.asistente.casos_uso import cu28_consultar_por_voz as cu28
from app.paquetes.asistente.schemas import ConsultaEntrada, EstadoAsistente, RespuestaAsistente, TurnoAnterior

router = APIRouter(prefix="/asistente", tags=["asistente"])


def _token(request: Request) -> str:
    return request.headers.get("authorization", "").removeprefix("Bearer ").strip()


def _historial(request: Request) -> list[TurnoAnterior]:
    """Lee X-Historial; si falta o no es válido, la pregunta se responde sin historial."""
    valor = request.headers.get("x-historial", "").strip()
    if not valor:
        return []
    try:
        turnos = json.loads(base64.b64decode(valor, validate=True).decode("utf-8"))
        return [TurnoAnterior(**t) for t in turnos[-6:]] if isinstance(turnos, list) else []
    except (ValueError, TypeError, ValidationError):
        return []


@router.get("/estado", response_model=EstadoAsistente, summary="CU28 - ¿Está habilitado el asistente por voz?")
async def estado(_: Usuario):
    return EstadoAsistente(habilitado=groq.habilitado())


@router.post("/consulta", response_model=RespuestaAsistente, summary="CU28 - Preguntar al asistente (texto)")
async def consulta(datos: ConsultaEntrada, usuario: Usuario, sesion: Sesion, request: Request):
    return await cu28.responder(sesion, usuario, datos, _token(request), ip_cliente(request))


@router.post("/voz", response_model=RespuestaAsistente, summary="CU28 - Preguntar al asistente (audio)")
async def voz(usuario: Usuario, sesion: Sesion, request: Request):
    audio = await request.body()
    return await cu28.responder_audio(sesion, usuario, audio, request.headers.get("content-type", ""),
                                      _token(request), ip_cliente(request), _historial(request))

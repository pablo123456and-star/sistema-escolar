"""
Traducción de errores a respuestas HTTP.

    ErrorNegocio (casos de uso / politicas)       -> 400 (o el estado indicado)
    NoEncontrado                                  -> 404
    Conflicto                                     -> 409
    Violación de CHECK / UNIQUE / FK de la BD      -> 409 con mensaje claro
    RAISE EXCEPTION de triggers y procedimientos  -> 400 con su mensaje
    Sin token / token inválido -> 401     Rol no permitido -> 403
Formato de respuesta: {"detalle": ..., "codigo": ...}
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorNegocio(Exception):
    estado = 400
    codigo = "regla_negocio"

    def __init__(self, detalle: str, codigo: str | None = None):
        super().__init__(detalle)
        self.detalle = detalle
        if codigo:
            self.codigo = codigo


class NoEncontrado(ErrorNegocio):
    estado = 404
    codigo = "no_encontrado"


class Conflicto(ErrorNegocio):
    estado = 409
    codigo = "conflicto"


class SinPermiso(ErrorNegocio):
    estado = 403
    codigo = "sin_permiso"


# Mensajes para las restricciones de la BD (nombre de la restricción -> mensaje)
MENSAJES_RESTRICCION = {
    "usuario_nombre_usuario_key": "El nombre de usuario ya está en uso.",
    "usuario_ci_persona_key": "La persona ya tiene una cuenta de usuario.",
    "persona_pkey": "Ya existe una persona con ese CI.",
    "estudiante_pkey": "La persona ya está registrada como estudiante.",
    "estudiante_rude_key": "El RUDE ya está registrado para otro estudiante.",
    "tutor_pkey": "La persona ya está registrada como tutor.",
    "tutor_estudiante_pkey": "El tutor ya está vinculado a ese estudiante.",
    "uq_tutor_principal": "El estudiante ya tiene un tutor principal.",
    "inscripcion_ci_estudiante_inscripcion_id_gestion_inscripcio_key": "El estudiante ya está inscrito en esa gestión.",
    "rol_nombre_rol_check": "Los roles del sistema son fijos: administrador, profesor, estudiante y tutor.",
}


def _causa(exc: DBAPIError):
    """Excepción original de asyncpg (tiene sqlstate, constraint_name y message)."""
    orig = exc.orig
    return getattr(orig, "__cause__", None) or orig


def _respuesta(estado: int, detalle: str, codigo: str, **extra) -> JSONResponse:
    return JSONResponse(status_code=estado, content={"detalle": detalle, "codigo": codigo, **extra})


def registrar_manejadores(app: FastAPI) -> None:
    @app.exception_handler(ErrorNegocio)
    async def _negocio(_: Request, exc: ErrorNegocio):
        return _respuesta(exc.estado, exc.detalle, exc.codigo)

    @app.exception_handler(IntegrityError)
    async def _integridad(_: Request, exc: IntegrityError):
        causa = _causa(exc)
        estado_sql = getattr(causa, "sqlstate", None)
        restriccion = getattr(causa, "constraint_name", None)
        if restriccion in MENSAJES_RESTRICCION:
            return _respuesta(409, MENSAJES_RESTRICCION[restriccion], "restriccion")
        if estado_sql in ("23503", "23001"):
            return _respuesta(409, "No se puede completar: el registro está relacionado con otros datos.", "relacionado")
        if estado_sql == "23505":
            return _respuesta(409, "Ya existe un registro con esos datos.", "duplicado")
        if estado_sql == "23514":
            return _respuesta(409, f"Dato no válido (regla {restriccion}).", "dato_invalido")
        return _respuesta(409, "Los datos no cumplen las reglas de la base de datos.", "integridad")

    @app.exception_handler(DBAPIError)
    async def _bd(_: Request, exc: DBAPIError):
        causa = _causa(exc)
        if getattr(causa, "sqlstate", None) == "P0001":   # RAISE EXCEPTION de triggers/procedimientos
            return _respuesta(400, getattr(causa, "message", str(causa)), "regla_bd")
        return _respuesta(500, "Error de base de datos.", "error_bd")

    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        codigos = {401: "no_autenticado", 403: "sin_permiso", 404: "no_encontrado"}
        return JSONResponse(
            status_code=exc.status_code,
            content={"detalle": exc.detail, "codigo": codigos.get(exc.status_code, "error")},
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def _validacion(_: Request, exc: RequestValidationError):
        errores = []
        for e in exc.errors():
            campo = ".".join(str(x) for x in e.get("loc", ())[1:]) or "datos"
            errores.append({"campo": campo, "mensaje": e.get("msg", "Valor no válido")})
        primero = errores[0] if errores else {"campo": "datos", "mensaje": "Datos no válidos"}
        return _respuesta(422, f"{primero['campo']}: {primero['mensaje']}", "validacion", errores=errores)

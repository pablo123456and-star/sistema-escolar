"""
Dependencias de FastAPI reutilizables.

  - sesion_bd(): la transacción de la petición, ya identificada con el usuario
    (para la bitácora) y con la zona horaria de Bolivia.
  - usuario_actual(): lee 'Authorization: Bearer <token>', valida el JWT y
    comprueba en la BD que la cuenta y la persona sigan activas (401 si no).
    El rol se toma de la BD, así un cambio de rol rige de inmediato.
  - requiere_rol("administrador", ...): 403 si el rol no está permitido.
"""
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo import bd
from app.nucleo.seguridad import leer_token

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class UsuarioActual:
    id_usuario: int
    nombre_usuario: str
    rol: str
    ci: str


def ip_cliente(request: Request) -> str:
    reenviada = request.headers.get("x-forwarded-for")
    if reenviada:
        return reenviada.split(",")[0].strip()
    return request.client.host if request.client else ""


def _no_autenticado(detalle: str) -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detalle, headers={"WWW-Authenticate": "Bearer"})


async def id_usuario_token(
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> int | None:
    """id del usuario del token, o None si la petición no trae token."""
    if credenciales is None:
        return None
    try:
        return int(leer_token(credenciales.credentials)["sub"])
    except (jwt.InvalidTokenError, ValueError, KeyError):
        raise _no_autenticado("La sesión no es válida o ya venció. Vuelva a iniciar sesión.")


async def sesion_bd(
    request: Request, id_usuario: Annotated[int | None, Depends(id_usuario_token)]
) -> AsyncIterator[AsyncSession]:
    async with bd.abrir_sesion(id_usuario, ip_cliente(request)) as sesion:
        yield sesion


# scope="function": el commit (o rollback) ocurre ANTES de enviar la respuesta,
# así un error al confirmar llega al cliente y la siguiente petición ya ve los cambios.
Sesion = Annotated[AsyncSession, Depends(sesion_bd, scope="function")]


async def usuario_actual(
    id_usuario: Annotated[int | None, Depends(id_usuario_token)], sesion: Sesion
) -> UsuarioActual:
    if id_usuario is None:
        raise _no_autenticado("Debe iniciar sesión.")
    fila = (
        await sesion.execute(
            text(
                """SELECT u.nombre_usuario, r.nombre_rol, u.ci_persona, u.estado_usuario, p.estado_persona
                     FROM usuario u
                     JOIN rol r     ON r.id_rol = u.id_rol_usuario
                     JOIN persona p ON p.ci = u.ci_persona
                    WHERE u.id_usuario = :id"""
            ),
            {"id": id_usuario},
        )
    ).one_or_none()
    if fila is None or fila.estado_usuario != "activo" or fila.estado_persona != "activo":
        raise _no_autenticado("La cuenta ya no está activa. Vuelva a iniciar sesión.")
    return UsuarioActual(id_usuario, fila.nombre_usuario, fila.nombre_rol, fila.ci_persona)


Usuario = Annotated[UsuarioActual, Depends(usuario_actual)]


def requiere_rol(*roles: str):
    async def _verificar(usuario: Usuario) -> UsuarioActual:
        if usuario.rol not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No tiene permiso para esta operación.")
        return usuario

    return _verificar


Administrador = Annotated[UsuarioActual, Depends(requiere_rol("administrador"))]

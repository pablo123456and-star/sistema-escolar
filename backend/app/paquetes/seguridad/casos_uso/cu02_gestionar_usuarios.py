"""
CU02 - Gestionar usuarios (CRUD)
Paquete: seguridad

Actores ........: Administrador
Rol del sistema : administrador
Tablas .........: usuario, rol, persona, administrativo, profesor, estudiante, tutor, bitacora
Usa de la BD ...: Trigger de auditoría de usuario

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - El rol debe coincidir con la especialización de la persona: administrador↔administrativo, profesor↔profesor, estudiante↔estudiante, tutor↔tutor.
    - Solo personas activas pueden recibir una cuenta.
    - Guardar la contraseña como hash bcrypt; nunca en texto.
    - Una persona tiene como máximo un usuario y nombre_usuario es único (lo asegura la BD).
    - No se borran usuarios: se desactivan o bloquean. El administrador no puede desactivarse a sí mismo.
    - Restablecer contraseña (atiende las solicitudes del CU01): genera una contraseña temporal que se
      muestra una sola vez al administrador y queda registrado en la bitácora.

Precondición:
    Sesión iniciada como administrador. La persona está registrada con la especialización del rol.

Postcondición:
    El usuario queda creado, actualizado o desactivado, y la acción queda en la bitácora.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import ErrorNegocio, NoEncontrado
from app.nucleo.esquemas import Pagina
from app.nucleo.seguridad import contrasena_temporal, hash_contrasena
from app.paquetes.personas.models import Persona
from app.paquetes.seguridad import repository as repo
from app.paquetes.seguridad.casos_uso import cu03_gestionar_roles_permisos as cu03
from app.paquetes.seguridad.models import Rol, Usuario
from app.paquetes.seguridad.politicas import ACCION_RESTABLECIDA, validar_especializacion, validar_no_es_uno_mismo
from app.paquetes.seguridad.schemas import (
    ContrasenaTemporalSalida, PersonaSinCuentaSalida, SolicitudRecuperacionSalida, UsuarioActualizar,
    UsuarioCrear, UsuarioSalida,
)


async def listar(sesion: AsyncSession, q: str | None, id_rol: int | None, estado: str | None,
                 pagina: int, tamano: int) -> Pagina[UsuarioSalida]:
    filas, total = await repo.listar_usuarios(sesion, q, id_rol, estado, pagina, tamano)
    return Pagina[UsuarioSalida](
        items=[UsuarioSalida.model_validate(f._asdict()) for f in filas], total=total, pagina=pagina, tamano=tamano
    )


async def obtener(sesion: AsyncSession, id_usuario: int) -> UsuarioSalida:
    fila = await repo.usuario_detalle(sesion, id_usuario)
    if fila is None:
        raise NoEncontrado("Usuario no encontrado.")
    return UsuarioSalida.model_validate(fila._asdict())


async def personas_sin_cuenta(sesion: AsyncSession, id_rol: int, q: str | None) -> list[PersonaSinCuentaSalida]:
    rol = await sesion.get(Rol, id_rol)
    if rol is None:
        raise NoEncontrado("Rol no encontrado.")
    return [PersonaSinCuentaSalida.model_validate(f._asdict()) for f in await repo.personas_sin_cuenta(sesion, rol.nombre_rol, q)]


async def crear(sesion: AsyncSession, datos: UsuarioCrear) -> UsuarioSalida:
    persona = await sesion.get(Persona, datos.ci_persona)
    if persona is None:
        raise NoEncontrado("No existe una persona con ese CI.")
    if persona.estado_persona != "activo":
        raise ErrorNegocio("La persona está dada de baja; reactívela antes de crearle una cuenta.")
    rol = await sesion.get(Rol, datos.id_rol)
    if rol is None:
        raise NoEncontrado("Rol no encontrado.")
    await validar_especializacion(sesion, persona.ci, rol.nombre_rol)

    usuario = Usuario(
        nombre_usuario=datos.nombre_usuario,
        password_hash=hash_contrasena(datos.contrasena),
        id_rol_usuario=rol.id_rol,
        ci_persona=persona.ci,
    )
    sesion.add(usuario)
    await sesion.flush()
    return await obtener(sesion, usuario.id_usuario)


async def actualizar(sesion: AsyncSession, admin: UsuarioActual, id_usuario: int,
                     datos: UsuarioActualizar) -> UsuarioSalida:
    usuario = await sesion.get(Usuario, id_usuario)
    if usuario is None:
        raise NoEncontrado("Usuario no encontrado.")
    if datos.estado_usuario and datos.estado_usuario != "activo":
        validar_no_es_uno_mismo(id_usuario, admin.id_usuario, "desactivar ni bloquear")
    if datos.estado_usuario == "activo" and usuario.estado_usuario != "activo":
        persona = await sesion.get(Persona, usuario.ci_persona)
        if persona.estado_persona != "activo":
            raise ErrorNegocio("La persona está dada de baja; no se puede activar su cuenta.")
    if datos.nombre_usuario is not None:
        usuario.nombre_usuario = datos.nombre_usuario
    if datos.estado_usuario is not None:
        usuario.estado_usuario = datos.estado_usuario
    await sesion.flush()
    if datos.id_rol is not None and datos.id_rol != usuario.id_rol_usuario:
        await cu03.asignar_rol(sesion, admin, id_usuario, datos.id_rol)
    return await obtener(sesion, id_usuario)


async def desactivar(sesion: AsyncSession, admin: UsuarioActual, id_usuario: int) -> UsuarioSalida:
    return await actualizar(sesion, admin, id_usuario, UsuarioActualizar(estado_usuario="inactivo"))


async def restablecer_contrasena(sesion: AsyncSession, id_usuario: int) -> ContrasenaTemporalSalida:
    usuario = await sesion.get(Usuario, id_usuario)
    if usuario is None:
        raise NoEncontrado("Usuario no encontrado.")
    temporal = contrasena_temporal()
    usuario.password_hash = hash_contrasena(temporal)
    await sesion.flush()
    await repo.registrar_en_bitacora(sesion, ACCION_RESTABLECIDA, "UPDATE", "usuario", str(id_usuario))
    return ContrasenaTemporalSalida(
        contrasena_temporal=temporal,
        mensaje=f"Entregue esta contraseña a {usuario.nombre_usuario}. Se muestra una sola vez; "
                "el usuario debe cambiarla desde 'Mi perfil' al ingresar.",
    )


async def solicitudes_recuperacion(sesion: AsyncSession) -> list[SolicitudRecuperacionSalida]:
    return [SolicitudRecuperacionSalida.model_validate(f._asdict()) for f in await repo.solicitudes_pendientes(sesion)]

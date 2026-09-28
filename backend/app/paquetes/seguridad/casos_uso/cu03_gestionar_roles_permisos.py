"""
CU03 - Gestionar roles y permisos
Paquete: seguridad

Actores ........: Administrador
Rol del sistema : administrador
Tablas .........: rol, usuario
Usa de la BD ...: Trigger de auditoría de rol y usuario

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Los 4 roles son fijos (CHECK en la BD): no se crean, no se renombran ni se borran; solo se edita su descripción.
    - Asignar o cambiar el rol de un usuario aplicando la regla de especialización del CU02.
    - El administrador no puede quitarse a sí mismo el rol administrador.
    - La matriz de permisos por rol es la de politicas.py (MATRIZ_PERMISOS); se muestra en pantalla.

Precondición:
    Sesión iniciada como administrador.

Postcondición:
    La descripción del rol o el rol del usuario queda actualizado; sus permisos cambian con su rol.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import NoEncontrado
from app.paquetes.seguridad import repository as repo
from app.paquetes.seguridad.models import Rol, Usuario
from app.paquetes.seguridad.politicas import MATRIZ_PERMISOS, validar_especializacion, validar_no_es_uno_mismo
from app.paquetes.seguridad.schemas import PermisoSalida, RolSalida


async def listar_roles(sesion: AsyncSession) -> list[RolSalida]:
    return [RolSalida.model_validate(f._asdict()) for f in await repo.roles_con_conteo(sesion)]


async def actualizar_descripcion(sesion: AsyncSession, id_rol: int, descripcion: str) -> RolSalida:
    rol = await sesion.get(Rol, id_rol)
    if rol is None:
        raise NoEncontrado("Rol no encontrado.")
    rol.descripcion_rol = descripcion.strip()
    await sesion.flush()
    return next(r for r in await listar_roles(sesion) if r.id_rol == id_rol)


def matriz_permisos() -> list[PermisoSalida]:
    return [PermisoSalida(paquete=p, codigo=c, caso_uso=n, roles=list(r)) for p, c, n, r in MATRIZ_PERMISOS]


async def asignar_rol(sesion: AsyncSession, admin: UsuarioActual, id_usuario: int, id_rol: int) -> None:
    usuario = await sesion.get(Usuario, id_usuario)
    if usuario is None:
        raise NoEncontrado("Usuario no encontrado.")
    rol = await sesion.get(Rol, id_rol)
    if rol is None:
        raise NoEncontrado("Rol no encontrado.")
    if rol.nombre_rol != "administrador":
        validar_no_es_uno_mismo(id_usuario, admin.id_usuario, "quitar el rol administrador a")
    await validar_especializacion(sesion, usuario.ci_persona, rol.nombre_rol)
    usuario.id_rol_usuario = rol.id_rol
    await sesion.flush()

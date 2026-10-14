"""
Reglas de negocio comunes del paquete horarios (compartido).

    - Solo el administrador gestiona aulas y horarios.
    - Un aula en 'mantenimiento' o 'inactiva' no se asigna.
    - Los choques de horario los impide la BD (trigger): el backend muestra su mensaje.
    - Cualquier usuario con sesión puede consultar horarios, pero solo los que le corresponden
      según su rol (CU20): administrador todos; profesor el suyo y el de sus cursos;
      estudiante el de su curso; tutor el de los cursos de sus estudiantes.

Las reglas propias de cada caso de uso están en el encabezado de su archivo en casos_uso/.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import ErrorNegocio, NoEncontrado, SinPermiso
from app.paquetes.academico.models import Gestion
from app.paquetes.academico.politicas import gestion_abierta
from app.paquetes.horarios import repository as repo


async def verificar_aula_asignable(sesion: AsyncSession, id_asignacion: int) -> None:
    """El aula asociada a la asignación debe estar 'disponible'."""
    fila = (
        await sesion.execute(
            text(
                """SELECT a.estado_aula
                     FROM asignacion_profesor_clase apc
                     JOIN aula a ON a.id_aula = apc.id_aula_asignacion
                    WHERE apc.id_asignacion = :id"""
            ),
            {"id": id_asignacion},
        )
    ).one_or_none()
    if fila is None:
        raise NoEncontrado("No existe la asignación indicada.")
    if fila.estado_aula != "disponible":
        raise ErrorNegocio(
            f"El aula no se puede asignar: está en estado '{fila.estado_aula}'."
        )


async def exigir_gestion_abierta(sesion: AsyncSession) -> Gestion:
    gestion = await gestion_abierta(sesion)
    if gestion is None:
        raise ErrorNegocio("No hay una gestión abierta.")
    return gestion


async def asignacion_del_curso(sesion: AsyncSession, id_asignacion: int, id_curso: int, gestion: Gestion) -> None:
    """CU19: la asignación debe existir, ser de ese curso y de la gestión abierta."""
    asignacion = await repo.datos_asignacion(sesion, id_asignacion)
    if asignacion is None:
        raise NoEncontrado("No existe la asignación indicada.")
    if asignacion.id_curso != id_curso:
        raise ErrorNegocio("La asignación no pertenece a ese curso.")
    if asignacion.id_gestion != gestion.id_gestion:
        raise ErrorNegocio(f"La asignación no es de la gestión abierta ({gestion.anio}).")


# ---- CU20: quién puede ver qué horario (el rol viene de la BD) -------------------
async def puede_ver_curso(sesion: AsyncSession, usuario: UsuarioActual, id_curso: int, gestion: Gestion) -> None:
    """administrador: cualquiera; profesor: donde dicta; estudiante: el suyo; tutor: el de sus estudiantes."""
    if usuario.rol == "administrador":
        return
    if usuario.rol == "profesor":
        cursos = await repo.cursos_del_profesor(sesion, usuario.ci, gestion.id_gestion)
        permitido = any(c.id_curso == id_curso for c in cursos)
    elif usuario.rol == "estudiante":
        curso = await repo.curso_del_estudiante(sesion, usuario.ci, gestion.id_gestion)
        permitido = curso is not None and curso.id_curso == id_curso
    elif usuario.rol == "tutor":
        estudiantes = await repo.estudiantes_del_tutor(sesion, usuario.ci, gestion.id_gestion)
        permitido = any(e.id_curso == id_curso for e in estudiantes)
    else:
        permitido = False
    if not permitido:
        raise SinPermiso("No tiene permiso para ver el horario de ese curso.")


def puede_ver_profesor(usuario: UsuarioActual, ci_profesor: str) -> None:
    """administrador: cualquier docente; profesor: solo el suyo."""
    if usuario.rol == "administrador" or (usuario.rol == "profesor" and usuario.ci == ci_profesor):
        return
    raise SinPermiso("No tiene permiso para ver el horario de ese docente.")

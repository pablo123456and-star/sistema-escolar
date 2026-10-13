"""
Reglas de negocio comunes del paquete horarios (compartido).

    - Solo el administrador gestiona aulas y horarios.
    - Un aula en 'mantenimiento' o 'inactiva' no se asigna.
    - Los choques de horario los impide la BD (trigger): el backend muestra su mensaje.
    - Cualquier usuario con sesión puede consultar horarios.

Las reglas propias de cada caso de uso están en el encabezado de su archivo en casos_uso/.

PENDIENTE.
"""
"""
Reglas de negocio comunes del paquete horarios (compartido).

    - Solo el administrador gestiona aulas y horarios.
    - Un aula en 'mantenimiento' o 'inactiva' no se asigna.
    - Los choques de horario los impide la BD (trigger): el backend muestra su mensaje.
    - Cualquier usuario con sesión puede consultar horarios.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.errores import ErrorNegocio, NoEncontrado


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

"""
Acceso a la base de datos del paquete horarios (compartido).

Consultas y escrituras con SQLAlchemy sobre las tablas de models.py.
Los procedimientos almacenados se ejecutan con CALL (ver basededato/sql/04).

PENDIENTE.
"""
"""
Acceso a la base de datos del paquete horarios (compartido).
"""
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.paquetes.horarios.models import Horario
from app.paquetes.horarios.schemas import HorarioCrear


async def existe_asignacion(sesion: AsyncSession, id_asignacion: int) -> bool:
    fila = await sesion.scalar(
        text("SELECT 1 FROM asignacion_profesor_clase WHERE id_asignacion = :id"),
        {"id": id_asignacion},
    )
    return fila is not None


async def crear_horario(sesion: AsyncSession, datos: HorarioCrear) -> int:
    """Inserta el bloque. Deja que el trigger valide choques."""
    horario = Horario(
        dia=datos.dia,
        hora_inicio_h=datos.hora_inicio,
        hora_final_f=datos.hora_final,
        id_asignacion_horario=datos.id_asignacion,
    )
    sesion.add(horario)
    await sesion.flush()   # aquí salta el trigger si hay choque
    return horario.id_horario


async def obtener_horario(sesion: AsyncSession, id_horario: int):
    fila = (
        await sesion.execute(
            text("SELECT * FROM v_horario WHERE id_horario = :id"), {"id": id_horario}
        )
    ).one_or_none()
    return fila


async def listar_por_gestion(sesion: AsyncSession, id_gestion: int):
    return (
        await sesion.execute(
            text(
                """SELECT * FROM v_horario
                    WHERE id_gestion = :g
                    ORDER BY id_curso, dia_orden, hora_inicio"""
            ),
            {"g": id_gestion},
        )
    ).all()

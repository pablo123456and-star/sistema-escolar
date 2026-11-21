"""Acceso a la base de datos del paquete asistente: solo la bitácora (el asistente lee a través de la API)."""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def registrar_consulta(sesion: AsyncSession, pregunta: str) -> None:
    await sesion.execute(
        text("SELECT fn_registrar_bitacora(:accion, 'ASISTENTE', 'OTRO')"),
        {"accion": f"Consultó al asistente: «{pregunta[:300]}»"},
    )


async def ahora(sesion: AsyncSession):
    """Fecha y hora según la BD (la sesión usa la hora de Bolivia)."""
    return await sesion.scalar(text("SELECT localtimestamp"))


async def gestion_abierta(sesion: AsyncSession) -> list[dict]:
    """Trimestres de la gestión abierta (para que el asistente no gaste consultas buscándolos)."""
    filas = await sesion.execute(text("""
        SELECT g.id_gestion, g.anio, p.id_periodo, p.nombre_periodo, p.estado_periodo,
               p.fecha_inicio_p, p.fecha_final_p
        FROM gestion g JOIN periodo p ON p.id_gestion_periodo = g.id_gestion
        WHERE g.estado_gestion = 'abierta'
        ORDER BY p.fecha_inicio_p"""))
    return [dict(f._mapping) for f in filas]

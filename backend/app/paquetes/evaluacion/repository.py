"""
Acceso a la base de datos del paquete evaluacion (compartido).

Consultas y escrituras con SQLAlchemy sobre las tablas de models.py.
Los procedimientos almacenados se ejecutan con CALL (ver basededato/sql/04).
"""
# ============================================================
# CU21 - REGISTRAR ASISTENCIA DE ESTUDIANTES
# ============================================================

from datetime import date

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Asignación con su curso, materia, profesor y días de clase (horario del CU19)
_CLASE = """
    SELECT a.id_asignacion, a.id_curso_asignacion AS id_curso, vc.nombre_curso AS curso,
           m.nombre_materia AS materia, a.ci_profesor_asignacion AS ci_profesor,
           p.nombre_persona || ' ' || p.apellidos AS profesor,
           coalesce((SELECT array_agg(d.dia ORDER BY d.dia_orden)
                       FROM (SELECT DISTINCT vh.dia, vh.dia_orden FROM v_horario vh
                              WHERE vh.id_asignacion = a.id_asignacion) d), '{}') AS dias,
           EXISTS (SELECT 1 FROM asistencia s
                    WHERE s.id_asignacion_asistencia = a.id_asignacion AND s.fecha_asistencia = CURRENT_DATE)
               AS registrada_hoy,
           a.id_gestion_asignacion AS id_gestion, g.anio, g.fecha_inicio_g, g.fecha_final_g, g.estado_gestion,
           vc.id_nivel, vc.orden_grado, vc.paralelo
      FROM asignacion_profesor_clase a
      JOIN v_curso vc ON vc.id_curso = a.id_curso_asignacion
      JOIN materia m  ON m.id_materia = a.id_materia_asignacion
      JOIN persona p  ON p.ci = a.ci_profesor_asignacion
      JOIN gestion g  ON g.id_gestion = a.id_gestion_asignacion
"""


async def hoy(sesion: AsyncSession) -> date:
    """Fecha actual en Bolivia (la sesión de BD usa la zona horaria America/La_Paz)."""
    return await sesion.scalar(text("SELECT CURRENT_DATE"))


async def clases_cu21(sesion: AsyncSession, id_gestion: int, ci_profesor: str | None):
    filtro = "AND a.ci_profesor_asignacion = :ci" if ci_profesor else ""
    return (
        await sesion.execute(
            text(f"""{_CLASE} WHERE a.id_gestion_asignacion = :g {filtro}
                     ORDER BY vc.id_nivel, vc.orden_grado, vc.paralelo, m.nombre_materia"""),
            {"g": id_gestion, "ci": ci_profesor},
        )
    ).all()


async def clase_cu21(sesion: AsyncSession, id_asignacion: int):
    return (
        await sesion.execute(text(f"{_CLASE} WHERE a.id_asignacion = :id"), {"id": id_asignacion})
    ).one_or_none()


async def periodo_de_fecha_cu21(sesion: AsyncSession, id_gestion: int, fecha: date):
    """Periodo (trimestre) de la gestión que contiene la fecha; None si cae entre periodos."""
    return (
        await sesion.execute(
            text("""SELECT nombre_periodo, estado_periodo FROM periodo
                     WHERE id_gestion_periodo = :g AND :f BETWEEN fecha_inicio_p AND fecha_final_p"""),
            {"g": id_gestion, "f": fecha},
        )
    ).one_or_none()


async def estudiantes_cu21(sesion: AsyncSession, id_asignacion: int, fecha: date):
    """Inscritos activos del curso de la clase, con su asistencia de esa fecha (si ya existe)."""
    return (
        await sesion.execute(
            text("""SELECT p.ci, p.nombre_persona, p.apellidos,
                           s.estado_asistencia AS estado, s.observacion_asistencia AS observacion
                      FROM asignacion_profesor_clase a
                      JOIN inscripcion i ON i.id_curso_inscripcion = a.id_curso_asignacion
                                        AND i.id_gestion_inscripcion = a.id_gestion_asignacion
                                        AND i.estado_inscripcion = 'activa'
                      JOIN persona p ON p.ci = i.ci_estudiante_inscripcion
                      LEFT JOIN asistencia s ON s.id_asignacion_asistencia = a.id_asignacion
                                            AND s.ci_estudiante_asistencia = p.ci
                                            AND s.fecha_asistencia = :f
                     WHERE a.id_asignacion = :id
                     ORDER BY p.apellidos, p.nombre_persona"""),
            {"id": id_asignacion, "f": fecha},
        )
    ).all()


async def guardar_cu21(sesion: AsyncSession, id_asignacion: int, fecha: date, registros: list[dict]) -> None:
    """Registra o corrige (un registro por estudiante, clase y día). Solo actualiza lo que cambió,
    así la bitácora (trigger trg_auditar_asistencia) guarda únicamente las correcciones reales."""
    await sesion.execute(
        text("""INSERT INTO asistencia (id_asignacion_asistencia, ci_estudiante_asistencia, fecha_asistencia,
                                        estado_asistencia, observacion_asistencia)
                VALUES (:id, :ci, :f, :estado, :observacion)
                ON CONFLICT (id_asignacion_asistencia, ci_estudiante_asistencia, fecha_asistencia)
                DO UPDATE SET estado_asistencia = EXCLUDED.estado_asistencia,
                              observacion_asistencia = EXCLUDED.observacion_asistencia
                 WHERE (asistencia.estado_asistencia, asistencia.observacion_asistencia)
                       IS DISTINCT FROM (EXCLUDED.estado_asistencia, EXCLUDED.observacion_asistencia)"""),
        [{"id": id_asignacion, "f": fecha, **r} for r in registros],
    )

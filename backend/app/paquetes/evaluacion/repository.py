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


# ============================================================
# CU22 - CONSULTAR HISTORIAL DE ASISTENCIA
# ============================================================

# Quién ve a quién (se agrega al WHERE de la inscripción i)
_VISIBLES_CU22 = {
    "administrador": "",
    "profesor": """AND EXISTS (SELECT 1 FROM asignacion_profesor_clase a
                                WHERE a.id_curso_asignacion = i.id_curso_inscripcion
                                  AND a.id_gestion_asignacion = i.id_gestion_inscripcion
                                  AND a.ci_profesor_asignacion = :usuario)""",
    "tutor": """AND EXISTS (SELECT 1 FROM tutor_estudiante te
                             WHERE te.ci_estudiante_tutorestudiante = i.ci_estudiante_inscripcion
                               AND te.ci_tutor_tutorestudiante = :usuario)""",
    "estudiante": "AND i.ci_estudiante_inscripcion = :usuario",
}


async def gestion_vigente_cu22(sesion: AsyncSession):
    """La gestión abierta; si no hay, la más reciente (para seguir consultando al cerrar el año)."""
    return (
        await sesion.execute(
            text("""SELECT id_gestion, anio FROM gestion
                     ORDER BY estado_gestion = 'abierta' DESC, anio DESC LIMIT 1""")
        )
    ).one_or_none()


async def gestiones_cu22(sesion: AsyncSession, ci_estudiante: str):
    """Gestiones en las que el estudiante estuvo inscrito (la más reciente primero)."""
    return (
        await sesion.execute(
            text("""SELECT g.id_gestion, g.anio, g.estado_gestion
                      FROM inscripcion i JOIN gestion g ON g.id_gestion = i.id_gestion_inscripcion
                     WHERE i.ci_estudiante_inscripcion = :ci
                     ORDER BY g.anio DESC"""),
            {"ci": ci_estudiante},
        )
    ).all()


async def estudiantes_cu22(sesion: AsyncSession, id_gestion: int, rol: str, ci_usuario: str,
                           ci_estudiante: str | None = None):
    """Inscritos de la gestión que el usuario puede consultar (según su rol); uno solo si se indica el CI."""
    filtro = "AND i.ci_estudiante_inscripcion = :ci" if ci_estudiante else ""
    return (
        await sesion.execute(
            text(f"""SELECT p.ci, p.nombre_persona, p.apellidos, vc.nombre_curso AS curso, i.estado_inscripcion
                       FROM inscripcion i
                       JOIN persona p  ON p.ci = i.ci_estudiante_inscripcion
                       JOIN v_curso vc ON vc.id_curso = i.id_curso_inscripcion
                      WHERE i.id_gestion_inscripcion = :g {_VISIBLES_CU22[rol]} {filtro}
                      ORDER BY vc.id_nivel, vc.orden_grado, vc.paralelo, p.apellidos, p.nombre_persona"""),
            {"g": id_gestion, "usuario": ci_usuario, "ci": ci_estudiante},
        )
    ).all()


async def materias_cu22(sesion: AsyncSession, ci_estudiante: str, id_gestion: int):
    """Materias del curso del estudiante en esa gestión (aunque todavía no tengan asistencia)."""
    return (
        await sesion.execute(
            text("""SELECT DISTINCT m.id_materia, m.nombre_materia AS materia
                      FROM inscripcion i
                      JOIN asignacion_profesor_clase a ON a.id_curso_asignacion = i.id_curso_inscripcion
                                                      AND a.id_gestion_asignacion = i.id_gestion_inscripcion
                      JOIN materia m ON m.id_materia = a.id_materia_asignacion
                     WHERE i.ci_estudiante_inscripcion = :ci AND i.id_gestion_inscripcion = :g
                     ORDER BY m.nombre_materia"""),
            {"ci": ci_estudiante, "g": id_gestion},
        )
    ).all()


async def historial_cu22(sesion: AsyncSession, ci_estudiante: str, id_gestion: int, desde: date | None,
                         hasta: date | None, id_materia: int | None):
    """Asistencia registrada del estudiante en la gestión (la más reciente primero)."""
    filtros = ""
    if desde:
        filtros += " AND s.fecha_asistencia >= :desde"
    if hasta:
        filtros += " AND s.fecha_asistencia <= :hasta"
    if id_materia:
        filtros += " AND m.id_materia = :materia"
    return (
        await sesion.execute(
            text(f"""SELECT s.fecha_asistencia AS fecha, m.id_materia, m.nombre_materia AS materia,
                            s.estado_asistencia AS estado, s.observacion_asistencia AS observacion
                       FROM asistencia s
                       JOIN asignacion_profesor_clase a ON a.id_asignacion = s.id_asignacion_asistencia
                       JOIN materia m ON m.id_materia = a.id_materia_asignacion
                      WHERE s.ci_estudiante_asistencia = :ci AND a.id_gestion_asignacion = :g {filtros}
                      ORDER BY s.fecha_asistencia DESC, m.nombre_materia"""),
            {"ci": ci_estudiante, "g": id_gestion, "desde": desde, "hasta": hasta, "materia": id_materia},
        )
    ).all()


# ============================================================
# CU24 - GENERAR Y CONSULTAR BOLETÍN/LIBRETA
# ============================================================


async def periodo_cu24(sesion: AsyncSession, id_periodo: int):
    """Obtiene el periodo (trimestre) por id, con el año y la nota mínima de aprobación de su gestión."""
    return (
        await sesion.execute(
            text("""SELECT pe.id_periodo, pe.nombre_periodo, pe.estado_periodo, g.anio, g.nota_minima_aprobacion
                      FROM periodo pe JOIN gestion g ON g.id_gestion = pe.id_gestion_periodo
                     WHERE pe.id_periodo = :id"""),
            {"id": id_periodo},
        )
    ).one_or_none()


async def curso_cu24(sesion: AsyncSession, id_curso: int):
    """Obtiene el curso con su nombre completo."""
    return (
        await sesion.execute(
            text("SELECT id_curso, nombre_curso FROM v_curso WHERE id_curso = :id"),
            {"id": id_curso},
        )
    ).one_or_none()


async def emitir_boletines_cu24(sesion: AsyncSession, id_periodo: int, id_curso: int | None) -> int:
    """Llama a sp_emitir_boletines y devuelve su INOUT p_boletines (boletines emitidos o reemitidos en esta llamada)."""
    cantidad = await sesion.scalar(
        text("CALL sp_emitir_boletines(:id_p, :id_c, NULL)"),
        {"id_p": id_periodo, "id_c": id_curso},
    )
    return cantidad or 0


async def boletin_cu24(sesion: AsyncSession, ci_estudiante: str, id_periodo: int):
    """Obtiene el boletín completo de un estudiante en un periodo."""
    return (
        await sesion.execute(
            text("""
            SELECT b.id_boletin, b.fecha_emision_b, b.promedio_general_b, b.observaciones_generales_boletin,
                   p.ci, p.nombre_persona, p.apellidos,
                   pe.nombre_periodo, pe.id_gestion_periodo,
                   g.anio,
                   i.id_curso_inscripcion, vc.nombre_curso,
                   array_agg(
                       json_build_object(
                           'id_materia', nf.id_materia,
                           'materia', m.nombre_materia,
                           'nota_final', nf.nota_final,
                           'dimensiones_registradas', nf.dimensiones_registradas,
                           'dimensiones_totales', nf.dimensiones_totales
                       ) ORDER BY m.nombre_materia
                   ) AS notas_por_materia
              FROM boletin b
              JOIN persona p ON p.ci = b.ci_estudiante_boletin
              JOIN periodo pe ON pe.id_periodo = b.id_periodo_boletin
              JOIN gestion g ON g.id_gestion = pe.id_gestion_periodo
              LEFT JOIN inscripcion i ON i.ci_estudiante_inscripcion = b.ci_estudiante_boletin
                                     AND i.id_gestion_inscripcion = pe.id_gestion_periodo
              LEFT JOIN v_curso vc ON vc.id_curso = i.id_curso_inscripcion
              LEFT JOIN v_nota_final nf ON nf.ci_estudiante = b.ci_estudiante_boletin
                                       AND nf.id_periodo = b.id_periodo_boletin
              LEFT JOIN materia m ON m.id_materia = nf.id_materia
             WHERE b.ci_estudiante_boletin = :ci AND b.id_periodo_boletin = :id_p
             GROUP BY b.id_boletin, p.ci, p.nombre_persona, p.apellidos,
                      pe.nombre_periodo, pe.id_gestion_periodo, g.anio,
                      i.id_curso_inscripcion, vc.nombre_curso
            """),
            {"ci": ci_estudiante, "id_p": id_periodo},
        )
    ).one_or_none()


async def es_mi_estudiante_cu24(sesion: AsyncSession, ci_tutor: str, ci_estudiante: str) -> bool:
    """Verifica si el estudiante está a cargo del tutor."""
    result = await sesion.scalar(
        text("""SELECT EXISTS (
                 SELECT 1 FROM tutor_estudiante
                  WHERE ci_tutor_tutorestudiante = :tutor
                    AND ci_estudiante_tutorestudiante = :estudiante
                )"""),
        {"tutor": ci_tutor, "estudiante": ci_estudiante},
    )
    return bool(result)


async def periodos_cu24(sesion: AsyncSession):
    """Periodos de todas las gestiones (la más reciente primero) para consultar también boletines anteriores."""
    return (
        await sesion.execute(
            text("""
            SELECT pe.id_periodo, pe.nombre_periodo, pe.estado_periodo, g.anio, g.estado_gestion
              FROM periodo pe
              JOIN gestion g ON g.id_gestion = pe.id_gestion_periodo
             ORDER BY g.anio DESC, pe.fecha_inicio_p
            """),
        )
    ).all()


# Estudiantes que cada rol puede elegir en el CU24 (el administrador ve a todos)
_VISIBLES_CU24 = {
    "administrador": "",
    "tutor": """AND EXISTS (SELECT 1 FROM tutor_estudiante te
                             WHERE te.ci_estudiante_tutorestudiante = i.ci_estudiante_inscripcion
                               AND te.ci_tutor_tutorestudiante = :usuario)""",
    "estudiante": "AND i.ci_estudiante_inscripcion = :usuario",
}


async def estudiantes_cu24(sesion: AsyncSession, id_periodo: int, rol: str, ci_usuario: str, id_curso: int | None):
    """Inscritos (no retirados) en la gestión del periodo que el usuario puede consultar, opcionalmente de un curso."""
    filtro_curso = "AND i.id_curso_inscripcion = :c" if id_curso else ""
    return (
        await sesion.execute(
            text(f"""
            SELECT p.ci, p.nombre_persona, p.apellidos, vc.nombre_curso
              FROM inscripcion i
              JOIN periodo pe ON pe.id_gestion_periodo = i.id_gestion_inscripcion
              JOIN persona p  ON p.ci = i.ci_estudiante_inscripcion
              JOIN v_curso vc ON vc.id_curso = i.id_curso_inscripcion
             WHERE pe.id_periodo = :p AND i.estado_inscripcion <> 'retirada'
                   {_VISIBLES_CU24[rol]} {filtro_curso}
             ORDER BY vc.id_nivel, vc.orden_grado, vc.paralelo, p.apellidos, p.nombre_persona
            """),
            {"p": id_periodo, "usuario": ci_usuario, "c": id_curso},
        )
    ).all()


async def cursos_cu24(sesion: AsyncSession):
    """Retorna todos los cursos con su información."""
    return (
        await sesion.execute(
            text("""
            SELECT id_curso, nombre_curso
              FROM v_curso
             ORDER BY id_nivel, orden_grado, paralelo
            """),
        )
    ).all()


async def materias_centralizador_cu24(sesion: AsyncSession, id_curso: int, id_periodo: int):
    """Columnas del centralizador: materias asignadas al curso en la gestión más las que ya tienen notas."""
    return (
        await sesion.execute(
            text("""
            SELECT DISTINCT m.id_materia, m.nombre_materia AS materia
              FROM materia m
             WHERE m.id_materia IN (
                   SELECT a.id_materia_asignacion
                     FROM asignacion_profesor_clase a
                     JOIN periodo pe ON pe.id_gestion_periodo = a.id_gestion_asignacion
                    WHERE a.id_curso_asignacion = :id_c AND pe.id_periodo = :id_p
                   UNION
                   SELECT nf.id_materia
                     FROM v_nota_final nf
                     JOIN inscripcion i ON i.ci_estudiante_inscripcion = nf.ci_estudiante
                                       AND i.id_gestion_inscripcion = nf.id_gestion
                    WHERE nf.id_periodo = :id_p AND i.id_curso_inscripcion = :id_c
                      AND i.estado_inscripcion <> 'retirada')
             ORDER BY m.nombre_materia
            """),
            {"id_c": id_curso, "id_p": id_periodo},
        )
    ).all()


async def centralizador_cu24(sesion: AsyncSession, id_curso: int, id_periodo: int):
    """Notas por estudiante y materia para el centralizador (inscritos no retirados, también de gestiones cerradas)."""
    return (
        await sesion.execute(
            text("""
            SELECT p.ci, p.nombre_persona, p.apellidos,
                   array_agg(
                       json_build_object(
                           'id_materia', nf.id_materia,
                           'materia', m.nombre_materia,
                           'nota_final', nf.nota_final,
                           'dimensiones_registradas', nf.dimensiones_registradas,
                           'dimensiones_totales', nf.dimensiones_totales
                       ) ORDER BY m.nombre_materia
                   ) FILTER (WHERE nf.id_materia IS NOT NULL) AS notas,
                   round(avg(nf.nota_final), 2) AS promedio_estudiante
              FROM inscripcion i
              JOIN persona p ON p.ci = i.ci_estudiante_inscripcion
              LEFT JOIN v_nota_final nf ON nf.ci_estudiante = i.ci_estudiante_inscripcion
                                       AND nf.id_periodo = :id_p
              LEFT JOIN materia m ON m.id_materia = nf.id_materia
             WHERE i.id_curso_inscripcion = :id_c
               AND i.id_gestion_inscripcion = (SELECT id_gestion_periodo FROM periodo WHERE id_periodo = :id_p)
               AND i.estado_inscripcion <> 'retirada'
             GROUP BY p.ci, p.nombre_persona, p.apellidos
             ORDER BY p.apellidos, p.nombre_persona
            """),
            {"id_c": id_curso, "id_p": id_periodo},
        )
    ).all()

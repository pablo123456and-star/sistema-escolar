"""
Acceso a la base de datos del paquete horarios (compartido).

Consultas y escrituras con SQLAlchemy sobre las tablas de models.py.
Los procedimientos almacenados se ejecutan con CALL (ver basededato/sql/04).
"""
from sqlalchemy import text
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


# ---- CU19: generar horario -------------------------------------------------------
async def cursos_con_avance(sesion: AsyncSession, id_gestion: int):
    return (
        await sesion.execute(
            text("""SELECT vc.id_curso, vc.nombre_curso, vc.id_grado, vc.nombre_grado, vc.paralelo,
                           vc.nombre_nivel AS nivel,
                           count(DISTINCT a.id_asignacion) AS asignaciones,
                           count(h.id_horario) AS bloques
                      FROM v_curso vc
                      LEFT JOIN asignacion_profesor_clase a
                             ON a.id_curso_asignacion = vc.id_curso AND a.id_gestion_asignacion = :g
                      LEFT JOIN horario h ON h.id_asignacion_horario = a.id_asignacion
                     GROUP BY vc.id_curso, vc.nombre_curso, vc.id_grado, vc.nombre_grado, vc.paralelo,
                              vc.nombre_nivel, vc.id_nivel, vc.orden_grado
                     ORDER BY vc.id_nivel, vc.orden_grado, vc.paralelo"""),
            {"g": id_gestion},
        )
    ).all()


async def nombre_curso(sesion: AsyncSession, id_curso: int) -> str | None:
    return await sesion.scalar(text("SELECT nombre_curso FROM v_curso WHERE id_curso = :c"), {"c": id_curso})


async def asignaciones_del_curso(sesion: AsyncSession, id_curso: int, id_gestion: int):
    return (
        await sesion.execute(
            text("""SELECT a.id_asignacion, m.id_materia, m.nombre_materia, m.carga_horaria,
                           a.ci_profesor_asignacion AS ci_profesor,
                           p.nombre_persona || ' ' || p.apellidos AS profesor, au.numero AS aula,
                           (SELECT count(*) FROM horario h WHERE h.id_asignacion_horario = a.id_asignacion) AS bloques
                      FROM asignacion_profesor_clase a
                      JOIN materia m ON m.id_materia = a.id_materia_asignacion
                      JOIN persona p ON p.ci = a.ci_profesor_asignacion
                      JOIN aula au   ON au.id_aula = a.id_aula_asignacion
                     WHERE a.id_curso_asignacion = :c AND a.id_gestion_asignacion = :g
                     ORDER BY m.nombre_materia"""),
            {"c": id_curso, "g": id_gestion},
        )
    ).all()


async def bloques_del_curso(sesion: AsyncSession, id_curso: int, id_gestion: int):
    return (
        await sesion.execute(
            text("""SELECT * FROM v_horario WHERE id_curso = :c AND id_gestion = :g
                     ORDER BY dia_orden, hora_inicio"""),
            {"c": id_curso, "g": id_gestion},
        )
    ).all()


async def datos_asignacion(sesion: AsyncSession, id_asignacion: int):
    """Curso y gestión de una asignación (para validar que se use en el curso correcto)."""
    return (
        await sesion.execute(
            text("""SELECT id_asignacion, id_curso_asignacion AS id_curso, id_gestion_asignacion AS id_gestion
                      FROM asignacion_profesor_clase WHERE id_asignacion = :id"""),
            {"id": id_asignacion},
        )
    ).one_or_none()


async def choque_horario(sesion: AsyncSession, *, id_asignacion: int, dia: str, hora_inicio, hora_final,
                         id_horario: int | None):
    """Bloque que choca con el indicado (misma lógica que el trigger fn_tg_validar_horario), con nombres."""
    return (
        await sesion.execute(
            text("""SELECT vh.nombre_materia, vh.nombre_curso, vh.profesor, vh.aula, vh.hora_inicio, vh.hora_final,
                           CASE WHEN vh.ci_profesor = n.ci_profesor_asignacion THEN 'docente'
                                WHEN vh.id_aula = n.id_aula_asignacion THEN 'aula'
                                ELSE 'curso' END AS tipo
                      FROM asignacion_profesor_clase n
                      JOIN v_horario vh ON vh.id_gestion = n.id_gestion_asignacion
                     WHERE n.id_asignacion = :a
                       AND vh.id_horario <> coalesce(CAST(:h AS INTEGER), -1)
                       AND vh.dia = :dia AND vh.hora_inicio < :fin AND :inicio < vh.hora_final
                       AND (vh.ci_profesor = n.ci_profesor_asignacion OR vh.id_aula = n.id_aula_asignacion
                            OR vh.id_curso = n.id_curso_asignacion)
                     ORDER BY (vh.ci_profesor = n.ci_profesor_asignacion) DESC, (vh.id_aula = n.id_aula_asignacion) DESC
                     LIMIT 1"""),
            {"a": id_asignacion, "h": id_horario, "dia": dia, "inicio": hora_inicio, "fin": hora_final},
        )
    ).one_or_none()


# ---- CU20: consultar horarios ----------------------------------------------------
async def bloques_del_profesor(sesion: AsyncSession, ci_profesor: str, id_gestion: int):
    return (
        await sesion.execute(
            text("""SELECT * FROM v_horario WHERE ci_profesor = :ci AND id_gestion = :g
                     ORDER BY dia_orden, hora_inicio"""),
            {"ci": ci_profesor, "g": id_gestion},
        )
    ).all()


async def nombre_persona(sesion: AsyncSession, ci: str) -> str | None:
    return await sesion.scalar(
        text("SELECT nombre_persona || ' ' || apellidos FROM persona WHERE ci = :ci"), {"ci": ci}
    )


async def cursos_de_la_gestion(sesion: AsyncSession, id_gestion: int):
    """Cursos que tienen asignaciones en la gestión."""
    return (
        await sesion.execute(
            text("""SELECT DISTINCT vc.id_curso, vc.nombre_curso, vc.id_nivel, vc.orden_grado, vc.paralelo
                      FROM v_curso vc
                      JOIN asignacion_profesor_clase a ON a.id_curso_asignacion = vc.id_curso
                     WHERE a.id_gestion_asignacion = :g
                     ORDER BY vc.id_nivel, vc.orden_grado, vc.paralelo"""),
            {"g": id_gestion},
        )
    ).all()


async def docentes_de_la_gestion(sesion: AsyncSession, id_gestion: int):
    return (
        await sesion.execute(
            text("""SELECT DISTINCT p.ci, p.apellidos || ' ' || p.nombre_persona AS nombre
                      FROM asignacion_profesor_clase a
                      JOIN persona p ON p.ci = a.ci_profesor_asignacion
                     WHERE a.id_gestion_asignacion = :g
                     ORDER BY nombre"""),
            {"g": id_gestion},
        )
    ).all()


async def cursos_del_profesor(sesion: AsyncSession, ci_profesor: str, id_gestion: int):
    return (
        await sesion.execute(
            text("""SELECT DISTINCT vc.id_curso, vc.nombre_curso, vc.id_nivel, vc.orden_grado, vc.paralelo
                      FROM v_curso vc
                      JOIN asignacion_profesor_clase a ON a.id_curso_asignacion = vc.id_curso
                     WHERE a.id_gestion_asignacion = :g AND a.ci_profesor_asignacion = :ci
                     ORDER BY vc.id_nivel, vc.orden_grado, vc.paralelo"""),
            {"g": id_gestion, "ci": ci_profesor},
        )
    ).all()


async def curso_del_estudiante(sesion: AsyncSession, ci_estudiante: str, id_gestion: int):
    """Curso de la inscripción activa del estudiante en la gestión."""
    return (
        await sesion.execute(
            text("""SELECT vc.id_curso, vc.nombre_curso
                      FROM inscripcion i
                      JOIN v_curso vc ON vc.id_curso = i.id_curso_inscripcion
                     WHERE i.ci_estudiante_inscripcion = :ci AND i.id_gestion_inscripcion = :g
                       AND i.estado_inscripcion = 'activa'"""),
            {"ci": ci_estudiante, "g": id_gestion},
        )
    ).one_or_none()


async def estudiantes_del_tutor(sesion: AsyncSession, ci_tutor: str, id_gestion: int):
    """Estudiantes del tutor con el curso de su inscripción activa (si tienen)."""
    return (
        await sesion.execute(
            text("""SELECT p.ci, p.nombre_persona || ' ' || p.apellidos AS nombre, vc.id_curso, vc.nombre_curso
                      FROM tutor_estudiante te
                      JOIN persona p ON p.ci = te.ci_estudiante_tutorestudiante
                      LEFT JOIN inscripcion i ON i.ci_estudiante_inscripcion = p.ci
                                             AND i.id_gestion_inscripcion = :g AND i.estado_inscripcion = 'activa'
                      LEFT JOIN v_curso vc    ON vc.id_curso = i.id_curso_inscripcion
                     WHERE te.ci_tutor_tutorestudiante = :ci
                     ORDER BY p.apellidos, p.nombre_persona"""),
            {"ci": ci_tutor, "g": id_gestion},
        )
    ).all()

"""
Acceso a la base de datos del paquete horarios (compartido).

Consultas y escrituras con SQLAlchemy sobre las tablas de models.py.
Los procedimientos almacenados se ejecutan con CALL (ver basededato/sql/04).
"""
import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.paquetes.horarios.models import Aula, Horario
from app.paquetes.horarios.schemas import AulaActualizar, AulaCrear, HorarioCrear


# ---- CU18: gestionar aulas -------------------------------------------------------
async def listar_aulas_con_conteo(sesion: AsyncSession):
    """Lista todas las aulas con el total de clases asignadas en asignacion_profesor_clase."""
    return (
        await sesion.execute(
            text(
                """SELECT a.id_aula,
                          a.numero,
                          a.capacidad,
                          a.tipo_aula,
                          a.estado_aula,
                          COUNT(apc.id_asignacion)::int AS total_clases_asignadas
                     FROM aula a
                     LEFT JOIN asignacion_profesor_clase apc ON apc.id_aula_asignacion = a.id_aula
                    GROUP BY a.id_aula, a.numero, a.capacidad, a.tipo_aula, a.estado_aula
                    ORDER BY a.numero ASC"""
            )
        )
    ).all()


async def obtener_aula_por_id(sesion: AsyncSession, id_aula: int) -> Aula | None:
    return await sesion.get(Aula, id_aula)


async def obtener_aula_detalle(sesion: AsyncSession, id_aula: int):
    """Obtiene un aula por su ID incluyendo el conteo de asignaciones."""
    return (
        await sesion.execute(
            text(
                """SELECT a.id_aula,
                          a.numero,
                          a.capacidad,
                          a.tipo_aula,
                          a.estado_aula,
                          COUNT(apc.id_asignacion)::int AS total_clases_asignadas
                     FROM aula a
                     LEFT JOIN asignacion_profesor_clase apc ON apc.id_aula_asignacion = a.id_aula
                    WHERE a.id_aula = :id
                    GROUP BY a.id_aula, a.numero, a.capacidad, a.tipo_aula, a.estado_aula"""
            ),
            {"id": id_aula},
        )
    ).one_or_none()


async def obtener_aula_por_numero(sesion: AsyncSession, numero: str) -> Aula | None:
    fila = (
        await sesion.execute(
            text("SELECT id_aula, numero, capacidad, tipo_aula, estado_aula FROM aula WHERE numero = :num"),
            {"num": numero.strip()},
        )
    ).one_or_none()
    return fila


async def contar_asignaciones_aula(sesion: AsyncSession, id_aula: int) -> int:
    return (
        await sesion.scalar(
            text("SELECT COUNT(*)::int FROM asignacion_profesor_clase WHERE id_aula_asignacion = :id"),
            {"id": id_aula},
        )
        or 0
    )


async def crear_aula(sesion: AsyncSession, datos: AulaCrear) -> Aula:
    aula = Aula(
        numero=datos.numero.strip(),
        capacidad=datos.capacidad,
        tipo_aula=datos.tipo_aula.strip() if datos.tipo_aula else None,
        estado_aula=datos.estado_aula,
    )
    sesion.add(aula)
    await sesion.flush()
    return aula


async def actualizar_aula(sesion: AsyncSession, aula: Aula, datos: AulaActualizar) -> Aula:
    cambios = datos.model_dump(exclude_unset=True)
    if "numero" in cambios and cambios["numero"] is not None:
        aula.numero = cambios["numero"].strip()
    if "capacidad" in cambios and cambios["capacidad"] is not None:
        aula.capacidad = cambios["capacidad"]
    if "tipo_aula" in cambios:
        aula.tipo_aula = cambios["tipo_aula"].strip() if cambios["tipo_aula"] else None
    if "estado_aula" in cambios and cambios["estado_aula"] is not None:
        aula.estado_aula = cambios["estado_aula"]
    await sesion.flush()
    return aula


async def eliminar_aula(sesion: AsyncSession, aula: Aula) -> None:
    await sesion.delete(aula)
    await sesion.flush()


async def registrar_bitacora_cu18(sesion: AsyncSession, accion: str, operacion: str, id_aula: int,
                                  antes: dict | None, despues: dict | None) -> None:
    """La tabla aula no tiene trigger de auditoría: altas, cambios y bajas se anotan a mano."""
    await sesion.execute(
        text("""SELECT fn_registrar_bitacora(:accion, 'HORARIOS', :operacion, 'aula', :id,
                                             CAST(:antes AS jsonb), CAST(:despues AS jsonb))"""),
        {"accion": accion, "operacion": operacion, "id": str(id_aula),
         "antes": json.dumps(antes) if antes is not None else None,
         "despues": json.dumps(despues) if despues is not None else None},
    )




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

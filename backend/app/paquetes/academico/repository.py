"""
Acceso a la base de datos del paquete academico (compartido).

Consultas y escrituras con SQLAlchemy sobre las tablas de models.py.
Los procedimientos almacenados se ejecutan con CALL (ver basededato/sql/04).

PENDIENTE.
"""
# ============================================================
# CU13 - REPOSITORIO DE MATERIAS Y PLAN DE ESTUDIOS
# ============================================================

import json

from sqlalchemy import select, func, exists, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.paquetes.academico.models import (
    Materia,
    MateriaGrado,
    NivelEducativo,
    Grado,
)


# CONSULTAS DE MATERIAS

async def listar_materias(
    sesion: AsyncSession,
    q: str | None = None,
    pagina: int = 1,
    tamano: int = 10,
):
    """Lista las materias con búsqueda y paginación."""

    consulta = select(Materia)

    if q and q.strip():
        consulta = consulta.where(
            Materia.nombre_materia.ilike(f"%{q.strip()}%")
        )

    total = await sesion.scalar(
        select(func.count()).select_from(consulta.subquery())
    )

    consulta = (
        consulta
        .order_by(Materia.nombre_materia)
        .offset((pagina - 1) * tamano)
        .limit(tamano)
    )

    resultado = await sesion.scalars(consulta)

    return resultado.all(), total or 0


async def buscar_materia_por_nombre(
    sesion: AsyncSession,
    nombre: str,
    id_excluir: int | None = None,
):
    """Busca una materia por nombre para evitar duplicados."""

    consulta = select(Materia).where(
        func.lower(Materia.nombre_materia) == nombre.strip().lower()
    )

    if id_excluir is not None:
        consulta = consulta.where(
            Materia.id_materia != id_excluir
        )

    return await sesion.scalar(consulta)


async def obtener_materia(
    sesion: AsyncSession,
    id_materia: int,
):
    """Obtiene una materia por su identificador."""

    return await sesion.get(Materia, id_materia)


# CONSULTAS DE NIVELES Y GRADOS

async def listar_niveles(sesion: AsyncSession):
    """Obtiene los niveles educativos registrados."""

    consulta = select(NivelEducativo).order_by(
        NivelEducativo.id_nivel
    )

    resultado = await sesion.scalars(consulta)

    return resultado.all()


async def listar_grados(sesion: AsyncSession):
    """Obtiene los grados ordenados por nivel."""

    consulta = select(Grado).order_by(
        Grado.id_nivel_educativo_grado,
        Grado.orden_grado,
    )

    resultado = await sesion.scalars(consulta)

    return resultado.all()


# CONSULTAS DEL PLAN DE ESTUDIOS

async def materias_del_grado(
    sesion: AsyncSession,
    id_grado: int,
):
    """Consulta las materias que pertenecen al plan de un grado."""

    consulta = (
        select(Materia)
        .join(
            MateriaGrado,
            Materia.id_materia == MateriaGrado.id_materia_mg,
        )
        .where(MateriaGrado.id_grado_mg == id_grado)
        .order_by(Materia.nombre_materia)
    )

    resultado = await sesion.scalars(consulta)

    return resultado.all()


async def materias_disponibles(
    sesion: AsyncSession,
    id_grado: int,
):
    """Consulta las materias que todavía no están en el plan."""

    materias_asignadas = (
        select(MateriaGrado.id_materia_mg)
        .where(MateriaGrado.id_grado_mg == id_grado)
    )

    consulta = (
        select(Materia)
        .where(Materia.id_materia.not_in(materias_asignadas))
        .order_by(Materia.nombre_materia)
    )

    resultado = await sesion.scalars(consulta)

    return resultado.all()


async def materia_en_plan(
    sesion: AsyncSession,
    id_grado: int,
    id_materia: int,
) -> bool:
    """Verifica si una materia pertenece al plan de un grado."""

    consulta = select(
        exists().where(
            MateriaGrado.id_grado_mg == id_grado,
            MateriaGrado.id_materia_mg == id_materia,
        )
    )

    return bool(await sesion.scalar(consulta))


# VALIDACIONES DE RELACIONES

async def materia_tiene_plan(
    sesion: AsyncSession,
    id_materia: int,
) -> bool:
    """Comprueba si la materia pertenece a algún plan de estudios."""

    consulta = select(
        exists().where(
            MateriaGrado.id_materia_mg == id_materia
        )
    )

    return bool(await sesion.scalar(consulta))


async def materia_tiene_asignaciones(
    sesion: AsyncSession,
    id_materia: int,
) -> bool:
    """Comprueba si existen asignaciones de profesores para la materia."""

    consulta = text("""
        SELECT EXISTS (
            SELECT 1
            FROM asignacion_profesor_clase
            WHERE id_materia_asignacion = :id_materia
        )
    """)

    resultado = await sesion.scalar(
        consulta,
        {"id_materia": id_materia},
    )

    return bool(resultado)


async def tiene_asignacion_en_gestion_abierta(
    sesion: AsyncSession,
    id_grado: int,
    id_materia: int,
) -> bool:
    """Verifica asignaciones de la materia en el grado durante una gestión abierta."""

    consulta = text("""
        SELECT EXISTS (
            SELECT 1
            FROM asignacion_profesor_clase a
            JOIN curso c
                ON c.id_curso = a.id_curso_asignacion
            JOIN gestion g
                ON g.id_gestion = a.id_gestion_asignacion
            WHERE c.id_grado_curso = :id_grado
              AND a.id_materia_asignacion = :id_materia
              AND g.estado_gestion = 'abierta'
        )
    """)

    resultado = await sesion.scalar(
        consulta,
        {
            "id_grado": id_grado,
            "id_materia": id_materia,
        },
    )

    return bool(resultado)

# ============================================================
# CU14 - REPOSITORIO DE ASIGNACIONES DE PROFESORES
# ============================================================


# ------------------------------------------------------------
# 1. LISTAR CURSOS
# ------------------------------------------------------------

async def listar_cursos_cu14(sesion: AsyncSession):
    """Obtiene los cursos con sus nombres completos."""

    consulta = text("""
        SELECT
            id_curso,
            nombre_curso,
            id_grado,
            nombre_grado,
            paralelo
        FROM v_curso
        ORDER BY id_nivel, orden_grado, paralelo
    """)

    resultado = await sesion.execute(consulta)

    return [
        dict(fila)
        for fila in resultado.mappings().all()
    ]


# ------------------------------------------------------------
# 2. LISTAR PROFESORES ACTIVOS
# ------------------------------------------------------------

async def listar_profesores_activos_cu14(sesion: AsyncSession):
    """Obtiene únicamente profesores cuya persona está activa."""

    consulta = text("""
        SELECT
            p.ci_profesor,
            CONCAT_WS(
                ' ',
                pe.nombre_persona,
                pe.apellidos
            ) AS nombre_profesor
        FROM profesor p
        JOIN persona pe
            ON pe.ci = p.ci_profesor
        WHERE pe.estado_persona = 'activo'
        ORDER BY pe.apellidos, pe.nombre_persona
    """)

    resultado = await sesion.execute(consulta)

    return [
        dict(fila)
        for fila in resultado.mappings().all()
    ]


# ------------------------------------------------------------
# 3. LISTAR AULAS DISPONIBLES
# ------------------------------------------------------------

async def listar_aulas_disponibles_cu14(sesion: AsyncSession):
    """Obtiene las aulas que pueden utilizarse en asignaciones."""

    consulta = text("""
        SELECT
            id_aula,
            numero,
            capacidad,
            tipo_aula
        FROM aula
        WHERE estado_aula = 'disponible'
        ORDER BY numero
    """)

    resultado = await sesion.execute(consulta)

    return [
        dict(fila)
        for fila in resultado.mappings().all()
    ]


# ------------------------------------------------------------
# 4. OBTENER CURSO
# ------------------------------------------------------------

async def obtener_curso_cu14(
    sesion: AsyncSession,
    id_curso: int,
):
    """Consulta un curso mediante la vista v_curso."""

    consulta = text("""
        SELECT
            id_curso,
            nombre_curso,
            id_grado,
            nombre_grado,
            paralelo
        FROM v_curso
        WHERE id_curso = :id_curso
    """)

    resultado = await sesion.execute(
        consulta,
        {"id_curso": id_curso},
    )

    fila = resultado.mappings().one_or_none()

    return dict(fila) if fila else None


# ------------------------------------------------------------
# 5. CONSULTAR MATERIAS Y ASIGNACIONES DE UN CURSO
# ------------------------------------------------------------

async def listar_materias_curso_cu14(
    sesion: AsyncSession,
    id_curso: int,
    id_gestion: int,
):
    """
    Obtiene las materias del plan del grado del curso.

    Muestra también el profesor y el aula cuando existe
    una asignación para la gestión indicada.
    """

    consulta = text("""
        SELECT
            m.id_materia,
            m.nombre_materia,
            m.carga_horaria,

            a.id_asignacion,

            a.ci_profesor_asignacion AS ci_profesor,

            CASE
                WHEN pe.ci IS NOT NULL
                THEN CONCAT_WS(
                    ' ',
                    pe.nombre_persona,
                    pe.apellidos
                )
                ELSE NULL
            END AS nombre_profesor,

            a.id_aula_asignacion AS id_aula,

            au.numero AS numero_aula

        FROM curso c

        JOIN materia_grado mg
            ON mg.id_grado_mg = c.id_grado_curso

        JOIN materia m
            ON m.id_materia = mg.id_materia_mg

        LEFT JOIN asignacion_profesor_clase a
            ON a.id_curso_asignacion = c.id_curso
            AND a.id_materia_asignacion = m.id_materia
            AND a.id_gestion_asignacion = :id_gestion

        LEFT JOIN persona pe
            ON pe.ci = a.ci_profesor_asignacion

        LEFT JOIN aula au
            ON au.id_aula = a.id_aula_asignacion

        WHERE c.id_curso = :id_curso

        ORDER BY m.nombre_materia
    """)

    resultado = await sesion.execute(
        consulta,
        {
            "id_curso": id_curso,
            "id_gestion": id_gestion,
        },
    )

    return [
        dict(fila)
        for fila in resultado.mappings().all()
    ]

# ============================================================
# CU14 - VALIDACIONES PARA ASIGNACIONES DE PROFESORES
# ============================================================


# ------------------------------------------------------------
# 6. VERIFICAR QUE EL PROFESOR ESTÉ ACTIVO
# ------------------------------------------------------------

async def profesor_activo_cu14(
    sesion: AsyncSession,
    ci_profesor: str,
) -> bool:
    """Comprueba que el profesor existe y está activo."""

    consulta = text("""
        SELECT EXISTS (
            SELECT 1
            FROM profesor p
            JOIN persona pe
                ON pe.ci = p.ci_profesor
            WHERE p.ci_profesor = :ci_profesor
              AND pe.estado_persona = 'activo'
        )
    """)

    resultado = await sesion.scalar(
        consulta,
        {"ci_profesor": ci_profesor},
    )

    return bool(resultado)


# ------------------------------------------------------------
# 7. VERIFICAR QUE EL AULA ESTÉ DISPONIBLE
# ------------------------------------------------------------

async def aula_disponible_cu14(
    sesion: AsyncSession,
    id_aula: int,
) -> bool:
    """Comprueba que el aula existe y está disponible."""

    consulta = text("""
        SELECT EXISTS (
            SELECT 1
            FROM aula
            WHERE id_aula = :id_aula
              AND estado_aula = 'disponible'
        )
    """)

    resultado = await sesion.scalar(
        consulta,
        {"id_aula": id_aula},
    )

    return bool(resultado)


# ------------------------------------------------------------
# 8. VERIFICAR QUE LA MATERIA PERTENEZCA AL GRADO
# ------------------------------------------------------------

async def materia_habilitada_en_curso_cu14(
    sesion: AsyncSession,
    id_curso: int,
    id_materia: int,
) -> bool:
    """
    Comprueba que la materia pertenece al plan
    de estudios del grado del curso.
    """

    consulta = text("""
        SELECT EXISTS (
            SELECT 1
            FROM curso c
            JOIN materia_grado mg
                ON mg.id_grado_mg = c.id_grado_curso
            WHERE c.id_curso = :id_curso
              AND mg.id_materia_mg = :id_materia
        )
    """)

    resultado = await sesion.scalar(
        consulta,
        {
            "id_curso": id_curso,
            "id_materia": id_materia,
        },
    )

    return bool(resultado)


# ------------------------------------------------------------
# 9. COMPROBAR ASIGNACIONES DUPLICADAS
# ------------------------------------------------------------

async def buscar_asignacion_duplicada_cu14(
    sesion: AsyncSession,
    id_curso: int,
    id_materia: int,
    id_gestion: int,
) -> int | None:
    """
    Busca una asignación existente para la misma
    materia, curso y gestión.

    Devuelve el ID si existe o None si no existe.
    """

    consulta = text("""
        SELECT id_asignacion
        FROM asignacion_profesor_clase
        WHERE id_curso_asignacion = :id_curso
          AND id_materia_asignacion = :id_materia
          AND id_gestion_asignacion = :id_gestion
        LIMIT 1
    """)

    resultado = await sesion.scalar(
        consulta,
        {
            "id_curso": id_curso,
            "id_materia": id_materia,
            "id_gestion": id_gestion,
        },
    )

    return resultado

# ============================================================
# CU14 - RESTRICCIONES DE ELIMINACION DE ASIGNACIONES
# ============================================================


# ------------------------------------------------------------
# 10. VERIFICAR ASISTENCIAS REGISTRADAS
# ------------------------------------------------------------

async def asignacion_con_asistencias_cu14(
    sesion: AsyncSession,
    id_asignacion: int,
) -> bool:
    """
    Comprueba si una asignacion tiene asistencias
    registradas.

    Si existen, no se debe permitir eliminarla.
    """

    consulta = text("""
        SELECT EXISTS (
            SELECT 1
            FROM asistencia
            WHERE id_asignacion_asistencia = :id_asignacion
        )
    """)

    resultado = await sesion.scalar(
        consulta,
        {"id_asignacion": id_asignacion},
    )

    return bool(resultado)


# ------------------------------------------------------------
# 11. VERIFICAR CALIFICACIONES REGISTRADAS
# ------------------------------------------------------------

async def asignacion_con_calificaciones_cu14(
    sesion: AsyncSession,
    id_asignacion: int,
) -> bool:
    """
    Comprueba si existen calificaciones correspondientes
    a la materia, curso y gestion de una asignacion.

    Relaciona:
    - asignacion_profesor_clase
    - periodo
    - calificacion
    - inscripcion

    Si existen calificaciones, no se permite eliminar
    la asignacion.
    """

    consulta = text("""
        SELECT EXISTS (
            SELECT 1

            FROM asignacion_profesor_clase a

            JOIN periodo p
                ON p.id_gestion_periodo =
                   a.id_gestion_asignacion

            JOIN calificacion c
                ON c.id_periodo_calificacion =
                   p.id_periodo
                AND c.id_materia_calificacion =
                    a.id_materia_asignacion

            JOIN inscripcion i
                ON i.ci_estudiante_inscripcion =
                   c.ci_estudiante_calificacion

                AND i.id_curso_inscripcion =
                    a.id_curso_asignacion

                AND i.id_gestion_inscripcion =
                    a.id_gestion_asignacion

            WHERE a.id_asignacion = :id_asignacion
        )
    """)

    resultado = await sesion.scalar(
        consulta,
        {"id_asignacion": id_asignacion},
    )

    return bool(resultado)

# ============================================================
# CU16 - INSCRIBIR ESTUDIANTE EN GESTIÓN ACADÉMICA
# ============================================================

# Inscripción del estudiante en la gestión abierta (cualquier estado: solo hay una por gestión)
_INSCRIPCION_GESTION_CU16 = """
    SELECT i.ci_estudiante_inscripcion AS ci, i.id_inscripcion, i.estado_inscripcion, vc.nombre_curso AS curso
      FROM inscripcion i
      JOIN gestion g  ON g.id_gestion = i.id_gestion_inscripcion AND g.estado_gestion = 'abierta'
      JOIN v_curso vc ON vc.id_curso = i.id_curso_inscripcion
"""


async def buscar_estudiantes_cu16(sesion: AsyncSession, *, q: str | None, pagina: int, tamano: int):
    filtros, params = ["TRUE"], {}
    if q:
        filtros.append("(lower(p.nombre_persona || ' ' || p.apellidos) LIKE :q OR p.ci LIKE :q "
                       "OR lower(coalesce(e.rude, '')) LIKE :q)")
        params["q"] = f"%{q.strip().lower()}%"
    base = f"""
        FROM estudiante e
        JOIN persona p ON p.ci = e.ci_estudiante
        LEFT JOIN ({_INSCRIPCION_GESTION_CU16}) ig ON ig.ci = e.ci_estudiante
        WHERE {' AND '.join(filtros)}"""
    total = await sesion.scalar(text(f"SELECT count(*) {base}"), params)
    filas = (
        await sesion.execute(
            text(f"""SELECT p.ci, p.expedido, p.nombre_persona, p.apellidos, e.rude, p.estado_persona,
                            ig.id_inscripcion, ig.estado_inscripcion, ig.curso
                     {base}
                     ORDER BY p.apellidos, p.nombre_persona
                     LIMIT :limite OFFSET :desde"""),
            {**params, "limite": tamano, "desde": (pagina - 1) * tamano},
        )
    ).all()
    return filas, total or 0


async def datos_boleta_cu16(sesion: AsyncSession, id_inscripcion: int):
    return (
        await sesion.execute(
            text("""SELECT i.id_inscripcion, i.fecha_inscripcion, i.estado_inscripcion,
                           p.ci, p.expedido, p.nombre_persona, p.apellidos, p.fecha_nacimiento, e.rude,
                           g.id_gestion, g.anio AS gestion, vc.id_curso, vc.nombre_curso AS curso,
                           vc.nombre_grado AS grado, vc.paralelo, vc.nombre_nivel AS nivel
                      FROM inscripcion i
                      JOIN persona p    ON p.ci = i.ci_estudiante_inscripcion
                      JOIN estudiante e ON e.ci_estudiante = i.ci_estudiante_inscripcion
                      JOIN gestion g    ON g.id_gestion = i.id_gestion_inscripcion
                      JOIN v_curso vc   ON vc.id_curso = i.id_curso_inscripcion
                     WHERE i.id_inscripcion = :id"""),
            {"id": id_inscripcion},
        )
    ).one_or_none()


async def materias_boleta_cu16(sesion: AsyncSession, id_curso: int, id_gestion: int):
    """Materias del plan del grado del curso, con su docente y aula si ya están asignados."""
    return (
        await sesion.execute(
            text("""SELECT m.nombre_materia AS materia, m.carga_horaria,
                           pp.nombre_persona || ' ' || pp.apellidos AS docente, au.numero AS aula
                      FROM curso c
                      JOIN materia_grado mg ON mg.id_grado_mg = c.id_grado_curso
                      JOIN materia m        ON m.id_materia = mg.id_materia_mg
                      LEFT JOIN asignacion_profesor_clase a
                             ON a.id_curso_asignacion = c.id_curso AND a.id_materia_asignacion = m.id_materia
                            AND a.id_gestion_asignacion = :g
                      LEFT JOIN persona pp ON pp.ci = a.ci_profesor_asignacion
                      LEFT JOIN aula au    ON au.id_aula = a.id_aula_asignacion
                     WHERE c.id_curso = :c
                     ORDER BY m.nombre_materia"""),
            {"c": id_curso, "g": id_gestion},
        )
    ).all()


async def horario_boleta_cu16(sesion: AsyncSession, id_curso: int, id_gestion: int):
    return (
        await sesion.execute(
            text("""SELECT dia, hora_inicio, hora_final, nombre_materia AS materia, profesor AS docente, aula
                      FROM v_horario
                     WHERE id_curso = :c AND id_gestion = :g
                     ORDER BY dia_orden, hora_inicio"""),
            {"c": id_curso, "g": id_gestion},
        )
    ).all()

# ============================================================
# CU12 - GESTIONAR NIVELES EDUCATIVOS Y CURSOS
# ============================================================

from app.paquetes.academico.models import Curso


async def grados_estructura_cu12(sesion: AsyncSession):
    """Grados con la cantidad de materias de su plan de estudios."""
    return (
        await sesion.execute(
            text("""SELECT g.id_grado, g.nombre_grado, g.orden_grado, g.id_nivel_educativo_grado AS id_nivel,
                           (SELECT count(*) FROM materia_grado mg WHERE mg.id_grado_mg = g.id_grado) AS materias
                      FROM grado g
                     ORDER BY g.id_nivel_educativo_grado, g.orden_grado""")
        )
    ).all()


async def cursos_estructura_cu12(sesion: AsyncSession, id_gestion: int | None):
    """Paralelos con sus inscripciones activas en la gestión indicada (0 si no hay gestión abierta)."""
    return (
        await sesion.execute(
            text("""SELECT c.id_curso, c.paralelo, c.cupo_maximo, c.id_grado_curso AS id_grado,
                           (SELECT count(*) FROM inscripcion i
                             WHERE i.id_curso_inscripcion = c.id_curso
                               AND i.id_gestion_inscripcion = :g
                               AND i.estado_inscripcion = 'activa') AS inscritos
                      FROM curso c
                     ORDER BY c.id_grado_curso, c.paralelo"""),
            {"g": id_gestion},
        )
    ).all()


async def buscar_nivel_cu12(sesion: AsyncSession, nombre: str, id_excluir: int | None = None):
    consulta = select(NivelEducativo).where(func.lower(NivelEducativo.nombre_nivel) == nombre.lower())
    if id_excluir is not None:
        consulta = consulta.where(NivelEducativo.id_nivel != id_excluir)
    return await sesion.scalar(consulta)


async def buscar_grado_cu12(sesion: AsyncSession, id_nivel: int, *, nombre: str | None = None,
                            orden: int | None = None, id_excluir: int | None = None):
    """Grado del mismo nivel con ese nombre (sin distinguir mayúsculas) o con ese orden."""
    consulta = select(Grado).where(Grado.id_nivel_educativo_grado == id_nivel)
    if nombre is not None:
        consulta = consulta.where(func.lower(Grado.nombre_grado) == nombre.lower())
    if orden is not None:
        consulta = consulta.where(Grado.orden_grado == orden)
    if id_excluir is not None:
        consulta = consulta.where(Grado.id_grado != id_excluir)
    return await sesion.scalar(consulta.limit(1))


async def buscar_curso_cu12(sesion: AsyncSession, id_grado: int, paralelo: str, id_excluir: int | None = None):
    consulta = select(Curso).where(Curso.id_grado_curso == id_grado, Curso.paralelo == paralelo)
    if id_excluir is not None:
        consulta = consulta.where(Curso.id_curso != id_excluir)
    return await sesion.scalar(consulta)


async def inscritos_activos_cu12(sesion: AsyncSession, id_curso: int, id_gestion: int) -> int:
    return await sesion.scalar(
        text("""SELECT count(*) FROM inscripcion
                 WHERE id_curso_inscripcion = :c AND id_gestion_inscripcion = :g
                   AND estado_inscripcion = 'activa'"""),
        {"c": id_curso, "g": id_gestion},
    ) or 0


async def uso_nivel_cu12(sesion: AsyncSession, id_nivel: int):
    """Registros que dependen del nivel: grados y aranceles."""
    return (
        await sesion.execute(
            text("""SELECT (SELECT count(*) FROM grado   WHERE id_nivel_educativo_grado = :n) AS grados,
                           (SELECT count(*) FROM arancel WHERE id_nivel_arancel = :n)         AS aranceles"""),
            {"n": id_nivel},
        )
    ).one()


async def uso_grado_cu12(sesion: AsyncSession, id_grado: int):
    """Registros que dependen del grado: paralelos y materias del plan de estudios."""
    return (
        await sesion.execute(
            text("""SELECT (SELECT count(*) FROM curso         WHERE id_grado_curso = :g) AS cursos,
                           (SELECT count(*) FROM materia_grado WHERE id_grado_mg = :g)    AS materias"""),
            {"g": id_grado},
        )
    ).one()


async def uso_curso_cu12(sesion: AsyncSession, id_curso: int):
    """Registros que dependen del paralelo: inscripciones, asignaciones de profesores y comunicados."""
    return (
        await sesion.execute(
            text("""SELECT (SELECT count(*) FROM inscripcion               WHERE id_curso_inscripcion = :c) AS inscripciones,
                           (SELECT count(*) FROM asignacion_profesor_clase WHERE id_curso_asignacion = :c)  AS asignaciones,
                           (SELECT count(*) FROM comunicado                WHERE id_curso_comunicado = :c)  AS comunicados"""),
            {"c": id_curso},
        )
    ).one()


# ============================================================
# CU15 - GESTIÓN ACADÉMICA, PERIODOS Y DIMENSIONES
# ============================================================

_SQL_GESTION = """SELECT g.id_gestion, g.anio, g.fecha_inicio_g, g.fecha_final_g, g.nota_minima_aprobacion, g.estado_gestion,
                         (SELECT count(*) FROM periodo p WHERE p.id_gestion_periodo = g.id_gestion) AS periodos,
                         (SELECT count(*) FROM inscripcion i WHERE i.id_gestion_inscripcion = g.id_gestion) AS inscritos
                    FROM gestion g"""


async def listar_gestiones_cu15(sesion: AsyncSession):
    return (await sesion.execute(text(_SQL_GESTION + " ORDER BY g.anio DESC"))).all()


async def obtener_gestion_cu15(sesion: AsyncSession, id_gestion: int):
    return (await sesion.execute(text(_SQL_GESTION + " WHERE g.id_gestion = :g"), {"g": id_gestion})).one_or_none()


async def gestion_abierta_cu15(sesion: AsyncSession):
    return (await sesion.execute(text("SELECT id_gestion, anio FROM gestion WHERE estado_gestion = 'abierta' LIMIT 1"))).one_or_none()


async def crear_gestion_cu15(sesion: AsyncSession, datos: dict) -> int:
    return await sesion.scalar(
        text("""INSERT INTO gestion (anio, fecha_inicio_g, fecha_final_g, nota_minima_aprobacion)
                VALUES (:anio, :fecha_inicio_g, :fecha_final_g, :nota_minima_aprobacion) RETURNING id_gestion"""),
        datos,
    )


async def actualizar_gestion_cu15(sesion: AsyncSession, id_gestion: int, datos: dict) -> None:
    await sesion.execute(
        text("""UPDATE gestion SET anio = :anio, fecha_inicio_g = :fecha_inicio_g, fecha_final_g = :fecha_final_g,
                       nota_minima_aprobacion = :nota_minima_aprobacion
                 WHERE id_gestion = :id"""),
        {**datos, "id": id_gestion},
    )


async def listar_periodos_cu15(sesion: AsyncSession, id_gestion: int):
    return (
        await sesion.execute(
            text("SELECT * FROM periodo WHERE id_gestion_periodo = :g ORDER BY fecha_inicio_p"), {"g": id_gestion}
        )
    ).all()


async def obtener_periodo_cu15(sesion: AsyncSession, id_periodo: int):
    return (await sesion.execute(text("SELECT * FROM periodo WHERE id_periodo = :p"), {"p": id_periodo})).one_or_none()


async def periodo_solapado_cu15(sesion: AsyncSession, id_gestion: int, inicio, fin, excepto: int | None = None):
    """Nombre de un periodo de la gestión que se solapa con [inicio, fin], o None."""
    return await sesion.scalar(
        text("""SELECT nombre_periodo FROM periodo
                 WHERE id_gestion_periodo = :g AND fecha_inicio_p <= :fin AND fecha_final_p >= :ini
                   AND (CAST(:ex AS INTEGER) IS NULL OR id_periodo <> :ex)
                 LIMIT 1"""),
        {"g": id_gestion, "ini": inicio, "fin": fin, "ex": excepto},
    )


async def crear_periodo_cu15(sesion: AsyncSession, id_gestion: int, datos: dict) -> int:
    return await sesion.scalar(
        text("""INSERT INTO periodo (nombre_periodo, tipo, fecha_inicio_p, fecha_final_p, observaciones_periodo, id_gestion_periodo)
                VALUES (:nombre_periodo, :tipo, :fecha_inicio_p, :fecha_final_p, :observaciones_periodo, :g)
                RETURNING id_periodo"""),
        {**datos, "g": id_gestion},
    )


async def actualizar_periodo_cu15(sesion: AsyncSession, id_periodo: int, datos: dict) -> None:
    await sesion.execute(
        text("""UPDATE periodo SET nombre_periodo = :nombre_periodo, tipo = :tipo, fecha_inicio_p = :fecha_inicio_p,
                       fecha_final_p = :fecha_final_p, observaciones_periodo = :observaciones_periodo
                 WHERE id_periodo = :id"""),
        {**datos, "id": id_periodo},
    )


async def eliminar_periodo_cu15(sesion: AsyncSession, id_periodo: int) -> None:
    await sesion.execute(text("DELETE FROM periodo WHERE id_periodo = :p"), {"p": id_periodo})


async def calificaciones_en_periodo_cu15(sesion: AsyncSession, id_periodo: int) -> int:
    return await sesion.scalar(
        text("SELECT count(*) FROM calificacion WHERE id_periodo_calificacion = :p"), {"p": id_periodo}
    ) or 0


async def calificaciones_en_gestion_cu15(sesion: AsyncSession, id_gestion: int) -> int:
    """Calificaciones registradas en cualquier periodo de la gestión."""
    return await sesion.scalar(
        text("""SELECT count(*) FROM calificacion c
                  JOIN periodo p ON p.id_periodo = c.id_periodo_calificacion
                 WHERE p.id_gestion_periodo = :g"""),
        {"g": id_gestion},
    ) or 0


async def listar_dimensiones_cu15(sesion: AsyncSession, id_gestion: int):
    return (
        await sesion.execute(
            text("""SELECT id_dimension, nombre_dimension, puntaje_maximo, es_autoevaluacion, orden_dimension
                      FROM dimension_evaluacion WHERE id_gestion_dimension = :g ORDER BY orden_dimension, id_dimension"""),
            {"g": id_gestion},
        )
    ).all()


async def notas_en_gestion_cu15(sesion: AsyncSession, id_gestion: int) -> int:
    """Detalles de calificación que usan alguna dimensión de la gestión."""
    return await sesion.scalar(
        text("""SELECT count(*) FROM calificacion_detalle cd
                  JOIN dimension_evaluacion d ON d.id_dimension = cd.id_dimension_detalle
                 WHERE d.id_gestion_dimension = :g"""),
        {"g": id_gestion},
    ) or 0


async def reemplazar_dimensiones_cu15(sesion: AsyncSession, id_gestion: int, dimensiones: list[dict]) -> None:
    await sesion.execute(text("DELETE FROM dimension_evaluacion WHERE id_gestion_dimension = :g"), {"g": id_gestion})
    for orden, d in enumerate(dimensiones, start=1):
        await sesion.execute(
            text("""INSERT INTO dimension_evaluacion
                        (nombre_dimension, puntaje_maximo, es_autoevaluacion, orden_dimension, id_gestion_dimension)
                    VALUES (:nombre_dimension, :puntaje_maximo, :es_autoevaluacion, :orden, :g)"""),
            {**d, "orden": orden, "g": id_gestion},
        )


async def resumen_gestion_cu15(sesion: AsyncSession, id_gestion: int):
    return (
        await sesion.execute(
            text("""SELECT
                      (SELECT count(*) FROM inscripcion WHERE id_gestion_inscripcion = :g AND estado_inscripcion = 'activa')     AS inscritos_activos,
                      (SELECT count(*) FROM inscripcion WHERE id_gestion_inscripcion = :g AND estado_inscripcion = 'retirada')   AS retirados,
                      (SELECT count(*) FROM inscripcion WHERE id_gestion_inscripcion = :g AND estado_inscripcion = 'finalizada') AS finalizados,
                      (SELECT round(avg(nota_final), 2) FROM v_nota_final WHERE id_gestion = :g)                                 AS promedio_general,
                      (SELECT coalesce(sum(monto), 0) FROM pago_mensualidad
                        WHERE id_gestion_pago = :g AND estado_pago = 'pagado')                                                   AS total_cobrado,
                      (SELECT coalesce(sum(monto), 0) FROM pago_mensualidad
                        WHERE id_gestion_pago = :g AND estado_pago = 'pendiente' AND fecha_vencimiento < CURRENT_DATE)           AS total_vencido"""),
            {"g": id_gestion},
        )
    ).one()


async def cerrar_gestion_cu15(sesion: AsyncSession, id_gestion: int) -> dict:
    """Ejecuta sp_cerrar_gestion y devuelve {'promovidos': n, 'reprobados': m}."""
    fila = (await sesion.execute(text("CALL sp_cerrar_gestion(:g, NULL)"), {"g": id_gestion})).one()
    valor = fila[0]
    return json.loads(valor) if isinstance(valor, str) else dict(valor)

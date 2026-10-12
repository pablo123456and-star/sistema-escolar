"""
Acceso a la base de datos del paquete academico (compartido).

Consultas y escrituras con SQLAlchemy sobre las tablas de models.py.
Los procedimientos almacenados se ejecutan con CALL (ver basededato/sql/04).

PENDIENTE.
"""
# ============================================================
# CU13 - REPOSITORIO DE MATERIAS Y PLAN DE ESTUDIOS
# ============================================================

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
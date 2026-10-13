"""
Acceso a la base de datos del paquete personas (compartido).

Consultas y escrituras con SQLAlchemy sobre las tablas de models.py.
"""
from sqlalchemy import and_, exists, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.paquetes.personas.models import Administrativo, Estudiante, Persona, Profesor, Tutor, TutorEstudiante
from app.paquetes.seguridad.models import Usuario

# Inscripción de la gestión abierta más reciente (con el nombre del curso)
_INSCRIPCION_ACTUAL = """
    SELECT DISTINCT ON (i.ci_estudiante_inscripcion)
           i.ci_estudiante_inscripcion AS ci, i.id_inscripcion, i.estado_inscripcion, i.fecha_inscripcion,
           g.anio AS gestion, vc.id_curso, vc.nombre_curso AS curso, vc.nombre_grado AS grado,
           vc.id_grado, vc.paralelo, vc.nombre_nivel AS nivel
      FROM inscripcion i
      JOIN gestion g  ON g.id_gestion = i.id_gestion_inscripcion AND g.estado_gestion = 'abierta'
      JOIN v_curso vc ON vc.id_curso = i.id_curso_inscripcion
     ORDER BY i.ci_estudiante_inscripcion, g.anio DESC
"""


def _like(q: str) -> str:
    return f"%{q.strip().lower()}%"


async def buscar_persona(sesion: AsyncSession, ci: str):
    consulta = select(
        Persona,
        exists().where(Estudiante.ci_estudiante == Persona.ci).label("es_estudiante"),
        exists().where(Tutor.ci_tutor == Persona.ci).label("es_tutor"),
        exists().where(Profesor.ci_profesor == Persona.ci).label("es_profesor"),
        exists().where(Administrativo.ci_administrativo == Persona.ci).label("es_administrativo"),
    ).where(Persona.ci == ci)
    return (await sesion.execute(consulta)).one_or_none()


async def tiene_usuario(sesion: AsyncSession, ci: str) -> bool:
    return bool(await sesion.scalar(select(exists().where(Usuario.ci_persona == ci))))


# ---- Estudiantes ----------------------------------------------------------------
async def listar_estudiantes(sesion: AsyncSession, *, q: str | None, id_grado: int | None, paralelo: str | None,
                             estado: str | None, pagina: int, tamano: int):
    filtros, params = ["TRUE"], {}
    if q:
        filtros.append("(lower(p.nombre_persona || ' ' || p.apellidos) LIKE :q OR p.ci LIKE :q "
                       "OR lower(coalesce(e.rude, '')) LIKE :q)")
        params["q"] = _like(q)
    if id_grado:
        filtros.append("ia.id_grado = :id_grado")
        params["id_grado"] = id_grado
    if paralelo:
        filtros.append("ia.paralelo = :paralelo")
        params["paralelo"] = paralelo
    if estado:
        filtros.append("p.estado_persona = :estado")
        params["estado"] = estado
    base = f"""
        FROM estudiante e
        JOIN persona p ON p.ci = e.ci_estudiante
        LEFT JOIN ({_INSCRIPCION_ACTUAL}) ia ON ia.ci = e.ci_estudiante AND ia.estado_inscripcion = 'activa'
        LEFT JOIN tutor_estudiante te ON te.ci_estudiante_tutorestudiante = e.ci_estudiante AND te.es_principal
        LEFT JOIN persona pt ON pt.ci = te.ci_tutor_tutorestudiante
        WHERE {' AND '.join(filtros)}"""
    total = await sesion.scalar(text(f"SELECT count(*) {base}"), params)
    filas = (
        await sesion.execute(
            text(f"""SELECT p.ci, p.expedido, p.nombre_persona, p.apellidos, p.sexo, p.fecha_nacimiento,
                            e.rude, p.estado_persona, ia.id_curso, ia.curso, ia.grado, ia.paralelo, ia.nivel,
                            pt.nombre_persona || ' ' || pt.apellidos AS tutor_principal
                     {base}
                     ORDER BY p.apellidos, p.nombre_persona
                     LIMIT :limite OFFSET :desde"""),
            {**params, "limite": tamano, "desde": (pagina - 1) * tamano},
        )
    ).all()
    return filas, total or 0


async def inscripcion_actual(sesion: AsyncSession, ci: str):
    return (
        await sesion.execute(text(f"SELECT * FROM ({_INSCRIPCION_ACTUAL}) ia WHERE ia.ci = :ci"), {"ci": ci})
    ).one_or_none()


async def opciones_cursos(sesion: AsyncSession):
    return (
        await sesion.execute(
            text(
                """SELECT vc.id_curso, vc.nombre_curso, vc.id_grado, vc.nombre_grado, vc.paralelo,
                          vc.nombre_nivel AS nivel, vc.cupo_maximo,
                          count(i.id_inscripcion) FILTER (WHERE i.estado_inscripcion = 'activa') AS inscritos
                     FROM v_curso vc
                     LEFT JOIN gestion g     ON g.estado_gestion = 'abierta'
                     LEFT JOIN inscripcion i ON i.id_curso_inscripcion = vc.id_curso
                                            AND i.id_gestion_inscripcion = g.id_gestion
                    GROUP BY vc.id_curso, vc.nombre_curso, vc.id_grado, vc.nombre_grado, vc.paralelo,
                             vc.nombre_nivel, vc.cupo_maximo, vc.id_nivel, vc.orden_grado
                    ORDER BY vc.id_nivel, vc.orden_grado, vc.paralelo"""
            )
        )
    ).all()


# ---- Vínculos tutor–estudiante --------------------------------------------------
async def vinculos(sesion: AsyncSession, *, ci_tutor: str | None = None, ci_estudiante: str | None = None):
    pt, pe = Persona.__table__.alias("pt"), Persona.__table__.alias("pe")
    consulta = (
        select(
            TutorEstudiante.ci_tutor_tutorestudiante.label("ci_tutor"),
            TutorEstudiante.ci_estudiante_tutorestudiante.label("ci_estudiante"),
            (pt.c.nombre_persona + " " + pt.c.apellidos).label("nombre_tutor"),
            (pe.c.nombre_persona + " " + pe.c.apellidos).label("nombre_estudiante"),
            pt.c.telefono.label("telefono_tutor"),
            TutorEstudiante.parentesco, TutorEstudiante.es_principal, TutorEstudiante.es_responsable_pago,
            TutorEstudiante.autorizado_recoger, pe.c.estado_persona.label("estado_estudiante"),
        )
        .join(pt, pt.c.ci == TutorEstudiante.ci_tutor_tutorestudiante)
        .join(pe, pe.c.ci == TutorEstudiante.ci_estudiante_tutorestudiante)
    )
    if ci_tutor:
        consulta = consulta.where(TutorEstudiante.ci_tutor_tutorestudiante == ci_tutor)
    if ci_estudiante:
        consulta = consulta.where(TutorEstudiante.ci_estudiante_tutorestudiante == ci_estudiante)
    filas = (await sesion.execute(
        consulta.order_by(TutorEstudiante.es_principal.desc(), pe.c.apellidos, pt.c.apellidos))).all()
    # curso actual de cada estudiante
    cis = list({f.ci_estudiante for f in filas})
    cursos = {}
    if cis:
        cursos = {
            r.ci: r.curso
            for r in (await sesion.execute(
                text(f"SELECT ia.ci, ia.curso FROM ({_INSCRIPCION_ACTUAL}) ia WHERE ia.ci = ANY(:cis)"), {"cis": cis}
            )).all()
        }
    return [{**f._asdict(), "curso_estudiante": cursos.get(f.ci_estudiante)} for f in filas]


async def pagos_del_vinculo(sesion: AsyncSession, ci_tutor: str, ci_estudiante: str) -> int:
    return await sesion.scalar(
        text("SELECT count(*) FROM pago_mensualidad WHERE ci_tutor_pago = :t AND ci_estudiante_pago = :e"),
        {"t": ci_tutor, "e": ci_estudiante},
    ) or 0


# ---- Tutores ---------------------------------------------------------------------
async def listar_tutores(sesion: AsyncSession, *, q: str | None, estado: str | None, pagina: int, tamano: int):
    cantidad = (
        select(func.count())
        .where(TutorEstudiante.ci_tutor_tutorestudiante == Tutor.ci_tutor)
        .correlate(Tutor)
        .scalar_subquery()
    )
    filtros = []
    if q:
        patron = _like(q)
        filtros.append(or_(func.lower(Persona.nombre_persona + " " + Persona.apellidos).like(patron),
                           Persona.ci.like(patron)))
    if estado:
        filtros.append(Persona.estado_persona == estado)
    base = (
        select(
            Persona.ci, Persona.expedido, Persona.nombre_persona, Persona.apellidos, Persona.telefono,
            Persona.email, Tutor.ocupacion, Persona.estado_persona, cantidad.label("cantidad_estudiantes"),
        )
        .join(Persona, Persona.ci == Tutor.ci_tutor)
        .where(and_(*filtros))
    )
    total = await sesion.scalar(select(func.count()).select_from(base.subquery()))
    filas = (await sesion.execute(
        base.order_by(Persona.apellidos, Persona.nombre_persona).offset((pagina - 1) * tamano).limit(tamano))).all()
    return filas, total or 0


# ---- Docentes ---------------------------------------------------------------------
async def listar_docentes(sesion: AsyncSession, *, q: str | None, estado: str | None, pagina: int, tamano: int):
    filtros, params = ["TRUE"], {}
    if q:
        filtros.append("(lower(p.nombre_persona || ' ' || p.apellidos) LIKE :q OR p.ci LIKE :q)")
        params["q"] = _like(q)
    if estado:
        filtros.append("p.estado_persona = :estado")
        params["estado"] = estado
    base = f"""
        FROM profesor pr
        JOIN persona p ON p.ci = pr.ci_profesor
        WHERE {' AND '.join(filtros)}"""
    total = await sesion.scalar(text(f"SELECT count(*) {base}"), params)
    filas = (
        await sesion.execute(
            text(f"""SELECT p.ci, p.expedido, p.nombre_persona, p.apellidos, p.sexo, p.telefono, p.email,
                            pr.titulo_academico, pr.anios_experiencia, p.estado_persona,
                            (SELECT count(*)
                               FROM asignacion_profesor_clase a
                               JOIN gestion g ON g.id_gestion = a.id_gestion_asignacion
                                             AND g.estado_gestion = 'abierta'
                              WHERE a.ci_profesor_asignacion = p.ci) AS cantidad_asignaciones
                     {base}
                     ORDER BY p.apellidos, p.nombre_persona
                     LIMIT :limite OFFSET :desde"""),
            {**params, "limite": tamano, "desde": (pagina - 1) * tamano},
        )
    ).all()
    return filas, total or 0


async def asignaciones_docente(sesion: AsyncSession, ci: str, id_gestion: int):
    """Materias que dicta el docente en la gestión indicada (con curso y aula)."""
    return (
        await sesion.execute(
            text(
                """SELECT a.id_asignacion, m.nombre_materia AS materia, vc.nombre_curso AS curso, au.numero AS aula
                     FROM asignacion_profesor_clase a
                     JOIN materia m  ON m.id_materia = a.id_materia_asignacion
                     JOIN v_curso vc ON vc.id_curso = a.id_curso_asignacion
                     JOIN aula au    ON au.id_aula = a.id_aula_asignacion
                    WHERE a.ci_profesor_asignacion = :ci AND a.id_gestion_asignacion = :g
                    ORDER BY vc.id_nivel, vc.orden_grado, vc.paralelo, m.nombre_materia"""
            ),
            {"ci": ci, "g": id_gestion},
        )
    ).all()

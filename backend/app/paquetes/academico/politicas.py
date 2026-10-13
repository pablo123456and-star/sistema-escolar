"""
Reglas de negocio comunes del paquete academico (compartido).

    - Solo el administrador modifica la estructura académica.
    - Una gestión 'cerrada' ya no admite inscripciones ni cambios.
    - La materia de una asignación debe estar en el plan de estudios (materia_grado) del grado del curso.
    - Un registro en uso no se elimina: la BD lo impide (FK) y el backend muestra un mensaje claro.

Las reglas propias de cada caso de uso están en el encabezado de su archivo en casos_uso/.

Implementado por ahora: la inscripción (reglas del CU16), que el CU06 usa para
inscribir al estudiante en el mismo paso en que se registra.
"""
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.errores import Conflicto, ErrorNegocio, NoEncontrado
from app.paquetes.academico.models import Curso, Gestion, Inscripcion


async def gestion_abierta(sesion: AsyncSession) -> Gestion | None:
    """La gestión abierta más reciente."""
    return await sesion.scalar(
        select(Gestion).where(Gestion.estado_gestion == "abierta").order_by(Gestion.anio.desc()).limit(1)
    )


async def inscribir(sesion: AsyncSession, ci_estudiante: str, id_curso: int) -> Inscripcion:
    """Inscribe en la gestión abierta aplicando las reglas del CU16."""
    gestion = await gestion_abierta(sesion)
    if gestion is None:
        raise ErrorNegocio("No hay una gestión abierta para inscribir.")
    estado = await sesion.scalar(
        text(
            """SELECT p.estado_persona FROM estudiante e JOIN persona p ON p.ci = e.ci_estudiante
                WHERE e.ci_estudiante = :ci"""
        ),
        {"ci": ci_estudiante},
    )
    if estado is None:
        raise NoEncontrado("No existe un estudiante con ese CI.")
    if estado != "activo":
        raise ErrorNegocio("El estudiante está inactivo: reactívelo antes de inscribirlo.")
    curso = await sesion.get(Curso, id_curso)
    if curso is None:
        raise NoEncontrado("Curso no encontrado.")

    ya_inscrito = await sesion.scalar(
        select(func.count()).where(
            Inscripcion.ci_estudiante_inscripcion == ci_estudiante,
            Inscripcion.id_gestion_inscripcion == gestion.id_gestion,
        )
    )
    if ya_inscrito:
        raise Conflicto(f"El estudiante ya está inscrito en la gestión {gestion.anio}.")

    inscritos = await sesion.scalar(
        select(func.count()).where(
            Inscripcion.id_curso_inscripcion == id_curso,
            Inscripcion.id_gestion_inscripcion == gestion.id_gestion,
            Inscripcion.estado_inscripcion == "activa",
        )
    )
    if inscritos >= curso.cupo_maximo:
        raise ErrorNegocio(f"El curso no tiene cupo ({inscritos} de {curso.cupo_maximo}).")

    deuda = await sesion.scalar(
        text(
            """SELECT count(*) FROM pago_mensualidad
                WHERE ci_estudiante_pago = :ci AND id_gestion_pago <> :g
                  AND estado_pago = 'pendiente' AND fecha_vencimiento < CURRENT_DATE"""
        ),
        {"ci": ci_estudiante, "g": gestion.id_gestion},
    )
    if deuda:
        raise ErrorNegocio("El estudiante tiene cuotas vencidas de gestiones anteriores.")

    inscripcion = Inscripcion(
        ci_estudiante_inscripcion=ci_estudiante, id_gestion_inscripcion=gestion.id_gestion, id_curso_inscripcion=id_curso
    )
    sesion.add(inscripcion)
    await sesion.flush()
    return inscripcion

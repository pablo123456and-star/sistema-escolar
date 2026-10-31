"""
CU22 - Consultar historial de asistencia
Paquete: evaluacion

Actores ........: Tutor, Administrativo
Rol del sistema : tutor, administrador, estudiante, profesor
Tablas .........: asistencia, asignacion_profesor_clase, materia, inscripcion, tutor_estudiante
Usa de la BD ...: —

Reglas de negocio que implementa este caso de uso (backend):
    - Administrador: todos. Profesor: los estudiantes de los cursos donde dicta clases.
      Tutor: sus estudiantes. Estudiante: el suyo. Si no, 403.
    - Gestión: la indicada, o la abierta (si no estuvo inscrito, la más reciente en la que estuvo).
    - Filtros opcionales: rango de fechas (desde <= hasta) y materia.
    - Porcentaje por materia = (presente + tardanza) / total de clases registradas, con 1 decimal;
      sin clases registradas se muestra "sin registros" (no se divide entre 0).

Precondición:
    Sesión iniciada. Un tutor solo consulta a sus estudiantes.

Postcondición:
    Se muestra el detalle de asistencia y el porcentaje por materia. No se modifica nada.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from collections import Counter
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import ErrorNegocio
from app.paquetes.evaluacion import politicas
from app.paquetes.evaluacion import repository as repo
from app.paquetes.evaluacion.schemas import (
    ConteoAsistenciaSalida, EstudianteHistorialSalida, EstudiantesHistorialSalida, GestionHistorialSalida,
    HistorialAsistenciaSalida, MateriaHistorialSalida, RegistroHistorialSalida,
)


def _conteo(registros) -> dict:
    """Conteos por estado y porcentaje de asistencia (presente + tardanza) de una lista de registros."""
    estados = Counter(r.estado for r in registros)
    total = len(registros)
    asistio = estados["presente"] + estados["tardanza"]
    return {
        "total": total,
        "presente": estados["presente"],
        "ausente": estados["ausente"],
        "tardanza": estados["tardanza"],
        "justificado": estados["justificado"],
        "porcentaje": round(asistio * 100 / total, 1) if total else None,
    }


async def estudiantes(sesion: AsyncSession, usuario: UsuarioActual) -> EstudiantesHistorialSalida:
    """Estudiantes de la gestión vigente que el usuario puede consultar."""
    gestion = await repo.gestion_vigente_cu22(sesion)
    filas = await repo.estudiantes_cu22(sesion, gestion.id_gestion, usuario.rol, usuario.ci) if gestion else []
    return EstudiantesHistorialSalida(
        gestion=gestion.anio if gestion else None,
        estudiantes=[EstudianteHistorialSalida.model_validate(f._asdict()) for f in filas],
    )


async def historial(sesion: AsyncSession, usuario: UsuarioActual, ci_estudiante: str, id_gestion: int | None,
                    desde: date | None, hasta: date | None, id_materia: int | None) -> HistorialAsistenciaSalida:
    if desde and hasta and desde > hasta:
        raise ErrorNegocio("La fecha 'desde' no puede ser posterior a la fecha 'hasta'.")

    gestiones = await repo.gestiones_cu22(sesion, ci_estudiante)
    if id_gestion is not None:
        gestion = next((g for g in gestiones if g.id_gestion == id_gestion), None)
    else:
        gestion = next((g for g in gestiones if g.estado_gestion == "abierta"), gestiones[0] if gestiones else None)
    inscrito = await politicas.estudiante_visible(sesion, usuario, ci_estudiante, gestion.id_gestion if gestion else None)

    registros = await repo.historial_cu22(sesion, ci_estudiante, gestion.id_gestion, desde, hasta, id_materia)
    materias = {m.id_materia: m.materia for m in await repo.materias_cu22(sesion, ci_estudiante, gestion.id_gestion)}
    materias.update({r.id_materia: r.materia for r in registros})   # por si cambió de curso en la gestión
    if id_materia:
        materias = {k: v for k, v in materias.items() if k == id_materia}

    return HistorialAsistenciaSalida(
        estudiante=EstudianteHistorialSalida.model_validate(inscrito._asdict()),
        id_gestion=gestion.id_gestion,
        gestion=gestion.anio,
        gestiones=[GestionHistorialSalida(id_gestion=g.id_gestion, anio=g.anio) for g in gestiones],
        desde=desde,
        hasta=hasta,
        general=ConteoAsistenciaSalida(**_conteo(registros)),
        materias=[
            MateriaHistorialSalida(id_materia=k, materia=v, **_conteo([r for r in registros if r.id_materia == k]))
            for k, v in sorted(materias.items(), key=lambda x: x[1])
        ],
        detalle=[RegistroHistorialSalida.model_validate(r._asdict()) for r in registros],
    )

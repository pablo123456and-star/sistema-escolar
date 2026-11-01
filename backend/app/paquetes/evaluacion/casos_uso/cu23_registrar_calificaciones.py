"""
CU23 - Registrar calificaciones y evaluaciones (incluye autoevaluación y cierre de periodo)
Paquete: evaluacion

Actores ........: Docente (Estudiante para su autoevaluación, Administrador para cerrar periodo)
Rol del sistema : profesor, estudiante, administrador
Tablas .........: calificacion, calificacion_detalle, dimension_evaluacion, periodo, inscripcion
Usa de la BD ...: Vista v_nota_final, procedimiento sp_emitir_boletines, triggers de auditoría
                  y fn_registrar_bitacora (cierre y reapertura del periodo)

Reglas de negocio que implementa este caso de uso (backend):
    - Profesor: solo las materias que dicta (asignación del curso en la gestión); el administrador, todas.
    - El estudiante debe estar inscrito (no retirado) en el curso de la clase.
    - El periodo debe ser de la gestión de la clase, haber empezado y estar 'abierto'; si está
      'cerrado', solo el administrador corrige. Con la gestión cerrada nadie modifica notas.
    - La dimensión debe ser de la gestión del periodo y el puntaje entre 0 y su puntaje_maximo.
    - La fecha de la calificación es la de hoy (hora de Bolivia), sin pasar del fin de la gestión.
    - Solo se escribe lo que cambió (la bitácora guarda las correcciones reales). Si una
      calificación queda sin dimensiones se borra, para que no cuente como nota 0 en el boletín.
    - Autoevaluación: solo el propio estudiante, por materia y solo en la dimensión es_autoevaluacion;
      el profesor no la modifica. El estudiante ve sus notas mientras el periodo está abierto.
    - Cerrar periodo (administrador): estado 'cerrado' + CALL sp_emitir_boletines.
    - Reabrir periodo (administrador): vuelve a 'abierto' para corregir; al cerrarlo otra vez se
      reemiten los boletines con las notas corregidas.

Precondición:
    El docente dicta la materia al estudiante. El periodo está abierto. Cada puntaje no supera el máximo de su dimensión.

Postcondición:
    Las notas quedan guardadas por dimensión y la nota final se calcula sola. Al cerrar el periodo se emiten los boletines.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import Conflicto, ErrorNegocio, NoEncontrado, SinPermiso
from app.paquetes.academico.politicas import gestion_abierta
from app.paquetes.evaluacion import politicas
from app.paquetes.evaluacion import repository as repo
from app.paquetes.evaluacion.schemas import (
    AutoevaluacionGuardar,
    CambioPeriodoSalida,
    ClaseCalificacionSalida,
    ClasesCalificacionSalida,
    DimensionSalida,
    MateriaNotasSalida,
    MisCalificacionesSalida,
    NotaEstudianteSalida,
    PeriodoCalificacionSalida,
    PlanillaGuardar,
    PlanillaSalida,
)


def _a_modelo(fila, modelo):
    return modelo.model_validate(fila._asdict())


def _puntajes(valor) -> dict[int, float]:
    """json_object_agg devuelve las claves como texto: se pasan a id_dimension (int)."""
    return {int(k): float(v) for k, v in (valor or {}).items()}


async def _periodos(sesion: AsyncSession, id_gestion: int) -> list[PeriodoCalificacionSalida]:
    return [_a_modelo(f, PeriodoCalificacionSalida) for f in await repo.periodos_cu23(sesion, id_gestion)]


async def _dimensiones(sesion: AsyncSession, id_gestion: int):
    return await repo.dimensiones_cu23(sesion, id_gestion)


def _nombre(fila) -> str:
    return f"{fila.apellidos} {fila.nombre_persona}"


async def _fecha_registro(sesion: AsyncSession, periodo):
    """Hoy (hora de Bolivia), sin pasar del último día de la gestión."""
    return min(await repo.hoy(sesion), periodo.fecha_final_g)


# ------------------------------------------------------------
# Docente / administrador: planilla de notas
# ------------------------------------------------------------

async def clases(sesion: AsyncSession, usuario: UsuarioActual) -> ClasesCalificacionSalida:
    """Clases de la gestión abierta (profesor: las suyas), sus trimestres y las dimensiones."""
    gestion = await gestion_abierta(sesion)
    if gestion is None:
        return ClasesCalificacionSalida(gestion=None, nota_minima=None, periodos=[], dimensiones=[], clases=[])
    filas = await repo.clases_cu23(sesion, gestion.id_gestion, None if usuario.rol == "administrador" else usuario.ci)
    return ClasesCalificacionSalida(
        gestion=gestion.anio,
        nota_minima=float(gestion.nota_minima_aprobacion),
        periodos=await _periodos(sesion, gestion.id_gestion),
        dimensiones=[_a_modelo(d, DimensionSalida) for d in await _dimensiones(sesion, gestion.id_gestion)],
        clases=[_a_modelo(f, ClaseCalificacionSalida) for f in filas],
    )


async def _clase_y_periodo(sesion: AsyncSession, usuario: UsuarioActual, id_asignacion: int, id_periodo: int):
    clase = await politicas.clase_para_notas(sesion, usuario, id_asignacion)
    periodo = await repo.periodo_cu23(sesion, id_periodo)
    if periodo is None:
        raise NoEncontrado("No existe ese periodo.")
    if periodo.id_gestion != clase.id_gestion:
        raise ErrorNegocio(f"El {periodo.nombre_periodo} no es de la gestión {clase.anio} de esa clase.")
    return clase, periodo


async def planilla(sesion: AsyncSession, usuario: UsuarioActual, id_asignacion: int, id_periodo: int) -> PlanillaSalida:
    clase, periodo = await _clase_y_periodo(sesion, usuario, id_asignacion, id_periodo)
    restriccion = politicas.restriccion_notas(usuario.rol, periodo)
    periodo_salida = next(p for p in await _periodos(sesion, clase.id_gestion) if p.id_periodo == id_periodo)
    return PlanillaSalida(
        clase=_a_modelo(clase, ClaseCalificacionSalida),
        periodo=periodo_salida,
        nota_minima=float(clase.nota_minima),
        dimensiones=[_a_modelo(d, DimensionSalida) for d in await _dimensiones(sesion, clase.id_gestion)],
        editable=restriccion is None,
        motivo_no_editable=restriccion.detalle if restriccion else None,
        estudiantes=[
            NotaEstudianteSalida(
                ci=e.ci, nombre_persona=e.nombre_persona, apellidos=e.apellidos, puntajes=_puntajes(e.puntajes),
                nota_final=float(e.nota_final) if e.nota_final is not None else None, observacion=e.observacion,
            )
            for e in await repo.planilla_cu23(sesion, id_asignacion, id_periodo)
        ],
    )


async def guardar(sesion: AsyncSession, usuario: UsuarioActual, id_asignacion: int,
                  datos: PlanillaGuardar) -> PlanillaSalida:
    """Registra o corrige las notas enviadas (solo los estudiantes y dimensiones que vienen)."""
    clase, periodo = await _clase_y_periodo(sesion, usuario, id_asignacion, datos.id_periodo)
    restriccion = politicas.restriccion_notas(usuario.rol, periodo)
    if restriccion:
        raise restriccion

    dimensiones = {d.id_dimension: d for d in await _dimensiones(sesion, clase.id_gestion)}
    inscritos = {e.ci: e for e in await repo.planilla_cu23(sesion, id_asignacion, datos.id_periodo)}
    ajenos = sorted({n.ci_estudiante for n in datos.notas} - inscritos.keys())
    if ajenos:
        raise ErrorNegocio(f"No están inscritos (o están retirados) en {clase.curso}: {', '.join(ajenos)}.")

    errores = []
    for nota in datos.notas:
        for id_dimension, valor in nota.puntajes.items():
            dimension = dimensiones.get(id_dimension)
            if dimension is None:
                raise ErrorNegocio(f"La dimensión {id_dimension} no es de la gestión {clase.anio}.")
            if dimension.es_autoevaluacion:
                raise SinPermiso("La autoevaluación la registra el propio estudiante.")
            if valor is not None and (mensaje := politicas.puntaje_valido(valor, dimension)):
                errores.append(f"{_nombre(inscritos[nota.ci_estudiante])}: {mensaje}")
    if errores:
        extra = f" (y {len(errores) - 5} más)" if len(errores) > 5 else ""
        raise ErrorNegocio("Revise los puntajes. " + "; ".join(errores[:5]) + extra + ".")

    fecha = await _fecha_registro(sesion, periodo)
    for nota in datos.notas:
        await repo.guardar_notas_cu23(
            sesion, nota.ci_estudiante, clase.id_materia, datos.id_periodo, fecha,
            {d: (round(v, 2) if v is not None else None) for d, v in nota.puntajes.items()},
            nota.observacion, "observacion" in nota.model_fields_set,
        )
    return await planilla(sesion, usuario, id_asignacion, datos.id_periodo)


# ------------------------------------------------------------
# Estudiante: sus notas y su autoevaluación
# ------------------------------------------------------------

async def mis_calificaciones(sesion: AsyncSession, usuario: UsuarioActual,
                             id_periodo: int | None) -> MisCalificacionesSalida:
    """Notas del estudiante por materia en un trimestre (por defecto, el último que ya empezó)."""
    gestion = await repo.gestion_del_estudiante_cu23(sesion, usuario.ci)
    if gestion is None:
        return MisCalificacionesSalida(gestion=None, curso=None, nota_minima=None, periodos=[], periodo=None,
                                       dimensiones=[], autoevaluacion_editable=False,
                                       motivo_no_editable="No tiene una inscripción vigente.", materias=[])
    periodos = await _periodos(sesion, gestion.id_gestion)
    if id_periodo is not None:
        elegido = next((p for p in periodos if p.id_periodo == id_periodo), None)
        if elegido is None:
            raise NoEncontrado("Ese periodo no es de su gestión.")
    else:
        iniciados = [p for p in periodos if p.iniciado]
        elegido = iniciados[-1] if iniciados else (periodos[0] if periodos else None)

    inscripcion = await repo.inscripcion_cu23(sesion, usuario.ci, gestion.id_gestion)
    materias, restriccion = [], ErrorNegocio("La gestión no tiene periodos.")
    if elegido is not None:
        restriccion = politicas.restriccion_notas(usuario.rol, await repo.periodo_cu23(sesion, elegido.id_periodo))
        materias = [
            MateriaNotasSalida(
                id_materia=m.id_materia, materia=m.materia, profesor=m.profesor, puntajes=_puntajes(m.puntajes),
                nota_final=float(m.nota_final) if m.nota_final is not None else None, observacion=m.observacion,
            )
            for m in await repo.notas_estudiante_cu23(
                sesion, usuario.ci, inscripcion.id_curso, gestion.id_gestion, elegido.id_periodo
            )
        ]
    return MisCalificacionesSalida(
        gestion=gestion.anio,
        curso=inscripcion.curso,
        nota_minima=float(gestion.nota_minima),
        periodos=periodos,
        periodo=elegido,
        dimensiones=[_a_modelo(d, DimensionSalida) for d in await _dimensiones(sesion, gestion.id_gestion)],
        autoevaluacion_editable=restriccion is None,
        motivo_no_editable=restriccion.detalle if restriccion else None,
        materias=materias,
    )


async def guardar_autoevaluacion(sesion: AsyncSession, usuario: UsuarioActual,
                                 datos: AutoevaluacionGuardar) -> MisCalificacionesSalida:
    """El estudiante registra su autoevaluación en cada materia del trimestre."""
    periodo = await repo.periodo_cu23(sesion, datos.id_periodo)
    if periodo is None:
        raise NoEncontrado("No existe ese periodo.")
    inscripcion = await repo.inscripcion_cu23(sesion, usuario.ci, periodo.id_gestion)
    if inscripcion is None:
        raise ErrorNegocio(f"No está inscrito en la gestión {periodo.anio}.")
    restriccion = politicas.restriccion_notas(usuario.rol, periodo)
    if restriccion:
        raise restriccion

    autoevaluacion = next((d for d in await _dimensiones(sesion, periodo.id_gestion) if d.es_autoevaluacion), None)
    if autoevaluacion is None:
        raise ErrorNegocio(f"La gestión {periodo.anio} no tiene dimensión de autoevaluación.")
    materias = {
        m.id_materia: m.materia
        for m in await repo.notas_estudiante_cu23(sesion, usuario.ci, inscripcion.id_curso, periodo.id_gestion,
                                                  periodo.id_periodo)
    }
    errores = []
    for a in datos.autoevaluaciones:
        if a.id_materia not in materias:
            raise ErrorNegocio("Solo puede autoevaluarse en las materias de su curso.")
        if a.puntaje is not None and (mensaje := politicas.puntaje_valido(a.puntaje, autoevaluacion)):
            errores.append(f"{materias[a.id_materia]}: {mensaje}")
    if errores:
        raise ErrorNegocio("Revise su autoevaluación. " + "; ".join(errores) + ".")

    fecha = await _fecha_registro(sesion, periodo)
    for a in datos.autoevaluaciones:
        await repo.guardar_notas_cu23(
            sesion, usuario.ci, a.id_materia, periodo.id_periodo, fecha,
            {autoevaluacion.id_dimension: round(a.puntaje, 2) if a.puntaje is not None else None}, None, False,
        )
    return await mis_calificaciones(sesion, usuario, periodo.id_periodo)


# ------------------------------------------------------------
# Administrador: cerrar y reabrir el trimestre
# ------------------------------------------------------------

async def _periodo_de_gestion_abierta(sesion: AsyncSession, id_periodo: int):
    periodo = await repo.periodo_cu23(sesion, id_periodo)
    if periodo is None:
        raise NoEncontrado("No existe ese periodo.")
    if periodo.estado_gestion != "abierta":
        raise ErrorNegocio(f"La gestión {periodo.anio} está cerrada: sus trimestres ya no cambian.")
    return periodo


async def cerrar_periodo(sesion: AsyncSession, id_periodo: int) -> CambioPeriodoSalida:
    """Cierra el trimestre (las notas quedan fijas) y emite los boletines de todo el trimestre."""
    periodo = await _periodo_de_gestion_abierta(sesion, id_periodo)
    if periodo.estado_periodo == "cerrado":
        raise Conflicto(f"El {periodo.nombre_periodo} ya está cerrado.")
    if not periodo.iniciado:
        raise ErrorNegocio(f"El {periodo.nombre_periodo} aún no empieza: no se puede cerrar.")
    await repo.cambiar_estado_periodo_cu23(sesion, id_periodo, "cerrado")
    await repo.registrar_bitacora_cu23(sesion, f"Cerró el {periodo.nombre_periodo} {periodo.anio}",
                                      id_periodo, "abierto", "cerrado")
    boletines = await repo.emitir_boletines_cu23(sesion, id_periodo)
    return CambioPeriodoSalida(periodo=periodo.nombre_periodo, estado_periodo="cerrado", boletines=boletines)


async def reabrir_periodo(sesion: AsyncSession, id_periodo: int) -> CambioPeriodoSalida:
    """Reabre el trimestre para corregir notas; al cerrarlo otra vez se reemiten los boletines."""
    periodo = await _periodo_de_gestion_abierta(sesion, id_periodo)
    if periodo.estado_periodo == "abierto":
        raise Conflicto(f"El {periodo.nombre_periodo} ya está abierto.")
    await repo.cambiar_estado_periodo_cu23(sesion, id_periodo, "abierto")
    await repo.registrar_bitacora_cu23(sesion, f"Reabrió el {periodo.nombre_periodo} {periodo.anio}",
                                      id_periodo, "cerrado", "abierto")
    return CambioPeriodoSalida(periodo=periodo.nombre_periodo, estado_periodo="abierto", boletines=None)

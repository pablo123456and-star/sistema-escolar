"""
CU21 - Registrar asistencia de estudiantes
Paquete: evaluacion

Actores ........: Docente
Rol del sistema : profesor, administrador
Tablas .........: asistencia, asignacion_profesor_clase, inscripcion
Usa de la BD ...: Trigger de auditoría de asistencia

Reglas de negocio que implementa este caso de uso (backend):
    - Solo el profesor de esa asignación (o administrador).
    - La fecha no puede ser futura (hora de Bolivia) y debe estar dentro de la gestión.
    - La gestión debe estar abierta; un periodo cerrado solo lo corrige el administrador.
    - Cada estudiante debe estar inscrito (no retirado) en el curso de la clase.
    - Un registro por estudiante, clase y día (lo asegura la BD): si ya existe, se corrige.
    - Registrar toda la clase en una sola operación (deben venir todos los inscritos).
    - Un día sin clase según el horario solo se avisa (se permite, ej. clase de recuperación).

Precondición:
    El docente dicta esa clase. La fecha no es futura y está dentro de la gestión.

Postcondición:
    La asistencia de la clase queda registrada o corregida y auditada.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import ErrorNegocio
from app.paquetes.academico.politicas import gestion_abierta
from app.paquetes.evaluacion import politicas
from app.paquetes.evaluacion import repository as repo
from app.paquetes.evaluacion.schemas import (
    AsistenciaGuardar, ClaseAsistenciaSalida, ClasesAsistenciaSalida, EstudianteAsistenciaSalida,
    ListaAsistenciaSalida,
)

DIAS = ("lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo")


def _clase_salida(clase) -> ClaseAsistenciaSalida:
    return ClaseAsistenciaSalida.model_validate(clase._asdict())


async def clases(sesion: AsyncSession, usuario: UsuarioActual) -> ClasesAsistenciaSalida:
    """Clases de la gestión abierta: el profesor ve las suyas; el administrador, todas."""
    gestion = await gestion_abierta(sesion)
    filas = []
    if gestion:
        filas = await repo.clases_cu21(sesion, gestion.id_gestion, None if usuario.rol == "administrador" else usuario.ci)
    return ClasesAsistenciaSalida(
        gestion=gestion.anio if gestion else None,
        fecha_inicio=gestion.fecha_inicio_g if gestion else None,
        hoy=await repo.hoy(sesion),
        clases=[_clase_salida(f) for f in filas],
    )


async def lista(sesion: AsyncSession, usuario: UsuarioActual, id_asignacion: int,
                fecha: date | None) -> ListaAsistenciaSalida:
    clase = await politicas.clase_propia(sesion, usuario, id_asignacion)
    fecha = fecha or await repo.hoy(sesion)
    await politicas.validar_fecha(sesion, clase, fecha)
    estudiantes = await repo.estudiantes_cu21(sesion, id_asignacion, fecha)
    periodo = await repo.periodo_de_fecha_cu21(sesion, clase.id_gestion, fecha)
    restriccion = await politicas.restriccion_edicion(sesion, usuario, clase, fecha)
    return ListaAsistenciaSalida(
        clase=_clase_salida(clase),
        fecha=fecha,
        registrada=any(e.estado for e in estudiantes),
        dia_con_clase=DIAS[fecha.weekday()] in clase.dias,
        periodo=periodo.nombre_periodo if periodo else None,
        editable=restriccion is None,
        motivo_no_editable=restriccion.detalle if restriccion else None,
        estudiantes=[EstudianteAsistenciaSalida.model_validate(e._asdict()) for e in estudiantes],
    )


async def guardar(sesion: AsyncSession, usuario: UsuarioActual, id_asignacion: int,
                  datos: AsistenciaGuardar) -> ListaAsistenciaSalida:
    clase = await politicas.clase_propia(sesion, usuario, id_asignacion)
    await politicas.validar_fecha(sesion, clase, datos.fecha)
    restriccion = await politicas.restriccion_edicion(sesion, usuario, clase, datos.fecha)
    if restriccion:
        raise restriccion

    inscritos = {e.ci: e for e in await repo.estudiantes_cu21(sesion, id_asignacion, datos.fecha)}
    if not inscritos:
        raise ErrorNegocio("El curso no tiene estudiantes inscritos.")
    enviados = {r.ci_estudiante for r in datos.registros}
    ajenos = enviados - inscritos.keys()
    if ajenos:
        raise ErrorNegocio(
            f"No están inscritos (o están retirados) en {clase.curso}: {', '.join(sorted(ajenos))}."
        )
    faltan = inscritos.keys() - enviados
    if faltan:
        nombres = sorted(f"{inscritos[ci].apellidos} {inscritos[ci].nombre_persona}" for ci in faltan)
        raise ErrorNegocio(f"Falta marcar la asistencia de: {', '.join(nombres)}.")

    await repo.guardar_cu21(sesion, id_asignacion, datos.fecha, [
        {"ci": r.ci_estudiante, "estado": r.estado, "observacion": r.observacion} for r in datos.registros
    ])
    return await lista(sesion, usuario, id_asignacion, datos.fecha)

"""
CU07 - Registrar antecedentes médicos y seguimiento del estudiante
Paquete: personas

Actores ........: Administrativo, Docente (registran); Padre/Tutor (consulta)
Rol del sistema : administrador, profesor; tutor (solo lectura)
Tablas .........: estudiante, seguimiento_estudiante; persona, inscripcion, asignacion_profesor_clase,
                  tutor_estudiante, usuario, rol (solo lectura)
Usa de la BD ...: Trigger de auditoría de estudiante y seguimiento; CHECK de tipo y gravedad

Reglas de negocio que implementa este caso de uso (backend):
    - Observación médica: solo el administrador la registra o modifica. El profesor y el tutor la ven
      (solo lectura) para atender al estudiante (alergias, medicación...).
    - Antecedentes académicos: se muestran aquí; se editan en el CU06.
    - Seguimiento: lo registra el administrador o un profesor que dicta alguna materia al estudiante en
      la gestión actual (gestión abierta, inscripción activa).
    - El autor del seguimiento es el usuario conectado (no se recibe del formulario).
    - Tipos: conducta, academico, salud, merito, otro. La gravedad es obligatoria para conducta y no se
      permite en los demás tipos (la BD también impide gravedad fuera de conducta).
    - La fecha del seguimiento no puede ser futura (por defecto, hoy).
    - No se registra seguimiento de un estudiante dado de baja.
    - Las anotaciones no se editan ni se borran: un error se aclara con otra anotación (queda historial).
    - Quién consulta: administrador (todos), profesor (sus estudiantes de la gestión actual) y tutor
      (sus estudiantes). A un estudiante ajeno se responde "sin permiso" sin revelar si existe.

Precondición:
    El estudiante existe. Un docente solo registra seguimiento de sus propios estudiantes.

Postcondición:
    La observación médica o el seguimiento queda guardado (y en la bitácora) y visible para sus tutores.

Flujo: router.py -> este caso de uso -> repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import ErrorNegocio, NoEncontrado, SinPermiso
from app.nucleo.esquemas import Pagina
from app.paquetes.academico import politicas as academico
from app.paquetes.personas import repository as repo
from app.paquetes.personas.models import Estudiante, Persona, SeguimientoEstudiante
from app.paquetes.personas.schemas import (
    AntecedentesActualizar, EstudianteSeguimientoSalida, FichaSeguimientoSalida, SeguimientoCrear,
    SeguimientoSalida,
)

_SOLO_SUYOS = {
    "profesor": "Solo puede ver el seguimiento de los estudiantes a los que dicta clases en la gestión actual.",
    "tutor": "Este estudiante no está a su cargo.",
}


async def _id_gestion_actual(sesion: AsyncSession) -> int | None:
    gestion = await academico.gestion_abierta(sesion)
    return gestion.id_gestion if gestion else None


async def _verificar_visible(sesion: AsyncSession, usuario: UsuarioActual, ci: str) -> None:
    """El permiso va primero: a un estudiante ajeno no se le revela si existe."""
    if usuario.rol == "administrador":
        if await sesion.get(Estudiante, ci) is None:
            raise NoEncontrado("No existe un estudiante con ese CI.")
        return
    if usuario.rol not in _SOLO_SUYOS:
        raise SinPermiso("Su rol no puede consultar el seguimiento de estudiantes.")
    if not await repo.estudiante_visible_cu07(sesion, usuario.rol, usuario.ci, await _id_gestion_actual(sesion), ci):
        raise SinPermiso(_SOLO_SUYOS[usuario.rol])


def _seguimiento_salida(fila, usuario: UsuarioActual) -> SeguimientoSalida:
    datos = fila._asdict()
    autor = datos.pop("ci_registrado_por")
    return SeguimientoSalida(**datos, es_mio=autor == usuario.ci)


async def listar(sesion: AsyncSession, usuario: UsuarioActual, q: str | None, pagina: int,
                 tamano: int) -> Pagina[EstudianteSeguimientoSalida]:
    filas, total = await repo.listar_estudiantes_cu07(
        sesion, rol=usuario.rol, ci_usuario=usuario.ci, id_gestion=await _id_gestion_actual(sesion),
        q=q, pagina=pagina, tamano=tamano,
    )
    return Pagina[EstudianteSeguimientoSalida](
        items=[EstudianteSeguimientoSalida.model_validate(f._asdict()) for f in filas],
        total=total, pagina=pagina, tamano=tamano,
    )


async def ficha(sesion: AsyncSession, usuario: UsuarioActual, ci: str) -> FichaSeguimientoSalida:
    await _verificar_visible(sesion, usuario, ci)
    fila = await repo.ficha_cu07(sesion, ci)
    activo = fila.estado_persona == "activo"
    return FichaSeguimientoSalida(
        **fila._asdict(),
        puede_editar_antecedentes=usuario.rol == "administrador",
        # el profesor que llegó hasta aquí ya dicta al estudiante en la gestión actual
        puede_registrar_seguimiento=activo and usuario.rol in ("administrador", "profesor"),
        seguimientos=[_seguimiento_salida(s, usuario) for s in await repo.seguimientos_cu07(sesion, ci)],
    )


async def actualizar_antecedentes(sesion: AsyncSession, usuario: UsuarioActual, ci: str,
                                  datos: AntecedentesActualizar) -> FichaSeguimientoSalida:
    """Solo administrador (lo exige el router)."""
    estudiante = await sesion.get(Estudiante, ci)
    if estudiante is None:
        raise NoEncontrado("No existe un estudiante con ese CI.")
    if "observacion_medica" in datos.model_fields_set:
        estudiante.observacion_medica = datos.observacion_medica
        await sesion.flush()
    return await ficha(sesion, usuario, ci)


def _validar_gravedad(datos: SeguimientoCrear) -> None:
    if datos.tipo == "conducta" and datos.gravedad is None:
        raise ErrorNegocio("Indique la gravedad de la falta de conducta (leve, grave o muy grave).")
    if datos.tipo != "conducta" and datos.gravedad is not None:
        raise ErrorNegocio("La gravedad solo se indica en los seguimientos de conducta.")


async def registrar_seguimiento(sesion: AsyncSession, usuario: UsuarioActual, ci: str,
                                datos: SeguimientoCrear) -> SeguimientoSalida:
    """Administrador o profesor (lo exige el router); el profesor, solo de sus estudiantes."""
    await _verificar_visible(sesion, usuario, ci)
    persona = await sesion.get(Persona, ci)
    if persona.estado_persona != "activo":
        raise ErrorNegocio("El estudiante está dado de baja: no se le puede registrar seguimiento.")
    _validar_gravedad(datos)
    hoy = await repo.hoy(sesion)
    fecha = datos.fecha or hoy
    if fecha > hoy:
        raise ErrorNegocio("La fecha del seguimiento no puede ser futura.")

    nuevo = SeguimientoEstudiante(
        fecha_seguimiento=fecha,
        tipo_seguimiento=datos.tipo,
        gravedad=datos.gravedad,
        descripcion_seguimiento=datos.descripcion,
        accion_tomada=datos.accion_tomada,
        ci_estudiante_seguimiento=ci,
        ci_registrado_por=usuario.ci,
    )
    sesion.add(nuevo)
    await sesion.flush()
    (fila,) = await repo.seguimientos_cu07(sesion, ci, id_seguimiento=nuevo.id_seguimiento)
    return _seguimiento_salida(fila, usuario)

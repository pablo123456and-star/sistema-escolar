"""
CU10 - Registrar docente
Paquete: personas

Actores ........: Administrador
Rol del sistema : administrador
Tablas .........: persona, profesor, usuario; asignacion_profesor_clase, gestion, materia, aula (solo lectura)
Usa de la BD ...: Trigger de auditoría de persona y profesor; vista v_curso

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Registrar persona + profesor en una sola transacción (reutilizando la persona si ya existe,
      por ejemplo un tutor que ahora es docente). Error si el CI ya está registrado como docente.
    - Datos profesionales: título académico, fecha de contrato, antecedentes laborales y años de
      experiencia (no negativos; también lo asegura la BD).
    - Listar con búsqueda (nombre o CI) y filtro de estado; consultar (con sus materias de la gestión
      abierta) y actualizar (actualización parcial).
    - Dar de baja (baja lógica): persona y usuario inactivos. No se permite si el docente tiene
      asignaciones en la gestión abierta (primero se reasignan en el CU14).
    - Reactivar: vuelve a activo (y su usuario).

Precondición:
    Sesión iniciada como administrador. El CI no está registrado como docente.

Postcondición:
    El profesor queda registrado y puede recibir asignaciones y una cuenta de usuario.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.errores import Conflicto, ErrorNegocio, NoEncontrado
from app.nucleo.esquemas import Pagina
from app.paquetes.academico import politicas as academico
from app.paquetes.academico.models import AsignacionProfesorClase
from app.paquetes.personas import politicas
from app.paquetes.personas import repository as repo
from app.paquetes.personas.models import Persona, Profesor
from app.paquetes.personas.schemas import (
    AsignacionDocenteSalida, DocenteActualizar, DocenteCrear, DocenteDetalleSalida, DocenteSalida, PersonaSalida,
)

CAMPOS_PROFESIONALES = ("titulo_academico", "fecha_contrato", "antecedentes_laborales", "anios_experiencia")


async def listar(sesion: AsyncSession, q: str | None, estado: str | None, pagina: int,
                 tamano: int) -> Pagina[DocenteSalida]:
    filas, total = await repo.listar_docentes(sesion, q=q, estado=estado, pagina=pagina, tamano=tamano)
    return Pagina[DocenteSalida](
        items=[DocenteSalida.model_validate(f._asdict()) for f in filas], total=total, pagina=pagina, tamano=tamano
    )


async def obtener(sesion: AsyncSession, ci: str) -> DocenteDetalleSalida:
    profesor = await _profesor(sesion, ci)
    persona = await sesion.get(Persona, ci)
    gestion = await academico.gestion_abierta(sesion)
    asignaciones = await repo.asignaciones_docente(sesion, ci, gestion.id_gestion) if gestion else []
    return DocenteDetalleSalida(
        **PersonaSalida.model_validate(persona, from_attributes=True).model_dump(),
        **{campo: getattr(profesor, campo) for campo in CAMPOS_PROFESIONALES},
        gestion=gestion.anio if gestion else None,
        asignaciones=[AsignacionDocenteSalida.model_validate(a._asdict()) for a in asignaciones],
        tiene_usuario=await repo.tiene_usuario(sesion, ci),
    )


async def registrar(sesion: AsyncSession, datos: DocenteCrear) -> DocenteDetalleSalida:
    persona = await politicas.registrar_o_reutilizar(sesion, datos.persona)
    if await sesion.get(Profesor, persona.ci) is not None:
        raise Conflicto("La persona ya está registrada como docente.")
    sesion.add(Profesor(ci_profesor=persona.ci, **datos.model_dump(include=set(CAMPOS_PROFESIONALES))))
    await sesion.flush()
    return await obtener(sesion, persona.ci)


async def actualizar(sesion: AsyncSession, ci: str, datos: DocenteActualizar) -> DocenteDetalleSalida:
    profesor = await _profesor(sesion, ci)
    if datos.persona is not None:
        politicas.aplicar_cambios(await sesion.get(Persona, ci), datos.persona)
    for campo in CAMPOS_PROFESIONALES:
        if campo in datos.model_fields_set:
            setattr(profesor, campo, getattr(datos, campo))
    await sesion.flush()
    return await obtener(sesion, ci)


async def dar_baja(sesion: AsyncSession, ci: str, motivo: str) -> DocenteDetalleSalida:
    await _profesor(sesion, ci)
    gestion = await academico.gestion_abierta(sesion)
    if gestion is not None:
        asignadas = await sesion.scalar(
            select(func.count()).where(
                AsignacionProfesorClase.ci_profesor_asignacion == ci,
                AsignacionProfesorClase.id_gestion_asignacion == gestion.id_gestion,
            )
        )
        if asignadas:
            raise ErrorNegocio(
                f"No se puede dar de baja: el docente tiene {asignadas} materia(s) asignada(s) en la gestión "
                f"{gestion.anio}. Reasígnelas primero a otro docente."
            )
    await politicas.dar_baja(sesion, ci, motivo)
    return await obtener(sesion, ci)


async def reactivar(sesion: AsyncSession, ci: str) -> DocenteDetalleSalida:
    await _profesor(sesion, ci)
    await politicas.reactivar(sesion, ci)
    return await obtener(sesion, ci)


async def _profesor(sesion: AsyncSession, ci: str) -> Profesor:
    profesor = await sesion.get(Profesor, ci)
    if profesor is None:
        raise NoEncontrado("No existe un docente con ese CI.")
    return profesor

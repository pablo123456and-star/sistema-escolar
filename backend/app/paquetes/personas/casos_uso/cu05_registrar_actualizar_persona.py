"""
CU05 - Registrar y actualizar datos de persona
Paquete: personas

Actores ........: Administrativo
Rol del sistema : administrador
Tablas .........: persona, usuario, inscripcion
Usa de la BD ...: Triggers de auditoría y actualizado_en

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Buscar personas (por CI, nombre o apellido, con paginación) y ver su ficha con sus roles
      (estudiante, tutor, profesor, administrativo), su usuario (solo nombre, rol y estado) y su inscripción actual.
    - Actualización parcial: solo cambian los campos enviados. El CI no se cambia aquí.
    - Dar de baja (baja lógica): persona 'inactivo' + su usuario 'inactivo' + sus inscripciones activas pasan a 'retirada' con fecha de hoy y motivo. Todo en una transacción.
    - Reactivar: persona 'activo' y su usuario 'inactivo' vuelve a 'activo'.
    - Nunca se borra físicamente una persona.
    - El administrador no puede darse de baja a sí mismo (se quedaría sin acceso).
    - Si la persona es docente, la baja aplica también la regla del CU10: no se permite si tiene
      materias asignadas en la gestión abierta.
    - El registro de personas nuevas se hace en el CU06 (estudiante), CU08 (tutor) y CU10 (docente).

Precondición:
    Sesión iniciada como administrador. Para actualizar o dar de baja: la persona existe.

Postcondición:
    Los datos quedan actualizados, o la persona queda inactiva con su usuario desactivado. Queda en la bitácora.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import ErrorNegocio, NoEncontrado
from app.nucleo.esquemas import Pagina
from app.paquetes.personas import politicas
from app.paquetes.personas import repository as repo
from app.paquetes.personas.casos_uso import cu10_registrar_docente as cu10
from app.paquetes.personas.models import Profesor
from app.paquetes.personas.schemas import (
    InscripcionActualSalida, PersonaActualizar, PersonaFichaSalida, PersonaListaSalida, PersonaSalida,
    UsuarioPersonaSalida,
)


async def listar(sesion: AsyncSession, buscar: str | None, estado: str | None, pagina: int,
                 tamano: int) -> Pagina[PersonaListaSalida]:
    filas, total = await repo.listar_personas_cu05(sesion, buscar=buscar, estado=estado, pagina=pagina, tamano=tamano)
    return Pagina[PersonaListaSalida](
        items=[PersonaListaSalida.model_validate(f._asdict()) for f in filas], total=total, pagina=pagina, tamano=tamano
    )


async def obtener(sesion: AsyncSession, usuario: UsuarioActual, ci: str) -> PersonaFichaSalida:
    fila = await repo.buscar_persona(sesion, ci)
    if fila is None:
        raise NoEncontrado("No existe una persona con ese CI.")
    cuenta = await repo.usuario_cu05(sesion, ci)
    ins = await repo.inscripcion_actual(sesion, ci)
    return PersonaFichaSalida(
        **PersonaSalida.model_validate(fila.Persona, from_attributes=True).model_dump(),
        es_estudiante=fila.es_estudiante, es_tutor=fila.es_tutor,
        es_profesor=fila.es_profesor, es_administrativo=fila.es_administrativo,
        usuario=UsuarioPersonaSalida.model_validate(cuenta._asdict()) if cuenta else None,
        inscripcion=InscripcionActualSalida.model_validate(ins._asdict()) if ins else None,
        es_usuario_actual=ci == usuario.ci,
    )


async def actualizar(sesion: AsyncSession, usuario: UsuarioActual, ci: str,
                     datos: PersonaActualizar) -> PersonaFichaSalida:
    politicas.aplicar_cambios(await politicas.obtener_persona(sesion, ci), datos)
    await sesion.flush()
    return await obtener(sesion, usuario, ci)


async def dar_baja(sesion: AsyncSession, usuario: UsuarioActual, ci: str, motivo: str) -> PersonaFichaSalida:
    await politicas.obtener_persona(sesion, ci)
    if ci == usuario.ci:
        raise ErrorNegocio("No puede darse de baja a sí mismo: perdería el acceso al sistema. "
                           "Pida a otro administrador que lo haga.")
    if await sesion.get(Profesor, ci) is not None:
        # Docente: misma baja que el CU10 (no se permite con materias asignadas en la gestión abierta)
        await cu10.dar_baja(sesion, ci, motivo)
    else:
        await politicas.dar_baja(sesion, ci, motivo)
    return await obtener(sesion, usuario, ci)


async def reactivar(sesion: AsyncSession, usuario: UsuarioActual, ci: str) -> PersonaFichaSalida:
    await politicas.reactivar(sesion, ci)
    return await obtener(sesion, usuario, ci)

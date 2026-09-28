"""
Reglas de negocio comunes del paquete personas (compartido).

    - Quién ve a una persona: administrador (todos); profesor (sus estudiantes y los tutores de ellos); tutor (sus estudiantes); estudiante (a sí mismo y a sus tutores); los nombres del personal son visibles para todos.
    - Solo el administrador registra o modifica personas.
    - Baja lógica: no se borran personas (la BD lo impide si tienen historial); se marcan 'inactivo'.
    - Si la persona ya existe (p. ej. un tutor que ahora es profesor), se reutiliza.

Las reglas propias de cada caso de uso están en el encabezado de su archivo en casos_uso/.
"""
from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.errores import ErrorNegocio, NoEncontrado
from app.paquetes.academico.models import Inscripcion
from app.paquetes.personas.models import Persona
from app.paquetes.personas.schemas import PersonaActualizar, PersonaEntrada
from app.paquetes.seguridad.models import Usuario

OBLIGATORIOS = {"nombre_persona", "apellidos"}


def aplicar_cambios(persona: Persona, datos: PersonaActualizar | PersonaEntrada) -> None:
    """Actualización parcial: solo cambian los campos enviados (los obligatorios no se vacían)."""
    for campo, valor in datos.model_dump(exclude_unset=True, exclude={"ci"}).items():
        if valor is None and campo in OBLIGATORIOS:
            continue
        setattr(persona, campo, valor)


async def registrar_o_reutilizar(sesion: AsyncSession, datos: PersonaEntrada) -> Persona:
    """Crea la persona o, si el CI ya existe, la reutiliza actualizando los datos enviados."""
    persona = await sesion.get(Persona, datos.ci)
    if persona is None:
        persona = Persona(**datos.model_dump())
        sesion.add(persona)
    else:
        if persona.estado_persona != "activo":
            raise ErrorNegocio("La persona con ese CI está dada de baja; reactívela antes de registrarla de nuevo.")
        aplicar_cambios(persona, datos)
    await sesion.flush()
    return persona


async def obtener_persona(sesion: AsyncSession, ci: str) -> Persona:
    persona = await sesion.get(Persona, ci)
    if persona is None:
        raise NoEncontrado("No existe una persona con ese CI.")
    return persona


async def dar_baja(sesion: AsyncSession, ci: str, motivo: str) -> None:
    """Baja lógica: persona inactiva, su usuario inactivo y sus inscripciones activas retiradas."""
    persona = await obtener_persona(sesion, ci)
    if persona.estado_persona == "inactivo":
        raise ErrorNegocio("La persona ya está dada de baja.")
    persona.estado_persona = "inactivo"
    await sesion.execute(
        update(Usuario).where(Usuario.ci_persona == ci, Usuario.estado_usuario == "activo").values(estado_usuario="inactivo")
    )
    await sesion.execute(
        update(Inscripcion)
        .where(Inscripcion.ci_estudiante_inscripcion == ci, Inscripcion.estado_inscripcion == "activa")
        .values(estado_inscripcion="retirada", fecha_retiro=func.current_date(), motivo_retiro=motivo)
    )
    await sesion.flush()


async def reactivar(sesion: AsyncSession, ci: str) -> None:
    """La persona vuelve a 'activo' y su usuario inactivo se reactiva (no las inscripciones retiradas)."""
    persona = await obtener_persona(sesion, ci)
    if persona.estado_persona == "activo":
        raise ErrorNegocio("La persona ya está activa.")
    persona.estado_persona = "activo"
    await sesion.execute(
        update(Usuario).where(Usuario.ci_persona == ci, Usuario.estado_usuario == "inactivo").values(estado_usuario="activo")
    )
    await sesion.flush()

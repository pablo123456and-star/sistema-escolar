"""
CU08 - Registrar tutor y asociarlo a estudiante
Paquete: personas

Actores ........: Administrativo (Secretaría)
Rol del sistema : administrador
Tablas .........: persona, tutor, tutor_estudiante, pago_mensualidad (solo lectura)
Usa de la BD ...: Trigger de auditoría de tutor_estudiante y persona

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Registrar persona + tutor (reutilizando la persona si ya existe).
    - Listar, consultar y actualizar tutores; ver los estudiantes a su cargo (consulta del CU09 para el administrador).
    - Vincular con un estudiante indicando parentesco, principal, responsable de pago y autorizado a recoger.
    - Solo se vinculan tutores y estudiantes activos; el tutor no puede ser el mismo estudiante.
    - Si el vínculo se marca como principal, se quita la marca al principal anterior (la BD solo permite uno).
    - No se puede desvincular un tutor que ya tiene pagos de ese estudiante: se muestra un mensaje claro.

Precondición:
    Sesión iniciada como administrador. El estudiante existe.

Postcondición:
    El tutor queda registrado y vinculado con su parentesco; cada estudiante tiene a lo sumo un tutor principal.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.errores import Conflicto, ErrorNegocio, NoEncontrado
from app.nucleo.esquemas import Pagina
from app.paquetes.personas import politicas
from app.paquetes.personas import repository as repo
from app.paquetes.personas.models import Estudiante, Persona, Tutor, TutorEstudiante
from app.paquetes.personas.schemas import (
    PersonaSalida, TutorActualizar, TutorCrear, TutorDetalleSalida, TutorSalida, VinculoActualizar, VinculoEntrada,
    VinculoSalida,
)


async def listar(sesion: AsyncSession, q: str | None, estado: str | None, pagina: int, tamano: int) -> Pagina[TutorSalida]:
    filas, total = await repo.listar_tutores(sesion, q=q, estado=estado, pagina=pagina, tamano=tamano)
    return Pagina[TutorSalida](
        items=[TutorSalida.model_validate(f._asdict()) for f in filas], total=total, pagina=pagina, tamano=tamano
    )


async def obtener(sesion: AsyncSession, ci: str) -> TutorDetalleSalida:
    tutor = await sesion.get(Tutor, ci)
    if tutor is None:
        raise NoEncontrado("No existe un tutor con ese CI.")
    persona = await sesion.get(Persona, ci)
    return TutorDetalleSalida(
        **PersonaSalida.model_validate(persona, from_attributes=True).model_dump(),
        ocupacion=tutor.ocupacion,
        estudiantes=[VinculoSalida.model_validate(v) for v in await repo.vinculos(sesion, ci_tutor=ci)],
        tiene_usuario=await repo.tiene_usuario(sesion, ci),
    )


async def registrar(sesion: AsyncSession, datos: TutorCrear) -> TutorDetalleSalida:
    persona = await politicas.registrar_o_reutilizar(sesion, datos.persona)
    if await sesion.get(Tutor, persona.ci) is not None:
        raise Conflicto("La persona ya está registrada como tutor.")
    sesion.add(Tutor(ci_tutor=persona.ci, ocupacion=datos.ocupacion))
    await sesion.flush()
    return await obtener(sesion, persona.ci)


async def actualizar(sesion: AsyncSession, ci: str, datos: TutorActualizar) -> TutorDetalleSalida:
    tutor = await sesion.get(Tutor, ci)
    if tutor is None:
        raise NoEncontrado("No existe un tutor con ese CI.")
    if datos.persona is not None:
        politicas.aplicar_cambios(await sesion.get(Persona, ci), datos.persona)
    if "ocupacion" in datos.model_fields_set:
        tutor.ocupacion = datos.ocupacion
    await sesion.flush()
    return await obtener(sesion, ci)


async def vincular(sesion: AsyncSession, ci_tutor: str, ci_estudiante: str, datos: VinculoEntrada) -> VinculoSalida:
    if ci_tutor == ci_estudiante:
        raise ErrorNegocio("El tutor no puede ser el mismo estudiante.")
    if await sesion.get(Tutor, ci_tutor) is None:
        raise NoEncontrado("No existe un tutor con ese CI.")
    if await sesion.get(Estudiante, ci_estudiante) is None:
        raise NoEncontrado("No existe un estudiante con ese CI.")
    for ci, quien in ((ci_tutor, "El tutor"), (ci_estudiante, "El estudiante")):
        if (await sesion.get(Persona, ci)).estado_persona != "activo":
            raise ErrorNegocio(f"{quien} está dado de baja.")
    if await sesion.get(TutorEstudiante, (ci_tutor, ci_estudiante)) is not None:
        raise Conflicto("El tutor ya está vinculado a ese estudiante.")
    if datos.es_principal:
        await _quitar_principal(sesion, ci_estudiante)
    sesion.add(TutorEstudiante(
        ci_tutor_tutorestudiante=ci_tutor, ci_estudiante_tutorestudiante=ci_estudiante, **datos.model_dump()
    ))
    await sesion.flush()
    return await _vinculo(sesion, ci_tutor, ci_estudiante)


async def actualizar_vinculo(sesion: AsyncSession, ci_tutor: str, ci_estudiante: str,
                             datos: VinculoActualizar) -> VinculoSalida:
    vinculo = await sesion.get(TutorEstudiante, (ci_tutor, ci_estudiante))
    if vinculo is None:
        raise NoEncontrado("El tutor no está vinculado a ese estudiante.")
    cambios = datos.model_dump(exclude_unset=True, exclude_none=True)
    if cambios.get("es_principal") and not vinculo.es_principal:
        await _quitar_principal(sesion, ci_estudiante)
    for campo, valor in cambios.items():
        setattr(vinculo, campo, valor)
    await sesion.flush()
    return await _vinculo(sesion, ci_tutor, ci_estudiante)


async def desvincular(sesion: AsyncSession, ci_tutor: str, ci_estudiante: str) -> None:
    vinculo = await sesion.get(TutorEstudiante, (ci_tutor, ci_estudiante))
    if vinculo is None:
        raise NoEncontrado("El tutor no está vinculado a ese estudiante.")
    if await repo.pagos_del_vinculo(sesion, ci_tutor, ci_estudiante):
        raise ErrorNegocio("No se puede desvincular: el tutor tiene pagos registrados de este estudiante.")
    await sesion.delete(vinculo)
    await sesion.flush()


async def _quitar_principal(sesion: AsyncSession, ci_estudiante: str) -> None:
    await sesion.execute(
        update(TutorEstudiante)
        .where(TutorEstudiante.ci_estudiante_tutorestudiante == ci_estudiante, TutorEstudiante.es_principal)
        .values(es_principal=False)
    )


async def _vinculo(sesion: AsyncSession, ci_tutor: str, ci_estudiante: str) -> VinculoSalida:
    filas = await repo.vinculos(sesion, ci_tutor=ci_tutor, ci_estudiante=ci_estudiante)
    return VinculoSalida.model_validate(filas[0])

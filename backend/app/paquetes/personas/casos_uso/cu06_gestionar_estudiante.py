"""
CU06 - Registrar y gestionar estudiante
Paquete: personas

Actores ........: Administrativo (Secretaría)
Rol del sistema : administrador
Tablas .........: persona, estudiante, tutor_estudiante, inscripcion, usuario
Usa de la BD ...: Trigger de auditoría de persona, estudiante, tutor_estudiante e inscripción; vista v_curso

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Registrar persona + estudiante en una sola transacción; si la persona ya existe, reutilizarla.
    - Opcional en el mismo paso: vincular tutor principal (reglas del CU08) e inscribir en la gestión
      abierta (reglas del CU16: cupo, sin inscripción previa, sin cuotas vencidas).
    - RUDE único (lo asegura la BD).
    - Listar con filtros (nombre/CI/RUDE, grado, paralelo, estado), consultar y actualizar datos.
    - Dar de baja (baja lógica): estudiante inactivo, su usuario inactivo y su inscripción activa retirada
      con fecha y motivo. Reactivar: vuelve a activo (y su usuario).

Precondición:
    Sesión iniciada como administrador. El CI no está registrado como estudiante.

Postcondición:
    La persona y el estudiante quedan registrados (opcionalmente con su tutor principal y su inscripción).

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.errores import Conflicto, NoEncontrado
from app.nucleo.esquemas import Pagina
from app.paquetes.academico import politicas as academico
from app.paquetes.personas import politicas
from app.paquetes.personas import repository as repo
from app.paquetes.personas.casos_uso import cu08_registrar_asociar_tutor as cu08
from app.paquetes.personas.models import Estudiante, Persona
from app.paquetes.personas.schemas import (
    CursoOpcion, EstudianteActualizar, EstudianteCrear, EstudianteDetalleSalida, EstudianteSalida,
    InscripcionActualSalida, OpcionesEstudianteSalida, PersonaSalida, VinculoEntrada, VinculoSalida,
)


async def listar(sesion: AsyncSession, *, q: str | None, id_grado: int | None, paralelo: str | None,
                 estado: str | None, pagina: int, tamano: int) -> Pagina[EstudianteSalida]:
    filas, total = await repo.listar_estudiantes(
        sesion, q=q, id_grado=id_grado, paralelo=paralelo, estado=estado, pagina=pagina, tamano=tamano
    )
    return Pagina[EstudianteSalida](
        items=[EstudianteSalida.model_validate(f._asdict()) for f in filas], total=total, pagina=pagina, tamano=tamano
    )


async def opciones(sesion: AsyncSession) -> OpcionesEstudianteSalida:
    gestion = await academico.gestion_abierta(sesion)
    cursos = [CursoOpcion.model_validate(c._asdict()) for c in await repo.opciones_cursos(sesion)]
    return OpcionesEstudianteSalida(
        gestion=gestion.anio if gestion else None,
        cursos=cursos,
        paralelos=sorted({c.paralelo for c in cursos}),
    )


async def obtener(sesion: AsyncSession, ci: str) -> EstudianteDetalleSalida:
    estudiante = await sesion.get(Estudiante, ci)
    if estudiante is None:
        raise NoEncontrado("No existe un estudiante con ese CI.")
    persona = await sesion.get(Persona, ci)
    ins = await repo.inscripcion_actual(sesion, ci)
    return EstudianteDetalleSalida(
        **PersonaSalida.model_validate(persona, from_attributes=True).model_dump(),
        rude=estudiante.rude,
        antecedentes_academicos=estudiante.antecedentes_academicos,
        inscripcion=InscripcionActualSalida.model_validate(ins._asdict()) if ins else None,
        tutores=[VinculoSalida.model_validate(v) for v in await repo.vinculos(sesion, ci_estudiante=ci)],
        tiene_usuario=await repo.tiene_usuario(sesion, ci),
    )


async def registrar(sesion: AsyncSession, datos: EstudianteCrear) -> EstudianteDetalleSalida:
    persona = await politicas.registrar_o_reutilizar(sesion, datos.persona)
    if await sesion.get(Estudiante, persona.ci) is not None:
        raise Conflicto("La persona ya está registrada como estudiante.")
    sesion.add(Estudiante(
        ci_estudiante=persona.ci, rude=datos.rude, antecedentes_academicos=datos.antecedentes_academicos
    ))
    await sesion.flush()

    if datos.tutor is not None:
        vinculo = VinculoEntrada.model_validate(datos.tutor.model_dump(exclude={"ci_tutor"}))
        await cu08.vincular(sesion, datos.tutor.ci_tutor, persona.ci, vinculo)
    if datos.id_curso is not None:
        await academico.inscribir(sesion, persona.ci, datos.id_curso)
    return await obtener(sesion, persona.ci)


async def actualizar(sesion: AsyncSession, ci: str, datos: EstudianteActualizar) -> EstudianteDetalleSalida:
    estudiante = await sesion.get(Estudiante, ci)
    if estudiante is None:
        raise NoEncontrado("No existe un estudiante con ese CI.")
    if datos.persona is not None:
        politicas.aplicar_cambios(await sesion.get(Persona, ci), datos.persona)
    for campo in ("rude", "antecedentes_academicos"):
        if campo in datos.model_fields_set:
            setattr(estudiante, campo, getattr(datos, campo))
    await sesion.flush()
    return await obtener(sesion, ci)


async def dar_baja(sesion: AsyncSession, ci: str, motivo: str) -> EstudianteDetalleSalida:
    if await sesion.get(Estudiante, ci) is None:
        raise NoEncontrado("No existe un estudiante con ese CI.")
    await politicas.dar_baja(sesion, ci, motivo)
    return await obtener(sesion, ci)


async def reactivar(sesion: AsyncSession, ci: str) -> EstudianteDetalleSalida:
    if await sesion.get(Estudiante, ci) is None:
        raise NoEncontrado("No existe un estudiante con ese CI.")
    await politicas.reactivar(sesion, ci)
    return await obtener(sesion, ci)

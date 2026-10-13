"""
CU19 - Generar horario de clases (aula, profesor, materia)
Paquete: horarios

Actores ........: Admin. académico
Rol del sistema : administrador
Tablas .........: horario, asignacion_profesor_clase (lectura: v_curso, v_horario, materia, persona, aula)
Usa de la BD ...: Trigger fn_tg_validar_horario; vistas v_curso y v_horario

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Se trabaja sobre un curso de la gestión abierta; si no tiene asignaciones: "Curso sin asignaciones".
    - La asignación del bloque debe existir, ser de ese curso y de la gestión abierta.
    - Día válido y hora final > hora inicial (lo valida el backend y lo asegura la BD).
    - Los choques de profesor, aula o curso los impide la BD (trigger): el backend muestra el
      mensaje con los nombres del docente, aula o curso que choca.
    - Modificar y eliminar un bloque (solo de la gestión abierta).

Precondición:
    La asignación existe y la gestión está abierta.

Postcondición:
    El bloque de horario queda registrado sin choques de profesor, aula ni curso en la misma gestión.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.errores import ErrorNegocio, NoEncontrado
from app.paquetes.academico.models import Gestion
from app.paquetes.horarios import politicas
from app.paquetes.horarios import repository as repo
from app.paquetes.horarios.models import Horario
from app.paquetes.horarios.schemas import (
    AsignacionBloqueSalida, CursoHorarioSalida, HorarioActualizar, HorarioCrear, HorarioCursoSalida, HorarioSalida,
)

DIAS = {"miercoles": "miércoles", "sabado": "sábado"}


async def cursos(sesion: AsyncSession) -> list[CursoHorarioSalida]:
    gestion = await politicas.exigir_gestion_abierta(sesion)
    return [CursoHorarioSalida.model_validate(c._asdict()) for c in await repo.cursos_con_avance(sesion, gestion.id_gestion)]


async def horario_curso(sesion: AsyncSession, id_curso: int) -> HorarioCursoSalida:
    gestion = await politicas.exigir_gestion_abierta(sesion)
    nombre = await repo.nombre_curso(sesion, id_curso)
    if nombre is None:
        raise NoEncontrado("Curso no encontrado.")
    return HorarioCursoSalida(
        id_curso=id_curso,
        nombre_curso=nombre,
        gestion=gestion.anio,
        asignaciones=[AsignacionBloqueSalida.model_validate(a._asdict())
                      for a in await repo.asignaciones_del_curso(sesion, id_curso, gestion.id_gestion)],
        bloques=[HorarioSalida.model_validate(b._asdict())
                 for b in await repo.bloques_del_curso(sesion, id_curso, gestion.id_gestion)],
    )


async def _guardar(sesion: AsyncSession, bloque: Horario, guardar) -> None:
    """Guarda dentro de un savepoint: si el trigger rechaza un choque, explica con nombres qué choca."""
    try:
        async with sesion.begin_nested():
            await guardar()
    except DBAPIError as e:
        causa = getattr(e.orig, "__cause__", None) or e.orig
        if getattr(causa, "sqlstate", None) != "P0001":
            raise
        choque = await repo.choque_horario(
            sesion, id_asignacion=bloque.id_asignacion_horario, dia=bloque.dia,
            hora_inicio=bloque.hora_inicio_h, hora_final=bloque.hora_final_f, id_horario=bloque.id_horario,
        )
        if choque is None:
            raise ErrorNegocio(getattr(causa, "message", str(causa))) from None
        franja = f"el {DIAS.get(bloque.dia, bloque.dia)} de {choque.hora_inicio:%H:%M} a {choque.hora_final:%H:%M}"
        motivo = {
            "docente": f"el docente {choque.profesor} ya tiene {choque.nombre_materia} en {choque.nombre_curso}",
            "aula": f"el aula {choque.aula} ya está ocupada por {choque.nombre_materia} de {choque.nombre_curso}",
            "curso": f"el curso ya tiene {choque.nombre_materia} en ese horario",
        }[choque.tipo]
        raise ErrorNegocio(f"Choque de horario {franja}: {motivo}.") from None


async def _salida(sesion: AsyncSession, id_horario: int) -> HorarioSalida:
    return HorarioSalida.model_validate((await repo.obtener_horario(sesion, id_horario))._asdict())


async def agregar(sesion: AsyncSession, id_curso: int, datos: HorarioCrear) -> HorarioSalida:
    gestion = await politicas.exigir_gestion_abierta(sesion)
    await politicas.asignacion_del_curso(sesion, datos.id_asignacion, id_curso, gestion)
    bloque = Horario(dia=datos.dia, hora_inicio_h=datos.hora_inicio, hora_final_f=datos.hora_final,
                     id_asignacion_horario=datos.id_asignacion)

    async def insertar():
        bloque.id_horario = await repo.crear_horario(sesion, datos)

    await _guardar(sesion, bloque, insertar)
    return await _salida(sesion, bloque.id_horario)


async def _bloque_de_gestion_abierta(sesion: AsyncSession, id_horario: int) -> tuple[Horario, int, Gestion]:
    gestion = await politicas.exigir_gestion_abierta(sesion)
    bloque = await sesion.get(Horario, id_horario)
    if bloque is None:
        raise NoEncontrado("No existe ese bloque de horario.")
    asignacion = await repo.datos_asignacion(sesion, bloque.id_asignacion_horario)
    if asignacion.id_gestion != gestion.id_gestion:
        raise ErrorNegocio("Solo se modifican horarios de la gestión abierta.")
    return bloque, asignacion.id_curso, gestion


async def modificar(sesion: AsyncSession, id_horario: int, datos: HorarioActualizar) -> HorarioSalida:
    bloque, id_curso, gestion = await _bloque_de_gestion_abierta(sesion, id_horario)
    cambios = datos.model_dump(exclude_unset=True)
    if cambios.get("id_asignacion") is not None:
        await politicas.asignacion_del_curso(sesion, cambios["id_asignacion"], id_curso, gestion)
    nuevo = Horario(
        id_horario=bloque.id_horario,
        dia=cambios.get("dia") or bloque.dia,
        hora_inicio_h=cambios.get("hora_inicio") or bloque.hora_inicio_h,
        hora_final_f=cambios.get("hora_final") or bloque.hora_final_f,
        id_asignacion_horario=cambios.get("id_asignacion") or bloque.id_asignacion_horario,
    )
    if nuevo.hora_final_f <= nuevo.hora_inicio_h:
        raise ErrorNegocio("La hora final debe ser posterior a la hora inicial.")

    async def actualizar():
        bloque.dia, bloque.hora_inicio_h = nuevo.dia, nuevo.hora_inicio_h
        bloque.hora_final_f, bloque.id_asignacion_horario = nuevo.hora_final_f, nuevo.id_asignacion_horario
        await sesion.flush()

    await _guardar(sesion, nuevo, actualizar)
    return await _salida(sesion, id_horario)


async def eliminar(sesion: AsyncSession, id_horario: int) -> None:
    bloque, _, _ = await _bloque_de_gestion_abierta(sesion, id_horario)
    await sesion.delete(bloque)
    await sesion.flush()

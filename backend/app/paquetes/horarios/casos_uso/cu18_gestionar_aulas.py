"""
CU18 - Gestionar aulas
Paquete: horarios

Actores ........: Administrador
Rol del sistema : administrador
Tablas .........: aula
Usa de la BD ...: —

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador (verificado en dependencias/router).
    - Número de aula único y capacidad > 0 (valida Pydantic y asegura la BD con UNIQUE y CHECK).
    - Estado solo: 'disponible', 'mantenimiento' o 'inactiva'.
    - No se puede ELIMINAR un aula que tiene asignaciones -> Conflicto (409) con el mensaje:
      "El aula tiene clases asignadas: márquela como inactiva".
    - Un aula en mantenimiento o inactiva no debe poder asignarse en CU14 / CU19.

Precondición:
    Sesión iniciada como administrador.

Postcondición:
    El aula queda registrada, actualizada o eliminada.

Flujo: router.py -> este caso de uso -> repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.errores import Conflicto, ErrorNegocio, NoEncontrado
from app.paquetes.horarios import repository as repo
from app.paquetes.horarios.schemas import AulaActualizar, AulaCrear, AulaSalida


async def listar_aulas(sesion: AsyncSession) -> list[AulaSalida]:
    """Lista todas las aulas con la cantidad de clases asignadas."""
    filas = await repo.listar_aulas_con_conteo(sesion)
    return [
        AulaSalida(
            id_aula=f.id_aula,
            numero=f.numero,
            capacidad=f.capacidad,
            tipo_aula=f.tipo_aula,
            estado_aula=f.estado_aula,
            total_clases_asignadas=f.total_clases_asignadas,
        )
        for f in filas
    ]


async def crear_aula(sesion: AsyncSession, datos: AulaCrear) -> AulaSalida:
    """Registra una nueva aula validando unicidad de número y capacidad."""
    if datos.capacidad <= 0:
        raise ErrorNegocio("La capacidad del aula debe ser mayor a 0.")

    numero_limpio = datos.numero.strip()
    existente = await repo.obtener_aula_por_numero(sesion, numero_limpio)
    if existente is not None:
        raise Conflicto("Ya existe un aula con ese número.")

    aula = await repo.crear_aula(sesion, datos)
    return AulaSalida(
        id_aula=aula.id_aula,
        numero=aula.numero,
        capacidad=aula.capacidad,
        tipo_aula=aula.tipo_aula,
        estado_aula=aula.estado_aula,
        total_clases_asignadas=0,
    )


async def editar_aula(sesion: AsyncSession, id_aula: int, datos: AulaActualizar) -> AulaSalida:
    """Modifica datos o estado de un aula existente."""
    aula = await repo.obtener_aula_por_id(sesion, id_aula)
    if aula is None:
        raise NoEncontrado("Aula no encontrada.")

    cambios = datos.model_dump(exclude_unset=True)
    if "capacidad" in cambios and cambios["capacidad"] is not None and cambios["capacidad"] <= 0:
        raise ErrorNegocio("La capacidad del aula debe ser mayor a 0.")

    if "numero" in cambios and cambios["numero"] is not None:
        numero_limpio = cambios["numero"].strip()
        existente = await repo.obtener_aula_por_numero(sesion, numero_limpio)
        if existente is not None and existente.id_aula != id_aula:
            raise Conflicto("Ya existe un aula con ese número.")

    aula_act = await repo.actualizar_aula(sesion, aula, datos)
    conteo = await repo.contar_asignaciones_aula(sesion, id_aula)
    return AulaSalida(
        id_aula=aula_act.id_aula,
        numero=aula_act.numero,
        capacidad=aula_act.capacidad,
        tipo_aula=aula_act.tipo_aula,
        estado_aula=aula_act.estado_aula,
        total_clases_asignadas=conteo,
    )


async def eliminar_aula(sesion: AsyncSession, id_aula: int) -> None:
    """Elimina un aula si no tiene clases asignadas."""
    aula = await repo.obtener_aula_por_id(sesion, id_aula)
    if aula is None:
        raise NoEncontrado("Aula no encontrada.")

    conteo = await repo.contar_asignaciones_aula(sesion, id_aula)
    if conteo > 0:
        raise Conflicto("El aula tiene clases asignadas: márquela como inactiva.")

    await repo.eliminar_aula(sesion, aula)

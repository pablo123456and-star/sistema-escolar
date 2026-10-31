"""
CU15 - Gestionar gestión académica (año lectivo)
Paquete: academico

Actores ........: Administrador
Rol del sistema : administrador
Tablas .........: gestion, periodo, dimension_evaluacion, inscripcion
Usa de la BD ...: Procedimiento sp_cerrar_gestion

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Una sola gestión abierta a la vez; el año coincide con el de la fecha de inicio.
    - El periodo debe estar dentro de las fechas de su gestión y no solaparse con otro periodo.
    - Las dimensiones de evaluación de una gestión suman 100: se pueden guardar incompletas
      (borrador) pero la gestión no se cierra hasta que sumen exactamente 100.
    - Las dimensiones no se reemplazan si ya hay calificaciones registradas con ellas.
    - Una gestión cerrada no admite cambios en sus periodos ni en sus dimensiones.
    - Cerrar la gestión: CALL sp_cerrar_gestion (promovido/reprobado de cada estudiante).
    - Resumen para el panel (inscritos, retirados, promedio, cobrado, vencido).

Precondición:
    Sesión iniciada como administrador. Para cerrar: la gestión está abierta.

Postcondición:
    La gestión, sus periodos y dimensiones quedan configurados. Al cerrarla, cada estudiante queda promovido o reprobado.

Flujo: router.py -> este caso de uso -> repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.errores import Conflicto, ErrorNegocio, NoEncontrado
from app.paquetes.academico import repository as repo
from app.paquetes.academico.schemas import (
    CierreGestionSalida, DimensionesGuardar, DimensionesSalida, DimensionSalida, GestionActualizar,
    GestionCrear, GestionSalida, PeriodoActualizar, PeriodoCrear, PeriodoSalida, ResumenGestionSalida,
)


def _fila(fila, modelo):
    return modelo.model_validate(fila._asdict())


async def _gestion(sesion: AsyncSession, id_gestion: int):
    fila = await repo.obtener_gestion_cu15(sesion, id_gestion)
    if fila is None:
        raise NoEncontrado("Gestión no encontrada.")
    return fila


async def _gestion_abierta(sesion: AsyncSession, id_gestion: int):
    gestion = await _gestion(sesion, id_gestion)
    if gestion.estado_gestion != "abierta":
        raise ErrorNegocio(f"La gestión {gestion.anio} está cerrada: ya no admite cambios.")
    return gestion


# ------------------------------------------------------------
# 1. GESTIONES
# ------------------------------------------------------------

async def listar_gestiones(sesion: AsyncSession) -> list[GestionSalida]:
    return [_fila(f, GestionSalida) for f in await repo.listar_gestiones_cu15(sesion)]


async def obtener_gestion(sesion: AsyncSession, id_gestion: int) -> GestionSalida:
    return _fila(await _gestion(sesion, id_gestion), GestionSalida)


async def crear_gestion(sesion: AsyncSession, datos: GestionCrear) -> GestionSalida:
    abierta = await repo.gestion_abierta_cu15(sesion)
    if abierta:
        raise Conflicto(f"Ya hay una gestión abierta ({abierta.anio}): ciérrela antes de crear otra.")
    id_gestion = await repo.crear_gestion_cu15(sesion, datos.model_dump())
    return await obtener_gestion(sesion, id_gestion)


async def actualizar_gestion(sesion: AsyncSession, id_gestion: int, datos: GestionActualizar) -> GestionSalida:
    actual = await _gestion_abierta(sesion, id_gestion)
    nuevos = {
        "anio": actual.anio,
        "fecha_inicio_g": actual.fecha_inicio_g,
        "fecha_final_g": actual.fecha_final_g,
        "nota_minima_aprobacion": actual.nota_minima_aprobacion,
        **datos.model_dump(exclude_unset=True, exclude_none=True),
    }
    if nuevos["fecha_final_g"] <= nuevos["fecha_inicio_g"]:
        raise ErrorNegocio("La fecha final debe ser posterior a la fecha de inicio.")
    if nuevos["fecha_inicio_g"].year != nuevos["anio"]:
        raise ErrorNegocio("El año debe coincidir con el año de la fecha de inicio.")
    fuera = [
        p.nombre_periodo
        for p in await repo.listar_periodos_cu15(sesion, id_gestion)
        if p.fecha_inicio_p < nuevos["fecha_inicio_g"] or p.fecha_final_p > nuevos["fecha_final_g"]
    ]
    if fuera:
        raise Conflicto(f"Las nuevas fechas dejan fuera de la gestión a: {', '.join(fuera)}.")
    await repo.actualizar_gestion_cu15(sesion, id_gestion, nuevos)
    return await obtener_gestion(sesion, id_gestion)


# ------------------------------------------------------------
# 2. PERIODOS
# ------------------------------------------------------------

async def _validar_periodo(sesion: AsyncSession, gestion, datos: dict, excepto: int | None = None) -> None:
    if datos["fecha_final_p"] <= datos["fecha_inicio_p"]:
        raise ErrorNegocio("La fecha final del periodo debe ser posterior a la de inicio.")
    if datos["fecha_inicio_p"] < gestion.fecha_inicio_g or datos["fecha_final_p"] > gestion.fecha_final_g:
        raise ErrorNegocio(
            f"El periodo debe estar dentro de la gestión {gestion.anio} "
            f"({gestion.fecha_inicio_g:%d/%m/%Y} al {gestion.fecha_final_g:%d/%m/%Y})."
        )
    otro = await repo.periodo_solapado_cu15(
        sesion, gestion.id_gestion, datos["fecha_inicio_p"], datos["fecha_final_p"], excepto
    )
    if otro:
        raise Conflicto(f"El periodo se solapa con «{otro}».")


async def listar_periodos(sesion: AsyncSession, id_gestion: int) -> list[PeriodoSalida]:
    await _gestion(sesion, id_gestion)
    return [_fila(f, PeriodoSalida) for f in await repo.listar_periodos_cu15(sesion, id_gestion)]


async def crear_periodo(sesion: AsyncSession, id_gestion: int, datos: PeriodoCrear) -> PeriodoSalida:
    gestion = await _gestion_abierta(sesion, id_gestion)
    valores = datos.model_dump()
    await _validar_periodo(sesion, gestion, valores)
    id_periodo = await repo.crear_periodo_cu15(sesion, id_gestion, valores)
    return _fila(await repo.obtener_periodo_cu15(sesion, id_periodo), PeriodoSalida)


async def _periodo(sesion: AsyncSession, id_periodo: int):
    periodo = await repo.obtener_periodo_cu15(sesion, id_periodo)
    if periodo is None:
        raise NoEncontrado("Periodo no encontrado.")
    return periodo


async def actualizar_periodo(sesion: AsyncSession, id_periodo: int, datos: PeriodoActualizar) -> PeriodoSalida:
    periodo = await _periodo(sesion, id_periodo)
    gestion = await _gestion_abierta(sesion, periodo.id_gestion_periodo)
    valores = {
        "nombre_periodo": periodo.nombre_periodo,
        "tipo": periodo.tipo,
        "fecha_inicio_p": periodo.fecha_inicio_p,
        "fecha_final_p": periodo.fecha_final_p,
        "observaciones_periodo": periodo.observaciones_periodo,
        **datos.model_dump(exclude_unset=True),
    }
    await _validar_periodo(sesion, gestion, valores, excepto=id_periodo)
    await repo.actualizar_periodo_cu15(sesion, id_periodo, valores)
    return _fila(await repo.obtener_periodo_cu15(sesion, id_periodo), PeriodoSalida)


async def eliminar_periodo(sesion: AsyncSession, id_periodo: int) -> None:
    periodo = await _periodo(sesion, id_periodo)
    await _gestion_abierta(sesion, periodo.id_gestion_periodo)
    n = await repo.calificaciones_en_periodo_cu15(sesion, id_periodo)
    if n:
        raise Conflicto(f"No se puede eliminar «{periodo.nombre_periodo}» porque tiene {n} calificaciones registradas.")
    await repo.eliminar_periodo_cu15(sesion, id_periodo)


# ------------------------------------------------------------
# 3. DIMENSIONES DE EVALUACIÓN
# ------------------------------------------------------------

async def _salida_dimensiones(sesion: AsyncSession, id_gestion: int) -> DimensionesSalida:
    filas = await repo.listar_dimensiones_cu15(sesion, id_gestion)
    suma = sum((f.puntaje_maximo for f in filas), Decimal(0))
    return DimensionesSalida(
        dimensiones=[_fila(f, DimensionSalida) for f in filas], suma_puntajes=suma, completa=suma == 100
    )


async def consultar_dimensiones(sesion: AsyncSession, id_gestion: int) -> DimensionesSalida:
    await _gestion(sesion, id_gestion)
    return await _salida_dimensiones(sesion, id_gestion)


async def guardar_dimensiones(sesion: AsyncSession, id_gestion: int, datos: DimensionesGuardar) -> DimensionesSalida:
    await _gestion_abierta(sesion, id_gestion)
    if await repo.notas_en_gestion_cu15(sesion, id_gestion):
        raise Conflicto("Ya hay calificaciones registradas con estas dimensiones: no se pueden reemplazar.")
    await repo.reemplazar_dimensiones_cu15(sesion, id_gestion, [d.model_dump() for d in datos.dimensiones])
    return await _salida_dimensiones(sesion, id_gestion)


# ------------------------------------------------------------
# 4. RESUMEN Y CIERRE
# ------------------------------------------------------------

async def resumen(sesion: AsyncSession, id_gestion: int) -> ResumenGestionSalida:
    gestion = await _gestion(sesion, id_gestion)
    r = await repo.resumen_gestion_cu15(sesion, id_gestion)
    return ResumenGestionSalida(id_gestion=id_gestion, anio=gestion.anio, **r._asdict())


async def cerrar_gestion(sesion: AsyncSession, id_gestion: int) -> CierreGestionSalida:
    gestion = await _gestion_abierta(sesion, id_gestion)
    dimensiones = await _salida_dimensiones(sesion, id_gestion)
    if not dimensiones.completa:
        raise ErrorNegocio(
            f"No se puede cerrar la gestión {gestion.anio}: las dimensiones de evaluación suman "
            f"{dimensiones.suma_puntajes} y deben sumar 100."
        )
    resultado = await repo.cerrar_gestion_cu15(sesion, id_gestion)
    return CierreGestionSalida(id_gestion=id_gestion, **resultado)

"""
CU26 - Gestionar inventario (registrar, actualizar, consultar bienes)
Paquete: administracion

Actores ........: Administrativo
Rol del sistema : administrador
Tablas .........: inventario, movimiento_inventario, administrativo
Usa de la BD ...: Trigger fn_tg_aplicar_movimiento (suma o resta el stock con cada movimiento),
                  CHECK de stock no negativo, UNIQUE del nombre, columna stock_minimo (script 11),
                  trigger de auditoría (bitácora)

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Un bien nuevo empieza con cantidad 0; el nombre no se repite (sin distinguir mayúsculas).
    - Del bien se corrigen el nombre, el stock mínimo y la observación; NUNCA la cantidad directa:
      el stock solo cambia registrando movimientos.
    - Movimiento: entrada o salida, cantidad > 0 y motivo; la salida además indica el destino.
    - No se puede sacar más de lo que hay: el backend lo verifica con la fila del bien bloqueada
      (dos salidas al mismo tiempo no sacan el mismo stock); la BD lo vuelve a asegurar.
    - Los movimientos no se editan ni se borran: se corrigen con un movimiento contrario.
    - El responsable del movimiento es el administrativo conectado.
    - Stock bajo: el bien avisa "stock bajo" cuando su cantidad llega a su stock mínimo
      (mínimo 0 = sin alerta) y "sin stock" cuando llega a 0.
    - Un bien solo se elimina si no tiene movimientos (registrado por error); con historial, no.

Precondición:
    Sesión iniciada como administrador. Para una salida: hay stock suficiente.

Postcondición:
    El bien queda registrado y su stock se actualiza con cada movimiento (queda en la bitácora).

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import Conflicto, ErrorNegocio, NoEncontrado
from app.nucleo.esquemas import Mensaje
from app.paquetes.administracion import politicas
from app.paquetes.administracion import repository as repo
from app.paquetes.administracion.models import Inventario, MovimientoInventario
from app.paquetes.administracion.schemas import (
    BienActualizar, BienCrear, BienSalida, EstadoStock, InventarioSalida, MovimientoCrear,
    MovimientoRegistradoSalida, MovimientosSalida, MovimientoSalida,
)


def _bien(fila) -> BienSalida:
    datos = fila._asdict()
    return BienSalida(**datos, estado=politicas.estado_stock(datos["cantidad"], datos["stock_minimo"]))


async def _bien_o_404(sesion: AsyncSession, id_inventario: int) -> BienSalida:
    filas = await repo.bienes_cu26(sesion, id_inventario=id_inventario)
    if not filas:
        raise NoEncontrado("No existe ese bien en el inventario.")
    return _bien(filas[0])


async def _nombre_libre(sesion: AsyncSession, nombre: str, excluir_id: int | None = None) -> None:
    if await repo.nombre_en_uso_cu26(sesion, nombre, excluir_id):
        raise Conflicto(f"Ya existe un bien llamado «{nombre}».")


# ------------------------------------------------------------
# 1. CONSULTAR BIENES
# ------------------------------------------------------------

async def listar(sesion: AsyncSession, buscar: str | None = None, estado: EstadoStock | None = None) -> InventarioSalida:
    bienes = [_bien(f) for f in await repo.bienes_cu26(sesion, buscar=(buscar or "").strip() or None)]
    if estado:
        bienes = [b for b in bienes if b.estado == estado]
    return InventarioSalida(
        bienes=bienes,
        total=len(bienes),
        sin_stock=sum(1 for b in bienes if b.estado == "sin_stock"),
        stock_bajo=sum(1 for b in bienes if b.estado == "bajo"),
    )


# ------------------------------------------------------------
# 2. REGISTRAR, CORREGIR Y ELIMINAR UN BIEN
# ------------------------------------------------------------

async def registrar(sesion: AsyncSession, datos: BienCrear) -> BienSalida:
    """El bien empieza con cantidad 0: el stock llega con la primera entrada."""
    await _nombre_libre(sesion, datos.nombre)
    bien = Inventario(
        nombre_inventario=datos.nombre, stock_minimo=datos.stock_minimo, observacion_inventario=datos.observacion
    )
    sesion.add(bien)
    await sesion.flush()
    return await _bien_o_404(sesion, bien.id_inventario)


async def actualizar(sesion: AsyncSession, id_inventario: int, datos: BienActualizar) -> BienSalida:
    """Corrige nombre, stock mínimo u observación. La cantidad no se toca (solo con movimientos)."""
    bien = await sesion.get(Inventario, id_inventario)
    if bien is None:
        raise NoEncontrado("No existe ese bien en el inventario.")
    cambios = datos.model_dump(exclude_unset=True)
    if "nombre" in cambios:
        await _nombre_libre(sesion, datos.nombre, id_inventario)
        bien.nombre_inventario = datos.nombre
    if "stock_minimo" in cambios:
        bien.stock_minimo = datos.stock_minimo
    if "observacion" in cambios:
        bien.observacion_inventario = datos.observacion
    await sesion.flush()
    return await _bien_o_404(sesion, id_inventario)


async def eliminar(sesion: AsyncSession, id_inventario: int) -> Mensaje:
    """Solo un bien sin movimientos (registrado por error). Con historial no se borra."""
    bien = await _bien_o_404(sesion, id_inventario)
    if bien.movimientos:
        raise Conflicto(
            f"«{bien.nombre}» tiene {bien.movimientos} movimiento(s) registrado(s): no se puede eliminar "
            "porque se perdería su historial."
        )
    await sesion.delete(await sesion.get(Inventario, id_inventario))
    await sesion.flush()
    return Mensaje(mensaje=f"Se eliminó «{bien.nombre}» del inventario.")


# ------------------------------------------------------------
# 3. MOVIMIENTOS (ENTRADAS Y SALIDAS)
# ------------------------------------------------------------

async def movimientos(sesion: AsyncSession, id_inventario: int) -> MovimientosSalida:
    bien = await _bien_o_404(sesion, id_inventario)
    filas = await repo.movimientos_cu26(sesion, id_inventario)
    return MovimientosSalida(bien=bien, movimientos=[MovimientoSalida.model_validate(f._asdict()) for f in filas])


async def registrar_movimiento(
    sesion: AsyncSession, usuario: UsuarioActual, id_inventario: int, datos: MovimientoCrear
) -> MovimientoRegistradoSalida:
    responsable = await politicas.responsable_inventario(sesion, usuario)
    bien = await repo.bien_bloqueado_cu26(sesion, id_inventario)
    if bien is None:
        raise NoEncontrado("No existe ese bien en el inventario.")
    if datos.tipo == "salida" and datos.cantidad > bien.cantidad_inventario:
        raise ErrorNegocio(
            f"Stock insuficiente de «{bien.nombre_inventario}»: hay {bien.cantidad_inventario} "
            f"y se quiere sacar {datos.cantidad}."
        )

    movimiento = MovimientoInventario(
        tipo_accion_inventario=datos.tipo, cantidad_movimiento=datos.cantidad, motivo_movimiento=datos.motivo,
        destino_movimiento=datos.destino, ci_administrativo_movimiento=responsable,
        id_inventario_movimiento=id_inventario,
    )
    sesion.add(movimiento)
    await sesion.flush()   # el trigger fn_tg_aplicar_movimiento actualiza el stock

    actualizado = await _bien_o_404(sesion, id_inventario)
    fila = (await repo.movimientos_cu26(sesion, id_inventario, movimiento.id_movimiento))[0]
    aviso = None
    if datos.tipo == "salida" and actualizado.estado == "sin_stock":
        aviso = f"«{actualizado.nombre}» se quedó sin stock."
    elif datos.tipo == "salida" and actualizado.estado == "bajo":
        aviso = (f"«{actualizado.nombre}» tiene stock bajo: quedan {actualizado.cantidad} "
                 f"(mínimo {actualizado.stock_minimo}).")
    return MovimientoRegistradoSalida(
        bien=actualizado, movimiento=MovimientoSalida.model_validate(fila._asdict()), aviso=aviso
    )

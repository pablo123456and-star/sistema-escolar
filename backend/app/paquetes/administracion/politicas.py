"""
Reglas de negocio comunes del paquete administracion (compartido).

    - Solo un administrativo cobra pagos y registra movimientos de inventario (queda como responsable).
    - Los pagos los ven el administrador, el propio estudiante y sus tutores (no los profesores).
    - Cada usuario ve solo los comunicados dirigidos a él (todos / su curso / su estudiante).

Las reglas propias de cada caso de uso están en el encabezado de su archivo en casos_uso/.

Implementado por ahora: lo que usa el CU25 (cajero administrativo, quién ve los pagos).
"""
# ============================================================
# CU25 - REGISTRAR PAGO DE MENSUALIDAD
# ============================================================

from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import ErrorNegocio, SinPermiso
from app.paquetes.administracion import repository as repo


async def cajero(sesion: AsyncSession, usuario: UsuarioActual) -> str:
    """CI del administrativo que cobra (el usuario conectado debe estar registrado como administrativo)."""
    if usuario.rol != "administrador" or not await repo.es_administrativo_cu25(sesion, usuario.ci):
        raise ErrorNegocio("Solo un administrativo registrado puede cobrar o corregir pagos.")
    return usuario.ci


async def pagos_visibles(sesion: AsyncSession, usuario: UsuarioActual, ci_estudiante: str) -> None:
    """Administrador: todos; estudiante: los suyos; tutor: los de sus estudiantes. Si no, 403."""
    if usuario.rol == "administrador":
        return
    if usuario.rol == "estudiante" and usuario.ci == ci_estudiante:
        return
    if usuario.rol == "tutor" and await repo.es_tutor_cu25(sesion, usuario.ci, ci_estudiante):
        return
    raise SinPermiso("Solo puede consultar los pagos propios o de sus estudiantes.")

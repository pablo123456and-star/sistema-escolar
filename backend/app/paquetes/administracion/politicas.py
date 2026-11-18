"""
Reglas de negocio comunes del paquete administracion (compartido).

    - Solo un administrativo cobra pagos y registra movimientos de inventario (queda como responsable).
    - Los pagos los ven el administrador, el propio estudiante y sus tutores (no los profesores).
    - Cada usuario ve solo los comunicados dirigidos a él (todos / su curso / su estudiante).

Las reglas propias de cada caso de uso están en el encabezado de su archivo en casos_uso/.

Implementado: lo que usa el CU25 (cajero administrativo, quién ve los pagos), el CU26 (responsable
del movimiento, estado del stock) y el CU27 (a quién puede publicar cada rol, quién ve el registro de lectura).
"""
# ============================================================
# CU25 - REGISTRAR PAGO DE MENSUALIDAD
# ============================================================

from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import ErrorNegocio, NoEncontrado, SinPermiso
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


# ============================================================
# CU26 - GESTIONAR INVENTARIO
# ============================================================

async def responsable_inventario(sesion: AsyncSession, usuario: UsuarioActual) -> str:
    """CI del administrativo que registra el movimiento (el usuario conectado debe estar registrado
    como administrativo: la FK de movimiento_inventario lo exige)."""
    if usuario.rol != "administrador" or not await repo.es_administrativo_cu25(sesion, usuario.ci):
        raise ErrorNegocio("Solo un administrativo registrado puede registrar entradas y salidas de inventario.")
    return usuario.ci


def estado_stock(cantidad: int, stock_minimo: int) -> str:
    """'sin_stock' si no queda nada; 'bajo' si llegó al mínimo (un mínimo de 0 = sin alerta); si no, 'normal'."""
    if cantidad == 0:
        return "sin_stock"
    if stock_minimo > 0 and cantidad <= stock_minimo:
        return "bajo"
    return "normal"


# ============================================================
# CU27 - GESTIONAR COMUNICADOS Y CITACIONES
# ============================================================

from app.paquetes.administracion.schemas import ComunicadoCrear  # noqa: E402

PUBLICAN = ("administrador", "profesor")


async def validar_destino(sesion: AsyncSession, usuario: UsuarioActual, datos: ComunicadoCrear, id_gestion: int) -> None:
    """Administrador: a todos, a cualquier curso o a cualquier estudiante inscrito.
    Profesor: solo a los cursos donde enseña o a sus estudiantes; nunca a 'todos'."""
    if usuario.rol not in PUBLICAN:
        raise SinPermiso("Solo el administrador y los docentes publican comunicados.")
    profesor = usuario.ci if usuario.rol == "profesor" else None

    if datos.alcance == "todos":
        if profesor:
            raise SinPermiso("Un docente no puede publicar a toda la comunidad: elija uno de sus cursos o estudiantes.")
        return

    if datos.alcance == "curso":
        if not await repo.cursos_destino_cu27(sesion, id_gestion, None, datos.id_curso):
            raise NoEncontrado("No existe ese curso.")
        if profesor and not await repo.cursos_destino_cu27(sesion, id_gestion, profesor, datos.id_curso):
            raise SinPermiso("Solo puede publicar a los cursos donde dicta clases.")
        return

    # alcance == "estudiante"
    if not await repo.estudiantes_destino_cu27(sesion, id_gestion, None, datos.ci_estudiante):
        raise NoEncontrado("El estudiante no tiene una inscripción activa en la gestión abierta.")
    if profesor and not await repo.estudiantes_destino_cu27(sesion, id_gestion, profesor, datos.ci_estudiante):
        raise SinPermiso("Solo puede enviar comunicados o citaciones a estudiantes de sus cursos.")


def puede_ver_lecturas_o_eliminar(usuario: UsuarioActual, comunicado) -> None:
    """El registro de lectura y la eliminación son del autor o del administrador."""
    if usuario.rol != "administrador" and not comunicado.es_mio:
        raise SinPermiso("Solo el autor del comunicado o el administrador pueden hacer esto.")

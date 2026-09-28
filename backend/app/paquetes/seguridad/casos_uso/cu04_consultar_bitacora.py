"""
CU04 - Consultar bitácora de actividades
Paquete: seguridad

Actores ........: Administrador
Rol del sistema : administrador
Tablas .........: bitacora, usuario
Usa de la BD ...: — (la BD impide editar o borrar la bitácora: fn_tg_bitacora_inmutable)

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Filtros por rango de fechas, módulo, tabla, usuario, operación y texto de la acción; paginado.
    - Solo lectura.
    - Nunca se muestran hashes de contraseñas: se ocultan en los datos antes/después.

Precondición:
    Sesión iniciada como administrador.

Postcondición:
    Se muestran los registros de auditoría filtrados. No se modifica nada.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.errores import ErrorNegocio
from app.nucleo.esquemas import Pagina
from app.paquetes.seguridad import repository as repo
from app.paquetes.seguridad.schemas import BitacoraSalida, OpcionesBitacoraSalida

CAMPOS_OCULTOS = {"password_hash"}


def _ocultar(datos: dict | None) -> dict | None:
    if not datos:
        return datos
    return {k: ("********" if k in CAMPOS_OCULTOS else v) for k, v in datos.items()}


async def listar(sesion: AsyncSession, *, desde: date | None, hasta: date | None, modulo: str | None,
                 tabla: str | None, operacion: str | None, usuario: str | None, texto: str | None,
                 pagina: int, tamano: int) -> Pagina[BitacoraSalida]:
    if desde and hasta and desde > hasta:
        raise ErrorNegocio("La fecha 'desde' no puede ser mayor que la fecha 'hasta'.")
    filas, total = await repo.listar_bitacora(
        sesion, desde=desde, hasta=hasta, modulo=modulo, tabla=tabla, operacion=operacion,
        usuario=usuario, texto=texto, pagina=pagina, tamano=tamano,
    )
    items = []
    for f in filas:
        d = f._asdict()
        d["datos_anteriores"] = _ocultar(d["datos_anteriores"])
        d["datos_nuevos"] = _ocultar(d["datos_nuevos"])
        items.append(BitacoraSalida.model_validate(d))
    return Pagina[BitacoraSalida](items=items, total=total, pagina=pagina, tamano=tamano)


async def opciones(sesion: AsyncSession) -> OpcionesBitacoraSalida:
    modulos, tablas, operaciones = await repo.opciones_bitacora(sesion)
    return OpcionesBitacoraSalida(modulos=modulos, tablas=tablas, operaciones=operaciones)

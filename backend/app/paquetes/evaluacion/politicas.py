"""
Reglas de negocio comunes del paquete evaluacion (compartido).

    - Un profesor solo registra asistencia y notas de SUS clases (asignaciones).
    - Un periodo 'cerrado' solo lo modifica el administrador.
    - Quién ve notas/asistencia/boletines: administrador (todo); profesor (sus estudiantes); tutor (sus estudiantes); estudiante (lo suyo).
    - Las fechas se validan con la hora de Bolivia (America/La_Paz).

Las reglas propias de cada caso de uso están en el encabezado de su archivo en casos_uso/.

Implementado por ahora: lo que usa el CU21 (clase propia, fecha válida, periodo cerrado).
"""
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import ErrorNegocio, NoEncontrado, SinPermiso
from app.paquetes.evaluacion import repository as repo


async def clase_propia(sesion: AsyncSession, usuario: UsuarioActual, id_asignacion: int):
    """La asignación existe y el usuario puede trabajar en ella (administrador o su profesor)."""
    clase = await repo.clase_cu21(sesion, id_asignacion)
    if clase is None:
        raise NoEncontrado("No existe esa clase (asignación de profesor).")
    if usuario.rol != "administrador" and clase.ci_profesor != usuario.ci:
        raise SinPermiso("Solo puede registrar la asistencia de sus propias clases.")
    return clase


async def validar_fecha(sesion: AsyncSession, clase, fecha: date) -> None:
    """La fecha no es futura (hora de Bolivia) y está dentro de la gestión de la clase."""
    if fecha > await repo.hoy(sesion):
        raise ErrorNegocio("No se puede registrar asistencia de una fecha futura.")
    if not clase.fecha_inicio_g <= fecha <= clase.fecha_final_g:
        raise ErrorNegocio(
            f"La fecha debe estar dentro de la gestión {clase.anio} "
            f"({clase.fecha_inicio_g:%d/%m/%Y} al {clase.fecha_final_g:%d/%m/%Y})."
        )


async def restriccion_edicion(sesion: AsyncSession, usuario: UsuarioActual, clase, fecha: date) -> ErrorNegocio | None:
    """Error que impide al usuario modificar la asistencia de esa fecha (None si puede).
    Se devuelve en lugar de lanzarse para que la consulta muestre el motivo sin fallar."""
    if clase.estado_gestion != "abierta":
        return ErrorNegocio(f"La gestión {clase.anio} está cerrada.")
    periodo = await repo.periodo_de_fecha_cu21(sesion, clase.id_gestion, fecha)
    if periodo and periodo.estado_periodo == "cerrado" and usuario.rol != "administrador":
        return SinPermiso(f"El {periodo.nombre_periodo} está cerrado: solo el administrador puede corregir su asistencia.")
    return None

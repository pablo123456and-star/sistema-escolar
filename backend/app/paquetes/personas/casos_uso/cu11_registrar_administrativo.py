"""
CU11 - Registrar personal administrativo
Paquete: personas

Actores ........: Administrador
Rol del sistema : administrador
Tablas .........: persona, administrativo, usuario
Usa de la BD ...: Trigger de auditoría de persona y administrativo

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Registrar persona + administrativo en una sola transacción (reutilizando la persona si ya existe,
      por ejemplo un tutor que ahora es administrativo). Error si el CI ya está registrado como administrativo.
    - Listar con búsqueda (nombre o CI) y filtro de estado (activo/inactivo).
    - Consultar detalle de administrativo (datos personales, cargo y si tiene usuario en el sistema).
    - Actualización parcial de datos personales y de cargo.
    - Dar de baja (baja lógica): persona y usuario asociados inactivos.
    - Reactivar: vuelve a activo (y su usuario asociado).

Precondición:
    Sesión iniciada como administrador.

Postcondición:
    El administrativo queda registrado y puede cobrar pagos, mover inventario y tener cuenta en el sistema.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.errores import Conflicto, NoEncontrado
from app.nucleo.esquemas import Pagina
from app.paquetes.personas import politicas
from app.paquetes.personas import repository as repo
from app.paquetes.personas.models import Administrativo, Persona
from app.paquetes.personas.schemas import (
    AdministrativoActualizar,
    AdministrativoCrear,
    AdministrativoDetalleSalida,
    AdministrativoSalida,
    PersonaSalida,
)


async def listar(
    sesion: AsyncSession, q: str | None, estado: str | None, pagina: int, tamano: int
) -> Pagina[AdministrativoSalida]:
    filas, total = await repo.listar_administrativos(sesion, q=q, estado=estado, pagina=pagina, tamano=tamano)
    return Pagina[AdministrativoSalida](
        items=[AdministrativoSalida.model_validate(f._asdict()) for f in filas],
        total=total,
        pagina=pagina,
        tamano=tamano,
    )


async def obtener(sesion: AsyncSession, ci: str) -> AdministrativoDetalleSalida:
    admin_obj = await _administrativo(sesion, ci)
    persona = await sesion.get(Persona, ci)
    return AdministrativoDetalleSalida(
        **PersonaSalida.model_validate(persona, from_attributes=True).model_dump(),
        cargo=admin_obj.cargo,
        tiene_usuario=await repo.tiene_usuario(sesion, ci),
    )


async def registrar(sesion: AsyncSession, datos: AdministrativoCrear) -> AdministrativoDetalleSalida:
    persona = await politicas.registrar_o_reutilizar(sesion, datos.persona)
    if await sesion.get(Administrativo, persona.ci) is not None:
        raise Conflicto("La persona ya está registrada como administrativo.")
    sesion.add(Administrativo(ci_administrativo=persona.ci, cargo=datos.cargo))
    await sesion.flush()
    return await obtener(sesion, persona.ci)


async def actualizar(sesion: AsyncSession, ci: str, datos: AdministrativoActualizar) -> AdministrativoDetalleSalida:
    admin_obj = await _administrativo(sesion, ci)
    if datos.persona is not None:
        politicas.aplicar_cambios(await sesion.get(Persona, ci), datos.persona)
    if "cargo" in datos.model_fields_set:
        admin_obj.cargo = datos.cargo
    await sesion.flush()
    return await obtener(sesion, ci)


async def dar_baja(sesion: AsyncSession, ci: str, motivo: str) -> AdministrativoDetalleSalida:
    await _administrativo(sesion, ci)
    await politicas.dar_baja(sesion, ci, motivo)
    return await obtener(sesion, ci)


async def reactivar(sesion: AsyncSession, ci: str) -> AdministrativoDetalleSalida:
    await _administrativo(sesion, ci)
    await politicas.reactivar(sesion, ci)
    return await obtener(sesion, ci)


async def _administrativo(sesion: AsyncSession, ci: str) -> Administrativo:
    admin_obj = await sesion.get(Administrativo, ci)
    if admin_obj is None:
        raise NoEncontrado("No existe un personal administrativo con ese CI.")
    return admin_obj

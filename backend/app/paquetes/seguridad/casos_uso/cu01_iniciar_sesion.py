"""
CU01 - Iniciar sesión (incluye recuperar contraseña)
Paquete: seguridad

Actores ........: Todos
Rol del sistema : administrador, profesor, estudiante, tutor
Tablas .........: usuario, rol, persona, bitacora
Usa de la BD ...: Trigger de auditoría de usuario (registra el acceso al actualizar ultimo_acceso)
                  y fn_registrar_bitacora (solicitudes de recuperación)

Reglas de negocio que implementa este caso de uso (backend):
    - Buscar el usuario por nombre_usuario o correo y verificar la contraseña contra password_hash (bcrypt).
    - Usuario o contraseña incorrectos: el mismo mensaje en ambos casos (no revela qué usuarios existen).
    - Rechazar si el usuario no está 'activo' o su persona está 'inactivo'.
    - Emitir un token JWT con id_usuario y rol (nucleo/seguridad.py) y actualizar ultimo_acceso.
      "Recordar sesión" emite un token de mayor duración.
    - Cerrar sesión: el frontend descarta el token.
    - Cambiar la propia contraseña: exige la contraseña actual.
    - Recuperar contraseña (flujo alternativo): el usuario indica su usuario o correo; si la cuenta
      existe y está activa, la solicitud queda en la bitácora para que el Administrador restablezca la
      contraseña (CU02). La respuesta es siempre la misma, exista o no la cuenta.

Precondición:
    El usuario existe, está 'activo' y su persona está 'activo'.

Postcondición:
    El usuario recibe un token válido; el sistema conoce su rol y le muestra el menú que le corresponde.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.bd import identificar
from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import ErrorNegocio, NoEncontrado
from app.nucleo.seguridad import crear_token, hash_contrasena, verificar_contrasena
from app.paquetes.seguridad import repository as repo
from app.paquetes.seguridad.models import Usuario
from app.paquetes.seguridad.politicas import ACCION_CAMBIO_PROPIO, ACCION_SOLICITUD
from app.paquetes.seguridad.schemas import (
    ActividadSalida, CambiarContrasenaEntrada, IniciarSesionEntrada, PerfilSalida, ResumenInicioSalida,
    SesionSalida,
)

MENSAJE_CREDENCIALES = "Usuario o contraseña incorrectos."
MENSAJE_RECUPERACION = (
    "Si la cuenta existe y está activa, su solicitud fue enviada al administrador, "
    "quien le entregará una contraseña temporal."
)


async def obtener_perfil(sesion: AsyncSession, id_usuario: int) -> PerfilSalida:
    fila = await repo.perfil(sesion, id_usuario)
    if fila is None:
        raise NoEncontrado("Usuario no encontrado.")
    return PerfilSalida.model_validate(fila._asdict())


async def iniciar_sesion(sesion: AsyncSession, datos: IniciarSesionEntrada) -> SesionSalida:
    candidatos = await repo.buscar_para_login(sesion, datos.identificador)
    # Un correo compartido por varias cuentas no sirve para identificar a una sola
    cuenta = candidatos[0] if len(candidatos) == 1 else None
    if not verificar_contrasena(datos.contrasena, cuenta.password_hash if cuenta else None):
        raise ErrorNegocio(MENSAJE_CREDENCIALES, "credenciales")
    if cuenta.estado_usuario != "activo" or cuenta.estado_persona != "activo":
        raise ErrorNegocio("La cuenta está inactiva o bloqueada. Comuníquese con el administrador.", "cuenta_inactiva")

    # Desde aquí la bitácora registra las acciones a nombre de este usuario
    await identificar(sesion, cuenta.id_usuario)
    await sesion.execute(
        update(Usuario).where(Usuario.id_usuario == cuenta.id_usuario).values(ultimo_acceso=func.now())
    )
    token, expira = crear_token(cuenta.id_usuario, cuenta.nombre_rol, datos.recordar)
    return SesionSalida(token=token, expira=expira, usuario=await obtener_perfil(sesion, cuenta.id_usuario))


async def cambiar_contrasena(sesion: AsyncSession, usuario: UsuarioActual, datos: CambiarContrasenaEntrada) -> None:
    cuenta = await sesion.get(Usuario, usuario.id_usuario)
    if not verificar_contrasena(datos.actual, cuenta.password_hash):
        raise ErrorNegocio("La contraseña actual no es correcta.")
    if datos.actual == datos.nueva:
        raise ErrorNegocio("La nueva contraseña debe ser distinta de la actual.")
    cuenta.password_hash = hash_contrasena(datos.nueva)
    await sesion.flush()
    await repo.registrar_en_bitacora(sesion, ACCION_CAMBIO_PROPIO, "UPDATE", "usuario", str(cuenta.id_usuario))


async def solicitar_recuperacion(sesion: AsyncSession, identificador: str) -> str:
    candidatos = await repo.buscar_para_login(sesion, identificador)
    if len(candidatos) == 1:
        cuenta = candidatos[0]
        if cuenta.estado_usuario == "activo" and cuenta.estado_persona == "activo":
            await identificar(sesion, cuenta.id_usuario)
            await repo.registrar_en_bitacora(sesion, ACCION_SOLICITUD, "OTRO", "usuario", str(cuenta.id_usuario))
    return MENSAJE_RECUPERACION


async def resumen_inicio(sesion: AsyncSession, usuario: UsuarioActual) -> ResumenInicioSalida:
    """Datos del panel de inicio. Las actividades recientes solo las ve el administrador."""
    r = await repo.resumen_inicio(sesion)
    actividades = []
    if usuario.rol == "administrador":
        actividades = [ActividadSalida.model_validate(a._asdict()) for a in await repo.actividades_recientes(sesion)]
    return ResumenInicioSalida(**r._asdict(), actividades=actividades)

"""
CU01 - Iniciar sesión, bloqueo temporal por intentos fallidos y recuperación por correo
Paquete: seguridad

Actores ........: Todos
Rol del sistema : administrador, profesor, estudiante, tutor
Tablas .........: usuario, rol, persona, token_recuperacion, bitacora
Usa de la BD ...: Trigger de auditoría de usuario (registra el acceso al actualizar ultimo_acceso)
                  y fn_registrar_bitacora (solicitudes y restablecimiento de contraseña)

Reglas de negocio que implementa este caso de uso (backend):
    - Protección contra fuerza bruta:
      * 3 intentos fallidos seguidos bloquean la cuenta temporalmente. Son "seguidos" si entre
        uno y otro pasan menos de 15 minutos (los fallos de días anteriores no se suman).
      * Después de cada bloqueo hay otra vez 3 intentos; si vuelve a fallar, el bloqueo escala:
        1er bloqueo: 15 min, 2do: 30 min, 3er: 1 hora, 4to: 2 horas, 5to en adelante: 24 horas.
      * Tras 24 horas sin fallos (desde que terminó el último bloqueo) se vuelve al primer nivel.
      * Un inicio de sesión exitoso o recuperar la contraseña por correo reinicia el contador y el nivel.
      * Mensajes claros con tiempo restante cuando la cuenta está bloqueada temporalmente.
      * Respuestas genéricas cuando las credenciales no coinciden (no revela si existe el usuario).
    - Autenticación:
      * Buscar por nombre_usuario o correo y verificar contra password_hash (bcrypt).
      * Rechazar cuentas inactivas o personas dadas de baja.
      * Emitir JWT con id_usuario y rol (expiración estándar o extendida si marca "Recordar").
    - Recuperación segura por correo electrónico:
      * Solicitud mediante correo electrónico vinculado a la cuenta.
      * Token criptográfico aleatorio de un solo uso con caducidad estricta (15 minutos).
      * El token se almacena en BD protegido con hash SHA-256 (nunca en texto plano).
      * Envío real por SMTP o emulación visible en consola en entorno de desarrollo.
      * Respuesta genérica para evitar la enumeración de cuentas.
      * Nueva contraseña debe cumplir requisitos de seguridad (mínimo 8 caracteres, números,
        mayúsculas, minúsculas y caracteres especiales).
      * Al restablecer: se consume el token inmediatamente, se restablecen los intentos fallidos
        y se registra en la bitácora.
    - Cambio de contraseña propio desde el perfil: exige la contraseña actual y valida la nueva.

Precondición:
    El usuario existe, está 'activo' y su persona está 'activo'.

Postcondición:
    El usuario recibe un token válido; el sistema conoce su rol y le muestra el menú que le corresponde.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.bd import identificar
from app.nucleo.config import obtener_config
from app.nucleo.correo import enviar_correo_recuperacion
from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import ErrorNegocio, NoEncontrado
from app.nucleo.seguridad import (
    crear_token, formatear_tiempo_restante, generar_token_recuperacion, registrar_fallo,
    hash_contrasena, hashear_token, verificar_contrasena,
)
from app.paquetes.seguridad import repository as repo
from app.paquetes.seguridad.models import Usuario
from app.paquetes.seguridad.politicas import (
    ACCION_CAMBIO_PROPIO, ACCION_RESTABLECIDA_CORREO, ACCION_SOLICITUD,
)
from app.paquetes.seguridad.schemas import (
    ActividadSalida, CambiarContrasenaEntrada, IniciarSesionEntrada, PerfilSalida,
    RestablecerContrasenaEntrada, ResumenInicioSalida, SesionSalida, ValidarTokenSalida,
)

MENSAJE_CREDENCIALES = "Usuario o contraseña incorrectos."
MENSAJE_RECUPERACION_GENERICO = (
    "Si el correo electrónico está vinculado a una cuenta activa, hemos enviado "
    "las instrucciones para restablecer su contraseña. Revise su bandeja de entrada (y la carpeta de spam)."
)


async def obtener_perfil(sesion: AsyncSession, id_usuario: int) -> PerfilSalida:
    fila = await repo.perfil(sesion, id_usuario)
    if fila is None:
        raise NoEncontrado("Usuario no encontrado.")
    return PerfilSalida.model_validate(fila._asdict())


async def iniciar_sesion(sesion: AsyncSession, datos: IniciarSesionEntrada, ip_cliente: str | None = None) -> SesionSalida:
    candidatos = await repo.buscar_para_login(sesion, datos.identificador)
    cuenta = candidatos[0] if len(candidatos) == 1 else None
    ahora = datetime.now(UTC)

    # 1. Si la cuenta existe, verificar si está bajo bloqueo temporal por intentos fallidos
    if cuenta:
        if cuenta.bloqueado_hasta:
            bh = cuenta.bloqueado_hasta
            if bh.tzinfo is None:
                bh = bh.replace(tzinfo=UTC)
            if ahora < bh:
                segundos_restantes = int((bh - ahora).total_seconds())
                tiempo_txt = formatear_tiempo_restante(segundos_restantes)
                raise ErrorNegocio(
                    f"Cuenta bloqueada temporalmente por intentos fallidos. Intente de nuevo en {tiempo_txt}.",
                    "cuenta_bloqueada",
                )

    # 2. Comprobación de contraseña
    password_ok = verificar_contrasena(datos.contrasena, cuenta.password_hash if cuenta else None)

    if not password_ok:
        if cuenta:
            # Solo se suman los fallos seguidos; al tercero se bloquea con el siguiente nivel
            intentos, nivel, bloqueado_hasta = registrar_fallo(
                ahora, cuenta.intentos_fallidos, cuenta.bloqueos_consecutivos,
                cuenta.ultimo_intento_fallido, cuenta.bloqueado_hasta,
            )
            await repo.registrar_intento_fallido(sesion, cuenta.id_usuario, intentos, bloqueado_hasta, nivel)
            await sesion.commit()
            if bloqueado_hasta:
                tiempo_bloqueo = formatear_tiempo_restante(int((bloqueado_hasta - ahora).total_seconds()))
                raise ErrorNegocio(
                    "Cuenta bloqueada temporalmente por 3 intentos fallidos seguidos. "
                    f"Debe esperar {tiempo_bloqueo} antes de volver a intentarlo "
                    "o recuperar su contraseña con «¿Olvidaste tu contraseña?».",
                    "cuenta_bloqueada",
                )
        raise ErrorNegocio(MENSAJE_CREDENCIALES, "credenciales")

    # 3. Contraseña correcta: verificar estado general de la cuenta y persona
    if cuenta.estado_usuario != "activo" or cuenta.estado_persona != "activo":
        raise ErrorNegocio(
            "La cuenta está inactiva o bloqueada por la administración. Comuníquese con la dirección.",
            "cuenta_inactiva",
        )

    # 4. Éxito: restablecer contadores de intentos fallidos y bloqueos
    await repo.restablecer_intentos(sesion, cuenta.id_usuario)

    # 5. Registrar acceso e identidad para bitácora
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


async def solicitar_recuperacion(sesion: AsyncSession, correo_o_identificador: str, ip_cliente: str | None = None) -> str:
    """Procesa una solicitud de recuperación de contraseña de forma segura."""
    cfg = obtener_config()
    ahora = datetime.now(UTC)

    ident = correo_o_identificador.strip()
    # Buscar cuentas asociadas
    cuentas = await repo.buscar_cuentas_por_correo(sesion, ident)
    if not cuentas:
        # Intentar también por nombre de usuario si no vino como email exacto
        candidatos = await repo.buscar_para_login(sesion, ident)
        cuentas = [c for c in candidatos if c.email and c.estado_usuario == "activo" and c.estado_persona == "activo"]

    for cuenta in cuentas:
        if not cuenta.email:
            continue
        token_plano, token_hash = generar_token_recuperacion()
        expira_en = ahora + timedelta(minutes=cfg.TOKEN_RECUPERACION_MINUTOS)
        await repo.crear_token_recuperacion(sesion, cuenta.id_usuario, token_hash, expira_en, ip_cliente)

        enlace = f"{cfg.FRONTEND_URL.rstrip('/')}/restablecer-contrasena?token={token_plano}"
        nombre = f"{cuenta.nombres} {cuenta.apellidos}".strip()
        await enviar_correo_recuperacion(cuenta.email, nombre, enlace, cfg.TOKEN_RECUPERACION_MINUTOS)

        # Registrar en bitácora la solicitud
        await identificar(sesion, cuenta.id_usuario)
        await repo.registrar_en_bitacora(sesion, ACCION_SOLICITUD, "OTRO", "usuario", str(cuenta.id_usuario))

    return MENSAJE_RECUPERACION_GENERICO


async def validar_token_recuperacion(sesion: AsyncSession, token_plano: str) -> ValidarTokenSalida:
    """Comprueba si un enlace de recuperación sigue siendo válido."""
    if not token_plano or len(token_plano) < 10:
        return ValidarTokenSalida(valido=False, mensaje="El enlace de recuperación es inválido.")

    token_hash = hashear_token(token_plano.strip())
    registro = await repo.obtener_token_recuperacion(sesion, token_hash)
    if not registro:
        return ValidarTokenSalida(valido=False, mensaje="El enlace de recuperación no es válido o ya no existe.")

    if registro.usado:
        return ValidarTokenSalida(valido=False, mensaje="Este enlace de recuperación ya ha sido utilizado.")

    ahora = datetime.now(UTC)
    exp = registro.expira_en
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=UTC)

    if ahora > exp:
        return ValidarTokenSalida(
            valido=False,
            mensaje="El enlace de recuperación ha caducado (duración máxima de 15 minutos). Por favor solicite uno nuevo.",
        )

    if registro.estado_usuario != "activo":
        return ValidarTokenSalida(valido=False, mensaje="La cuenta de usuario se encuentra inactiva o deshabilitada.")

    nombre_completo = f"{registro.nombres} {registro.apellidos}".strip()
    return ValidarTokenSalida(
        valido=True,
        nombre_usuario=registro.nombre_usuario,
        nombre_completo=nombre_completo,
        mensaje="Enlace válido. Puede definir su nueva contraseña.",
    )


async def restablecer_contrasena_con_token(
    sesion: AsyncSession, datos: RestablecerContrasenaEntrada, ip_cliente: str | None = None
) -> str:
    """Consume el token de recuperación y establece la nueva contraseña segura."""
    token_hash = hashear_token(datos.token.strip())
    registro = await repo.obtener_token_recuperacion(sesion, token_hash)
    if not registro or registro.usado:
        raise ErrorNegocio("El enlace de recuperación no es válido o ya fue utilizado.", "token_invalido")

    ahora = datetime.now(UTC)
    exp = registro.expira_en
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=UTC)

    if ahora > exp:
        raise ErrorNegocio("El enlace de recuperación ha caducado. Por favor solicite uno nuevo.", "token_expirado")

    cuenta = await sesion.get(Usuario, registro.id_usuario)
    if not cuenta or cuenta.estado_usuario != "activo":
        raise ErrorNegocio("La cuenta no se encuentra activa para restablecer su contraseña.", "cuenta_inactiva")

    # 1. Invalidar el token inmediatamente (de un solo uso)
    await repo.consumir_token_recuperacion(sesion, registro.id_recuperacion)

    # 2. Guardar la nueva contraseña hasheada con bcrypt
    cuenta.password_hash = hash_contrasena(datos.nueva)

    # 3. Restablecer contadores de intentos fallidos y bloqueos
    await repo.restablecer_intentos(sesion, cuenta.id_usuario)

    # 4. Registrar en bitácora
    await identificar(sesion, cuenta.id_usuario)
    await repo.registrar_en_bitacora(sesion, ACCION_RESTABLECIDA_CORREO, "UPDATE", "usuario", str(cuenta.id_usuario))

    return "Su contraseña ha sido restablecida exitosamente. Ya puede iniciar sesión con su nueva credencial."


async def resumen_inicio(sesion: AsyncSession, usuario: UsuarioActual) -> ResumenInicioSalida:
    """Datos del panel de inicio. Las actividades recientes solo las ve el administrador."""
    r = await repo.resumen_inicio(sesion)
    actividades = []
    if usuario.rol == "administrador":
        actividades = [ActividadSalida.model_validate(a._asdict()) for a in await repo.actividades_recientes(sesion)]
    return ResumenInicioSalida(**r._asdict(), actividades=actividades)

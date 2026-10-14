"""
Acceso a la base de datos del paquete seguridad (compartido).

Consultas y escrituras con SQLAlchemy sobre las tablas de models.py.
"""
from datetime import UTC, date, datetime

from sqlalchemy import Date, and_, cast, func, or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.paquetes.personas.models import Administrativo, Persona
from app.paquetes.seguridad.models import Bitacora, Rol, TokenRecuperacion, Usuario
from app.paquetes.seguridad.politicas import (
    ACCION_CAMBIO_PROPIO, ACCION_RESTABLECIDA, ACCION_SOLICITUD, ESPECIALIZACION,
)


def _columnas_usuario():
    return (
        Usuario.id_usuario, Usuario.nombre_usuario, Usuario.estado_usuario, Usuario.ultimo_acceso,
        Usuario.creado_en, Rol.id_rol, Rol.nombre_rol, Persona.ci, Persona.expedido,
        Persona.nombre_persona.label("nombres"), Persona.apellidos, Persona.email,
    )


def _base_usuarios():
    return (
        select(*_columnas_usuario())
        .join(Rol, Rol.id_rol == Usuario.id_rol_usuario)
        .join(Persona, Persona.ci == Usuario.ci_persona)
    )


# ---- CU01 -------------------------------------------------------------------
async def buscar_para_login(sesion: AsyncSession, identificador: str):
    """Usuarios cuyo nombre de usuario o correo coincide (sin distinguir mayúsculas)."""
    ident = identificador.strip().lower()
    consulta = (
        select(
            Usuario.id_usuario,
            Usuario.nombre_usuario,
            Usuario.password_hash,
            Usuario.estado_usuario,
            Usuario.intentos_fallidos,
            Usuario.bloqueado_hasta,
            Usuario.bloqueos_consecutivos,
            Rol.nombre_rol,
            Persona.estado_persona,
            Persona.nombre_persona.label("nombres"),
            Persona.apellidos,
            Persona.email,
        )
        .join(Rol, Rol.id_rol == Usuario.id_rol_usuario)
        .join(Persona, Persona.ci == Usuario.ci_persona)
        .where(or_(func.lower(Usuario.nombre_usuario) == ident, func.lower(Persona.email) == ident))
    )
    return (await sesion.execute(consulta)).all()


async def perfil(sesion: AsyncSession, id_usuario: int):
    consulta = (
        select(
            Usuario.id_usuario, Usuario.nombre_usuario, Rol.nombre_rol.label("rol"), Persona.ci,
            Persona.nombre_persona.label("nombres"), Persona.apellidos, Persona.email,
            Administrativo.cargo, Usuario.ultimo_acceso,
        )
        .join(Rol, Rol.id_rol == Usuario.id_rol_usuario)
        .join(Persona, Persona.ci == Usuario.ci_persona)
        .outerjoin(Administrativo, Administrativo.ci_administrativo == Persona.ci)
        .where(Usuario.id_usuario == id_usuario)
    )
    return (await sesion.execute(consulta)).one_or_none()


async def resumen_inicio(sesion: AsyncSession):
    return (
        await sesion.execute(
            text(
                """SELECT (SELECT count(*) FROM usuario WHERE estado_usuario = 'activo')          AS usuarios_activos,
                          (SELECT count(*) FROM estudiante e JOIN persona p ON p.ci = e.ci_estudiante
                            WHERE p.estado_persona = 'activo')                                    AS estudiantes_activos,
                          (SELECT count(*) FROM tutor)                                            AS tutores,
                          (SELECT count(*) FROM curso)                                            AS cursos,
                          (SELECT 'Gestión ' || anio FROM gestion WHERE estado_gestion = 'abierta'
                            ORDER BY anio DESC LIMIT 1)                                           AS gestion"""
            )
        )
    ).one()


async def actividades_recientes(sesion: AsyncSession, cantidad: int = 6):
    consulta = (
        select(Bitacora.fecha_hora, Bitacora.accion, Bitacora.modulo, Usuario.nombre_usuario)
        .outerjoin(Usuario, Usuario.id_usuario == Bitacora.id_usuario_bitacora)
        .order_by(Bitacora.id_bitacora.desc())
        .limit(cantidad)
    )
    return (await sesion.execute(consulta)).all()


# ---- CU02 -------------------------------------------------------------------
async def listar_usuarios(sesion: AsyncSession, q: str | None, id_rol: int | None, estado: str | None,
                          pagina: int, tamano: int):
    filtros = []
    if q:
        patron = f"%{q.strip().lower()}%"
        filtros.append(or_(
            func.lower(Usuario.nombre_usuario).like(patron),
            func.lower(Persona.nombre_persona + " " + Persona.apellidos).like(patron),
            func.lower(func.coalesce(Persona.email, "")).like(patron),
            Persona.ci.like(patron),
        ))
    if id_rol:
        filtros.append(Usuario.id_rol_usuario == id_rol)
    if estado:
        filtros.append(Usuario.estado_usuario == estado)
    base = _base_usuarios().where(and_(*filtros))
    total = await sesion.scalar(select(func.count()).select_from(base.subquery()))
    filas = (
        await sesion.execute(
            base.order_by(Persona.apellidos, Persona.nombre_persona).offset((pagina - 1) * tamano).limit(tamano)
        )
    ).all()
    return filas, total or 0


async def usuario_detalle(sesion: AsyncSession, id_usuario: int):
    return (await sesion.execute(_base_usuarios().where(Usuario.id_usuario == id_usuario))).one_or_none()


async def personas_sin_cuenta(sesion: AsyncSession, nombre_rol: str, q: str | None, limite: int = 20):
    """Personas activas con la especialización del rol y sin cuenta de usuario."""
    tabla, columna, _ = ESPECIALIZACION[nombre_rol]
    consulta = (
        select(Persona.ci, Persona.nombre_persona.label("nombres"), Persona.apellidos, Persona.email)
        .join(tabla, columna == Persona.ci)
        .outerjoin(Usuario, Usuario.ci_persona == Persona.ci)
        .where(Usuario.id_usuario.is_(None), Persona.estado_persona == "activo")
    )
    if q:
        patron = f"%{q.strip().lower()}%"
        consulta = consulta.where(or_(
            func.lower(Persona.nombre_persona + " " + Persona.apellidos).like(patron), Persona.ci.like(patron)
        ))
    return (await sesion.execute(consulta.order_by(Persona.apellidos).limit(limite))).all()


async def solicitudes_pendientes(sesion: AsyncSession, dias: int = 7):
    """Solicitudes de recuperación de los últimos días que aún no fueron atendidas
    (sin contraseña restablecida o cambiada después). Una por usuario, la más reciente."""
    filas = (
        await sesion.execute(
            text(
                """SELECT DISTINCT ON (u.id_usuario)
                          b.id_bitacora, b.fecha_hora, u.id_usuario, u.nombre_usuario,
                          p.nombre_persona AS nombres, p.apellidos, host(b.ip) AS ip
                     FROM bitacora b
                     JOIN usuario u ON u.id_usuario = b.id_usuario_bitacora
                     JOIN persona p ON p.ci = u.ci_persona
                    WHERE b.accion = :solicitud
                      AND b.fecha_hora > now() - make_interval(days => :dias)
                      AND NOT EXISTS (SELECT 1 FROM bitacora r
                                       WHERE r.accion IN (:restablecida, :cambio)
                                         AND r.registro_id = u.id_usuario::text
                                         AND r.fecha_hora >= b.fecha_hora)
                    ORDER BY u.id_usuario, b.fecha_hora DESC"""
            ),
            {"solicitud": ACCION_SOLICITUD, "restablecida": ACCION_RESTABLECIDA,
             "cambio": ACCION_CAMBIO_PROPIO, "dias": dias},
        )
    ).all()
    return sorted(filas, key=lambda f: f.fecha_hora, reverse=True)


# ---- CU03 -------------------------------------------------------------------
async def roles_con_conteo(sesion: AsyncSession):
    consulta = (
        select(
            Rol.id_rol, Rol.nombre_rol, Rol.descripcion_rol,
            func.count(Usuario.id_usuario).filter(Usuario.estado_usuario == "activo").label("usuarios_activos"),
            func.count(Usuario.id_usuario).label("usuarios_total"),
        )
        .outerjoin(Usuario, Usuario.id_rol_usuario == Rol.id_rol)
        .group_by(Rol.id_rol)
        .order_by(Rol.id_rol)
    )
    return (await sesion.execute(consulta)).all()


# ---- CU04 -------------------------------------------------------------------
async def listar_bitacora(sesion: AsyncSession, *, desde: date | None, hasta: date | None,
                          modulo: str | None, tabla: str | None, operacion: str | None, usuario: str | None,
                          texto: str | None, pagina: int, tamano: int):
    filtros = []
    # cast a date usa la zona horaria de la sesión (America/La_Paz)
    if desde:
        filtros.append(cast(Bitacora.fecha_hora, Date) >= desde)
    if hasta:
        filtros.append(cast(Bitacora.fecha_hora, Date) <= hasta)
    if modulo:
        filtros.append(Bitacora.modulo == modulo)
    if tabla:
        filtros.append(Bitacora.tabla_afectada == tabla)
    if operacion:
        filtros.append(Bitacora.operacion == operacion)
    if usuario:
        filtros.append(func.lower(Usuario.nombre_usuario).like(f"%{usuario.strip().lower()}%"))
    if texto:
        filtros.append(func.lower(Bitacora.accion).like(f"%{texto.strip().lower()}%"))
    base = (
        select(
            Bitacora.id_bitacora, Bitacora.fecha_hora, Bitacora.accion, Bitacora.operacion,
            Bitacora.tabla_afectada, Bitacora.registro_id, Bitacora.modulo, func.host(Bitacora.ip).label("ip"),
            Bitacora.id_usuario_bitacora.label("id_usuario"), Usuario.nombre_usuario,
            Bitacora.datos_anteriores, Bitacora.datos_nuevos,
        )
        .outerjoin(Usuario, Usuario.id_usuario == Bitacora.id_usuario_bitacora)
        .where(and_(*filtros))
    )
    total = await sesion.scalar(select(func.count()).select_from(base.subquery()))
    filas = (
        await sesion.execute(base.order_by(Bitacora.id_bitacora.desc()).offset((pagina - 1) * tamano).limit(tamano))
    ).all()
    return filas, total or 0


async def opciones_bitacora(sesion: AsyncSession):
    modulos = (await sesion.scalars(
        select(Bitacora.modulo).where(Bitacora.modulo.is_not(None)).distinct().order_by(Bitacora.modulo))).all()
    tablas = (await sesion.scalars(
        select(Bitacora.tabla_afectada).where(Bitacora.tabla_afectada.is_not(None)).distinct()
        .order_by(Bitacora.tabla_afectada))).all()
    operaciones = (await sesion.scalars(
        select(Bitacora.operacion).where(Bitacora.operacion.is_not(None)).distinct().order_by(Bitacora.operacion))).all()
    return list(modulos), list(tablas), list(operaciones)


async def registrar_en_bitacora(sesion: AsyncSession, accion: str, operacion: str = "OTRO",
                                tabla: str | None = None, registro_id: str | None = None) -> None:
    """Registra una acción propia del backend usando la función de la BD (toma usuario e IP de la transacción)."""
    await sesion.execute(
        text("SELECT fn_registrar_bitacora(:accion, 'SEGURIDAD', :operacion, :tabla, :registro)"),
        {"accion": accion, "operacion": operacion, "tabla": tabla, "registro": registro_id},
    )


# ---- Bloqueo por intentos fallidos y recuperación de cuentas -----------------
async def registrar_intento_fallido(
    sesion: AsyncSession, id_usuario: int, bloqueado_hasta: datetime | None, nivel_bloqueo: int
) -> None:
    await sesion.execute(
        update(Usuario)
        .where(Usuario.id_usuario == id_usuario)
        .values(
            intentos_fallidos=Usuario.intentos_fallidos + 1,
            bloqueado_hasta=bloqueado_hasta,
            bloqueos_consecutivos=nivel_bloqueo,
            ultimo_intento_fallido=datetime.now(UTC),
        )
    )


async def restablecer_intentos(sesion: AsyncSession, id_usuario: int) -> None:
    await sesion.execute(
        update(Usuario)
        .where(Usuario.id_usuario == id_usuario)
        .values(
            intentos_fallidos=0,
            bloqueado_hasta=None,
            bloqueos_consecutivos=0,
            ultimo_intento_fallido=None,
        )
    )


async def buscar_cuentas_por_correo(sesion: AsyncSession, correo: str):
    """Busca cuentas de usuario activas asociadas a un correo electrónico."""
    c = correo.strip().lower()
    consulta = (
        select(
            Usuario.id_usuario,
            Usuario.nombre_usuario,
            Persona.nombre_persona.label("nombres"),
            Persona.apellidos,
            Persona.email,
        )
        .join(Persona, Persona.ci == Usuario.ci_persona)
        .where(
            func.lower(Persona.email) == c,
            Usuario.estado_usuario == "activo",
            Persona.estado_persona == "activo",
        )
    )
    return (await sesion.execute(consulta)).all()


async def crear_token_recuperacion(
    sesion: AsyncSession, id_usuario: int, token_hash: str, expira_en: datetime, ip_solicitud: str | None
) -> TokenRecuperacion:
    """Invalida tokens anteriores del usuario y registra uno nuevo."""
    await sesion.execute(
        update(TokenRecuperacion)
        .where(TokenRecuperacion.id_usuario == id_usuario, TokenRecuperacion.usado.is_(False))
        .values(usado=True, usado_en=datetime.now(UTC))
    )
    nuevo = TokenRecuperacion(
        id_usuario=id_usuario,
        token_hash=token_hash,
        expira_en=expira_en,
        ip_solicitud=ip_solicitud,
    )
    sesion.add(nuevo)
    await sesion.flush()
    return nuevo


async def obtener_token_recuperacion(sesion: AsyncSession, token_hash: str):
    consulta = (
        select(
            TokenRecuperacion.id_recuperacion,
            TokenRecuperacion.id_usuario,
            TokenRecuperacion.expira_en,
            TokenRecuperacion.usado,
            Usuario.nombre_usuario,
            Usuario.estado_usuario,
            Persona.nombre_persona.label("nombres"),
            Persona.apellidos,
        )
        .join(Usuario, Usuario.id_usuario == TokenRecuperacion.id_usuario)
        .join(Persona, Persona.ci == Usuario.ci_persona)
        .where(TokenRecuperacion.token_hash == token_hash)
    )
    return (await sesion.execute(consulta)).one_or_none()


async def consumir_token_recuperacion(sesion: AsyncSession, id_recuperacion: int) -> None:
    await sesion.execute(
        update(TokenRecuperacion)
        .where(TokenRecuperacion.id_recuperacion == id_recuperacion)
        .values(usado=True, usado_en=datetime.now(UTC))
    )

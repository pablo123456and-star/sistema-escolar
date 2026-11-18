"""
Acceso a la base de datos del paquete administracion (compartido).

Consultas y escrituras con SQLAlchemy sobre las tablas de models.py.
Los procedimientos almacenados se ejecutan con CALL (ver basededato/sql/04).
"""
# ============================================================
# CU25 - REGISTRAR PAGO DE MENSUALIDAD
# ============================================================

from datetime import date

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.paquetes.administracion.models import Arancel, Beca, PagoMensualidad

# Curso del estudiante en la gestión de la fila (alias de la tabla con el CI y la gestión)
_CURSO = """(SELECT vc.nombre_curso FROM inscripcion i JOIN v_curso vc ON vc.id_curso = i.id_curso_inscripcion
              WHERE i.ci_estudiante_inscripcion = {ci} AND i.id_gestion_inscripcion = {g})"""


async def hoy_cu25(sesion: AsyncSession) -> date:
    """Fecha actual en Bolivia (la sesión de BD usa la zona horaria America/La_Paz)."""
    return await sesion.scalar(text("SELECT CURRENT_DATE"))


async def es_administrativo_cu25(sesion: AsyncSession, ci: str) -> bool:
    return bool(await sesion.scalar(text("SELECT 1 FROM administrativo WHERE ci_administrativo = :ci"), {"ci": ci}))


# ---------- Aranceles y becas ----------

async def aranceles_cu25(sesion: AsyncSession, id_gestion: int):
    """Todos los niveles con su arancel de la gestión (sin arancel: columnas en NULL)."""
    return (
        await sesion.execute(
            text("""SELECT n.id_nivel, n.nombre_nivel AS nivel, a.id_arancel, a.monto_mensual, a.dia_vencimiento
                      FROM nivel_educativo n
                      LEFT JOIN arancel a ON a.id_nivel_arancel = n.id_nivel AND a.id_gestion_arancel = :g
                     ORDER BY n.id_nivel"""),
            {"g": id_gestion},
        )
    ).all()


async def arancel_de_nivel_cu25(sesion: AsyncSession, id_gestion: int, id_nivel: int) -> Arancel | None:
    return await sesion.scalar(
        select(Arancel).where(Arancel.id_gestion_arancel == id_gestion, Arancel.id_nivel_arancel == id_nivel)
    )


async def nombre_nivel_cu25(sesion: AsyncSession, id_nivel: int) -> str | None:
    return await sesion.scalar(text("SELECT nombre_nivel FROM nivel_educativo WHERE id_nivel = :n"), {"n": id_nivel})


async def becas_cu25(sesion: AsyncSession, id_gestion: int, id_beca: int | None = None):
    filtro = "AND b.id_beca = :id" if id_beca else ""
    return (
        await sesion.execute(
            text(f"""SELECT b.id_beca, b.ci_estudiante_beca AS ci_estudiante, p.nombre_persona, p.apellidos,
                            {_CURSO.format(ci="b.ci_estudiante_beca", g="b.id_gestion_beca")} AS curso,
                            b.porcentaje_descuento, b.motivo_beca
                       FROM beca b JOIN persona p ON p.ci = b.ci_estudiante_beca
                      WHERE b.id_gestion_beca = :g {filtro}
                      ORDER BY p.apellidos, p.nombre_persona"""),
            {"g": id_gestion, "id": id_beca},
        )
    ).all()


async def beca_de_estudiante_cu25(sesion: AsyncSession, id_gestion: int, ci_estudiante: str) -> Beca | None:
    return await sesion.scalar(
        select(Beca).where(Beca.id_gestion_beca == id_gestion, Beca.ci_estudiante_beca == ci_estudiante)
    )


async def inscripcion_activa_cu25(sesion: AsyncSession, ci_estudiante: str, id_gestion: int) -> bool:
    return bool(
        await sesion.scalar(
            text("""SELECT 1 FROM inscripcion WHERE ci_estudiante_inscripcion = :ci
                       AND id_gestion_inscripcion = :g AND estado_inscripcion = 'activa'"""),
            {"ci": ci_estudiante, "g": id_gestion},
        )
    )


# ---------- Cuotas ----------

async def generar_cuotas_cu25(sesion: AsyncSession, id_gestion: int, mes: int) -> int:
    """CALL sp_generar_cuotas_mes: devuelve cuántas cuotas creó (parámetro INOUT)."""
    return await sesion.scalar(text("CALL sp_generar_cuotas_mes(:g, :m, NULL)"), {"g": id_gestion, "m": mes})


async def estudiantes_pago_cu25(sesion: AsyncSession, id_gestion: int, buscar: str | None):
    """Inscritos de la gestión con sus cuotas pendientes y atrasadas (de todas sus gestiones)."""
    filtro = ""
    if buscar:
        filtro = """AND (p.ci ILIKE :buscar OR p.nombre_persona || ' ' || p.apellidos ILIKE :buscar
                         OR p.apellidos || ' ' || p.nombre_persona ILIKE :buscar)"""
    return (
        await sesion.execute(
            text(f"""SELECT p.ci, p.nombre_persona, p.apellidos, vc.nombre_curso AS curso,
                            count(v.id_pago) FILTER (WHERE v.estado_actual IN ('pendiente', 'atrasado')) AS pendientes,
                            count(v.id_pago) FILTER (WHERE v.estado_actual = 'atrasado') AS atrasadas,
                            coalesce(sum(v.monto) FILTER (WHERE v.estado_actual = 'atrasado'), 0) AS deuda
                       FROM inscripcion i
                       JOIN persona p  ON p.ci = i.ci_estudiante_inscripcion
                       JOIN v_curso vc ON vc.id_curso = i.id_curso_inscripcion
                       LEFT JOIN v_estado_pagos v ON v.ci_estudiante = p.ci
                      WHERE i.id_gestion_inscripcion = :g {filtro}
                      GROUP BY p.ci, p.nombre_persona, p.apellidos, vc.nombre_curso, vc.id_nivel, vc.orden_grado, vc.paralelo
                      ORDER BY vc.id_nivel, vc.orden_grado, vc.paralelo, p.apellidos, p.nombre_persona
                      LIMIT 100"""),
            {"g": id_gestion, "buscar": f"%{buscar}%"},
        )
    ).all()


async def estudiante_cu25(sesion: AsyncSession, ci_estudiante: str):
    """Datos del estudiante con el curso de su última inscripción (None si no es estudiante)."""
    return (
        await sesion.execute(
            text("""SELECT p.ci, p.nombre_persona, p.apellidos,
                           (SELECT vc.nombre_curso FROM inscripcion i
                              JOIN gestion g  ON g.id_gestion = i.id_gestion_inscripcion
                              JOIN v_curso vc ON vc.id_curso = i.id_curso_inscripcion
                             WHERE i.ci_estudiante_inscripcion = p.ci
                             ORDER BY g.anio DESC LIMIT 1) AS curso
                      FROM estudiante e JOIN persona p ON p.ci = e.ci_estudiante
                     WHERE e.ci_estudiante = :ci"""),
            {"ci": ci_estudiante},
        )
    ).one_or_none()


async def tutores_cu25(sesion: AsyncSession, ci_estudiante: str):
    """Tutores del estudiante: primero el responsable de pago, luego el principal."""
    return (
        await sesion.execute(
            text("""SELECT te.ci_tutor_tutorestudiante AS ci, p.nombre_persona, p.apellidos, te.parentesco,
                           te.es_responsable_pago
                      FROM tutor_estudiante te JOIN persona p ON p.ci = te.ci_tutor_tutorestudiante
                     WHERE te.ci_estudiante_tutorestudiante = :ci
                     ORDER BY te.es_responsable_pago DESC, te.es_principal DESC, p.apellidos"""),
            {"ci": ci_estudiante},
        )
    ).all()


async def es_tutor_cu25(sesion: AsyncSession, ci_tutor: str, ci_estudiante: str) -> bool:
    return bool(
        await sesion.scalar(
            text("""SELECT 1 FROM tutor_estudiante
                     WHERE ci_tutor_tutorestudiante = :t AND ci_estudiante_tutorestudiante = :e"""),
            {"t": ci_tutor, "e": ci_estudiante},
        )
    )


async def estudiantes_de_tutor_cu25(sesion: AsyncSession, ci_tutor: str) -> list[str]:
    return list(
        await sesion.scalars(
            text("""SELECT te.ci_estudiante_tutorestudiante FROM tutor_estudiante te
                      JOIN persona p ON p.ci = te.ci_estudiante_tutorestudiante
                     WHERE te.ci_tutor_tutorestudiante = :t
                     ORDER BY p.apellidos, p.nombre_persona"""),
            {"t": ci_tutor},
        )
    )


async def cuotas_cu25(sesion: AsyncSession, ci_estudiante: str):
    """Cuotas del estudiante con su estado real a hoy (v_estado_pagos calcula 'atrasado')."""
    return (
        await sesion.execute(
            text("""SELECT v.id_pago, v.anio, v.mes, v.monto, v.descuento_aplicado, v.fecha_vencimiento,
                           v.fecha_pago, v.metodo_pago, v.numero_recibo, v.estado_pago, v.estado_actual,
                           v.dias_atraso, pm.observacion_pago
                      FROM v_estado_pagos v JOIN pago_mensualidad pm ON pm.id_pago = v.id_pago
                     WHERE v.ci_estudiante = :ci
                     ORDER BY v.anio DESC, v.mes"""),
            {"ci": ci_estudiante},
        )
    ).all()


async def cuota_para_cambiar_cu25(sesion: AsyncSession, id_pago: int) -> PagoMensualidad | None:
    """La cuota bloqueada (FOR UPDATE): dos cajeros no pueden cobrarla a la vez."""
    return await sesion.get(PagoMensualidad, id_pago, with_for_update=True, populate_existing=True)


async def siguiente_recibo_cu25(sesion: AsyncSession) -> int:
    return await sesion.scalar(text("SELECT nextval('seq_numero_recibo')"))


async def recibo_cu25(sesion: AsyncSession, id_pago: int):
    return (
        await sesion.execute(
            text(f"""SELECT pm.id_pago, pm.numero_recibo, pm.fecha_pago, pm.mes, pm.monto, pm.descuento_aplicado,
                            pm.metodo_pago, pm.estado_pago, g.anio AS gestion, pm.ci_estudiante_pago AS ci_estudiante,
                            pe.apellidos || ', ' || pe.nombre_persona AS estudiante,
                            {_CURSO.format(ci="pm.ci_estudiante_pago", g="pm.id_gestion_pago")} AS curso,
                            pt.nombre_persona || ' ' || pt.apellidos AS tutor, te.parentesco,
                            pc.nombre_persona || ' ' || pc.apellidos AS cajero, ad.cargo
                       FROM pago_mensualidad pm
                       JOIN gestion g  ON g.id_gestion = pm.id_gestion_pago
                       JOIN persona pe ON pe.ci = pm.ci_estudiante_pago
                       LEFT JOIN persona pt ON pt.ci = pm.ci_tutor_pago
                       LEFT JOIN tutor_estudiante te ON te.ci_tutor_tutorestudiante = pm.ci_tutor_pago
                                                    AND te.ci_estudiante_tutorestudiante = pm.ci_estudiante_pago
                       LEFT JOIN persona pc ON pc.ci = pm.ci_administrativo_pago
                       LEFT JOIN administrativo ad ON ad.ci_administrativo = pm.ci_administrativo_pago
                      WHERE pm.id_pago = :id"""),
            {"id": id_pago},
        )
    ).one_or_none()


# ---------- Morosos ----------

async def morosos_cu25(sesion: AsyncSession):
    """Cuotas atrasadas (v_estado_pagos) con el tutor responsable de pago y su teléfono."""
    return (
        await sesion.execute(
            text(f"""SELECT v.ci_estudiante, v.estudiante, v.id_pago, v.anio, v.mes, v.monto, v.dias_atraso,
                            {_CURSO.format(ci="v.ci_estudiante", g="v.id_gestion")} AS curso,
                            t.tutor, t.telefono
                       FROM v_estado_pagos v
                       LEFT JOIN LATERAL (
                            SELECT p.nombre_persona || ' ' || p.apellidos AS tutor, p.telefono
                              FROM tutor_estudiante te JOIN persona p ON p.ci = te.ci_tutor_tutorestudiante
                             WHERE te.ci_estudiante_tutorestudiante = v.ci_estudiante
                             ORDER BY te.es_responsable_pago DESC, te.es_principal DESC
                             LIMIT 1) t ON true
                      WHERE v.estado_actual = 'atrasado'
                      ORDER BY v.estudiante, v.anio, v.mes""")
        )
    ).all()


# ============================================================
# CU26 - GESTIONAR INVENTARIO
# ============================================================

from app.paquetes.administracion.models import Inventario  # noqa: E402

_BIENES = """SELECT i.id_inventario, i.nombre_inventario AS nombre, i.cantidad_inventario AS cantidad,
                    i.stock_minimo, i.observacion_inventario AS observacion,
                    (SELECT count(*) FROM movimiento_inventario m
                      WHERE m.id_inventario_movimiento = i.id_inventario) AS movimientos,
                    (SELECT max(m.fecha_acceso_inventario) FROM movimiento_inventario m
                      WHERE m.id_inventario_movimiento = i.id_inventario) AS ultimo_movimiento
               FROM inventario i"""


async def bienes_cu26(sesion: AsyncSession, buscar: str | None = None, id_inventario: int | None = None):
    """Bienes con su stock, cuántos movimientos tienen y la fecha del último (por nombre)."""
    filtros, params = [], {}
    if buscar:
        filtros.append("(i.nombre_inventario ILIKE :b OR i.observacion_inventario ILIKE :b)")
        params["b"] = f"%{buscar}%"
    if id_inventario is not None:
        filtros.append("i.id_inventario = :id")
        params["id"] = id_inventario
    donde = ("WHERE " + " AND ".join(filtros)) if filtros else ""
    return (await sesion.execute(text(f"{_BIENES} {donde} ORDER BY i.nombre_inventario"), params)).all()


async def bien_bloqueado_cu26(sesion: AsyncSession, id_inventario: int) -> Inventario | None:
    """El bien con su fila bloqueada (FOR UPDATE) hasta el fin de la transacción:
    dos salidas al mismo tiempo no pueden sacar el mismo stock."""
    return await sesion.scalar(
        select(Inventario).where(Inventario.id_inventario == id_inventario).with_for_update()
    )


async def nombre_en_uso_cu26(sesion: AsyncSession, nombre: str, excluir_id: int | None = None) -> bool:
    """Ya hay otro bien con ese nombre (sin distinguir mayúsculas ni minúsculas)."""
    return bool(
        await sesion.scalar(
            text("""SELECT 1 FROM inventario
                     WHERE lower(nombre_inventario) = lower(:n)
                       AND (CAST(:excluir AS integer) IS NULL OR id_inventario <> :excluir)"""),
            {"n": nombre, "excluir": excluir_id},
        )
    )


async def movimientos_cu26(sesion: AsyncSession, id_inventario: int, id_movimiento: int | None = None):
    """Movimientos del bien (o uno solo) con el responsable y el saldo después de cada uno,
    del más reciente al más antiguo."""
    return (
        await sesion.execute(
            text("""SELECT * FROM (
                        SELECT m.id_movimiento, m.fecha_acceso_inventario AS fecha,
                               m.tipo_accion_inventario AS tipo, m.cantidad_movimiento AS cantidad,
                               m.motivo_movimiento AS motivo, m.destino_movimiento AS destino,
                               m.ci_administrativo_movimiento AS ci_responsable,
                               p.nombre_persona || ' ' || p.apellidos AS responsable,
                               sum(CASE WHEN m.tipo_accion_inventario = 'entrada' THEN m.cantidad_movimiento
                                        ELSE -m.cantidad_movimiento END)
                                   OVER (ORDER BY m.fecha_acceso_inventario, m.id_movimiento)::int AS saldo
                          FROM movimiento_inventario m
                          JOIN persona p ON p.ci = m.ci_administrativo_movimiento
                         WHERE m.id_inventario_movimiento = :id) x
                     WHERE CAST(:mov AS integer) IS NULL OR x.id_movimiento = :mov
                     ORDER BY x.fecha DESC, x.id_movimiento DESC"""),
            {"id": id_inventario, "mov": id_movimiento},
        )
    ).all()


# ============================================================
# CU27 - GESTIONAR COMUNICADOS Y CITACIONES
# ============================================================

# A quién LE LLEGA un comunicado (alias c = comunicado, :ci = usuario conectado):
#   - 'todos': a toda la comunidad (menos al autor).
#   - 'curso': a los estudiantes inscritos en ese curso en la gestión del comunicado y a sus tutores.
#   - 'estudiante': al estudiante y a sus tutores. Una citación solo a sus tutores.
_PARA_TODOS = "(c.alcance = 'todos' AND c.ci_autor <> :ci)"
_DESTINATARIO = {
    "administrador": _PARA_TODOS,
    "profesor": _PARA_TODOS,
    "estudiante": f"""({_PARA_TODOS}
        OR (c.alcance = 'curso' AND EXISTS (
                SELECT 1 FROM inscripcion i
                 WHERE i.ci_estudiante_inscripcion = :ci
                   AND i.id_curso_inscripcion = c.id_curso_comunicado
                   AND i.id_gestion_inscripcion = c.id_gestion_comunicado))
        OR (c.alcance = 'estudiante' AND c.tipo_comunicado = 'general' AND c.ci_estudiante_comunicado = :ci))""",
    "tutor": f"""({_PARA_TODOS}
        OR (c.alcance = 'curso' AND EXISTS (
                SELECT 1 FROM inscripcion i
                  JOIN tutor_estudiante te ON te.ci_estudiante_tutorestudiante = i.ci_estudiante_inscripcion
                 WHERE te.ci_tutor_tutorestudiante = :ci
                   AND i.id_curso_inscripcion = c.id_curso_comunicado
                   AND i.id_gestion_inscripcion = c.id_gestion_comunicado))
        OR (c.alcance = 'estudiante' AND EXISTS (
                SELECT 1 FROM tutor_estudiante te
                 WHERE te.ci_tutor_tutorestudiante = :ci
                   AND te.ci_estudiante_tutorestudiante = c.ci_estudiante_comunicado)))""",
}
# Qué comunicados VE cada rol: el administrador todos; el profesor los suyos, los que le llegan y los de
# los cursos donde enseña; estudiante y tutor solo los que les llegan.
_VISIBLE = {
    "administrador": "TRUE",
    "profesor": f"""(c.ci_autor = :ci OR {_DESTINATARIO['profesor']}
        OR (c.alcance = 'curso' AND EXISTS (
                SELECT 1 FROM asignacion_profesor_clase a
                 WHERE a.ci_profesor_asignacion = :ci
                   AND a.id_curso_asignacion = c.id_curso_comunicado
                   AND a.id_gestion_asignacion = c.id_gestion_comunicado)))""",
    "estudiante": _DESTINATARIO["estudiante"],
    "tutor": _DESTINATARIO["tutor"],
}


async def comunicados_cu27(sesion: AsyncSession, rol: str, ci: str, id_comunicado: int | None = None):
    """Comunicados que ve el usuario (o uno solo), del más reciente al más antiguo, con su lectura."""
    if rol not in _VISIBLE:
        return []
    filtro = "AND c.id_comunicado = :id" if id_comunicado is not None else ""
    return (
        await sesion.execute(
            text(f"""SELECT c.id_comunicado, c.titulo, c.contenido, c.tipo_comunicado, c.alcance,
                            c.id_curso_comunicado AS id_curso, c.ci_estudiante_comunicado AS ci_estudiante,
                            g.anio AS gestion, c.fecha_publicacion, c.fecha_citacion, c.ci_autor,
                            pa.nombre_persona || ' ' || pa.apellidos AS autor,
                            (SELECT r.nombre_rol FROM usuario u JOIN rol r ON r.id_rol = u.id_rol_usuario
                              WHERE u.ci_persona = c.ci_autor) AS rol_autor,
                            CASE c.alcance WHEN 'todos' THEN 'Toda la comunidad'
                                           WHEN 'curso' THEN vc.nombre_curso
                                           ELSE pe.nombre_persona || ' ' || pe.apellidos END AS destinatario,
                            c.ci_autor = :ci AS es_mio,
                            {_DESTINATARIO[rol]} AS es_destinatario,
                            l.leido_en,
                            (SELECT count(*) FROM comunicado_lectura x
                              WHERE x.id_comunicado_lectura = c.id_comunicado) AS lecturas
                       FROM comunicado c
                       JOIN gestion g  ON g.id_gestion = c.id_gestion_comunicado
                       JOIN persona pa ON pa.ci = c.ci_autor
                       LEFT JOIN v_curso vc ON vc.id_curso = c.id_curso_comunicado
                       LEFT JOIN persona pe ON pe.ci = c.ci_estudiante_comunicado
                       LEFT JOIN comunicado_lectura l
                              ON l.id_comunicado_lectura = c.id_comunicado AND l.ci_persona_lectura = :ci
                      WHERE {_VISIBLE[rol]} {filtro}
                      ORDER BY c.fecha_publicacion DESC, c.id_comunicado DESC"""),
            {"ci": ci, "id": id_comunicado},
        )
    ).all()


async def marcar_leido_cu27(sesion: AsyncSession, id_comunicado: int, ci: str) -> None:
    """Registra la lectura una sola vez (si ya estaba leído, se conserva la primera fecha)."""
    await sesion.execute(
        text("""INSERT INTO comunicado_lectura (id_comunicado_lectura, ci_persona_lectura)
                VALUES (:id, :ci) ON CONFLICT DO NOTHING"""),
        {"id": id_comunicado, "ci": ci},
    )


async def destinatarios_cu27(sesion: AsyncSession, id_comunicado: int):
    """Personas a las que llega el comunicado, con su lectura (NULL si aún no lo leyó)."""
    return (
        await sesion.execute(
            text("""WITH c AS (SELECT * FROM comunicado WHERE id_comunicado = :id),
                    est AS (   -- estudiantes alcanzados (los del curso o el estudiante elegido)
                         SELECT i.ci_estudiante_inscripcion AS ci
                           FROM c JOIN inscripcion i ON i.id_curso_inscripcion = c.id_curso_comunicado
                                                    AND i.id_gestion_inscripcion = c.id_gestion_comunicado
                          WHERE c.alcance = 'curso'
                         UNION
                         SELECT c.ci_estudiante_comunicado FROM c WHERE c.alcance = 'estudiante'),
                    dest AS (
                         SELECT est.ci, 'Estudiante' AS relacion
                           FROM est, c WHERE c.tipo_comunicado = 'general'
                         UNION ALL
                         SELECT te.ci_tutor_tutorestudiante,
                                'Tutor de ' || pe.nombre_persona || ' ' || pe.apellidos
                           FROM est JOIN tutor_estudiante te ON te.ci_estudiante_tutorestudiante = est.ci
                           JOIN persona pe ON pe.ci = est.ci
                         UNION ALL
                         SELECT u.ci_persona, initcap(r.nombre_rol)
                           FROM c, usuario u JOIN rol r ON r.id_rol = u.id_rol_usuario
                          WHERE c.alcance = 'todos' AND u.estado_usuario = 'activo' AND u.ci_persona <> c.ci_autor)
                    SELECT d.ci, p.nombre_persona || ' ' || p.apellidos AS nombre,
                           string_agg(DISTINCT d.relacion, ', ') AS relacion,
                           EXISTS (SELECT 1 FROM usuario u WHERE u.ci_persona = d.ci
                                      AND u.estado_usuario = 'activo') AS tiene_cuenta,
                           l.leido_en
                      FROM dest d
                      JOIN persona p ON p.ci = d.ci
                      LEFT JOIN comunicado_lectura l ON l.id_comunicado_lectura = :id AND l.ci_persona_lectura = d.ci
                     GROUP BY d.ci, p.nombre_persona, p.apellidos, l.leido_en
                     ORDER BY l.leido_en IS NULL, p.apellidos, p.nombre_persona"""),
            {"id": id_comunicado},
        )
    ).all()


# ---------- Destinos posibles al publicar (gestión abierta) ----------

async def cursos_destino_cu27(sesion: AsyncSession, id_gestion: int, ci_profesor: str | None,
                              id_curso: int | None = None):
    """Todos los cursos (administrador) o solo aquellos donde enseña el profesor en la gestión."""
    filtros = []
    if ci_profesor:
        filtros.append("""EXISTS (SELECT 1 FROM asignacion_profesor_clase a
                                   WHERE a.id_curso_asignacion = vc.id_curso AND a.id_gestion_asignacion = :g
                                     AND a.ci_profesor_asignacion = :ci)""")
    if id_curso is not None:
        filtros.append("vc.id_curso = :curso")
    donde = ("WHERE " + " AND ".join(filtros)) if filtros else ""
    return (
        await sesion.execute(
            text(f"""SELECT vc.id_curso, vc.nombre_curso FROM v_curso vc {donde}
                      ORDER BY vc.id_nivel, vc.orden_grado, vc.paralelo"""),
            {"g": id_gestion, "ci": ci_profesor, "curso": id_curso},
        )
    ).all()


async def estudiantes_destino_cu27(sesion: AsyncSession, id_gestion: int, ci_profesor: str | None,
                                   ci_estudiante: str | None = None):
    """Estudiantes con inscripción activa en la gestión (del profesor: solo los de sus cursos)."""
    filtros = ""
    if ci_profesor:
        filtros += """ AND EXISTS (SELECT 1 FROM asignacion_profesor_clase a
                                    WHERE a.id_curso_asignacion = i.id_curso_inscripcion
                                      AND a.id_gestion_asignacion = :g AND a.ci_profesor_asignacion = :ci)"""
    if ci_estudiante:
        filtros += " AND i.ci_estudiante_inscripcion = :est"
    return (
        await sesion.execute(
            text(f"""SELECT p.ci, p.apellidos || ' ' || p.nombre_persona AS nombre, vc.nombre_curso AS curso
                       FROM inscripcion i
                       JOIN persona p  ON p.ci = i.ci_estudiante_inscripcion
                       JOIN v_curso vc ON vc.id_curso = i.id_curso_inscripcion
                      WHERE i.id_gestion_inscripcion = :g AND i.estado_inscripcion = 'activa' {filtros}
                      ORDER BY vc.id_nivel, vc.orden_grado, vc.paralelo, p.apellidos, p.nombre_persona"""),
            {"g": id_gestion, "ci": ci_profesor, "est": ci_estudiante},
        )
    ).all()

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

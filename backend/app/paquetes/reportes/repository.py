"""
Acceso a la base de datos del paquete reportes (solo lectura, más el registro en la bitácora).

Reportes estáticos: consultas fijas con 1 o 2 parámetros.
Reporte dinámico: cada fuente define su FROM, sus columnas y sus filtros en una lista fija
(FUENTES). El usuario solo elige claves de esa lista; los valores van siempre como parámetros
de la consulta, nunca dentro del SQL.
"""
from dataclasses import dataclass, field
from datetime import timedelta, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
         "Noviembre", "Diciembre"]
_MES_SQL = "(ARRAY['" + "','".join(MESES) + "'])[{}]"

# Tutor principal (o responsable de pago) de un estudiante: nombre y teléfono
_TUTOR = """(SELECT pt.apellidos || ' ' || pt.nombre_persona FROM tutor_estudiante te
               JOIN persona pt ON pt.ci = te.ci_tutor_tutorestudiante
              WHERE te.ci_estudiante_tutorestudiante = {ci}
              ORDER BY te.{orden} DESC, te.es_principal DESC LIMIT 1)"""
_TELEFONO_TUTOR = """(SELECT pt.telefono FROM tutor_estudiante te
                        JOIN persona pt ON pt.ci = te.ci_tutor_tutorestudiante
                       WHERE te.ci_estudiante_tutorestudiante = {ci}
                       ORDER BY te.{orden} DESC, te.es_principal DESC LIMIT 1)"""


async def registrar_bitacora(sesion: AsyncSession, accion: str) -> None:
    """Deja constancia de cada reporte descargado (usuario e IP los pone la transacción)."""
    await sesion.execute(text("SELECT fn_registrar_bitacora(:accion, 'REPORTES', 'OTRO')"), {"accion": accion})


async def ahora(sesion: AsyncSession):
    """Fecha y hora de Bolivia (la sesión de BD usa America/La_Paz; Bolivia no tiene horario de verano: -04:00)."""
    return (await sesion.scalar(text("SELECT LOCALTIMESTAMP(0)"))).replace(tzinfo=timezone(timedelta(hours=-4)))


# ------------------------------------------------------------------ opciones para los filtros

async def opciones(sesion: AsyncSession) -> dict:
    gestiones = (await sesion.execute(text(
        "SELECT id_gestion, anio, estado_gestion FROM gestion ORDER BY anio DESC"))).mappings().all()
    niveles = (await sesion.execute(text(
        "SELECT id_nivel, nombre_nivel FROM nivel_educativo ORDER BY id_nivel"))).mappings().all()
    cursos = (await sesion.execute(text(
        "SELECT id_curso, nombre_curso, id_nivel FROM v_curso ORDER BY id_nivel, orden_grado, paralelo"))).mappings().all()
    periodos = (await sesion.execute(text(
        """SELECT pe.id_periodo, pe.nombre_periodo, pe.id_gestion_periodo AS id_gestion, g.anio
             FROM periodo pe JOIN gestion g ON g.id_gestion = pe.id_gestion_periodo
            ORDER BY g.anio DESC, pe.fecha_inicio_p"""))).mappings().all()
    materias = (await sesion.execute(text(
        "SELECT id_materia, nombre_materia FROM materia ORDER BY nombre_materia"))).mappings().all()
    return {"gestiones": gestiones, "niveles": niveles, "cursos": cursos, "periodos": periodos, "materias": materias}


async def gestion_por_defecto(sesion: AsyncSession):
    """La gestión abierta; si no hay, la más reciente."""
    return (await sesion.execute(text(
        "SELECT id_gestion, anio FROM gestion ORDER BY estado_gestion = 'abierta' DESC, anio DESC LIMIT 1"))).one_or_none()


async def gestion(sesion: AsyncSession, id_gestion: int):
    return (await sesion.execute(text(
        "SELECT id_gestion, anio, nota_minima_aprobacion FROM gestion WHERE id_gestion = :g"), {"g": id_gestion})).one_or_none()


async def curso(sesion: AsyncSession, id_curso: int):
    return (await sesion.execute(text(
        "SELECT id_curso, nombre_curso FROM v_curso WHERE id_curso = :c"), {"c": id_curso})).one_or_none()


async def periodo(sesion: AsyncSession, id_periodo: int):
    return (await sesion.execute(text(
        """SELECT pe.id_periodo, pe.nombre_periodo, pe.fecha_inicio_p, pe.fecha_final_p, g.id_gestion, g.anio,
                  g.nota_minima_aprobacion
             FROM periodo pe JOIN gestion g ON g.id_gestion = pe.id_gestion_periodo
            WHERE pe.id_periodo = :p"""), {"p": id_periodo})).one_or_none()


# ------------------------------------------------------------------ reportes estáticos

async def morosos(sesion: AsyncSession, id_gestion: int):
    """Cuotas atrasadas de la gestión con el curso y el tutor responsable de pago."""
    return (await sesion.execute(text(f"""
        SELECT v.ci_estudiante AS ci, v.estudiante, vc.nombre_curso AS curso, {_MES_SQL.format('v.mes')} AS mes,
               v.fecha_vencimiento, v.dias_atraso, v.monto,
               {_TUTOR.format(ci='v.ci_estudiante', orden='es_responsable_pago')} AS tutor,
               {_TELEFONO_TUTOR.format(ci='v.ci_estudiante', orden='es_responsable_pago')} AS telefono
          FROM v_estado_pagos v
          LEFT JOIN inscripcion i ON i.ci_estudiante_inscripcion = v.ci_estudiante
                                 AND i.id_gestion_inscripcion = v.id_gestion
          LEFT JOIN v_curso vc ON vc.id_curso = i.id_curso_inscripcion
         WHERE v.estado_actual = 'atrasado' AND v.id_gestion = :g
         ORDER BY vc.id_nivel, vc.orden_grado, vc.paralelo, v.estudiante, v.mes"""), {"g": id_gestion})).mappings().all()


async def inscritos(sesion: AsyncSession, id_gestion: int, id_curso: int):
    """Lista del curso en la gestión (incluye retirados, con su estado)."""
    return (await sesion.execute(text(f"""
        SELECT p.ci, p.apellidos || ' ' || p.nombre_persona AS estudiante, p.sexo, i.fecha_inscripcion,
               initcap(i.estado_inscripcion) AS estado,
               {_TUTOR.format(ci='p.ci', orden='es_principal')} AS tutor,
               {_TELEFONO_TUTOR.format(ci='p.ci', orden='es_principal')} AS telefono
          FROM inscripcion i JOIN persona p ON p.ci = i.ci_estudiante_inscripcion
         WHERE i.id_gestion_inscripcion = :g AND i.id_curso_inscripcion = :c
         ORDER BY i.estado_inscripcion = 'retirada', p.apellidos, p.nombre_persona"""),
        {"g": id_gestion, "c": id_curso})).mappings().all()


async def asistencia_curso(sesion: AsyncSession, id_curso: int, id_periodo: int):
    """Conteo de asistencia de cada estudiante del curso en las fechas del periodo (todas las materias)."""
    return (await sesion.execute(text("""
        SELECT p.ci, p.apellidos || ' ' || p.nombre_persona AS estudiante,
               count(s.id_asistencia) FILTER (WHERE s.estado_asistencia = 'presente')    AS presente,
               count(s.id_asistencia) FILTER (WHERE s.estado_asistencia = 'ausente')     AS ausente,
               count(s.id_asistencia) FILTER (WHERE s.estado_asistencia = 'tardanza')    AS tardanza,
               count(s.id_asistencia) FILTER (WHERE s.estado_asistencia = 'justificado') AS justificado,
               count(s.id_asistencia) AS total
          FROM periodo pe
          JOIN inscripcion i ON i.id_gestion_inscripcion = pe.id_gestion_periodo AND i.id_curso_inscripcion = :c
                            AND i.estado_inscripcion <> 'retirada'
          JOIN persona p ON p.ci = i.ci_estudiante_inscripcion
          LEFT JOIN asignacion_profesor_clase a ON a.id_curso_asignacion = :c
                                               AND a.id_gestion_asignacion = pe.id_gestion_periodo
          LEFT JOIN asistencia s ON s.id_asignacion_asistencia = a.id_asignacion AND s.ci_estudiante_asistencia = p.ci
                                AND s.fecha_asistencia BETWEEN pe.fecha_inicio_p AND pe.fecha_final_p
         WHERE pe.id_periodo = :p
         GROUP BY p.ci, p.apellidos, p.nombre_persona
         ORDER BY p.apellidos, p.nombre_persona"""), {"c": id_curso, "p": id_periodo})).mappings().all()


async def rendimiento_curso(sesion: AsyncSession, id_curso: int, id_periodo: int):
    """Promedio y materias reprobadas de cada estudiante del curso en el periodo (v_nota_final)."""
    return (await sesion.execute(text("""
        SELECT p.ci, p.apellidos || ' ' || p.nombre_persona AS estudiante,
               count(nf.id_calificacion) AS materias, round(avg(nf.nota_final), 2) AS promedio,
               count(nf.id_calificacion) FILTER (WHERE nf.nota_final < g.nota_minima_aprobacion) AS reprobadas
          FROM periodo pe
          JOIN gestion g ON g.id_gestion = pe.id_gestion_periodo
          JOIN inscripcion i ON i.id_gestion_inscripcion = pe.id_gestion_periodo AND i.id_curso_inscripcion = :c
                            AND i.estado_inscripcion <> 'retirada'
          JOIN persona p ON p.ci = i.ci_estudiante_inscripcion
          LEFT JOIN v_nota_final nf ON nf.ci_estudiante = p.ci AND nf.id_periodo = pe.id_periodo
         WHERE pe.id_periodo = :p
         GROUP BY p.ci, p.apellidos, p.nombre_persona
         ORDER BY p.apellidos, p.nombre_persona"""), {"c": id_curso, "p": id_periodo})).mappings().all()


async def promedio_por_materia(sesion: AsyncSession, id_curso: int, id_periodo: int):
    return (await sesion.execute(text("""
        SELECT m.nombre_materia AS materia, round(avg(nf.nota_final), 2) AS promedio
          FROM v_nota_final nf
          JOIN materia m ON m.id_materia = nf.id_materia
          JOIN inscripcion i ON i.ci_estudiante_inscripcion = nf.ci_estudiante AND i.id_gestion_inscripcion = nf.id_gestion
                            AND i.id_curso_inscripcion = :c AND i.estado_inscripcion <> 'retirada'
         WHERE nf.id_periodo = :p
         GROUP BY m.nombre_materia
         ORDER BY promedio"""), {"c": id_curso, "p": id_periodo})).mappings().all()


# ------------------------------------------------------------------ reporte dinámico

@dataclass
class Col:
    sql: str
    titulo: str
    tipo: str = "texto"
    por_defecto: bool = False


@dataclass
class Filtro:
    sql: str                        # condición con :v como valor
    titulo: str
    tipo: str                       # gestion, nivel, curso, periodo, materia, opcion, fecha, numero
    opciones: list[tuple[str, str]] = field(default_factory=list)   # (valor, etiqueta) para tipo 'opcion'


@dataclass
class Fuente:
    nombre: str
    descripcion: str
    desde: str
    columnas: dict[str, Col]
    filtros: dict[str, Filtro]
    orden: str                      # ORDER BY por defecto


_CURSO_ORDEN = "vc.id_nivel, vc.orden_grado, vc.paralelo"

FUENTES: dict[str, Fuente] = {
    "estudiantes": Fuente(
        "Estudiantes e inscripciones", "Datos de los estudiantes y su inscripción en cada gestión.",
        """inscripcion i
           JOIN persona p    ON p.ci = i.ci_estudiante_inscripcion
           JOIN estudiante e ON e.ci_estudiante = p.ci
           JOIN gestion g    ON g.id_gestion = i.id_gestion_inscripcion
           JOIN v_curso vc   ON vc.id_curso = i.id_curso_inscripcion""",
        {
            "ci": Col("p.ci", "CI", por_defecto=True),
            "estudiante": Col("p.apellidos || ' ' || p.nombre_persona", "Estudiante", por_defecto=True),
            "sexo": Col("p.sexo", "Sexo"),
            "fecha_nacimiento": Col("p.fecha_nacimiento", "Fecha de nacimiento", "fecha"),
            "edad": Col("date_part('year', age(p.fecha_nacimiento))::int", "Edad", "entero"),
            "rude": Col("e.rude", "RUDE"),
            "gestion": Col("g.anio", "Gestión", "entero"),
            "nivel": Col("vc.nombre_nivel", "Nivel"),
            "curso": Col("vc.nombre_curso", "Curso", por_defecto=True),
            "fecha_inscripcion": Col("i.fecha_inscripcion", "Fecha de inscripción", "fecha"),
            "estado": Col("initcap(i.estado_inscripcion)", "Estado", por_defecto=True),
            "resultado": Col("initcap(i.resultado_final)", "Resultado final"),
            "fecha_retiro": Col("i.fecha_retiro", "Fecha de retiro", "fecha"),
            "motivo_retiro": Col("i.motivo_retiro", "Motivo de retiro"),
            "direccion": Col("p.direccion", "Dirección"),
            "tutor": Col(_TUTOR.format(ci="p.ci", orden="es_principal"), "Tutor principal"),
            "telefono_tutor": Col(_TELEFONO_TUTOR.format(ci="p.ci", orden="es_principal"), "Teléfono del tutor"),
        },
        {
            "gestion": Filtro("g.id_gestion = :v", "Gestión", "gestion"),
            "nivel": Filtro("vc.id_nivel = :v", "Nivel", "nivel"),
            "curso": Filtro("vc.id_curso = :v", "Curso", "curso"),
            "estado": Filtro("i.estado_inscripcion = :v", "Estado de la inscripción", "opcion",
                             [("activa", "Activa"), ("retirada", "Retirada"), ("finalizada", "Finalizada")]),
            "resultado": Filtro("i.resultado_final = :v", "Resultado final", "opcion",
                                [("promovido", "Promovido"), ("reprobado", "Reprobado")]),
            "sexo": Filtro("p.sexo = :v", "Sexo", "opcion", [("M", "Masculino"), ("F", "Femenino")]),
        },
        f"g.anio DESC, {_CURSO_ORDEN}, p.apellidos, p.nombre_persona"),
    "pagos": Fuente(
        "Pagos de mensualidad", "Cuotas con su estado real a la fecha (pendiente, atrasado, pagado o anulado).",
        """v_estado_pagos v
           LEFT JOIN inscripcion i ON i.ci_estudiante_inscripcion = v.ci_estudiante
                                  AND i.id_gestion_inscripcion = v.id_gestion
           LEFT JOIN v_curso vc ON vc.id_curso = i.id_curso_inscripcion""",
        {
            "ci": Col("v.ci_estudiante", "CI", por_defecto=True),
            "estudiante": Col("v.estudiante", "Estudiante", por_defecto=True),
            "gestion": Col("v.anio", "Gestión", "entero"),
            "curso": Col("vc.nombre_curso", "Curso", por_defecto=True),
            "mes": Col(_MES_SQL.format("v.mes"), "Mes", por_defecto=True),
            "monto": Col("v.monto", "Monto (Bs)", "decimal", True),
            "descuento": Col("v.descuento_aplicado", "Descuento beca (Bs)", "decimal"),
            "vencimiento": Col("v.fecha_vencimiento", "Vencimiento", "fecha"),
            "estado": Col("initcap(v.estado_actual)", "Estado", por_defecto=True),
            "dias_atraso": Col("v.dias_atraso", "Días de atraso", "entero"),
            "fecha_pago": Col("v.fecha_pago", "Fecha de pago", "fecha"),
            "metodo": Col("initcap(v.metodo_pago)", "Método de pago"),
            "recibo": Col("v.numero_recibo", "N.º de recibo", "entero"),
        },
        {
            "gestion": Filtro("v.id_gestion = :v", "Gestión", "gestion"),
            "curso": Filtro("vc.id_curso = :v", "Curso", "curso"),
            "estado": Filtro("v.estado_actual = :v", "Estado", "opcion",
                             [("pendiente", "Pendiente"), ("atrasado", "Atrasado"), ("pagado", "Pagado"),
                              ("anulado", "Anulado")]),
            "mes": Filtro("v.mes = CAST(:v AS int)", "Mes", "opcion", [(str(i + 1), m) for i, m in enumerate(MESES)]),
            "metodo": Filtro("v.metodo_pago = :v", "Método de pago", "opcion",
                             [("efectivo", "Efectivo"), ("transferencia", "Transferencia"), ("qr", "QR"),
                              ("tarjeta", "Tarjeta")]),
            "pago_desde": Filtro("v.fecha_pago >= :v", "Pagado desde", "fecha"),
            "pago_hasta": Filtro("v.fecha_pago <= :v", "Pagado hasta", "fecha"),
        },
        f"v.anio DESC, {_CURSO_ORDEN}, v.estudiante, v.mes"),
    "asistencia": Fuente(
        "Asistencia", "Registro diario de asistencia por estudiante, clase y fecha.",
        """asistencia s
           JOIN asignacion_profesor_clase a ON a.id_asignacion = s.id_asignacion_asistencia
           JOIN materia m  ON m.id_materia = a.id_materia_asignacion
           JOIN v_curso vc ON vc.id_curso = a.id_curso_asignacion
           JOIN persona p  ON p.ci = s.ci_estudiante_asistencia
           JOIN persona pp ON pp.ci = a.ci_profesor_asignacion
           JOIN gestion g  ON g.id_gestion = a.id_gestion_asignacion""",
        {
            "fecha": Col("s.fecha_asistencia", "Fecha", "fecha", True),
            "ci": Col("p.ci", "CI"),
            "estudiante": Col("p.apellidos || ' ' || p.nombre_persona", "Estudiante", por_defecto=True),
            "curso": Col("vc.nombre_curso", "Curso", por_defecto=True),
            "materia": Col("m.nombre_materia", "Materia", por_defecto=True),
            "profesor": Col("pp.apellidos || ' ' || pp.nombre_persona", "Docente"),
            "estado": Col("initcap(s.estado_asistencia)", "Estado", por_defecto=True),
            "observacion": Col("s.observacion_asistencia", "Observación"),
        },
        {
            "gestion": Filtro("g.id_gestion = :v", "Gestión", "gestion"),
            "curso": Filtro("vc.id_curso = :v", "Curso", "curso"),
            "materia": Filtro("m.id_materia = :v", "Materia", "materia"),
            "estado": Filtro("s.estado_asistencia = :v", "Estado", "opcion",
                             [("presente", "Presente"), ("ausente", "Ausente"), ("tardanza", "Tardanza"),
                              ("justificado", "Justificado")]),
            "desde": Filtro("s.fecha_asistencia >= :v", "Desde", "fecha"),
            "hasta": Filtro("s.fecha_asistencia <= :v", "Hasta", "fecha"),
        },
        f"s.fecha_asistencia DESC, {_CURSO_ORDEN}, p.apellidos, p.nombre_persona"),
    "calificaciones": Fuente(
        "Calificaciones", "Nota final de cada estudiante por materia y periodo (suma de sus dimensiones).",
        """v_nota_final nf
           JOIN periodo pe ON pe.id_periodo = nf.id_periodo
           JOIN gestion g  ON g.id_gestion = nf.id_gestion
           JOIN persona p  ON p.ci = nf.ci_estudiante
           JOIN materia m  ON m.id_materia = nf.id_materia
           LEFT JOIN inscripcion i ON i.ci_estudiante_inscripcion = nf.ci_estudiante
                                  AND i.id_gestion_inscripcion = nf.id_gestion
           LEFT JOIN v_curso vc ON vc.id_curso = i.id_curso_inscripcion""",
        {
            "ci": Col("p.ci", "CI"),
            "estudiante": Col("p.apellidos || ' ' || p.nombre_persona", "Estudiante", por_defecto=True),
            "gestion": Col("g.anio", "Gestión", "entero"),
            "periodo": Col("pe.nombre_periodo", "Periodo", por_defecto=True),
            "curso": Col("vc.nombre_curso", "Curso", por_defecto=True),
            "materia": Col("m.nombre_materia", "Materia", por_defecto=True),
            "nota_final": Col("nf.nota_final", "Nota final", "decimal", True),
            "dimensiones": Col("nf.dimensiones_registradas || ' de ' || nf.dimensiones_totales", "Dimensiones"),
            "situacion": Col("CASE WHEN nf.nota_final >= g.nota_minima_aprobacion THEN 'Aprobado' ELSE 'Reprobado' END",
                             "Situación", por_defecto=True),
        },
        {
            "gestion": Filtro("g.id_gestion = :v", "Gestión", "gestion"),
            "periodo": Filtro("pe.id_periodo = :v", "Periodo", "periodo"),
            "curso": Filtro("vc.id_curso = :v", "Curso", "curso"),
            "materia": Filtro("m.id_materia = :v", "Materia", "materia"),
            "situacion": Filtro("(nf.nota_final >= g.nota_minima_aprobacion) = (CAST(:v AS text) = 'aprobado')", "Situación", "opcion",
                                [("aprobado", "Aprobado"), ("reprobado", "Reprobado")]),
            "nota_desde": Filtro("nf.nota_final >= :v", "Nota desde", "numero"),
            "nota_hasta": Filtro("nf.nota_final <= :v", "Nota hasta", "numero"),
        },
        f"g.anio DESC, pe.fecha_inicio_p, {_CURSO_ORDEN}, p.apellidos, p.nombre_persona, m.nombre_materia"),
}


def _consulta(fuente: Fuente, columnas: list[str], filtros: dict, orden: str | None, descendente: bool):
    """Arma el SELECT con columnas y filtros de la lista fija; los valores van como parámetros."""
    select = ", ".join(f"{fuente.columnas[c].sql} AS {c}" for c in columnas)
    condiciones, params = [], {}
    for i, (clave, valor) in enumerate(filtros.items()):
        condiciones.append(fuente.filtros[clave].sql.replace(":v", f":f{i}"))
        params[f"f{i}"] = valor
    donde = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    orden_sql = f"{fuente.columnas[orden].sql} {'DESC' if descendente else 'ASC'} NULLS LAST" if orden else fuente.orden
    return select, donde, orden_sql, params


async def dinamico(sesion: AsyncSession, clave_fuente: str, columnas: list[str], filtros: dict, orden: str | None,
                   descendente: bool, limite: int):
    """Filas del reporte (hasta `limite`) y el total que cumple los filtros."""
    fuente = FUENTES[clave_fuente]
    select, donde, orden_sql, params = _consulta(fuente, columnas, filtros, orden, descendente)
    total = await sesion.scalar(text(f"SELECT count(*) FROM {fuente.desde} {donde}"), params)
    filas = (await sesion.execute(text(f"SELECT {select} FROM {fuente.desde} {donde} ORDER BY {orden_sql} LIMIT :lim"),
                                  {**params, "lim": limite})).mappings().all()
    return filas, total


async def nombre_de(sesion: AsyncSession, tipo: str, valor) -> str | None:
    """Texto de un filtro para mostrarlo en el encabezado del reporte (por ejemplo el nombre del curso)."""
    consultas = {
        "gestion": "SELECT anio::text FROM gestion WHERE id_gestion = :v",
        "nivel": "SELECT nombre_nivel FROM nivel_educativo WHERE id_nivel = :v",
        "curso": "SELECT nombre_curso FROM v_curso WHERE id_curso = :v",
        "periodo": """SELECT pe.nombre_periodo || ' ' || g.anio FROM periodo pe
                        JOIN gestion g ON g.id_gestion = pe.id_gestion_periodo WHERE pe.id_periodo = :v""",
        "materia": "SELECT nombre_materia FROM materia WHERE id_materia = :v",
    }
    if tipo not in consultas:
        return None
    return await sesion.scalar(text(consultas[tipo]), {"v": valor})


async def nombre_usuario(sesion: AsyncSession, ci: str) -> str | None:
    """Nombre de la persona que genera el reporte (para el pie del PDF y del Excel)."""
    return await sesion.scalar(text("SELECT nombre_persona || ' ' || apellidos FROM persona WHERE ci = :ci"), {"ci": ci})

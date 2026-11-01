"""
Reportes estáticos (consigna del ciclo 3: «Reportes: estático y dinámico. Generar a 2 formatos»)
Paquete: reportes

Actores ........: Director, Secretaría
Rol del sistema : administrador
Tablas .........: pago_mensualidad, inscripcion, asistencia, calificacion (solo lectura), bitacora
Usa de la BD ...: Vistas v_estado_pagos, v_nota_final y v_curso; fn_registrar_bitacora

Reglas de negocio que implementa (backend):
    - Solo administrador.
    - Reportes con estructura fija; el usuario solo elige la gestión, el curso o el periodo:
        * Morosos: cuotas atrasadas de la gestión con el tutor responsable de pago y su teléfono.
        * Inscritos por curso: lista del curso en la gestión con el tutor principal.
        * Asistencia por curso: presentes, ausentes, tardanzas, justificados y % en el periodo.
        * Rendimiento por curso: promedio, materias reprobadas y situación de cada estudiante en el periodo.
    - Se ven en pantalla y se descargan en PDF o Excel; cada descarga queda en la bitácora.

Precondición:
    Sesión iniciada como administrador.

Postcondición:
    Se entrega el reporte; no se modifica ningún dato (solo se anota la descarga en la bitácora).

Flujo: router.py -> este caso de uso -> repository.py -> BD; nucleo/exportar.py arma el PDF y el Excel.
Estado: IMPLEMENTADO.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import ErrorNegocio, NoEncontrado
from app.nucleo.exportar import Columna, Tabla
from app.paquetes.reportes import repository as repo
from app.paquetes.reportes.schemas import ReporteEstaticoInfo

CATALOGO = [
    ReporteEstaticoInfo(clave="morosos", nombre="Morosos",
                        descripcion="Cuotas atrasadas de la gestión con el tutor responsable de pago y su teléfono.",
                        parametros=["gestion"]),
    ReporteEstaticoInfo(clave="inscritos", nombre="Inscritos por curso",
                        descripcion="Lista del curso en la gestión: estado de la inscripción y tutor principal.",
                        parametros=["gestion", "curso"]),
    ReporteEstaticoInfo(clave="asistencia", nombre="Asistencia por curso",
                        descripcion="Presentes, ausentes, tardanzas, justificados y porcentaje de asistencia en el periodo.",
                        parametros=["curso", "periodo"]),
    ReporteEstaticoInfo(clave="rendimiento", nombre="Rendimiento por curso",
                        descripcion="Promedio, materias reprobadas y situación de cada estudiante en el periodo.",
                        parametros=["curso", "periodo"]),
]


def catalogo() -> list[ReporteEstaticoInfo]:
    return CATALOGO


def _bs(valor) -> str:
    return f"Bs {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


async def _gestion(sesion: AsyncSession, id_gestion: int | None):
    if id_gestion is None:
        g = await repo.gestion_por_defecto(sesion)
        if g is None:
            raise ErrorNegocio("Todavía no hay gestiones registradas.")
        id_gestion = g.id_gestion
    g = await repo.gestion(sesion, id_gestion)
    if g is None:
        raise NoEncontrado("No existe esa gestión.")
    return g


async def _curso(sesion: AsyncSession, id_curso: int | None):
    if id_curso is None:
        raise ErrorNegocio("Elija el curso.")
    c = await repo.curso(sesion, id_curso)
    if c is None:
        raise NoEncontrado("No existe ese curso.")
    return c


async def _periodo(sesion: AsyncSession, id_periodo: int | None):
    if id_periodo is None:
        raise ErrorNegocio("Elija el periodo.")
    p = await repo.periodo(sesion, id_periodo)
    if p is None:
        raise NoEncontrado("No existe ese periodo.")
    return p


async def generar(sesion: AsyncSession, usuario: UsuarioActual, clave: str, id_gestion: int | None,
                  id_curso: int | None, id_periodo: int | None) -> Tabla:
    """Arma la tabla del reporte elegido (la misma para la pantalla, el PDF y el Excel)."""
    if clave == "morosos":
        g = await _gestion(sesion, id_gestion)
        filas = [dict(f) for f in await repo.morosos(sesion, g.id_gestion)]
        tabla = Tabla("Reporte de morosos", [
            Columna("ci", "CI"), Columna("estudiante", "Estudiante"), Columna("curso", "Curso"), Columna("mes", "Mes"),
            Columna("fecha_vencimiento", "Vencimiento", "fecha"), Columna("dias_atraso", "Días de atraso", "entero"),
            Columna("monto", "Monto (Bs)", "decimal"), Columna("tutor", "Tutor responsable"),
            Columna("telefono", "Teléfono")], filas, [f"Gestión: {g.anio}"])
        deudores = len({f["ci"] for f in filas})
        tabla.resumen = [f"{len(filas)} cuotas atrasadas de {deudores} estudiantes. "
                         f"Total adeudado: {_bs(sum(f['monto'] for f in filas))}."]
    elif clave == "inscritos":
        g = await _gestion(sesion, id_gestion)
        c = await _curso(sesion, id_curso)
        filas = [{"n": i, **dict(f)} for i, f in enumerate(await repo.inscritos(sesion, g.id_gestion, c.id_curso), start=1)]
        tabla = Tabla("Inscritos por curso", [
            Columna("n", "N.º", "entero"), Columna("ci", "CI"), Columna("estudiante", "Estudiante"), Columna("sexo", "Sexo"),
            Columna("fecha_inscripcion", "Inscrito el", "fecha"), Columna("estado", "Estado"),
            Columna("tutor", "Tutor principal"), Columna("telefono", "Teléfono del tutor")],
            filas, [f"Gestión: {g.anio}", f"Curso: {c.nombre_curso}"])
        por_estado = {e: sum(1 for f in filas if f["estado"].lower() == e) for e in ("activa", "retirada", "finalizada")}
        tabla.resumen = [f"Total: {len(filas)} · Activas: {por_estado['activa']} · Retiradas: {por_estado['retirada']}"
                         f" · Finalizadas: {por_estado['finalizada']}."]
    elif clave in ("asistencia", "rendimiento"):
        c = await _curso(sesion, id_curso)
        p = await _periodo(sesion, id_periodo)
        encabezado = [f"Curso: {c.nombre_curso}",
                      f"Periodo: {p.nombre_periodo} {p.anio} ({p.fecha_inicio_p:%d/%m/%Y} al {p.fecha_final_p:%d/%m/%Y})"]
        if clave == "asistencia":
            filas = []
            for f in await repo.asistencia_curso(sesion, c.id_curso, p.id_periodo):
                f = dict(f)
                f["porcentaje"] = round(100 * (f["presente"] + f["tardanza"]) / f["total"], 1) if f["total"] else None
                filas.append(f)
            tabla = Tabla("Asistencia por curso", [
                Columna("ci", "CI"), Columna("estudiante", "Estudiante"), Columna("presente", "Presente", "entero"),
                Columna("ausente", "Ausente", "entero"), Columna("tardanza", "Tardanza", "entero"),
                Columna("justificado", "Justificado", "entero"), Columna("total", "Clases", "entero"),
                Columna("porcentaje", "% asistencia", "porcentaje")], filas,
                encabezado + ["% de asistencia = (presente + tardanza) / clases registradas."])
            con_datos = [f["porcentaje"] for f in filas if f["porcentaje"] is not None]
            bajos = sum(1 for x in con_datos if x < 80)
            tabla.resumen = [f"Asistencia promedio del curso: {sum(con_datos) / len(con_datos):.1f} %. "
                             f"Estudiantes con menos del 80 %: {bajos}.".replace(".", ",", 1) if con_datos
                             else "No hay asistencia registrada en el periodo."]
        else:
            minima = float(p.nota_minima_aprobacion)
            filas = []
            for f in await repo.rendimiento_curso(sesion, c.id_curso, p.id_periodo):
                f = dict(f)
                f["situacion"] = ("Sin notas" if f["promedio"] is None
                                  else "Aprobado" if float(f["promedio"]) >= minima else "Reprobado")
                filas.append(f)
            tabla = Tabla("Rendimiento por curso", [
                Columna("ci", "CI"), Columna("estudiante", "Estudiante"), Columna("materias", "Materias con nota", "entero"),
                Columna("promedio", "Promedio", "decimal"), Columna("reprobadas", "Materias reprobadas", "entero"),
                Columna("situacion", "Situación")], filas, encabezado + [f"Nota mínima de aprobación: {minima:g}."])
            con_nota = [float(f["promedio"]) for f in filas if f["promedio"] is not None]
            materias = await repo.promedio_por_materia(sesion, c.id_curso, p.id_periodo)
            tabla.resumen = [
                f"Promedio del curso: {sum(con_nota) / len(con_nota):.2f}. Aprobados: "
                f"{sum(1 for f in filas if f['situacion'] == 'Aprobado')} · Reprobados: "
                f"{sum(1 for f in filas if f['situacion'] == 'Reprobado')} · Sin notas: "
                f"{sum(1 for f in filas if f['situacion'] == 'Sin notas')}." if con_nota
                else "No hay notas registradas en el periodo."]
            if materias:
                tabla.resumen.append(f"Materia con menor promedio: {materias[0]['materia']} ({materias[0]['promedio']}). "
                                     f"Con mayor promedio: {materias[-1]['materia']} ({materias[-1]['promedio']}).")
    else:
        raise NoEncontrado("No existe ese reporte.")

    tabla.generado_por = await repo.nombre_usuario(sesion, usuario.ci) or usuario.nombre_usuario
    tabla.generado_en = await repo.ahora(sesion)
    return tabla

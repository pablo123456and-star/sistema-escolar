"""Pruebas del CU22: consultar historial de asistencia.

Datos de 08_datos_prueba: mquispe es el estudiante 4500001 (1ro A Secundaria); marioq es tutor
de 4500001 y 4500007 (6to A Primaria); rflores (2000001) dicta en 1ro A Secundaria y erojas
(2000006) en 6to A Primaria. Hay asistencia del 1 al 24 de septiembre de 2026, nada en agosto.
"""
from datetime import date

from sqlalchemy import text

from app.nucleo import bd
from tests.conftest import iniciar


async def _sql(consulta: str, **params):
    """Ejecuta SQL directo dentro de la transacción de la prueba (se deshace al terminar)."""
    async with bd._fabrica() as sesion:
        resultado = await sesion.execute(text(consulta), params)
        valor = resultado.scalar() if resultado.returns_rows else None
        await sesion.commit()
        return valor


async def _historial(cliente, cabecera, ci: str, **params):
    return await cliente.get(f"/evaluacion/asistencia/historial/{ci}", params=params, headers=cabecera)


async def test_cu22_estudiante_solo_ve_lo_suyo(cliente):
    cabecera = await iniciar(cliente, "mquispe")
    r = await cliente.get("/evaluacion/asistencia/historial/estudiantes", headers=cabecera)
    assert r.status_code == 200, r.text
    assert [e["ci"] for e in r.json()["estudiantes"]] == ["4500001"]
    r = await _historial(cliente, cabecera, "4500001")
    assert r.status_code == 200, r.text
    assert r.json()["estudiante"]["ci"] == "4500001" and r.json()["gestion"] == 2026
    assert (await _historial(cliente, cabecera, "4500002")).status_code == 403


async def test_cu22_tutor_ve_solo_a_sus_estudiantes(cliente):
    cabecera = await iniciar(cliente, "marioq")
    r = await cliente.get("/evaluacion/asistencia/historial/estudiantes", headers=cabecera)
    assert {e["ci"] for e in r.json()["estudiantes"]} == {"4500001", "4500007"}
    assert (await _historial(cliente, cabecera, "4500007")).status_code == 200
    assert (await _historial(cliente, cabecera, "4500002")).status_code == 403
    assert (await _historial(cliente, cabecera, "9999999")).status_code == 403   # no revela si existe


async def test_cu22_profesor_ve_solo_a_estudiantes_de_sus_cursos(cliente, profesor):
    r = await cliente.get("/evaluacion/asistencia/historial/estudiantes", headers=profesor)
    assert {e["ci"] for e in r.json()["estudiantes"]} == {f"450000{n}" for n in range(1, 7)}
    assert (await _historial(cliente, profesor, "4500002")).status_code == 200
    assert (await _historial(cliente, profesor, "4500007")).status_code == 403
    erojas = await iniciar(cliente, "erojas")
    assert (await _historial(cliente, erojas, "4500001")).status_code == 403


async def test_cu22_administrador_ve_a_todos(cliente, admin):
    r = await cliente.get("/evaluacion/asistencia/historial/estudiantes", headers=admin)
    assert len(r.json()["estudiantes"]) == await _sql(
        "SELECT count(*) FROM inscripcion i JOIN gestion g ON g.id_gestion = i.id_gestion_inscripcion "
        "WHERE g.estado_gestion = 'abierta'")
    assert (await _historial(cliente, admin, "4500011")).status_code == 200
    assert (await _historial(cliente, admin, "9999999")).status_code == 404


async def test_cu22_porcentaje_por_materia(cliente, admin):
    """Una semana de agosto sin datos: 4 registros de Matemática -> (presente + tardanza) / 4 = 50 %."""
    id_matematica = await _sql(
        "SELECT a.id_asignacion FROM asignacion_profesor_clase a JOIN materia m ON m.id_materia = a.id_materia_asignacion "
        "WHERE a.ci_profesor_asignacion = '2000001' AND m.nombre_materia = 'Matematica'")
    for dia, estado in ((3, "presente"), (4, "tardanza"), (5, "ausente"), (6, "justificado")):
        await _sql("INSERT INTO asistencia (id_asignacion_asistencia, ci_estudiante_asistencia, fecha_asistencia, "
                   "estado_asistencia) VALUES (:a, '4500001', :f, :e)", a=id_matematica, f=date(2026, 8, dia), e=estado)

    r = await _historial(cliente, admin, "4500001", desde="2026-08-01", hasta="2026-08-31")
    assert r.status_code == 200, r.text
    datos = r.json()
    matematica = next(m for m in datos["materias"] if m["materia"] == "Matematica")
    assert (matematica["total"], matematica["porcentaje"]) == (4, 50.0)
    assert (matematica["presente"], matematica["tardanza"], matematica["ausente"], matematica["justificado"]) == (1, 1, 1, 1)
    otras = [m for m in datos["materias"] if m["materia"] != "Matematica"]
    assert otras and all(m["total"] == 0 and m["porcentaje"] is None for m in otras)   # "sin registros"
    assert datos["general"]["porcentaje"] == 50.0 and len(datos["detalle"]) == 4
    assert [d["fecha"] for d in datos["detalle"]] == ["2026-08-06", "2026-08-05", "2026-08-04", "2026-08-03"]


async def test_cu22_porcentaje_coincide_con_la_bd(cliente, admin):
    r = await _historial(cliente, admin, "4500003")
    general = r.json()["general"]
    total, asistio = (
        await _sql("SELECT count(*) FROM asistencia WHERE ci_estudiante_asistencia = '4500003'"),
        await _sql("SELECT count(*) FROM asistencia WHERE ci_estudiante_asistencia = '4500003' "
                   "AND estado_asistencia IN ('presente', 'tardanza')"),
    )
    assert general["total"] == total and general["porcentaje"] == round(asistio * 100 / total, 1)


async def test_cu22_filtro_por_materia(cliente, admin):
    id_materia = await _sql("SELECT id_materia FROM materia WHERE nombre_materia = 'Matematica'")
    r = await _historial(cliente, admin, "4500001", id_materia=id_materia)
    datos = r.json()
    assert [m["materia"] for m in datos["materias"]] == ["Matematica"]
    assert datos["detalle"] and {d["materia"] for d in datos["detalle"]} == {"Matematica"}


async def test_cu22_rango_de_fechas_invalido(cliente, admin):
    r = await _historial(cliente, admin, "4500001", desde="2026-09-20", hasta="2026-09-01")
    assert r.status_code == 400

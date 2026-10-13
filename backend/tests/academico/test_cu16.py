"""Pruebas del CU16: inscribir estudiante en la gestión abierta y emitir la boleta."""
from sqlalchemy import text

from app.nucleo import bd

NUEVO = {
    "ci": "7716001", "expedido": "SC", "nombre_persona": "Tomás", "apellidos": "Arteaga Ríos",
    "sexo": "M", "fecha_nacimiento": "2014-03-21",
}


async def _sql(consulta: str, **params):
    """Ejecuta SQL directo dentro de la transacción de la prueba (se deshace al terminar)."""
    async with bd._fabrica() as sesion:
        await sesion.execute(text(consulta), params)
        await sesion.commit()


async def _nuevo_estudiante(cliente, admin, ci: str = NUEVO["ci"]) -> str:
    r = await cliente.post("/personas/estudiantes", headers=admin, json={"persona": {**NUEVO, "ci": ci}})
    assert r.status_code == 201, r.text
    return ci


async def _curso_con_cupo(cliente, admin) -> int:
    opciones = (await cliente.get("/personas/estudiantes/opciones", headers=admin)).json()
    return next(c["id_curso"] for c in opciones["cursos"] if c["inscritos"] < c["cupo_maximo"])


async def test_cu16_solo_administrador(cliente, profesor):
    assert (await cliente.get("/academico/inscripciones/estudiantes", headers=profesor)).status_code == 403
    r = await cliente.post("/academico/inscripciones", headers=profesor, json={"ci_estudiante": "4500001", "id_curso": 1})
    assert r.status_code == 403


async def test_cu16_buscar_por_ci_rude_y_nombre(cliente, admin):
    for q in ("4500001", "rude-4500001"):
        r = (await cliente.get("/academico/inscripciones/estudiantes", params={"q": q}, headers=admin)).json()
        assert r["total"] == 1 and r["items"][0]["id_inscripcion"] is not None
    await _nuevo_estudiante(cliente, admin)
    r = (await cliente.get("/academico/inscripciones/estudiantes", params={"q": "arteaga"}, headers=admin)).json()
    assert r["total"] == 1 and r["items"][0]["id_inscripcion"] is None


async def test_cu16_inscribir_y_emitir_boleta(cliente, admin):
    ci = await _nuevo_estudiante(cliente, admin)
    id_curso = await _curso_con_cupo(cliente, admin)
    r = await cliente.post("/academico/inscripciones", headers=admin, json={"ci_estudiante": ci, "id_curso": id_curso})
    assert r.status_code == 201, r.text
    boleta = r.json()
    assert boleta["ci"] == ci and boleta["estado_inscripcion"] == "activa" and boleta["gestion"] == 2026
    assert isinstance(boleta["materias"], list) and isinstance(boleta["horario"], list)

    r = await cliente.get(f"/academico/inscripciones/{boleta['id_inscripcion']}/boleta", headers=admin)
    assert r.status_code == 200 and r.json()["curso"] == boleta["curso"]

    r = await cliente.post("/academico/inscripciones", headers=admin, json={"ci_estudiante": ci, "id_curso": id_curso})
    assert r.status_code == 409


async def test_cu16_boleta_con_materias_y_horario(cliente, admin):
    r = await cliente.get("/academico/inscripciones/1/boleta", headers=admin)
    assert r.status_code == 200, r.text
    boleta = r.json()
    assert boleta["ci"] == "4500001" and boleta["materias"]
    dias = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    orden = [(dias.index(b["dia"]), b["hora_inicio"]) for b in boleta["horario"]]
    assert orden == sorted(orden)
    assert (await cliente.get("/academico/inscripciones/999999/boleta", headers=admin)).status_code == 404


async def test_cu16_estudiante_inactivo(cliente, admin):
    ci = await _nuevo_estudiante(cliente, admin)
    r = await cliente.post(f"/personas/estudiantes/{ci}/baja", json={"motivo": "Prueba"}, headers=admin)
    assert r.status_code == 200, r.text
    r = await cliente.post("/academico/inscripciones", headers=admin,
                           json={"ci_estudiante": ci, "id_curso": await _curso_con_cupo(cliente, admin)})
    assert r.status_code == 400 and "inactivo" in r.json()["detalle"]


async def test_cu16_estudiante_inexistente(cliente, admin):
    r = await cliente.post("/academico/inscripciones", headers=admin, json={"ci_estudiante": "9999999", "id_curso": 1})
    assert r.status_code == 404


async def test_cu16_curso_sin_cupo(cliente, admin):
    ci = await _nuevo_estudiante(cliente, admin)
    await _sql("UPDATE curso SET cupo_maximo = 6 WHERE id_curso = 3")   # ya tiene 6 inscritos activos
    r = await cliente.post("/academico/inscripciones", headers=admin, json={"ci_estudiante": ci, "id_curso": 3})
    assert r.status_code == 400 and "cupo" in r.json()["detalle"]


async def test_cu16_cuotas_vencidas_de_gestion_anterior(cliente, admin):
    ci = await _nuevo_estudiante(cliente, admin)
    await _sql("""INSERT INTO gestion (anio, fecha_inicio_g, fecha_final_g, estado_gestion)
                  VALUES (2025, '2025-02-03', '2025-12-05', 'cerrada')""")
    await _sql("""INSERT INTO pago_mensualidad (mes, monto, fecha_vencimiento, ci_estudiante_pago, id_gestion_pago)
                  SELECT 11, 350, '2025-11-10', :ci, id_gestion FROM gestion WHERE anio = 2025""", ci=ci)
    r = await cliente.post("/academico/inscripciones", headers=admin,
                           json={"ci_estudiante": ci, "id_curso": await _curso_con_cupo(cliente, admin)})
    assert r.status_code == 400 and "cuotas vencidas" in r.json()["detalle"]

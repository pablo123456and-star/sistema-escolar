"""Pruebas del CU10: registrar y gestionar docentes."""

NUEVO = {
    "ci": "7700010", "expedido": "LP", "nombre_persona": "Carla", "apellidos": "Vargas Peña",
    "sexo": "F", "fecha_nacimiento": "1990-04-15", "telefono": "71111111",
}
PROFESIONALES = {"titulo_academico": "Lic. en Química", "fecha_contrato": "2026-02-01", "anios_experiencia": 4}


async def test_cu10_solo_administrador(cliente, profesor):
    assert (await cliente.get("/personas/docentes", headers=profesor)).status_code == 403
    assert (await cliente.post("/personas/docentes", headers=profesor, json={"persona": NUEVO})).status_code == 403


async def test_cu10_registrar_y_listar(cliente, admin):
    r = await cliente.post("/personas/docentes", headers=admin, json={"persona": NUEVO, **PROFESIONALES})
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["estado_persona"] == "activo" and d["titulo_academico"] == "Lic. en Química"
    assert d["anios_experiencia"] == 4 and d["asignaciones"] == [] and not d["tiene_usuario"]

    lista = (await cliente.get("/personas/docentes", params={"q": "7700010"}, headers=admin)).json()
    assert lista["total"] == 1 and lista["items"][0]["cantidad_asignaciones"] == 0

    r = await cliente.post("/personas/docentes", headers=admin, json={"persona": NUEVO})
    assert r.status_code == 409


async def test_cu10_validaciones(cliente, admin):
    r = await cliente.post("/personas/docentes", headers=admin, json={"persona": NUEVO, "anios_experiencia": -1})
    assert r.status_code == 422
    r = await cliente.post("/personas/docentes", headers=admin, json={"persona": {**NUEVO, "ci": "12ab"}})
    assert r.status_code == 422


async def test_cu10_reutiliza_persona_existente(cliente, admin):
    # 3000006 ya es tutora (de profesión, profesora): se registra también como docente sin duplicar la persona
    buscada = (await cliente.get("/personas/buscar/3000006", headers=admin)).json()
    assert buscada["es_tutor"] and not buscada["es_profesor"]
    persona = {k: buscada[k] for k in ("ci", "nombre_persona", "apellidos")}
    r = await cliente.post("/personas/docentes", headers=admin, json={"persona": persona, "anios_experiencia": 2})
    assert r.status_code == 201, r.text
    buscada = (await cliente.get("/personas/buscar/3000006", headers=admin)).json()
    assert buscada["es_tutor"] and buscada["es_profesor"]


async def test_cu10_detalle_y_actualizacion_parcial(cliente, admin):
    d = (await cliente.get("/personas/docentes/2000001", headers=admin)).json()
    assert d["tiene_usuario"] and d["gestion"] is not None
    assert "Matematica" in [a["materia"] for a in d["asignaciones"]]

    r = await cliente.patch("/personas/docentes/2000001", headers=admin,
                            json={"titulo_academico": "M.Sc. en Matemática", "persona": {"telefono": "70000001"}})
    assert r.status_code == 200
    d2 = r.json()
    assert d2["titulo_academico"] == "M.Sc. en Matemática" and d2["telefono"] == "70000001"
    # lo que no se envió no cambia
    assert d2["anios_experiencia"] == d["anios_experiencia"] and d2["fecha_contrato"] == d["fecha_contrato"]

    assert (await cliente.get("/personas/docentes/4500001", headers=admin)).status_code == 404


async def test_cu10_no_da_baja_con_asignaciones(cliente, admin):
    r = await cliente.post("/personas/docentes/2000001/baja", json={"motivo": "Renuncia"}, headers=admin)
    assert r.status_code == 400 and "asignada" in r.json()["detalle"]


async def test_cu10_baja_y_reactivar(cliente, admin):
    await cliente.post("/personas/docentes", headers=admin, json={"persona": NUEVO})
    r = await cliente.post("/personas/docentes/7700010/baja", json={"motivo": "Fin de contrato"}, headers=admin)
    assert r.status_code == 200 and r.json()["estado_persona"] == "inactivo"
    lista = (await cliente.get("/personas/docentes", params={"estado": "inactivo"}, headers=admin)).json()
    assert "7700010" in [d["ci"] for d in lista["items"]]

    r = await cliente.post("/personas/docentes/7700010/baja", json={"motivo": "Otra vez"}, headers=admin)
    assert r.status_code == 400

    r = await cliente.post("/personas/docentes/7700010/reactivar", headers=admin)
    assert r.status_code == 200 and r.json()["estado_persona"] == "activo"

"""Pruebas del paquete personas: CU06 (estudiantes) y CU08 (tutores y vínculos)."""

NUEVO = {
    "ci": "7700001", "expedido": "SC", "nombre_persona": "Lucía", "apellidos": "Gutiérrez Paz",
    "sexo": "F", "fecha_nacimiento": "2015-05-10", "telefono": "71234567",
}


async def _curso_con_cupo(cliente, admin) -> int:
    opciones = (await cliente.get("/personas/estudiantes/opciones", headers=admin)).json()
    return next(c["id_curso"] for c in opciones["cursos"] if c["inscritos"] < c["cupo_maximo"])


# ---- CU06 ---------------------------------------------------------------------
async def test_cu06_solo_administrador(cliente, profesor):
    assert (await cliente.get("/personas/estudiantes", headers=profesor)).status_code == 403


async def test_cu06_registrar_con_tutor_e_inscripcion(cliente, admin):
    id_curso = await _curso_con_cupo(cliente, admin)
    r = await cliente.post("/personas/estudiantes", headers=admin, json={
        "persona": NUEVO, "rude": "RUDE-7700001",
        "tutor": {"ci_tutor": "3000002", "parentesco": "Madre", "es_principal": True, "es_responsable_pago": True},
        "id_curso": id_curso,
    })
    assert r.status_code == 201, r.text
    e = r.json()
    assert e["estado_persona"] == "activo" and e["inscripcion"]["estado_inscripcion"] == "activa"
    assert e["tutores"][0]["ci_tutor"] == "3000002" and e["tutores"][0]["es_principal"]

    lista = (await cliente.get("/personas/estudiantes", params={"q": "gutiérrez"}, headers=admin)).json()
    assert lista["total"] == 1 and lista["items"][0]["tutor_principal"]

    r = await cliente.post("/personas/estudiantes", headers=admin, json={"persona": NUEVO})
    assert r.status_code == 409


async def test_cu06_reutiliza_persona_existente(cliente, admin):
    # 3000002 ya es tutora: se registra también como estudiante sin duplicar la persona
    buscada = (await cliente.get("/personas/buscar/3000002", headers=admin)).json()
    assert buscada["es_tutor"] and not buscada["es_estudiante"]
    persona = {k: buscada[k] for k in ("ci", "nombre_persona", "apellidos")}
    r = await cliente.post("/personas/estudiantes", headers=admin, json={"persona": persona})
    assert r.status_code == 201


async def test_cu06_rude_duplicado_y_validaciones(cliente, admin):
    rude = (await cliente.get("/personas/estudiantes/4500001", headers=admin)).json()["rude"]
    r = await cliente.post("/personas/estudiantes", headers=admin, json={"persona": NUEVO, "rude": rude})
    assert r.status_code == 409 and "RUDE" in r.json()["detalle"]
    r = await cliente.post("/personas/estudiantes", headers=admin, json={"persona": {**NUEVO, "ci": "12ab"}})
    assert r.status_code == 422


async def test_cu06_actualizar_filtrar_y_baja(cliente, admin):
    r = await cliente.patch("/personas/estudiantes/4500001", headers=admin,
                            json={"persona": {"telefono": "76543210", "direccion": ""}})
    assert r.status_code == 200 and r.json()["telefono"] == "76543210" and r.json()["direccion"] is None

    ins = r.json()["inscripcion"]
    grado = next(c for c in (await cliente.get("/personas/estudiantes/opciones", headers=admin)).json()["cursos"]
                 if c["nombre_curso"] == ins["curso"])
    lista = (await cliente.get("/personas/estudiantes", headers=admin,
                               params={"id_grado": grado["id_grado"], "paralelo": grado["paralelo"]})).json()
    assert "4500001" in [e["ci"] for e in lista["items"]]

    r = await cliente.post("/personas/estudiantes/4500001/baja", json={"motivo": "Cambio de ciudad"}, headers=admin)
    assert r.status_code == 200 and r.json()["estado_persona"] == "inactivo" and r.json()["inscripcion"] is not None
    assert r.json()["inscripcion"]["estado_inscripcion"] == "retirada"
    # su usuario (mquispe) ya no puede ingresar
    r = await cliente.post("/seguridad/sesion", json={"identificador": "mquispe", "contrasena": "Escuela2026"})
    assert r.status_code == 400

    r = await cliente.post("/personas/estudiantes/4500001/reactivar", headers=admin)
    assert r.json()["estado_persona"] == "activo"
    r = await cliente.post("/seguridad/sesion", json={"identificador": "mquispe", "contrasena": "Escuela2026"})
    assert r.status_code == 200


# ---- CU08 ---------------------------------------------------------------------
async def test_cu08_registrar_tutor_y_vincular(cliente, admin):
    r = await cliente.post("/personas/tutores", headers=admin,
                           json={"persona": {**NUEVO, "ci": "7700002", "fecha_nacimiento": "1985-01-01"},
                                 "ocupacion": "Comerciante"})
    assert r.status_code == 201 and r.json()["estudiantes"] == []

    r = await cliente.post("/personas/tutores/7700002/estudiantes", headers=admin,
                           json={"ci_estudiante": "4500002", "parentesco": "Tía", "es_principal": True})
    assert r.status_code == 201 and r.json()["es_principal"]
    # el principal anterior (3000003) dejó de serlo: solo hay uno por estudiante
    tutores = (await cliente.get("/personas/estudiantes/4500002", headers=admin)).json()["tutores"]
    assert [t["ci_tutor"] for t in tutores if t["es_principal"]] == ["7700002"]

    r = await cliente.post("/personas/tutores/7700002/estudiantes", headers=admin,
                           json={"ci_estudiante": "4500002", "parentesco": "Tía"})
    assert r.status_code == 409

    r = await cliente.patch("/personas/tutores/7700002/estudiantes/4500002", headers=admin,
                            json={"autorizado_recoger": False})
    assert r.json()["autorizado_recoger"] is False

    assert (await cliente.delete("/personas/tutores/7700002/estudiantes/4500002", headers=admin)).status_code == 204


async def test_cu08_no_desvincula_si_hay_pagos(cliente, admin):
    r = await cliente.delete("/personas/tutores/3000003/estudiantes/4500002", headers=admin)
    assert r.status_code == 400 and "pagos" in r.json()["detalle"]


async def test_cu08_listar_y_detalle(cliente, admin):
    r = (await cliente.get("/personas/tutores", params={"q": "3000006"}, headers=admin)).json()
    assert r["total"] == 1 and r["items"][0]["cantidad_estudiantes"] == 4
    d = (await cliente.get("/personas/tutores/3000001", headers=admin)).json()
    assert d["tiene_usuario"] and len(d["estudiantes"]) == 2

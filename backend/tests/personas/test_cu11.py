"""Pruebas del CU11: registrar y gestionar personal administrativo."""

NUEVO = {
    "ci": "8800011",
    "expedido": "LP",
    "nombre_persona": "Beatriz",
    "apellidos": "Miranda Rojas",
    "sexo": "F",
    "fecha_nacimiento": "1992-07-20",
    "telefono": "72222222",
    "email": "beatriz@colegio.edu.bo",
}


async def test_cu11_solo_administrador(cliente, profesor):
    assert (await cliente.get("/personas/administrativos", headers=profesor)).status_code == 403
    assert (
        await cliente.post("/personas/administrativos", headers=profesor, json={"persona": NUEVO, "cargo": "Secretaria"})
    ).status_code == 403


async def test_cu11_registrar_y_listar(cliente, admin):
    r = await cliente.post("/personas/administrativos", headers=admin, json={"persona": NUEVO, "cargo": "Secretaria"})
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["estado_persona"] == "activo"
    assert d["cargo"] == "Secretaria"
    assert not d["tiene_usuario"]

    lista = (await cliente.get("/personas/administrativos", params={"q": "8800011"}, headers=admin)).json()
    assert lista["total"] == 1
    assert lista["items"][0]["cargo"] == "Secretaria"

    # Conflicto al registrar con el mismo CI como administrativo
    r_dup = await cliente.post(
        "/personas/administrativos", headers=admin, json={"persona": NUEVO, "cargo": "Auxiliar"}
    )
    assert r_dup.status_code == 409


async def test_cu11_validaciones(cliente, admin):
    # Cargo excede longitud
    r = await cliente.post(
        "/personas/administrativos", headers=admin, json={"persona": NUEVO, "cargo": "A" * 51}
    )
    assert r.status_code == 422
    # CI inválido
    r_ci = await cliente.post(
        "/personas/administrativos", headers=admin, json={"persona": {**NUEVO, "ci": "invalido"}, "cargo": "Cajero"}
    )
    assert r_ci.status_code == 422


async def test_cu11_detalle_y_actualizacion_parcial(cliente, admin):
    r = await cliente.post(
        "/personas/administrativos",
        headers=admin,
        json={"persona": {**NUEVO, "ci": "8800012"}, "cargo": "Encargado de Almacén"},
    )
    assert r.status_code == 201
    d = (await cliente.get("/personas/administrativos/8800012", headers=admin)).json()
    assert d["cargo"] == "Encargado de Almacén"

    r_patch = await cliente.patch(
        "/personas/administrativos/8800012",
        headers=admin,
        json={"cargo": "Jefe de Inventario", "persona": {"telefono": "73333333"}},
    )
    assert r_patch.status_code == 200
    d2 = r_patch.json()
    assert d2["cargo"] == "Jefe de Inventario"
    assert d2["telefono"] == "73333333"
    # Lo que no se envió se mantiene
    assert d2["email"] == d["email"]


async def test_cu11_baja_y_reactivacion(cliente, admin):
    await cliente.post(
        "/personas/administrativos",
        headers=admin,
        json={"persona": {**NUEVO, "ci": "8800013"}, "cargo": "Regente"},
    )
    # Baja lógica
    r_baja = await cliente.post(
        "/personas/administrativos/8800013/baja",
        headers=admin,
        json={"motivo": "Fin de contrato temporal"},
    )
    assert r_baja.status_code == 200
    assert r_baja.json()["estado_persona"] == "inactivo"

    # Reactivación
    r_reac = await cliente.post("/personas/administrativos/8800013/reactivar", headers=admin)
    assert r_reac.status_code == 200
    assert r_reac.json()["estado_persona"] == "activo"

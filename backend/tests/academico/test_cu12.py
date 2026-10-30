"""Pruebas del CU12: gestionar niveles educativos, grados y paralelos (cursos)."""


async def _estructura(cliente, admin) -> dict:
    r = await cliente.get("/academico/estructura", headers=admin)
    assert r.status_code == 200, r.text
    return r.json()


def _nivel(estructura: dict, nombre: str) -> dict:
    return next(n for n in estructura["niveles"] if n["nombre_nivel"] == nombre)


def _primero_secundaria_a(estructura: dict) -> dict:
    """1ro A de Secundaria: en 08_datos_prueba tiene 6 estudiantes inscritos en 2026."""
    grado = next(g for g in _nivel(estructura, "Secundaria")["grados"] if g["orden_grado"] == 1)
    return next(c for c in grado["cursos"] if c["paralelo"] == "A")


async def _nuevo_nivel(cliente, admin, nombre: str = "Técnico Medio") -> int:
    r = await cliente.post("/academico/niveles", headers=admin, json={"nombre_nivel": nombre})
    assert r.status_code == 201, r.text
    return r.json()["id_nivel"]


async def _nuevo_grado(cliente, admin, id_nivel: int, nombre: str = "1ro", orden: int = 1) -> int:
    r = await cliente.post("/academico/grados", headers=admin,
                           json={"id_nivel": id_nivel, "nombre_grado": nombre, "orden_grado": orden})
    assert r.status_code == 201, r.text
    return r.json()["id_grado"]


async def test_cu12_solo_administrador(cliente, profesor):
    assert (await cliente.get("/academico/estructura", headers=profesor)).status_code == 403
    assert (await cliente.post("/academico/niveles", headers=profesor, json={"nombre_nivel": "X"})).status_code == 403
    assert (await cliente.delete("/academico/cursos/1", headers=profesor)).status_code == 403


async def test_cu12_estructura_con_inscritos(cliente, admin):
    e = await _estructura(cliente, admin)
    assert e["gestion"] == 2026
    assert [n["nombre_nivel"] for n in e["niveles"]][:3] == ["Inicial", "Primaria", "Secundaria"]
    secundaria = _nivel(e, "Secundaria")
    assert [g["orden_grado"] for g in secundaria["grados"]] == [1, 2, 3, 4, 5, 6]
    assert all(g["materias"] > 0 for g in secundaria["grados"])
    assert _primero_secundaria_a(e)["inscritos"] == 6


async def test_cu12_niveles(cliente, admin):
    r = await cliente.post("/academico/niveles", headers=admin, json={"nombre_nivel": "  Técnico   Medio "})
    assert r.status_code == 201 and r.json()["nombre_nivel"] == "Técnico Medio"
    id_nivel = r.json()["id_nivel"]

    r = await cliente.post("/academico/niveles", headers=admin, json={"nombre_nivel": "técnico medio"})
    assert r.status_code == 409

    r = await cliente.patch(f"/academico/niveles/{id_nivel}", headers=admin, json={"nombre_nivel": "Primaria"})
    assert r.status_code == 409
    r = await cliente.patch(f"/academico/niveles/{id_nivel}", headers=admin, json={"nombre_nivel": "Técnico"})
    assert r.status_code == 200 and r.json()["nombre_nivel"] == "Técnico"

    assert (await cliente.delete(f"/academico/niveles/{id_nivel}", headers=admin)).status_code == 204
    assert (await cliente.delete(f"/academico/niveles/{id_nivel}", headers=admin)).status_code == 404


async def test_cu12_no_elimina_nivel_en_uso(cliente, admin):
    secundaria = _nivel(await _estructura(cliente, admin), "Secundaria")
    r = await cliente.delete(f"/academico/niveles/{secundaria['id_nivel']}", headers=admin)
    assert r.status_code == 409
    assert "6 grado(s)" in r.json()["detalle"] and "arancel" in r.json()["detalle"]


async def test_cu12_grados(cliente, admin):
    id_nivel = await _nuevo_nivel(cliente, admin)
    id_grado = await _nuevo_grado(cliente, admin, id_nivel)

    r = await cliente.post("/academico/grados", headers=admin,
                           json={"id_nivel": id_nivel, "nombre_grado": "1RO", "orden_grado": 2})
    assert r.status_code == 409 and "llamado" in r.json()["detalle"]
    r = await cliente.post("/academico/grados", headers=admin,
                           json={"id_nivel": id_nivel, "nombre_grado": "2do", "orden_grado": 1})
    assert r.status_code == 409 and "orden 1" in r.json()["detalle"]
    r = await cliente.post("/academico/grados", headers=admin,
                           json={"id_nivel": 999999, "nombre_grado": "2do", "orden_grado": 2})
    assert r.status_code == 404

    r = await cliente.patch(f"/academico/grados/{id_grado}", headers=admin,
                            json={"nombre_grado": "Primero", "orden_grado": 3})
    assert r.status_code == 200 and r.json()["orden_grado"] == 3
    r = await cliente.patch(f"/academico/grados/{id_grado}", headers=admin, json={})
    assert r.status_code == 422

    # Un nivel con grados no se elimina; el grado vacío sí
    assert (await cliente.delete(f"/academico/niveles/{id_nivel}", headers=admin)).status_code == 409
    assert (await cliente.delete(f"/academico/grados/{id_grado}", headers=admin)).status_code == 204
    assert (await cliente.delete(f"/academico/niveles/{id_nivel}", headers=admin)).status_code == 204


async def test_cu12_no_elimina_grado_con_plan_de_estudios(cliente, admin):
    id_grado = await _nuevo_grado(cliente, admin, await _nuevo_nivel(cliente, admin))
    materia = await cliente.post("/academico/materias", headers=admin,
                                 json={"nombre_materia": "Robótica CU12", "carga_horaria": 2})
    r = await cliente.post(f"/academico/grados/{id_grado}/materias", headers=admin,
                           json={"id_materia": materia.json()["id_materia"]})
    assert r.status_code == 201, r.text

    r = await cliente.delete(f"/academico/grados/{id_grado}", headers=admin)
    assert r.status_code == 409 and "plan de estudios" in r.json()["detalle"]


async def test_cu12_paralelos(cliente, admin):
    id_grado = await _nuevo_grado(cliente, admin, await _nuevo_nivel(cliente, admin))

    r = await cliente.post("/academico/cursos", headers=admin, json={"id_grado": id_grado, "paralelo": " a ", "cupo_maximo": 30})
    assert r.status_code == 201 and r.json()["paralelo"] == "A"
    id_curso = r.json()["id_curso"]

    assert (await cliente.post("/academico/cursos", headers=admin,
                               json={"id_grado": id_grado, "paralelo": "A", "cupo_maximo": 30})).status_code == 409
    for invalido in ({"paralelo": "B", "cupo_maximo": 0}, {"paralelo": "A-1", "cupo_maximo": 30}):
        r = await cliente.post("/academico/cursos", headers=admin, json={"id_grado": id_grado, **invalido})
        assert r.status_code == 422

    r = await cliente.patch(f"/academico/cursos/{id_curso}", headers=admin, json={"paralelo": "b", "cupo_maximo": 25})
    assert r.status_code == 200 and r.json() == {**r.json(), "paralelo": "B", "cupo_maximo": 25}

    # Un grado con paralelos no se elimina; el paralelo vacío sí
    r = await cliente.delete(f"/academico/grados/{id_grado}", headers=admin)
    assert r.status_code == 409 and "paralelo" in r.json()["detalle"]
    assert (await cliente.delete(f"/academico/cursos/{id_curso}", headers=admin)).status_code == 204


async def test_cu12_cupo_no_menor_a_inscritos(cliente, admin):
    curso = _primero_secundaria_a(await _estructura(cliente, admin))
    r = await cliente.patch(f"/academico/cursos/{curso['id_curso']}", headers=admin, json={"cupo_maximo": 5})
    assert r.status_code == 400 and "6 inscritos" in r.json()["detalle"]
    r = await cliente.patch(f"/academico/cursos/{curso['id_curso']}", headers=admin, json={"cupo_maximo": 6})
    assert r.status_code == 200


async def test_cu12_no_elimina_paralelo_en_uso(cliente, admin):
    curso = _primero_secundaria_a(await _estructura(cliente, admin))
    r = await cliente.delete(f"/academico/cursos/{curso['id_curso']}", headers=admin)
    assert r.status_code == 409
    assert "inscripción" in r.json()["detalle"] and "profesor" in r.json()["detalle"]

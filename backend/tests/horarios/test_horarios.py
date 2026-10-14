"""Pruebas del paquete horarios: CU19 (generar horario) y CU20 (consultar horarios).

Datos de 08_datos_prueba.sql: curso 14 = 1ro A Secundaria (5 asignaciones, 7 bloques) y curso 3 = 6to A Primaria.
rflores (2000001) dicta Matemática solo en el curso 14; mquispe (4500001) está en el curso 14;
marioq (3000001) es tutor de 4500001 (curso 14) y de 4500007 (curso 3).
"""
from tests.conftest import USUARIOS, iniciar


# ---- CU19 ---------------------------------------------------------------------
async def test_cu19_solo_administrador(cliente, profesor):
    assert (await cliente.get("/horarios/cursos", headers=profesor)).status_code == 403
    r = await cliente.post("/horarios/cursos/14/bloques", headers=profesor,
                           json={"id_asignacion": 5, "dia": "miercoles", "hora_inicio": "09:45", "hora_final": "11:15"})
    assert r.status_code == 403


async def test_cu19_cursos_y_horario_del_curso(cliente, admin):
    cursos = (await cliente.get("/horarios/cursos", headers=admin)).json()
    curso = next(c for c in cursos if c["id_curso"] == 14)
    assert curso["asignaciones"] == 5 and curso["bloques"] == 7

    r = (await cliente.get("/horarios/cursos/14", headers=admin)).json()
    assert len(r["asignaciones"]) == 5 and len(r["bloques"]) == 7
    assert [b["dia_orden"] for b in r["bloques"]] == sorted(b["dia_orden"] for b in r["bloques"])

    sin_asignaciones = next(c for c in cursos if c["asignaciones"] == 0)
    r = (await cliente.get(f"/horarios/cursos/{sin_asignaciones['id_curso']}", headers=admin)).json()
    assert r["asignaciones"] == [] and r["bloques"] == []
    assert (await cliente.get("/horarios/cursos/99999", headers=admin)).status_code == 404


async def test_cu19_agregar_modificar_y_eliminar(cliente, admin):
    r = await cliente.post("/horarios/cursos/14/bloques", headers=admin,
                           json={"id_asignacion": 5, "dia": "miercoles", "hora_inicio": "09:45", "hora_final": "11:15"})
    assert r.status_code == 201, r.text
    bloque = r.json()
    assert bloque["nombre_materia"] == "Matematica" and bloque["aula"] == "B-201"

    r = await cliente.patch(f"/horarios/bloques/{bloque['id_horario']}", headers=admin,
                            json={"dia": "viernes", "hora_inicio": "11:30", "hora_final": "13:00"})
    assert r.status_code == 200, r.text
    assert r.json()["dia"] == "viernes" and r.json()["hora_inicio"] == "11:30:00"

    assert (await cliente.delete(f"/horarios/bloques/{bloque['id_horario']}", headers=admin)).status_code == 204
    assert len((await cliente.get("/horarios/cursos/14", headers=admin)).json()["bloques"]) == 7


async def test_cu19_choques_los_detecta_la_bd(cliente, admin):
    # La docente de Comunicación (2000002) ya dicta el martes 08:00 en 6to A
    r = await cliente.post("/horarios/cursos/14/bloques", headers=admin,
                           json={"id_asignacion": 7, "dia": "martes", "hora_inicio": "08:00", "hora_final": "09:30"})
    assert r.status_code == 400 and "docente" in r.json()["detalle"] and "6to A" in r.json()["detalle"]

    # El curso 14 ya tiene Biología el martes 08:00 (otro docente y otra aula)
    r = await cliente.post("/horarios/cursos/14/bloques", headers=admin,
                           json={"id_asignacion": 9, "dia": "martes", "hora_inicio": "08:30", "hora_final": "09:00"})
    assert r.status_code == 400 and "el curso ya tiene Biologia-Geografia" in r.json()["detalle"]

    # Mover un bloque encima de otro también choca
    r = await cliente.patch("/horarios/bloques/7", headers=admin, json={"dia": "lunes"})
    assert r.status_code == 400 and "Choque de horario" in r.json()["detalle"]


async def test_cu19_validaciones(cliente, admin):
    r = await cliente.post("/horarios/cursos/14/bloques", headers=admin,
                           json={"id_asignacion": 1, "dia": "sabado", "hora_inicio": "08:00", "hora_final": "09:00"})
    assert r.status_code == 400 and "no pertenece" in r.json()["detalle"]

    r = await cliente.post("/horarios/cursos/14/bloques", headers=admin,
                           json={"id_asignacion": 5, "dia": "sabado", "hora_inicio": "10:00", "hora_final": "09:00"})
    assert r.status_code == 422

    r = await cliente.patch("/horarios/bloques/7", headers=admin, json={"hora_final": "07:00"})
    assert r.status_code == 400 and "hora final" in r.json()["detalle"]

    assert (await cliente.patch("/horarios/bloques/7", headers=admin, json={})).status_code == 422
    assert (await cliente.delete("/horarios/bloques/99999", headers=admin)).status_code == 404


# ---- CU20 ---------------------------------------------------------------------
async def test_cu20_administrador_ve_cualquier_curso_o_docente(cliente, admin):
    opciones = (await cliente.get("/horarios/consulta/opciones", headers=admin)).json()
    assert {3, 14} <= {c["id_curso"] for c in opciones["cursos"]} and opciones["docentes"]

    r = (await cliente.get("/horarios/consulta", params={"id_curso": 3}, headers=admin)).json()
    assert r["tipo"] == "curso" and len(r["bloques"]) == 7
    r = (await cliente.get("/horarios/consulta", params={"ci_profesor": "2000002"}, headers=admin)).json()
    assert r["tipo"] == "docente" and {b["id_curso"] for b in r["bloques"]} == {3, 14}

    assert (await cliente.get("/horarios/consulta", headers=admin)).status_code == 400


async def test_cu20_profesor(cliente, profesor):
    opciones = (await cliente.get("/horarios/consulta/opciones", headers=profesor)).json()
    assert [c["id_curso"] for c in opciones["cursos"]] == [14] and opciones["docentes"][0]["ci"] == "2000001"

    r = await cliente.get("/horarios/consulta", params={"ci_profesor": "2000001"}, headers=profesor)
    assert r.status_code == 200 and len(r.json()["bloques"]) == 2
    assert (await cliente.get("/horarios/consulta", params={"id_curso": 14}, headers=profesor)).status_code == 200
    assert (await cliente.get("/horarios/consulta", params={"id_curso": 3}, headers=profesor)).status_code == 403
    assert (await cliente.get("/horarios/consulta", params={"ci_profesor": "2000002"}, headers=profesor)).status_code == 403


async def test_cu20_estudiante_solo_su_curso(cliente):
    estudiante = await iniciar(cliente, USUARIOS["estudiante"])
    opciones = (await cliente.get("/horarios/consulta/opciones", headers=estudiante)).json()
    assert [c["id_curso"] for c in opciones["cursos"]] == [14]

    assert (await cliente.get("/horarios/consulta", params={"id_curso": 14}, headers=estudiante)).status_code == 200
    assert (await cliente.get("/horarios/consulta", params={"id_curso": 3}, headers=estudiante)).status_code == 403
    r = await cliente.get("/horarios/consulta", params={"ci_profesor": "2000001"}, headers=estudiante)
    assert r.status_code == 403


async def test_cu20_tutor_ve_los_cursos_de_sus_estudiantes(cliente):
    tutor = await iniciar(cliente, USUARIOS["tutor"])
    opciones = (await cliente.get("/horarios/consulta/opciones", headers=tutor)).json()
    assert {e["id_curso"] for e in opciones["estudiantes"]} == {3, 14}

    for id_curso in (3, 14):
        assert (await cliente.get("/horarios/consulta", params={"id_curso": id_curso}, headers=tutor)).status_code == 200
    assert (await cliente.get("/horarios/consulta", params={"id_curso": 1}, headers=tutor)).status_code == 403


async def test_cu20_requiere_sesion(cliente):
    assert (await cliente.get("/horarios/consulta", params={"id_curso": 14})).status_code == 401

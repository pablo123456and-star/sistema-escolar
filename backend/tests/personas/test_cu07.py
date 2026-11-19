"""Pruebas del CU07: antecedentes médicos y seguimiento del estudiante.

Datos de 08_datos_prueba.sql:
  - rflores (2000001) dicta Matemática en 1ro A Secundaria (estudiantes 4500001 a 4500006),
    no dicta en 6to A Primaria (4500007 a 4500012).
  - marioq (3000001) es tutor de Mateo (4500001) y Sofía (4500007).
  - 4500002 tiene observación médica ("Asma leve..."); 4500007 tiene un seguimiento de mérito.
"""
from datetime import date, timedelta

from tests.conftest import iniciar

URL = "/personas/seguimiento/estudiantes"
CONDUCTA = {"tipo": "conducta", "gravedad": "leve", "descripcion": "Usa el celular durante la clase",
            "accion_tomada": "Llamada de atención verbal"}


async def test_cu07_roles(cliente, admin):
    estudiante = await iniciar(cliente, "mquispe")
    assert (await cliente.get(URL, headers=estudiante)).status_code == 403
    assert (await cliente.get(f"{URL}/4500001", headers=estudiante)).status_code == 403
    assert (await cliente.get(URL)).status_code == 401
    tutor = await iniciar(cliente, "marioq")
    r = await cliente.post(f"{URL}/4500001/seguimientos", headers=tutor, json={"tipo": "otro", "descripcion": "Prueba"})
    assert r.status_code == 403
    r = await cliente.put(f"{URL}/4500001/antecedentes", headers=tutor, json={"observacion_medica": "x"})
    assert r.status_code == 403


async def test_cu07_lista_segun_rol(cliente, admin, profesor):
    todos = (await cliente.get(URL, headers=admin, params={"tamano": 100})).json()
    assert {f"45000{n:02d}" for n in range(1, 13)} <= {e["ci"] for e in todos["items"]}

    suyos = (await cliente.get(URL, headers=profesor, params={"tamano": 100})).json()
    assert {e["ci"] for e in suyos["items"]} == {f"450000{n}" for n in range(1, 7)}
    diego = next(e for e in suyos["items"] if e["ci"] == "4500002")
    assert diego["tiene_observacion_medica"] and diego["curso"].startswith("1ro A")

    tutor = await iniciar(cliente, "marioq")
    hijos = (await cliente.get(URL, headers=tutor)).json()
    assert {e["ci"] for e in hijos["items"]} == {"4500001", "4500007"}
    sofia = next(e for e in hijos["items"] if e["ci"] == "4500007")
    assert sofia["cantidad_seguimientos"] == 1 and sofia["ultimo_seguimiento"] == "2026-09-15"

    buscado = (await cliente.get(URL, headers=profesor, params={"q": "diego"})).json()
    assert buscado["total"] == 1 and buscado["items"][0]["ci"] == "4500002"


async def test_cu07_ficha_y_permisos(cliente, admin, profesor):
    r = await cliente.get(f"{URL}/4500002", headers=profesor)
    assert r.status_code == 200, r.text
    f = r.json()
    assert f["observacion_medica"].startswith("Asma leve")       # el profesor la ve...
    assert not f["puede_editar_antecedentes"]                      # ...pero no la edita
    assert f["puede_registrar_seguimiento"]

    # Estudiante de otro curso: sin permiso (no se revela si existe)
    assert (await cliente.get(f"{URL}/4500007", headers=profesor)).status_code == 403
    assert (await cliente.get(f"{URL}/9999999", headers=profesor)).status_code == 403
    assert (await cliente.get(f"{URL}/9999999", headers=admin)).status_code == 404

    tutor = await iniciar(cliente, "marioq")
    f = (await cliente.get(f"{URL}/4500007", headers=tutor)).json()
    assert not f["puede_editar_antecedentes"] and not f["puede_registrar_seguimiento"]
    assert [s["tipo"] for s in f["seguimientos"]] == ["merito"]
    assert (await cliente.get(f"{URL}/4500002", headers=tutor)).status_code == 403

    f = (await cliente.get(f"{URL}/4500001", headers=admin)).json()
    assert f["puede_editar_antecedentes"] and f["puede_registrar_seguimiento"] and f["gestion"] is not None


async def test_cu07_observacion_medica_solo_administrador(cliente, admin, profesor):
    cuerpo = {"observacion_medica": "Alergia a la penicilina.\nUsa lentes."}
    assert (await cliente.put(f"{URL}/4500001/antecedentes", headers=profesor, json=cuerpo)).status_code == 403

    r = await cliente.put(f"{URL}/4500001/antecedentes", headers=admin, json=cuerpo)
    assert r.status_code == 200, r.text
    assert r.json()["observacion_medica"] == "Alergia a la penicilina.\nUsa lentes."   # conserva los párrafos

    # el tutor la ve
    tutor = await iniciar(cliente, "marioq")
    assert (await cliente.get(f"{URL}/4500001", headers=tutor)).json()["observacion_medica"].startswith("Alergia")

    # vaciarla = sin observaciones
    r = await cliente.put(f"{URL}/4500001/antecedentes", headers=admin, json={"observacion_medica": "   "})
    assert r.json()["observacion_medica"] is None
    assert (await cliente.put(f"{URL}/9999999/antecedentes", headers=admin, json=cuerpo)).status_code == 404


async def test_cu07_profesor_registra_seguimiento_de_su_estudiante(cliente, profesor):
    r = await cliente.post(f"{URL}/4500003/seguimientos", headers=profesor, json=CONDUCTA)
    assert r.status_code == 201, r.text
    s = r.json()
    assert s["tipo"] == "conducta" and s["gravedad"] == "leve" and s["es_mio"]
    assert s["registrado_por"].startswith("Roberto Flores") and s["rol_registrado_por"] == "profesor"
    assert s["fecha"] is not None                                   # por defecto, hoy

    f = (await cliente.get(f"{URL}/4500003", headers=profesor)).json()
    assert f["seguimientos"][0]["id_seguimiento"] == s["id_seguimiento"]

    # no puede registrar a un estudiante al que no le dicta clases
    r = await cliente.post(f"{URL}/4500008/seguimientos", headers=profesor, json=CONDUCTA)
    assert r.status_code == 403


async def test_cu07_seguimiento_visible_para_el_tutor(cliente, admin):
    r = await cliente.post(f"{URL}/4500001/seguimientos", headers=admin,
                           json={"tipo": "merito", "descripcion": "Representó al colegio en la olimpiada de Matemática"})
    assert r.status_code == 201, r.text
    tutor = await iniciar(cliente, "marioq")
    f = (await cliente.get(f"{URL}/4500001", headers=tutor)).json()
    assert f["seguimientos"][0]["descripcion"].startswith("Representó") and not f["seguimientos"][0]["es_mio"]


async def test_cu07_validaciones(cliente, admin):
    url = f"{URL}/4500001/seguimientos"
    # conducta sin gravedad / gravedad en otro tipo
    r = await cliente.post(url, headers=admin, json={**CONDUCTA, "gravedad": None})
    assert r.status_code == 400 and "gravedad" in r.json()["detalle"]
    r = await cliente.post(url, headers=admin, json={**CONDUCTA, "tipo": "academico"})
    assert r.status_code == 400 and "solo se indica" in r.json()["detalle"]
    # fecha futura
    manana = (date.today() + timedelta(days=2)).isoformat()
    r = await cliente.post(url, headers=admin, json={**CONDUCTA, "fecha": manana})
    assert r.status_code == 400 and "futura" in r.json()["detalle"]
    # fecha pasada sí se acepta
    r = await cliente.post(url, headers=admin, json={**CONDUCTA, "fecha": "2026-03-10"})
    assert r.status_code == 201 and r.json()["fecha"] == "2026-03-10"
    # tipo inexistente, descripción vacía o muy corta
    assert (await cliente.post(url, headers=admin, json={**CONDUCTA, "tipo": "castigo"})).status_code == 422
    assert (await cliente.post(url, headers=admin, json={**CONDUCTA, "descripcion": "   "})).status_code == 422
    assert (await cliente.post(url, headers=admin, json={**CONDUCTA, "descripcion": "mal"})).status_code == 422
    assert (await cliente.post(f"{URL}/9999999/seguimientos", headers=admin, json=CONDUCTA)).status_code == 404


async def test_cu07_no_se_registra_a_un_estudiante_dado_de_baja(cliente, admin):
    r = await cliente.post("/personas/estudiantes/4500012/baja", headers=admin, json={"motivo": "Cambio de colegio"})
    assert r.status_code == 200, r.text
    f = (await cliente.get(f"{URL}/4500012", headers=admin)).json()
    assert not f["puede_registrar_seguimiento"]
    r = await cliente.post(f"{URL}/4500012/seguimientos", headers=admin, json=CONDUCTA)
    assert r.status_code == 400 and "baja" in r.json()["detalle"]


async def test_cu07_queda_en_la_bitacora(cliente, admin, profesor):
    r = await cliente.post(f"{URL}/4500004/seguimientos", headers=profesor, json=CONDUCTA)
    id_seguimiento = r.json()["id_seguimiento"]
    bitacora = (await cliente.get("/seguridad/bitacora", headers=admin,
                                  params={"tabla": "seguimiento_estudiante", "tamano": 20})).json()
    filas = [b for b in bitacora["items"] if b["registro_id"] == str(id_seguimiento)]
    assert filas and filas[0]["nombre_usuario"] == "rflores" and filas[0]["operacion"] == "INSERT"

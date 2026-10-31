"""Pruebas del CU15: gestión académica (año lectivo), periodos, dimensiones y cierre.

Datos de 08_datos_prueba: la gestión 2026 está abierta, con 3 trimestres y 5 dimensiones que suman 100.
"""

GESTION_NUEVA = {"anio": 2027, "fecha_inicio_g": "2027-02-01", "fecha_final_g": "2027-11-30"}


async def _gestion_2026(cliente, admin) -> dict:
    r = await cliente.get("/academico/gestiones", headers=admin)
    assert r.status_code == 200, r.text
    return next(g for g in r.json() if g["anio"] == 2026)


async def test_cu15_solo_administrador(cliente, profesor):
    assert (await cliente.get("/academico/gestiones", headers=profesor)).status_code == 403
    assert (await cliente.post("/academico/gestiones", headers=profesor, json=GESTION_NUEVA)).status_code == 403
    assert (await cliente.post("/academico/gestiones/1/cerrar", headers=profesor)).status_code == 403


async def test_cu15_listar_y_resumen(cliente, admin):
    g = await _gestion_2026(cliente, admin)
    assert g["estado_gestion"] == "abierta" and g["periodos"] == 3 and g["inscritos"] > 0
    r = await cliente.get(f"/academico/gestiones/{g['id_gestion']}/resumen", headers=admin)
    assert r.status_code == 200, r.text
    assert r.json()["inscritos_activos"] > 0


async def test_cu15_crear_gestion(cliente, admin):
    # con la 2026 abierta no se puede crear otra
    r = await cliente.post("/academico/gestiones", headers=admin, json=GESTION_NUEVA)
    assert r.status_code == 409

    # el año debe coincidir con la fecha de inicio
    r = await cliente.post("/academico/gestiones", headers=admin, json={**GESTION_NUEVA, "anio": 2028})
    assert r.status_code == 422


async def test_cu15_periodos(cliente, admin):
    g = await _gestion_2026(cliente, admin)
    id_g = g["id_gestion"]

    # fuera de las fechas de la gestión
    r = await cliente.post(f"/academico/gestiones/{id_g}/periodos", headers=admin, json={
        "nombre_periodo": "Fuera", "fecha_inicio_p": "2025-01-01", "fecha_final_p": "2025-02-01"})
    assert r.status_code == 400

    # solapado con un trimestre existente
    existentes = (await cliente.get(f"/academico/gestiones/{id_g}/periodos", headers=admin)).json()
    primero = existentes[0]
    r = await cliente.post(f"/academico/gestiones/{id_g}/periodos", headers=admin, json={
        "nombre_periodo": "Solapado", "fecha_inicio_p": primero["fecha_inicio_p"], "fecha_final_p": primero["fecha_final_p"]})
    assert r.status_code == 400

    # al modificar, las fechas y el nombre no pueden llegar vacíos (antes daba 500)
    for campo in ("fecha_inicio_p", "fecha_final_p", "nombre_periodo"):
        r = await cliente.patch(f"/academico/periodos/{primero['id_periodo']}", headers=admin, json={campo: None})
        assert r.status_code == 422, r.text

    # un periodo con calificaciones no se elimina
    r = await cliente.delete(f"/academico/periodos/{primero['id_periodo']}", headers=admin)
    assert r.status_code == 409


async def test_cu15_dimensiones(cliente, admin):
    g = await _gestion_2026(cliente, admin)
    id_g = g["id_gestion"]

    r = await cliente.get(f"/academico/gestiones/{id_g}/dimensiones", headers=admin)
    assert r.status_code == 200 and r.json()["completa"] is True

    # deben sumar exactamente 100: ni más ni menos
    for puntajes in ([60, 60], [40, 30]):
        dims = [{"nombre_dimension": n, "puntaje_maximo": p} for n, p in zip("AB", puntajes)]
        r = await cliente.put(f"/academico/gestiones/{id_g}/dimensiones", headers=admin, json={"dimensiones": dims})
        assert r.status_code == 400, r.text

    # ni nombres repetidos, ni dos autoevaluaciones
    rep = [{"nombre_dimension": "A", "puntaje_maximo": 50}, {"nombre_dimension": "a", "puntaje_maximo": 50}]
    assert (await cliente.put(f"/academico/gestiones/{id_g}/dimensiones", headers=admin,
                              json={"dimensiones": rep})).status_code == 422
    auto = [{"nombre_dimension": n, "puntaje_maximo": 50, "es_autoevaluacion": True} for n in "AB"]
    assert (await cliente.put(f"/academico/gestiones/{id_g}/dimensiones", headers=admin,
                              json={"dimensiones": auto})).status_code == 422

    # la gestión 2026 ya tiene calificaciones: no se reemplazan
    ok = [{"nombre_dimension": "A", "puntaje_maximo": 100}]
    r = await cliente.put(f"/academico/gestiones/{id_g}/dimensiones", headers=admin, json={"dimensiones": ok})
    assert r.status_code == 409


async def test_cu15_nota_minima_bloqueada_con_calificaciones(cliente, admin):
    g = await _gestion_2026(cliente, admin)
    id_g = g["id_gestion"]
    actual = float(g["nota_minima_aprobacion"])

    # la gestión 2026 ya tiene calificaciones: no se cambia la nota mínima
    r = await cliente.patch(f"/academico/gestiones/{id_g}", headers=admin, json={"nota_minima_aprobacion": actual + 1})
    assert r.status_code == 409, r.text

    # enviar el mismo valor no es un cambio y sí se permite
    r = await cliente.patch(f"/academico/gestiones/{id_g}", headers=admin, json={"nota_minima_aprobacion": actual})
    assert r.status_code == 200, r.text


async def test_cu15_cerrar_gestion(cliente, admin):
    g = await _gestion_2026(cliente, admin)
    id_g = g["id_gestion"]

    r = await cliente.post(f"/academico/gestiones/{id_g}/cerrar", headers=admin)
    assert r.status_code == 200, r.text
    assert r.json()["promovidos"] + r.json()["reprobados"] > 0

    assert (await _gestion_2026(cliente, admin))["estado_gestion"] == "cerrada"

    # cerrada: no se cierra de nuevo ni admite cambios
    assert (await cliente.post(f"/academico/gestiones/{id_g}/cerrar", headers=admin)).status_code == 400
    r = await cliente.patch(f"/academico/gestiones/{id_g}", headers=admin, json={"nota_minima_aprobacion": 60})
    assert r.status_code == 400

    # y ahora sí se puede abrir la siguiente
    r = await cliente.post("/academico/gestiones", headers=admin, json=GESTION_NUEVA)
    assert r.status_code == 201 and r.json()["estado_gestion"] == "abierta"

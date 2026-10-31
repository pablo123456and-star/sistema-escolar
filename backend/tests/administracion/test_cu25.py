"""Pruebas del CU25: registrar pago de mensualidad (aranceles, becas, cuotas, cobro y morosos).

Datos de 08_datos_prueba: cuotas de febrero a septiembre de 2026, pagadas salvo las de los
morosos (4500005 debe jul-sep, 4500011 ago-sep, 4500002 y 4500008 sep). 4500003 tiene beca
del 50 % y 4500009 del 100 %. "direccion" (1000001) es administrativa; marioq (3000001) es
tutor de 4500001 y 4500007; el responsable de pago de 4500005 es 3000006.
"""
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


async def _id_cuota(ci: str, mes: int) -> int:
    return await _sql("SELECT id_pago FROM pago_mensualidad WHERE ci_estudiante_pago = :ci AND mes = :m", ci=ci, m=mes)


async def _cobrar(cliente, cabecera, id_pago: int, metodo: str = "efectivo", **extra):
    return await cliente.post(f"/administracion/pagos/{id_pago}/cobrar", headers=cabecera,
                              json={"metodo_pago": metodo, **extra})


async def test_cu25_permisos_por_rol(cliente):
    for usuario in ("mquispe", "marioq", "rflores"):
        cabecera = await iniciar(cliente, usuario)
        assert (await cliente.get("/administracion/aranceles", headers=cabecera)).status_code == 403
        assert (await cliente.get("/administracion/cuotas", params={"ci_estudiante": "4500001"},
                                  headers=cabecera)).status_code == 403
        assert (await _cobrar(cliente, cabecera, await _id_cuota("4500005", 7))).status_code == 403
    rflores = await iniciar(cliente, "rflores")
    assert (await cliente.get("/administracion/mis-cuotas", headers=rflores)).status_code == 403


async def test_cu25_cobrar_asigna_recibo_correlativo_y_cajero(cliente, admin):
    ultimo = await _sql("SELECT max(numero_recibo) FROM pago_mensualidad")
    r = await _cobrar(cliente, admin, await _id_cuota("4500005", 7), "qr")
    assert r.status_code == 200, r.text
    recibo = r.json()
    assert recibo["numero_recibo"] > ultimo
    assert recibo["fecha_pago"] == (await _sql("SELECT CURRENT_DATE")).isoformat()
    assert recibo["metodo_pago"] == "qr" and recibo["total"] == 550 and recibo["descuento"] == 0
    assert recibo["cajero"].startswith("Juana") and recibo["tutor"] is not None   # tutor responsable por defecto
    guardado = await _sql("SELECT ci_administrativo_pago || '/' || ci_tutor_pago FROM pago_mensualidad "
                          "WHERE id_pago = :id", id=recibo["id_pago"])
    assert guardado == "1000001/3000006"

    siguiente = await _cobrar(cliente, admin, await _id_cuota("4500005", 8))
    assert siguiente.json()["numero_recibo"] == recibo["numero_recibo"] + 1


async def test_cu25_recibo_con_beca(cliente, admin):
    await _sql("UPDATE pago_mensualidad SET estado_pago = 'pendiente', fecha_pago = NULL, numero_recibo = NULL, "
               "metodo_pago = NULL, ci_administrativo_pago = NULL, ci_tutor_pago = NULL "
               "WHERE ci_estudiante_pago = '4500003' AND mes = 9")
    r = await _cobrar(cliente, admin, await _id_cuota("4500003", 9))
    assert r.status_code == 200, r.text
    recibo = r.json()
    assert (recibo["monto_mensual"], recibo["descuento"], recibo["porcentaje_beca"], recibo["total"]) == (550, 275, 50, 275)


async def test_cu25_solo_se_cobra_una_cuota_pendiente(cliente, admin):
    pagada = await _id_cuota("4500001", 2)
    assert (await _cobrar(cliente, admin, pagada)).status_code == 400
    pendiente = await _id_cuota("4500011", 8)
    r = await cliente.post(f"/administracion/pagos/{pendiente}/anular", headers=admin,
                           json={"motivo": "Retiro del estudiante"})
    assert r.status_code == 200, r.text
    assert (await _cobrar(cliente, admin, pendiente)).status_code == 400
    assert (await cliente.post(f"/administracion/pagos/{pendiente}/anular", headers=admin,
                               json={"motivo": "Otra vez"})).status_code == 400
    assert (await _cobrar(cliente, admin, 999999)).status_code == 404


async def test_cu25_tutor_que_paga_debe_ser_tutor_del_estudiante(cliente, admin):
    id_pago = await _id_cuota("4500005", 9)
    r = await _cobrar(cliente, admin, id_pago, ci_tutor="3000001")
    assert r.status_code == 400 and "no es tutor" in r.json()["detalle"]
    r = await _cobrar(cliente, admin, id_pago, ci_tutor="3000006")
    assert r.status_code == 200


async def test_cu25_metodo_de_pago_valido(cliente, admin):
    assert (await _cobrar(cliente, admin, await _id_cuota("4500005", 9), "cheque")).status_code == 422


async def test_cu25_anular_o_revertir_sin_motivo(cliente, admin):
    id_pago = await _id_cuota("4500002", 9)
    for accion in ("anular", "revertir"):
        assert (await cliente.post(f"/administracion/pagos/{id_pago}/{accion}", headers=admin, json={})).status_code == 422
        assert (await cliente.post(f"/administracion/pagos/{id_pago}/{accion}", headers=admin,
                                   json={"motivo": "   "})).status_code == 422


async def test_cu25_revertir_cobro(cliente, admin):
    id_pago = await _id_cuota("4500008", 9)
    primero = (await _cobrar(cliente, admin, id_pago, "tarjeta")).json()
    r = await cliente.post(f"/administracion/pagos/{id_pago}/revertir", headers=admin,
                           json={"motivo": "Se registró con el método equivocado"})
    assert r.status_code == 200, r.text
    cuota = next(c for c in r.json()["cuotas"] if c["id_pago"] == id_pago)
    assert cuota["estado_pago"] == "pendiente" and cuota["numero_recibo"] is None and cuota["fecha_pago"] is None
    assert f"recibo N° {primero['numero_recibo']}" in cuota["observacion_pago"]

    segundo = (await _cobrar(cliente, admin, id_pago, "efectivo")).json()
    assert segundo["numero_recibo"] > primero["numero_recibo"]   # el número revertido no se reutiliza
    assert (await cliente.post(f"/administracion/pagos/{id_pago}/anular", headers=admin,
                               json={"motivo": "No se puede anular pagada"})).status_code == 400
    pendiente = await _id_cuota("4500002", 9)
    assert (await cliente.post(f"/administracion/pagos/{pendiente}/revertir", headers=admin,
                               json={"motivo": "No está pagada"})).status_code == 400


async def test_cu25_tutor_y_estudiante_solo_ven_lo_suyo(cliente):
    tutor = await iniciar(cliente, "marioq")
    r = await cliente.get("/administracion/mis-cuotas", headers=tutor)
    assert r.status_code == 200, r.text
    assert {c["estudiante"]["ci"] for c in r.json()} == {"4500001", "4500007"}
    assert (await cliente.get(f"/administracion/pagos/{await _id_cuota('4500007', 2)}/recibo", headers=tutor)).status_code == 200
    assert (await cliente.get(f"/administracion/pagos/{await _id_cuota('4500002', 2)}/recibo", headers=tutor)).status_code == 403

    estudiante = await iniciar(cliente, "mquispe")
    r = await cliente.get("/administracion/mis-cuotas", headers=estudiante)
    assert [c["estudiante"]["ci"] for c in r.json()] == ["4500001"]
    assert (await cliente.get(f"/administracion/pagos/{await _id_cuota('4500007', 2)}/recibo",
                              headers=estudiante)).status_code == 403


async def test_cu25_generar_cuotas(cliente, admin):
    esperadas = await _sql(
        "SELECT count(*) FROM inscripcion i JOIN gestion g ON g.id_gestion = i.id_gestion_inscripcion "
        "LEFT JOIN beca b ON b.ci_estudiante_beca = i.ci_estudiante_inscripcion AND b.id_gestion_beca = g.id_gestion "
        "WHERE g.estado_gestion = 'abierta' AND i.estado_inscripcion = 'activa' "
        "AND coalesce(b.porcentaje_descuento, 0) < 100")
    r = await cliente.post("/administracion/cuotas/generar", headers=admin, json={"mes": 10})
    assert r.status_code == 200, r.text
    assert r.json()["cuotas_creadas"] == esperadas
    assert await _sql("SELECT monto FROM pago_mensualidad WHERE ci_estudiante_pago = '4500003' AND mes = 10") == 275
    assert await _sql("SELECT count(*) FROM pago_mensualidad WHERE ci_estudiante_pago = '4500009'") == 0
    r = await cliente.post("/administracion/cuotas/generar", headers=admin, json={"mes": 10})
    assert r.json()["cuotas_creadas"] == 0                                  # no duplica
    assert (await cliente.post("/administracion/cuotas/generar", headers=admin, json={"mes": 1})).status_code == 400

    await _sql("DELETE FROM arancel WHERE id_nivel_arancel = (SELECT id_nivel FROM nivel_educativo "
               "WHERE nombre_nivel = 'Primaria')")
    r = await cliente.post("/administracion/cuotas/generar", headers=admin, json={"mes": 11})
    assert r.status_code == 400 and "Primaria" in r.json()["detalle"]


async def test_cu25_morosos_solo_atrasadas(cliente, admin):
    r = await cliente.get("/administracion/morosos", headers=admin)
    assert r.status_code == 200, r.text
    morosos = {m["ci_estudiante"]: m for m in r.json()["morosos"]}
    atrasados = await _sql("SELECT count(DISTINCT ci_estudiante) FROM v_estado_pagos WHERE estado_actual = 'atrasado'")
    assert len(morosos) == atrasados
    assert {"4500005", "4500011", "4500002", "4500008"} <= morosos.keys() and "4500001" not in morosos
    assert [c["mes"] for c in morosos["4500005"]["cuotas"]] == [7, 8, 9]
    assert morosos["4500005"]["deuda"] == 1650 and morosos["4500005"]["telefono"]


async def test_cu25_aranceles_y_becas(cliente, admin):
    r = await cliente.get("/administracion/aranceles", headers=admin)
    secundaria = next(n for n in r.json()["niveles"] if n["nivel"] == "Secundaria")
    assert secundaria["monto_mensual"] == 550
    r = await cliente.post("/administracion/aranceles", headers=admin,
                           json={"id_nivel": secundaria["id_nivel"], "monto_mensual": 600})
    assert r.status_code == 409
    r = await cliente.patch(f"/administracion/aranceles/{secundaria['id_arancel']}", headers=admin,
                            json={"monto_mensual": 600, "dia_vencimiento": 5})
    assert r.status_code == 200 and (r.json()["monto_mensual"], r.json()["dia_vencimiento"]) == (600, 5)
    assert (await cliente.patch(f"/administracion/aranceles/{secundaria['id_arancel']}", headers=admin,
                                json={"dia_vencimiento": 31})).status_code == 422

    r = await cliente.post("/administracion/becas", headers=admin,
                           json={"ci_estudiante": "4500001", "porcentaje_descuento": 30, "motivo_beca": "Hermanos"})
    assert r.status_code == 201, r.text
    beca = r.json()
    assert beca["porcentaje_descuento"] == 30 and beca["curso"]
    assert (await cliente.post("/administracion/becas", headers=admin,
                               json={"ci_estudiante": "4500001", "porcentaje_descuento": 10})).status_code == 409
    assert (await cliente.post("/administracion/becas", headers=admin,
                               json={"ci_estudiante": "3000001", "porcentaje_descuento": 10})).status_code == 400
    assert (await cliente.post("/administracion/becas", headers=admin,
                               json={"ci_estudiante": "4500002", "porcentaje_descuento": 150})).status_code == 422
    r = await cliente.patch(f"/administracion/becas/{beca['id_beca']}", headers=admin, json={"porcentaje_descuento": 40})
    assert r.status_code == 200 and r.json()["porcentaje_descuento"] == 40 and r.json()["motivo_beca"] == "Hermanos"

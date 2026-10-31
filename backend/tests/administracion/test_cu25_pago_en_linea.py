"""Pruebas del pago en línea del CU25 (Stripe en modo de prueba).

No se llama a Stripe: se reemplazan crear_sesion_pago y obtener_sesion por respuestas simuladas.
marioq (3000001) es tutor de 4500001; la cuota de septiembre de 4500001 se deja pendiente para pagarla.
"""
import pytest
from sqlalchemy import text

from app.nucleo import bd, pasarela_pago
from app.nucleo.config import obtener_config
from tests.conftest import iniciar

ID_SESION = "cs_test_a1B2c3D4e5F6"


async def _sql(consulta: str, **params):
    async with bd._fabrica() as sesion:
        resultado = await sesion.execute(text(consulta), params)
        valor = resultado.scalar() if resultado.returns_rows else None
        await sesion.commit()
        return valor


@pytest.fixture
async def stripe(monkeypatch, cliente):
    """Stripe 'configurado' con una clave de prueba, el cajero de pagos en línea y una cuota pendiente."""
    monkeypatch.setattr(obtener_config(), "STRIPE_SECRET_KEY", "sk_test_solo_para_pruebas")
    await _sql("INSERT INTO persona (ci, nombre_persona, apellidos) VALUES ('PAGO-EN-LINEA', 'Pagos en linea', "
               "'Pasarela Stripe') ON CONFLICT DO NOTHING")
    await _sql("INSERT INTO administrativo (ci_administrativo, cargo) VALUES ('PAGO-EN-LINEA', 'Pasarela de pago') "
               "ON CONFLICT DO NOTHING")
    id_pago = await _sql("SELECT id_pago FROM pago_mensualidad WHERE ci_estudiante_pago = '4500001' AND mes = 9")
    await _sql("UPDATE pago_mensualidad SET estado_pago = 'pendiente', fecha_pago = NULL, numero_recibo = NULL, "
               "metodo_pago = NULL, ci_administrativo_pago = NULL, ci_tutor_pago = NULL WHERE id_pago = :id", id=id_pago)
    llamadas = {}

    async def crear(monto_centavos, descripcion, referencia, url_exito, url_cancelar):
        llamadas.update(monto=monto_centavos, descripcion=descripcion, referencia=referencia, url_exito=url_exito)
        return {"id": ID_SESION, "url": "https://checkout.stripe.com/c/pay/" + ID_SESION}

    sesion_stripe = {"id": ID_SESION, "pagado": True, "monto_centavos": 55000, "moneda": "bob",
                     "referencia": {"id_pago": str(id_pago), "ci_tutor": "3000001"}}

    async def obtener(id_sesion):
        return dict(sesion_stripe)

    monkeypatch.setattr(pasarela_pago, "crear_sesion_pago", crear)
    monkeypatch.setattr(pasarela_pago, "obtener_sesion", obtener)
    return {"id_pago": id_pago, "llamadas": llamadas, "sesion": sesion_stripe}


async def test_cu25_pago_en_linea_deshabilitado_sin_clave(cliente, monkeypatch):
    monkeypatch.setattr(obtener_config(), "STRIPE_SECRET_KEY", "")
    tutor = await iniciar(cliente, "marioq")
    assert (await cliente.get("/administracion/pagos/en-linea/estado", headers=tutor)).json() == {"habilitado": False}
    id_pago = await _sql("SELECT id_pago FROM pago_mensualidad WHERE ci_estudiante_pago = '4500001' AND mes = 9")
    assert (await cliente.post(f"/administracion/pagos/{id_pago}/pagar-en-linea", headers=tutor)).status_code == 400


async def test_cu25_pago_en_linea_solo_claves_de_prueba(cliente, monkeypatch):
    monkeypatch.setattr(obtener_config(), "STRIPE_SECRET_KEY", "sk_live_no_se_acepta")
    tutor = await iniciar(cliente, "marioq")
    assert (await cliente.get("/administracion/pagos/en-linea/estado", headers=tutor)).json() == {"habilitado": False}


async def test_cu25_iniciar_pago_en_linea(cliente, stripe):
    tutor = await iniciar(cliente, "marioq")
    r = await cliente.post(f"/administracion/pagos/{stripe['id_pago']}/pagar-en-linea", headers=tutor)
    assert r.status_code == 200, r.text
    assert r.json()["url"].startswith("https://checkout.stripe.com/")
    llamadas = stripe["llamadas"]
    assert llamadas["monto"] == 55000                                   # Bs 550,00 en centavos
    assert llamadas["referencia"] == {"id_pago": stripe["id_pago"], "ci_tutor": "3000001"}
    assert "{CHECKOUT_SESSION_ID}" in llamadas["url_exito"] and "septiembre" in llamadas["descripcion"]


async def test_cu25_pago_en_linea_solo_cuotas_propias_y_pendientes(cliente, stripe):
    tutor = await iniciar(cliente, "marioq")
    ajena = await _sql("SELECT id_pago FROM pago_mensualidad WHERE ci_estudiante_pago = '4500005' AND mes = 7")
    assert (await cliente.post(f"/administracion/pagos/{ajena}/pagar-en-linea", headers=tutor)).status_code == 403
    pagada = await _sql("SELECT id_pago FROM pago_mensualidad WHERE ci_estudiante_pago = '4500001' AND mes = 2")
    assert (await cliente.post(f"/administracion/pagos/{pagada}/pagar-en-linea", headers=tutor)).status_code == 400
    admin = await iniciar(cliente, "direccion")
    assert (await cliente.post(f"/administracion/pagos/{stripe['id_pago']}/pagar-en-linea",
                               headers=admin)).status_code == 403


async def test_cu25_confirmar_pago_en_linea(cliente, stripe):
    tutor = await iniciar(cliente, "marioq")
    r = await cliente.post("/administracion/pagos/en-linea/confirmar", headers=tutor, json={"id_sesion": ID_SESION})
    assert r.status_code == 200, r.text
    recibo = r.json()
    assert recibo["metodo_pago"] == "tarjeta" and recibo["total"] == 550
    assert recibo["cajero"].startswith("Pagos en linea") and recibo["tutor"].startswith("Mario")
    fila = await _sql("SELECT estado_pago || '/' || ci_administrativo_pago FROM pago_mensualidad WHERE id_pago = :id",
                      id=stripe["id_pago"])
    assert fila == "pagado/PAGO-EN-LINEA"

    # Confirmar otra vez (recargar la página) no cobra dos veces
    otra = await cliente.post("/administracion/pagos/en-linea/confirmar", headers=tutor, json={"id_sesion": ID_SESION})
    assert otra.status_code == 200 and otra.json()["numero_recibo"] == recibo["numero_recibo"]


async def test_cu25_confirmar_pago_no_aprobado_o_alterado(cliente, stripe):
    tutor = await iniciar(cliente, "marioq")
    stripe["sesion"]["pagado"] = False
    r = await cliente.post("/administracion/pagos/en-linea/confirmar", headers=tutor, json={"id_sesion": ID_SESION})
    assert r.status_code == 400
    stripe["sesion"].update(pagado=True, monto_centavos=100)          # pagó Bs 1 en vez de Bs 550
    r = await cliente.post("/administracion/pagos/en-linea/confirmar", headers=tutor, json={"id_sesion": ID_SESION})
    assert r.status_code == 400 and "monto" in r.json()["detalle"]
    estado = await _sql("SELECT estado_pago FROM pago_mensualidad WHERE id_pago = :id", id=stripe["id_pago"])
    assert estado == "pendiente"
    assert (await cliente.post("/administracion/pagos/en-linea/confirmar", headers=tutor,
                               json={"id_sesion": "no-es-una-sesion"})).status_code == 422


async def test_cu25_estudiante_confirma_solo_sus_pagos(cliente, stripe):
    estudiante = await iniciar(cliente, "mquispe")      # 4500001: la cuota es suya
    r = await cliente.post("/administracion/pagos/en-linea/confirmar", headers=estudiante, json={"id_sesion": ID_SESION})
    assert r.status_code == 200
    stripe["sesion"]["referencia"]["id_pago"] = str(
        await _sql("SELECT id_pago FROM pago_mensualidad WHERE ci_estudiante_pago = '4500005' AND mes = 7"))
    r = await cliente.post("/administracion/pagos/en-linea/confirmar", headers=estudiante, json={"id_sesion": ID_SESION})
    assert r.status_code == 403

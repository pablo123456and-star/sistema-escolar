"""Pruebas del CU26: gestionar inventario (bienes, entradas y salidas de stock, stock bajo).

Datos de 08_datos_prueba (stock calculado por el trigger con sus movimientos):
    Pupitres 120, Sillas 150, Proyector multimedia 4, Balones de futbol 12 (15 - 3),
    Resmas de papel bond 28 (40 - 12), Marcadores de pizarra 80 (100 - 20).
direccion (1000001) y secretaria (1000002) son administradores y administrativos.
Requiere el script 11 (columna stock_minimo).
"""
from sqlalchemy import text

from app.nucleo import bd
from tests.conftest import iniciar

URL = "/administracion/inventario"


async def _sql(consulta: str, **params):
    async with bd._fabrica() as sesion:
        resultado = await sesion.execute(text(consulta), params)
        valor = resultado.scalar() if resultado.returns_rows else None
        await sesion.commit()
        return valor


async def _id(nombre: str) -> int:
    return await _sql("SELECT id_inventario FROM inventario WHERE nombre_inventario = :n", n=nombre)


async def _nuevo(cliente, cabecera, nombre: str = "Mesas plegables", **extra) -> dict:
    r = await cliente.post(URL, headers=cabecera, json={"nombre": nombre, **extra})
    assert r.status_code == 201, r.text
    return r.json()


async def _mover(cliente, cabecera, id_bien: int, tipo: str, cantidad: int, destino: str | None = "Aula 5"):
    cuerpo = {"tipo": tipo, "cantidad": cantidad, "motivo": "Prueba de movimiento"}
    if destino:
        cuerpo["destino"] = destino
    return await cliente.post(f"{URL}/{id_bien}/movimientos", headers=cabecera, json=cuerpo)


async def test_cu26_solo_administrador(cliente):
    for usuario in ("rflores", "mquispe", "marioq"):
        cabecera = await iniciar(cliente, usuario)
        assert (await cliente.get(URL, headers=cabecera)).status_code == 403
        assert (await cliente.post(URL, headers=cabecera, json={"nombre": "Sillas nuevas"})).status_code == 403
        assert (await _mover(cliente, cabecera, await _id("Pupitres"), "entrada", 1)).status_code == 403
    assert (await cliente.get(URL)).status_code == 401


async def test_cu26_lista_bienes_con_stock_de_los_movimientos(cliente, admin):
    r = await cliente.get(URL, headers=admin)
    assert r.status_code == 200, r.text
    bienes = {b["nombre"]: b for b in r.json()["bienes"]}
    assert bienes["Balones de futbol"]["cantidad"] == 12 and bienes["Balones de futbol"]["movimientos"] == 2
    assert bienes["Resmas de papel bond"]["cantidad"] == 28
    assert r.json()["total"] == len(bienes)

    r = await cliente.get(URL, headers=admin, params={"buscar": "balon"})
    assert [b["nombre"] for b in r.json()["bienes"]] == ["Balones de futbol"]


async def test_cu26_bien_nuevo_empieza_en_cero_y_nombre_unico(cliente, admin):
    bien = await _nuevo(cliente, admin, "Mesas plegables", stock_minimo=5, observacion="  Para el patio  ")
    assert bien["cantidad"] == 0 and bien["estado"] == "sin_stock" and bien["movimientos"] == 0
    assert bien["stock_minimo"] == 5 and bien["observacion"] == "Para el patio"

    # La cantidad no se puede enviar al registrar
    r = await cliente.post(URL, headers=admin, json={"nombre": "Pelotas", "cantidad": 50})
    assert r.status_code == 422

    # Nombre repetido (sin distinguir mayúsculas)
    r = await cliente.post(URL, headers=admin, json={"nombre": "PUPITRES"})
    assert r.status_code == 409 and "Pupitres".lower() in r.json()["detalle"].lower()


async def test_cu26_editar_no_cambia_la_cantidad(cliente, admin):
    id_balones = await _id("Balones de futbol")
    r = await cliente.patch(f"{URL}/{id_balones}", headers=admin,
                            json={"nombre": "Balones de fútbol N.º 5", "stock_minimo": 15, "observacion": "Cancha"})
    assert r.status_code == 200, r.text
    bien = r.json()
    assert bien["nombre"] == "Balones de fútbol N.º 5" and bien["cantidad"] == 12
    assert bien["stock_minimo"] == 15 and bien["estado"] == "bajo"

    assert (await cliente.patch(f"{URL}/{id_balones}", headers=admin, json={"cantidad": 999})).status_code == 422
    assert (await cliente.patch(f"{URL}/{id_balones}", headers=admin, json={})).status_code == 422
    assert (await cliente.patch(f"{URL}/{id_balones}", headers=admin, json={"nombre": "Sillas"})).status_code == 409
    assert (await cliente.patch(f"{URL}/999999", headers=admin, json={"nombre": "X bien"})).status_code == 404

    # La observación se puede borrar
    r = await cliente.patch(f"{URL}/{id_balones}", headers=admin, json={"observacion": ""})
    assert r.json()["observacion"] is None and r.json()["cantidad"] == 12


async def test_cu26_entrada_suma_y_salida_resta_con_responsable(cliente, admin):
    bien = await _nuevo(cliente, admin)
    r = await _mover(cliente, admin, bien["id_inventario"], "entrada", 30, destino=None)
    assert r.status_code == 201, r.text
    assert r.json()["bien"]["cantidad"] == 30 and r.json()["aviso"] is None
    mov = r.json()["movimiento"]
    assert mov["ci_responsable"] == "1000001" and mov["saldo"] == 30 and mov["destino"] is None

    secretaria = await iniciar(cliente, "secretaria")
    r = await _mover(cliente, secretaria, bien["id_inventario"], "salida", 8, destino="Patio")
    assert r.status_code == 201, r.text
    assert r.json()["bien"]["cantidad"] == 22 and r.json()["movimiento"]["ci_responsable"] == "1000002"

    historial = (await cliente.get(f"{URL}/{bien['id_inventario']}/movimientos", headers=admin)).json()
    assert [(m["tipo"], m["cantidad"], m["saldo"]) for m in historial["movimientos"]] == [
        ("salida", 8, 22), ("entrada", 30, 30)
    ]
    assert historial["bien"]["movimientos"] == 2
    assert await _sql("SELECT cantidad_inventario FROM inventario WHERE id_inventario = :i",
                      i=bien["id_inventario"]) == 22


async def test_cu26_salida_mayor_al_stock_no_se_registra(cliente, admin):
    id_proyector = await _id("Proyector multimedia")
    r = await _mover(cliente, admin, id_proyector, "salida", 5)
    assert r.status_code == 400 and "Stock insuficiente" in r.json()["detalle"]
    assert await _sql("SELECT cantidad_inventario FROM inventario WHERE id_inventario = :i", i=id_proyector) == 4
    assert await _sql("SELECT count(*) FROM movimiento_inventario WHERE id_inventario_movimiento = :i",
                      i=id_proyector) == 1

    # Datos del movimiento: cantidad > 0, motivo y destino de la salida
    assert (await _mover(cliente, admin, id_proyector, "salida", 0)).status_code == 422
    assert (await _mover(cliente, admin, id_proyector, "salida", 1, destino=None)).status_code == 422
    r = await cliente.post(f"{URL}/{id_proyector}/movimientos", headers=admin, json={"tipo": "entrada", "cantidad": 1})
    assert r.status_code == 422
    assert (await _mover(cliente, admin, 999999, "entrada", 1)).status_code == 404


async def test_cu26_stock_bajo_y_sin_stock(cliente, admin):
    bien = await _nuevo(cliente, admin, "Tizas", stock_minimo=10)
    await _mover(cliente, admin, bien["id_inventario"], "entrada", 25, destino=None)

    r = await _mover(cliente, admin, bien["id_inventario"], "salida", 15)
    assert r.json()["bien"]["estado"] == "bajo" and "stock bajo" in r.json()["aviso"]

    lista = (await cliente.get(URL, headers=admin, params={"estado": "bajo"})).json()
    assert "Tizas" in [b["nombre"] for b in lista["bienes"]] and lista["stock_bajo"] == lista["total"]

    r = await _mover(cliente, admin, bien["id_inventario"], "salida", 10)
    assert r.json()["bien"]["estado"] == "sin_stock" and "sin stock" in r.json()["aviso"]

    # Un mínimo de 0 no da alerta
    r = await cliente.patch(f"{URL}/{await _id('Sillas')}", headers=admin, json={"stock_minimo": 0})
    assert r.json()["estado"] == "normal"


async def test_cu26_movimientos_no_se_editan_ni_borran(cliente, admin):
    id_pupitres = await _id("Pupitres")
    id_mov = await _sql("SELECT id_movimiento FROM movimiento_inventario WHERE id_inventario_movimiento = :i",
                        i=id_pupitres)
    for metodo in ("put", "patch", "delete"):
        r = await getattr(cliente, metodo)(f"{URL}/{id_pupitres}/movimientos", headers=admin)
        assert r.status_code == 405
        r = await getattr(cliente, metodo)(f"{URL}/{id_pupitres}/movimientos/{id_mov}", headers=admin)
        assert r.status_code in (404, 405)


async def test_cu26_eliminar_solo_sin_movimientos(cliente, admin):
    bien = await _nuevo(cliente, admin, "Registrado por error")
    r = await cliente.delete(f"{URL}/{bien['id_inventario']}", headers=admin)
    assert r.status_code == 200, r.text
    assert (await cliente.delete(f"{URL}/{bien['id_inventario']}", headers=admin)).status_code == 404

    r = await cliente.delete(f"{URL}/{await _id('Pupitres')}", headers=admin)
    assert r.status_code == 409 and "historial" in r.json()["detalle"]

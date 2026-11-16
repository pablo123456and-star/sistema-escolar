"""Pruebas del CU27: gestionar comunicados y citaciones (publicar, bandeja, lectura, eliminar).

Datos de 08_datos_prueba (gestión 2026 abierta):
    - "Inicio del 3er Trimestre": a 'todos', autora direccion (1000001, administradora).
    - "Examen de Matematica": al curso 1ro A Secundaria, autor rflores (2000001).
    - "Citacion a la tutora de Mariana Ticona": citación al estudiante 4500006, autor rflores.
rflores enseña en 1ro A Sec. (estudiantes 4500001-4500006); erojas (2000006) en 6to A Pri.
(4500007-4500012). mquispe (4500001) es de 1ro A Sec.; marioq (3000001) es tutor de 4500001 y 4500007.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import text

from app.nucleo import bd
from tests.conftest import iniciar

URL = "/administracion/comunicados"


async def _sql(consulta: str, **params):
    async with bd._fabrica() as sesion:
        resultado = await sesion.execute(text(consulta), params)
        valor = resultado.scalar() if resultado.returns_rows else None
        await sesion.commit()
        return valor


async def _id(titulo: str) -> int:
    return await _sql("SELECT id_comunicado FROM comunicado WHERE titulo = :t", t=titulo)


async def _id_curso(nivel: str) -> int:
    """1ro A de Secundaria (curso de rflores) o 6to A de Primaria (curso de erojas)."""
    orden = "ASC" if nivel == "Secundaria" else "DESC"
    return await _sql(f"SELECT id_curso FROM v_curso WHERE nombre_nivel = :n AND paralelo = 'A' "
                      f"ORDER BY orden_grado {orden} LIMIT 1", n=nivel)


async def _titulos(cliente, cabecera) -> set[str]:
    r = await cliente.get(URL, headers=cabecera)
    assert r.status_code == 200, r.text
    return {c["titulo"] for c in r.json()["comunicados"]}


def _futuro(dias: int = 3) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=dias)).isoformat()


async def test_cu27_permisos_por_rol(cliente):
    for usuario in ("mquispe", "marioq"):
        cabecera = await iniciar(cliente, usuario)
        assert (await cliente.get(f"{URL}/destinos", headers=cabecera)).status_code == 403
        r = await cliente.post(URL, headers=cabecera, json={"titulo": "Hola", "contenido": "Prueba de envío",
                                                            "alcance": "todos"})
        assert r.status_code == 403
        assert (await cliente.get(f"{URL}/{await _id('Inicio del 3er Trimestre')}/lecturas",
                                  headers=cabecera)).status_code == 403
    assert (await cliente.get(URL)).status_code == 401


async def test_cu27_cada_rol_ve_solo_lo_dirigido_a_el(cliente, admin):
    todos, examen, citacion = "Inicio del 3er Trimestre", "Examen de Matematica", "Citacion a la tutora de Mariana Ticona"
    assert await _titulos(cliente, admin) >= {todos, examen, citacion}
    assert await _titulos(cliente, await iniciar(cliente, "rflores")) == {todos, examen, citacion}
    assert await _titulos(cliente, await iniciar(cliente, "erojas")) == {todos}          # no enseña en 1ro A Sec.
    assert await _titulos(cliente, await iniciar(cliente, "mquispe")) == {todos, examen}  # la citación es de otra
    assert await _titulos(cliente, await iniciar(cliente, "marioq")) == {todos, examen}

    # Un comunicado que no le corresponde no se puede abrir
    mquispe = await iniciar(cliente, "mquispe")
    assert (await cliente.get(f"{URL}/{await _id(citacion)}", headers=mquispe)).status_code == 404


async def test_cu27_profesor_solo_publica_a_sus_cursos_y_estudiantes(cliente, profesor):
    sec, pri = await _id_curso("Secundaria"), await _id_curso("Primaria")

    r = await cliente.get(f"{URL}/destinos", headers=profesor)
    assert r.status_code == 200, r.text
    destinos = r.json()
    assert destinos["puede_todos"] is False
    assert [c["id_curso"] for c in destinos["cursos"]] == [sec]
    assert {e["ci"] for e in destinos["estudiantes"]} == {f"450000{n}" for n in range(1, 7)}

    base = {"titulo": "Tarea de Matemática", "contenido": "Resolver los ejercicios de la página 20."}
    assert (await cliente.post(URL, headers=profesor, json={**base, "alcance": "todos"})).status_code == 403
    assert (await cliente.post(URL, headers=profesor, json={**base, "alcance": "curso", "id_curso": pri})).status_code == 403
    assert (await cliente.post(URL, headers=profesor, json={**base, "alcance": "estudiante",
                                                            "ci_estudiante": "4500007"})).status_code == 403

    r = await cliente.post(URL, headers=profesor, json={**base, "alcance": "curso", "id_curso": sec})
    assert r.status_code == 201, r.text
    creado = r.json()
    assert creado["ci_autor"] == "2000001" and creado["es_mio"] and creado["destinatario"].startswith("1ro A")
    assert creado["lecturas"] == 0 and creado["gestion"] == 2026
    assert "Tarea de Matemática" in await _titulos(cliente, await iniciar(cliente, "mquispe"))
    assert "Tarea de Matemática" not in await _titulos(cliente, await iniciar(cliente, "erojas"))


async def test_cu27_administrador_publica_a_todos(cliente, admin):
    r = await cliente.post(URL, headers=admin, json={"titulo": "Feriado", "contenido": "No habrá clases el lunes.",
                                                     "alcance": "todos", "id_curso": 99})
    assert r.status_code == 201, r.text
    assert r.json()["destinatario"] == "Toda la comunidad" and r.json()["id_curso"] is None
    for usuario in ("rflores", "erojas", "mquispe", "marioq", "secretaria"):
        assert "Feriado" in await _titulos(cliente, await iniciar(cliente, usuario))

    base = {"titulo": "Aviso", "contenido": "Contenido del aviso"}
    assert (await cliente.post(URL, headers=admin, json={**base, "alcance": "curso", "id_curso": 999999})).status_code == 404
    assert (await cliente.post(URL, headers=admin, json={**base, "alcance": "estudiante",
                                                         "ci_estudiante": "1000001"})).status_code == 404
    assert (await cliente.post(URL, headers=admin, json={**base, "alcance": "curso"})).status_code == 422


async def test_cu27_citacion_solo_a_tutores_y_con_fecha_futura(cliente, profesor):
    base = {"titulo": "Citación", "contenido": "Se cita al tutor para conversar.", "tipo_comunicado": "citacion"}
    sec = await _id_curso("Secundaria")
    assert (await cliente.post(URL, headers=profesor, json={**base, "alcance": "curso", "id_curso": sec,
                                                            "fecha_citacion": _futuro()})).status_code == 422
    assert (await cliente.post(URL, headers=profesor, json={**base, "alcance": "estudiante",
                                                            "ci_estudiante": "4500001"})).status_code == 422
    r = await cliente.post(URL, headers=profesor, json={**base, "alcance": "estudiante", "ci_estudiante": "4500001",
                                                        "fecha_citacion": "2020-01-01T10:00"})
    assert r.status_code == 400

    r = await cliente.post(URL, headers=profesor, json={**base, "alcance": "estudiante", "ci_estudiante": "4500001",
                                                        "fecha_citacion": _futuro()})
    assert r.status_code == 201, r.text
    assert r.json()["tipo_comunicado"] == "citacion" and r.json()["fecha_citacion"] is not None
    assert "Citación" in await _titulos(cliente, await iniciar(cliente, "marioq"))       # su tutor
    assert "Citación" not in await _titulos(cliente, await iniciar(cliente, "mquispe"))  # el estudiante no

    lecturas = (await cliente.get(f"{URL}/{r.json()['id_comunicado']}/lecturas", headers=profesor)).json()
    assert {d["ci"] for d in lecturas["destinatarios"]} == {"3000001", "3000002"}         # padre y madre


async def test_cu27_marcar_leido_una_vez_y_registro_de_lectura(cliente, profesor):
    examen = await _id("Examen de Matematica")
    mquispe = await iniciar(cliente, "mquispe")

    antes = (await cliente.get(URL, headers=mquispe)).json()["no_leidos"]
    r = await cliente.post(f"{URL}/{examen}/leido", headers=mquispe)
    assert r.status_code == 200, r.text
    primera = r.json()["leido_en"]
    assert primera is not None and r.json()["lecturas"] is None       # el conteo es solo del autor
    assert (await cliente.get(URL, headers=mquispe)).json()["no_leidos"] == antes - 1

    otra = await cliente.post(f"{URL}/{examen}/leido", headers=mquispe)
    assert otra.json()["leido_en"] == primera                          # no cambia la primera lectura
    assert await _sql("SELECT count(*) FROM comunicado_lectura WHERE id_comunicado_lectura = :id", id=examen) == 1

    # El autor no "lee" su propio comunicado
    assert (await cliente.post(f"{URL}/{examen}/leido", headers=profesor)).status_code == 400

    r = await cliente.get(f"{URL}/{examen}/lecturas", headers=profesor)
    assert r.status_code == 200, r.text
    registro = r.json()
    assert registro["total_leidos"] == 1
    leidos = [d for d in registro["destinatarios"] if d["leido_en"]]
    assert [d["ci"] for d in leidos] == ["4500001"]
    cis = {d["ci"] for d in registro["destinatarios"]}
    assert {"4500001", "4500006", "3000001", "3000002"} <= cis and "4500007" not in cis
    assert registro["total_destinatarios"] == len(registro["destinatarios"])

    # Otro docente no ve el registro de un comunicado ajeno
    erojas = await iniciar(cliente, "erojas")
    assert (await cliente.get(f"{URL}/{examen}/lecturas", headers=erojas)).status_code == 404
    todos = await _id("Inicio del 3er Trimestre")
    assert (await cliente.get(f"{URL}/{todos}/lecturas", headers=erojas)).status_code == 403


async def test_cu27_eliminar_solo_autor_o_administrador(cliente, admin, profesor):
    todos, examen = await _id("Inicio del 3er Trimestre"), await _id("Examen de Matematica")
    assert (await cliente.delete(f"{URL}/{todos}", headers=profesor)).status_code == 403

    await cliente.post(f"{URL}/{examen}/leido", headers=await iniciar(cliente, "mquispe"))
    r = await cliente.delete(f"{URL}/{examen}", headers=profesor)
    assert r.status_code == 200, r.text
    assert (await cliente.get(f"{URL}/{examen}", headers=profesor)).status_code == 404
    assert await _sql("SELECT count(*) FROM comunicado_lectura WHERE id_comunicado_lectura = :id", id=examen) == 0

    assert (await cliente.delete(f"{URL}/{todos}", headers=admin)).status_code == 200
    assert (await cliente.delete(f"{URL}/{todos}", headers=admin)).status_code == 404

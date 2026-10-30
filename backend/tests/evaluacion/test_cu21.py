"""Pruebas del CU21: registrar asistencia de estudiantes.

Datos de 08_datos_prueba: rflores (CI 2000001) dicta Matemática en 1ro A de Secundaria
(lunes y jueves); Comunicación del mismo curso es de otro profesor (2000002). El 1er
trimestre está cerrado. Las fechas se calculan desde "hoy" para no depender del día de la semana.
"""
from datetime import date, timedelta

from sqlalchemy import text

from app.nucleo import bd
from tests.conftest import iniciar

ESTADOS = ("presente", "ausente", "tardanza", "justificado")


async def _sql(consulta: str, **params):
    """Ejecuta SQL directo dentro de la transacción de la prueba (se deshace al terminar)."""
    async with bd._fabrica() as sesion:
        await sesion.execute(text(consulta), params)
        await sesion.commit()


async def _clases(cliente, cabecera) -> dict:
    r = await cliente.get("/evaluacion/asistencia/clases", headers=cabecera)
    assert r.status_code == 200, r.text
    return r.json()


def _clase(clases: dict, materia: str) -> dict:
    return next(c for c in clases["clases"] if c["materia"] == materia and c["curso"].startswith("1ro A"))


def _lunes_pasado(hoy: date) -> date:
    """Lunes de la semana anterior (3er trimestre, abierto)."""
    return hoy - timedelta(days=hoy.weekday() + 7)


async def _lista(cliente, cabecera, id_asignacion: int, fecha: date):
    return await cliente.get(f"/evaluacion/asistencia/{id_asignacion}", params={"fecha": fecha.isoformat()},
                             headers=cabecera)


def _registros(lista: dict, estado: str = "presente") -> list[dict]:
    return [{"ci_estudiante": e["ci"], "estado": estado} for e in lista["estudiantes"]]


async def _guardar(cliente, cabecera, id_asignacion: int, fecha: date, registros: list[dict]):
    return await cliente.put(f"/evaluacion/asistencia/{id_asignacion}", headers=cabecera,
                             json={"fecha": fecha.isoformat(), "registros": registros})


async def _matematica(cliente, profesor) -> tuple[int, date]:
    clases = await _clases(cliente, profesor)
    return _clase(clases, "Matematica")["id_asignacion"], date.fromisoformat(clases["hoy"])


async def test_cu21_solo_administrador_y_profesor(cliente):
    for usuario in ("mquispe", "marioq"):   # estudiante y tutor
        cabecera = await iniciar(cliente, usuario)
        assert (await cliente.get("/evaluacion/asistencia/clases", headers=cabecera)).status_code == 403
        assert (await cliente.put("/evaluacion/asistencia/1", headers=cabecera,
                                  json={"fecha": "2026-09-01", "registros": []})).status_code == 403


async def test_cu21_profesor_ve_solo_sus_clases(cliente, admin, profesor):
    propias = await _clases(cliente, profesor)
    assert propias["gestion"] == 2026 and propias["clases"]
    assert {c["ci_profesor"] for c in propias["clases"]} == {"2000001"}
    assert _clase(propias, "Matematica")["dias"] == ["lunes", "jueves"]
    todas = await _clases(cliente, admin)
    assert len(todas["clases"]) > len(propias["clases"])


async def test_cu21_profesor_no_registra_clase_ajena(cliente, admin, profesor):
    ajena = _clase(await _clases(cliente, admin), "Comunicacion y Lenguajes")["id_asignacion"]
    _, hoy = await _matematica(cliente, profesor)
    assert (await _lista(cliente, profesor, ajena, _lunes_pasado(hoy))).status_code == 403
    r = await _guardar(cliente, profesor, ajena, _lunes_pasado(hoy), [{"ci_estudiante": "4500001", "estado": "presente"}])
    assert r.status_code == 403
    assert (await _lista(cliente, profesor, 999999, _lunes_pasado(hoy))).status_code == 404


async def test_cu21_lista_y_aviso_de_dia_sin_clase(cliente, profesor):
    id_mat, hoy = await _matematica(cliente, profesor)
    lunes = _lunes_pasado(hoy)
    r = await _lista(cliente, profesor, id_mat, lunes)
    assert r.status_code == 200, r.text
    lista = r.json()
    assert lista["dia_con_clase"] and lista["editable"] and lista["periodo"] == "3er Trimestre"
    assert len(lista["estudiantes"]) >= 6
    martes = (await _lista(cliente, profesor, id_mat, lunes + timedelta(days=1))).json()
    assert martes["dia_con_clase"] is False and martes["editable"]   # solo aviso


async def test_cu21_registrar_y_corregir_sin_duplicar(cliente, profesor):
    id_mat, hoy = await _matematica(cliente, profesor)
    fecha = _lunes_pasado(hoy)
    lista = (await _lista(cliente, profesor, id_mat, fecha)).json()
    registros = _registros(lista)
    registros[0] = {**registros[0], "estado": "ausente", "observacion": "  Sin   aviso "}

    r = await _guardar(cliente, profesor, id_mat, fecha, registros)
    assert r.status_code == 200, r.text
    guardada = r.json()
    assert guardada["registrada"]
    assert guardada["estudiantes"][0]["estado"] == "ausente"
    assert guardada["estudiantes"][0]["observacion"] == "Sin aviso"

    registros[0] = {**registros[0], "estado": "justificado", "observacion": "Certificado médico"}
    r = await _guardar(cliente, profesor, id_mat, fecha, registros)
    assert r.status_code == 200 and r.json()["estudiantes"][0]["estado"] == "justificado"

    async with bd._fabrica() as sesion:
        filas = await sesion.scalar(
            text("SELECT count(*) FROM asistencia WHERE id_asignacion_asistencia = :a AND fecha_asistencia = :f"),
            {"a": id_mat, "f": fecha},
        )
    assert filas == len(registros)


async def test_cu21_fechas_invalidas(cliente, profesor):
    id_mat, hoy = await _matematica(cliente, profesor)
    lista = (await _lista(cliente, profesor, id_mat, _lunes_pasado(hoy))).json()
    for fecha, texto in ((hoy + timedelta(days=1), "futura"), (date(2025, 11, 3), "gestión 2026")):
        r = await _guardar(cliente, profesor, id_mat, fecha, _registros(lista))
        assert r.status_code == 400 and texto in r.json()["detalle"], r.text
        assert (await _lista(cliente, profesor, id_mat, fecha)).status_code == 400


async def test_cu21_toda_la_clase_y_solo_inscritos(cliente, profesor):
    id_mat, hoy = await _matematica(cliente, profesor)
    fecha = _lunes_pasado(hoy)
    registros = _registros((await _lista(cliente, profesor, id_mat, fecha)).json())

    r = await _guardar(cliente, profesor, id_mat, fecha, registros[1:])
    assert r.status_code == 400 and "Falta marcar" in r.json()["detalle"]
    r = await _guardar(cliente, profesor, id_mat, fecha, [*registros, {"ci_estudiante": "4500007", "estado": "presente"}])
    assert r.status_code == 400 and "4500007" in r.json()["detalle"]   # estudiante de Primaria
    r = await _guardar(cliente, profesor, id_mat, fecha, [*registros, registros[0]])
    assert r.status_code == 422
    r = await _guardar(cliente, profesor, id_mat, fecha, [{**registros[0], "estado": "feriado"}, *registros[1:]])
    assert r.status_code == 422


async def test_cu21_estudiante_retirado_no_aparece(cliente, profesor):
    id_mat, hoy = await _matematica(cliente, profesor)
    fecha = _lunes_pasado(hoy)
    await _sql("""UPDATE inscripcion SET estado_inscripcion = 'retirada', fecha_retiro = CURRENT_DATE
                   WHERE ci_estudiante_inscripcion = '4500001'""")
    lista = (await _lista(cliente, profesor, id_mat, fecha)).json()
    assert "4500001" not in {e["ci"] for e in lista["estudiantes"]}
    r = await _guardar(cliente, profesor, id_mat, fecha,
                       [*_registros(lista), {"ci_estudiante": "4500001", "estado": "presente"}])
    assert r.status_code == 400 and "retirados" in r.json()["detalle"]


async def test_cu21_periodo_cerrado_solo_administrador(cliente, admin, profesor):
    id_mat, _ = await _matematica(cliente, profesor)
    fecha = date(2026, 3, 2)   # 1er trimestre (cerrado en los datos de prueba)

    lista = (await _lista(cliente, profesor, id_mat, fecha)).json()
    assert lista["editable"] is False and "1er Trimestre" in lista["motivo_no_editable"]
    r = await _guardar(cliente, profesor, id_mat, fecha, _registros(lista))
    assert r.status_code == 403 and "administrador" in r.json()["detalle"]

    assert (await _lista(cliente, admin, id_mat, fecha)).json()["editable"]
    r = await _guardar(cliente, admin, id_mat, fecha, _registros(lista, "tardanza"))
    assert r.status_code == 200 and {e["estado"] for e in r.json()["estudiantes"]} == {"tardanza"}

"""Pruebas del CU23: registrar calificaciones, autoevaluación y cierre del trimestre.

Datos de 08_datos_prueba: gestión 2026 con 1er trimestre cerrado (con notas y boletines),
2do trimestre abierto (con notas) y 3er trimestre abierto sin notas. Dimensiones: Ser 10,
Saber 35, Hacer 35, Decidir 10 y Autoevaluación 10. Profesor rflores; estudiante mquispe (4500001).
"""
from sqlalchemy import text

from app.nucleo import bd
from tests.conftest import USUARIOS, iniciar


async def _sql(consulta: str, **params):
    async with bd._fabrica() as sesion:
        await sesion.execute(text(consulta), params)
        await sesion.commit()


async def _valor(consulta: str, **params):
    async with bd._fabrica() as sesion:
        return await sesion.scalar(text(consulta), params)


async def _datos_profesor(cliente):
    """Cabecera del profesor, su primera clase, los periodos por nombre y las dimensiones por nombre."""
    cabecera = await iniciar(cliente, USUARIOS["profesor"])
    r = await cliente.get("/evaluacion/calificaciones/clases", headers=cabecera)
    assert r.status_code == 200, r.text
    datos = r.json()
    periodos = {p["nombre_periodo"]: p["id_periodo"] for p in datos["periodos"]}
    dimensiones = {d["nombre_dimension"]: d["id_dimension"] for d in datos["dimensiones"]}
    return cabecera, datos["clases"][0]["id_asignacion"], periodos, dimensiones


def _notas(dim, ser=None, saber=None, hacer=None, decidir=None):
    valores = {"Ser": ser, "Saber": saber, "Hacer": hacer, "Decidir": decidir}
    return {str(dim[k]): v for k, v in valores.items()}


async def test_cu23_profesor_ve_solo_sus_clases(cliente):
    cabecera = await iniciar(cliente, USUARIOS["profesor"])
    r = await cliente.get("/evaluacion/calificaciones/clases", headers=cabecera)
    assert r.status_code == 200, r.text
    datos = r.json()
    assert datos["gestion"] == 2026 and datos["nota_minima"] == 51
    assert len(datos["periodos"]) == 3 and len(datos["dimensiones"]) == 5
    assert datos["clases"] and len({c["profesor"] for c in datos["clases"]}) == 1
    for usuario in ("tutor", "estudiante"):
        r = await cliente.get("/evaluacion/calificaciones/clases", headers=await iniciar(cliente, USUARIOS[usuario]))
        assert r.status_code == 403


async def test_cu23_profesor_registra_y_corrige_notas(cliente):
    cabecera, clase, periodos, dim = await _datos_profesor(cliente)
    url = f"/evaluacion/calificaciones/planilla/{clase}"
    r = await cliente.get(url, headers=cabecera, params={"id_periodo": periodos["3er Trimestre"]})
    assert r.status_code == 200, r.text
    planilla = r.json()
    assert planilla["editable"] is True
    ci = planilla["estudiantes"][0]["ci"]
    # 08_datos_prueba ya trae solo el "Saber" de Matemática en el 3er trimestre: la nota está incompleta
    assert list(planilla["estudiantes"][0]["puntajes"]) in ([], [str(dim["Saber"])])

    cuerpo = {"id_periodo": periodos["3er Trimestre"],
              "notas": [{"ci_estudiante": ci, "puntajes": _notas(dim, 9, 30, 31, 8), "observacion": "Buen trimestre"}]}
    r = await cliente.put(url, headers=cabecera, json=cuerpo)
    assert r.status_code == 200, r.text
    fila = next(e for e in r.json()["estudiantes"] if e["ci"] == ci)
    assert fila["nota_final"] == 78 and fila["observacion"] == "Buen trimestre"

    # Corrección de una sola dimensión: las demás no cambian
    cuerpo = {"id_periodo": periodos["3er Trimestre"], "notas": [{"ci_estudiante": ci, "puntajes": {str(dim["Saber"]): 33}}]}
    r = await cliente.put(url, headers=cabecera, json=cuerpo)
    fila = next(e for e in r.json()["estudiantes"] if e["ci"] == ci)
    assert fila["nota_final"] == 81 and fila["observacion"] == "Buen trimestre"


async def test_cu23_puntaje_fuera_de_rango(cliente):
    cabecera, clase, periodos, dim = await _datos_profesor(cliente)
    url = f"/evaluacion/calificaciones/planilla/{clase}"
    ci = (await cliente.get(url, headers=cabecera, params={"id_periodo": periodos["3er Trimestre"]})).json()["estudiantes"][0]["ci"]
    for saber in (36, -1):
        r = await cliente.put(url, headers=cabecera, json={
            "id_periodo": periodos["3er Trimestre"], "notas": [{"ci_estudiante": ci, "puntajes": _notas(dim, saber=saber)}]})
        assert r.status_code == 400, r.text
        assert "Saber debe estar entre 0 y 35" in r.json()["detalle"]


async def test_cu23_profesor_no_registra_autoevaluacion(cliente):
    cabecera, clase, periodos, dim = await _datos_profesor(cliente)
    url = f"/evaluacion/calificaciones/planilla/{clase}"
    ci = (await cliente.get(url, headers=cabecera, params={"id_periodo": periodos["3er Trimestre"]})).json()["estudiantes"][0]["ci"]
    r = await cliente.put(url, headers=cabecera, json={
        "id_periodo": periodos["3er Trimestre"], "notas": [{"ci_estudiante": ci, "puntajes": {str(dim["Autoevaluacion"]): 9}}]})
    assert r.status_code == 403


async def test_cu23_profesor_no_registra_clase_ajena(cliente):
    cabecera, _, periodos, _ = await _datos_profesor(cliente)
    ajena = await _valor("""SELECT a.id_asignacion FROM asignacion_profesor_clase a
                             WHERE a.ci_profesor_asignacion <> (SELECT ci_persona FROM usuario WHERE nombre_usuario = 'rflores')
                             LIMIT 1""")
    r = await cliente.get(f"/evaluacion/calificaciones/planilla/{ajena}", headers=cabecera,
                          params={"id_periodo": periodos["3er Trimestre"]})
    assert r.status_code == 403


async def test_cu23_estudiante_no_inscrito_en_el_curso(cliente):
    cabecera, clase, periodos, dim = await _datos_profesor(cliente)
    r = await cliente.put(f"/evaluacion/calificaciones/planilla/{clase}", headers=cabecera, json={
        "id_periodo": periodos["3er Trimestre"], "notas": [{"ci_estudiante": "9999999", "puntajes": _notas(dim, ser=5)}]})
    assert r.status_code == 400 and "No están inscritos" in r.json()["detalle"]


async def test_cu23_periodo_cerrado_solo_lo_corrige_el_administrador(cliente, admin):
    cabecera, clase, periodos, dim = await _datos_profesor(cliente)
    url = f"/evaluacion/calificaciones/planilla/{clase}"
    t1 = periodos["1er Trimestre"]
    planilla = (await cliente.get(url, headers=cabecera, params={"id_periodo": t1})).json()
    assert planilla["editable"] is False and "cerrado" in planilla["motivo_no_editable"]
    ci = planilla["estudiantes"][0]["ci"]
    cuerpo = {"id_periodo": t1, "notas": [{"ci_estudiante": ci, "puntajes": _notas(dim, ser=10)}]}
    assert (await cliente.put(url, headers=cabecera, json=cuerpo)).status_code == 403
    r = await cliente.put(url, headers=admin, json=cuerpo)
    assert r.status_code == 200, r.text


async def test_cu23_trimestre_que_no_empezo_no_admite_notas(cliente):
    cabecera, clase, periodos, dim = await _datos_profesor(cliente)
    t3 = periodos["3er Trimestre"]
    await _sql("UPDATE periodo SET fecha_inicio_p = CURRENT_DATE + 5 WHERE id_periodo = :p", p=t3)
    url = f"/evaluacion/calificaciones/planilla/{clase}"
    planilla = (await cliente.get(url, headers=cabecera, params={"id_periodo": t3})).json()
    assert planilla["editable"] is False and "aún no empieza" in planilla["motivo_no_editable"]
    r = await cliente.put(url, headers=cabecera, json={
        "id_periodo": t3, "notas": [{"ci_estudiante": planilla["estudiantes"][0]["ci"], "puntajes": _notas(dim, ser=5)}]})
    assert r.status_code == 400


async def test_cu23_vaciar_todas_las_dimensiones_borra_la_nota(cliente):
    """Una calificación sin dimensiones no debe quedar como nota 0 en el boletín."""
    cabecera, clase, periodos, dim = await _datos_profesor(cliente)
    url = f"/evaluacion/calificaciones/planilla/{clase}"
    t3 = periodos["3er Trimestre"]
    ci = (await cliente.get(url, headers=cabecera, params={"id_periodo": t3})).json()["estudiantes"][0]["ci"]
    await cliente.put(url, headers=cabecera, json={"id_periodo": t3, "notas": [{"ci_estudiante": ci, "puntajes": _notas(dim, 5, 5)}]})
    r = await cliente.put(url, headers=cabecera, json={"id_periodo": t3, "notas": [{"ci_estudiante": ci, "puntajes": _notas(dim)}]})
    assert next(e for e in r.json()["estudiantes"] if e["ci"] == ci)["nota_final"] is None
    assert await _valor("SELECT count(*) FROM calificacion WHERE ci_estudiante_calificacion = :ci AND id_periodo_calificacion = :p",
                        ci=ci, p=t3) == 0


async def test_cu23_estudiante_ve_sus_notas_y_se_autoevalua(cliente):
    cabecera = await iniciar(cliente, USUARIOS["estudiante"])
    r = await cliente.get("/evaluacion/calificaciones/mias", headers=cabecera)
    assert r.status_code == 200, r.text
    datos = r.json()
    assert datos["periodo"]["nombre_periodo"] == "3er Trimestre" and datos["autoevaluacion_editable"] is True
    materia = datos["materias"][0]["id_materia"]
    t3 = datos["periodo"]["id_periodo"]
    auto = next(d["id_dimension"] for d in datos["dimensiones"] if d["es_autoevaluacion"])

    r = await cliente.put("/evaluacion/calificaciones/autoevaluacion", headers=cabecera, json={
        "id_periodo": t3, "autoevaluaciones": [{"id_materia": materia, "puntaje": 9}]})
    assert r.status_code == 200, r.text
    fila = next(m for m in r.json()["materias"] if m["id_materia"] == materia)
    assert fila["puntajes"][str(auto)] == 9 and fila["nota_final"] == 9

    r = await cliente.put("/evaluacion/calificaciones/autoevaluacion", headers=cabecera, json={
        "id_periodo": t3, "autoevaluaciones": [{"id_materia": materia, "puntaje": 11}]})
    assert r.status_code == 400
    r = await cliente.put("/evaluacion/calificaciones/autoevaluacion", headers=cabecera, json={
        "id_periodo": t3, "autoevaluaciones": [{"id_materia": 999999, "puntaje": 5}]})
    assert r.status_code == 400

    # Ve también las notas de un trimestre anterior (con todas las dimensiones)
    t2 = next(p["id_periodo"] for p in datos["periodos"] if p["nombre_periodo"] == "2do Trimestre")
    r = await cliente.get("/evaluacion/calificaciones/mias", headers=cabecera, params={"id_periodo": t2})
    assert all(m["nota_final"] is not None for m in r.json()["materias"])


async def test_cu23_autoevaluacion_en_trimestre_cerrado(cliente):
    cabecera = await iniciar(cliente, USUARIOS["estudiante"])
    datos = (await cliente.get("/evaluacion/calificaciones/mias", headers=cabecera)).json()
    t1 = next(p["id_periodo"] for p in datos["periodos"] if p["nombre_periodo"] == "1er Trimestre")
    r = await cliente.put("/evaluacion/calificaciones/autoevaluacion", headers=cabecera, json={
        "id_periodo": t1, "autoevaluaciones": [{"id_materia": datos["materias"][0]["id_materia"], "puntaje": 8}]})
    assert r.status_code == 403


async def test_cu23_cerrar_y_reabrir_trimestre(cliente, admin):
    cabecera, clase, periodos, dim = await _datos_profesor(cliente)
    t2 = periodos["2do Trimestre"]
    bitacora = await _valor("SELECT count(*) FROM bitacora WHERE tabla_afectada = 'periodo'")

    for usuario in ("profesor", "estudiante"):
        r = await cliente.post(f"/evaluacion/calificaciones/periodos/{t2}/cerrar", headers=await iniciar(cliente, USUARIOS[usuario]))
        assert r.status_code == 403

    r = await cliente.post(f"/evaluacion/calificaciones/periodos/{t2}/cerrar", headers=admin)
    assert r.status_code == 200, r.text
    assert r.json()["estado_periodo"] == "cerrado" and r.json()["boletines"] > 0
    assert (await cliente.post(f"/evaluacion/calificaciones/periodos/{t2}/cerrar", headers=admin)).status_code == 409

    # Cerrado: el profesor ya no corrige
    url = f"/evaluacion/calificaciones/planilla/{clase}"
    ci = (await cliente.get(url, headers=cabecera, params={"id_periodo": t2})).json()["estudiantes"][0]["ci"]
    cuerpo = {"id_periodo": t2, "notas": [{"ci_estudiante": ci, "puntajes": _notas(dim, ser=10)}]}
    assert (await cliente.put(url, headers=cabecera, json=cuerpo)).status_code == 403

    # Reabierto: vuelve a corregir
    r = await cliente.post(f"/evaluacion/calificaciones/periodos/{t2}/reabrir", headers=admin)
    assert r.status_code == 200 and r.json()["estado_periodo"] == "abierto"
    assert (await cliente.post(f"/evaluacion/calificaciones/periodos/{t2}/reabrir", headers=admin)).status_code == 409
    assert (await cliente.put(url, headers=cabecera, json=cuerpo)).status_code == 200

    assert await _valor("SELECT count(*) FROM bitacora WHERE tabla_afectada = 'periodo'") == bitacora + 2


async def test_cu23_no_se_cierra_un_trimestre_que_no_empezo(cliente, admin):
    _, _, periodos, _ = await _datos_profesor(cliente)
    t3 = periodos["3er Trimestre"]
    await _sql("UPDATE periodo SET fecha_inicio_p = CURRENT_DATE + 5 WHERE id_periodo = :p", p=t3)
    r = await cliente.post(f"/evaluacion/calificaciones/periodos/{t3}/cerrar", headers=admin)
    assert r.status_code == 400 and "aún no empieza" in r.json()["detalle"]

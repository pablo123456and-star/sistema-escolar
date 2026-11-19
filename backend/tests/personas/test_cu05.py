"""Pruebas del CU05: buscar, consultar, actualizar, dar de baja y reactivar personas."""
from sqlalchemy import text

from app.nucleo import bd
from tests.conftest import CONTRASENA_PRUEBA, iniciar

P = "/personas/personas"
MATEO = "4500001"       # estudiante de 1ro A Sec., usuario mquispe, inscripción activa
DIRECCION = "1000001"   # administradora conectada en el fixture admin
INEXISTENTE = "4599999"


async def _inscripcion(ci: str):
    """Estado, fecha y motivo de retiro de la inscripción de la gestión abierta (leído directo de la BD)."""
    async with bd._fabrica() as s:
        return (
            await s.execute(
                text("""SELECT i.estado_inscripcion, i.fecha_retiro, i.motivo_retiro, current_date AS hoy
                          FROM inscripcion i
                          JOIN gestion g ON g.id_gestion = i.id_gestion_inscripcion AND g.estado_gestion = 'abierta'
                         WHERE i.ci_estudiante_inscripcion = :ci"""),
                {"ci": ci},
            )
        ).one()


async def test_cu05_solo_administrador(cliente, profesor):
    estudiante = await iniciar(cliente, "mquispe")
    for cabecera in (profesor, estudiante):
        assert (await cliente.get(P, headers=cabecera)).status_code == 403
        assert (await cliente.get(f"{P}/{MATEO}", headers=cabecera)).status_code == 403
        assert (await cliente.patch(f"{P}/{MATEO}", headers=cabecera, json={"telefono": "70000000"})).status_code == 403
        assert (await cliente.post(f"{P}/{MATEO}/baja", headers=cabecera, json={"motivo": "Prueba"})).status_code == 403
        assert (await cliente.post(f"{P}/{MATEO}/reactivar", headers=cabecera)).status_code == 403


async def test_cu05_buscar_y_paginar(cliente, admin):
    r = await cliente.get(P, params={"buscar": "quispe"}, headers=admin)
    assert r.status_code == 200
    datos = r.json()
    mateo = next(p for p in datos["items"] if p["ci"] == MATEO)
    assert mateo["es_estudiante"] and not mateo["es_profesor"] and mateo["nombre_usuario"] == "mquispe"
    assert datos["total"] >= 2

    pagina = (await cliente.get(P, params={"buscar": "quispe", "tamano": 1, "pagina": 2}, headers=admin)).json()
    assert len(pagina["items"]) == 1 and pagina["total"] == datos["total"] and pagina["pagina"] == 2

    por_ci = (await cliente.get(P, params={"buscar": MATEO}, headers=admin)).json()
    assert [p["ci"] for p in por_ci["items"]] == [MATEO]

    activos = (await cliente.get(P, params={"estado": "inactivo", "buscar": MATEO}, headers=admin)).json()
    assert activos["total"] == 0


async def test_cu05_ficha_sin_datos_sensibles(cliente, admin):
    r = await cliente.get(f"{P}/{MATEO}", headers=admin)
    assert r.status_code == 200
    d = r.json()
    assert d["es_estudiante"] and d["inscripcion"]["estado_inscripcion"] == "activa"
    assert d["usuario"] == {"nombre_usuario": "mquispe", "rol": "estudiante", "estado_usuario": "activo"}
    assert "password_hash" not in r.text and not d["es_usuario_actual"]

    propia = (await cliente.get(f"{P}/{DIRECCION}", headers=admin)).json()
    assert propia["es_usuario_actual"] and propia["es_administrativo"]


async def test_cu05_patch_cambia_solo_lo_enviado(cliente, admin):
    antes = (await cliente.get(f"{P}/{MATEO}", headers=admin)).json()
    r = await cliente.patch(f"{P}/{MATEO}", headers=admin,
                            json={"telefono": "70011122", "ci": "4500099", "nombre_persona": None})
    assert r.status_code == 200, r.text
    despues = r.json()
    assert despues["telefono"] == "70011122"
    # el CI no cambia y los obligatorios no se vacían
    assert despues["ci"] == MATEO and despues["nombre_persona"] == antes["nombre_persona"]
    for campo in ("expedido", "apellidos", "sexo", "fecha_nacimiento", "direccion", "email", "estado_persona"):
        assert despues[campo] == antes[campo], campo

    r = await cliente.patch(f"{P}/{MATEO}", headers=admin, json={"email": "no-es-correo"})
    assert r.status_code == 422


async def test_cu05_baja_y_reactivar(cliente, admin):
    r = await cliente.post(f"{P}/{MATEO}/baja", headers=admin, json={"motivo": "Cambio de colegio"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["estado_persona"] == "inactivo" and d["usuario"]["estado_usuario"] == "inactivo"
    assert d["inscripcion"]["estado_inscripcion"] == "retirada"
    ins = await _inscripcion(MATEO)
    assert ins.estado_inscripcion == "retirada" and ins.fecha_retiro == ins.hoy
    assert ins.motivo_retiro == "Cambio de colegio"

    # su cuenta ya no puede entrar
    sesion = await cliente.post("/seguridad/sesion", json={"identificador": "mquispe", "contrasena": CONTRASENA_PRUEBA})
    assert sesion.status_code != 200

    assert (await cliente.post(f"{P}/{MATEO}/baja", headers=admin, json={"motivo": "Otra vez"})).status_code == 400

    r = await cliente.post(f"{P}/{MATEO}/reactivar", headers=admin)
    assert r.status_code == 200
    d = r.json()
    assert d["estado_persona"] == "activo" and d["usuario"]["estado_usuario"] == "activo"
    # la inscripción retirada no se restaura
    assert d["inscripcion"]["estado_inscripcion"] == "retirada"
    assert (await cliente.post(f"{P}/{MATEO}/reactivar", headers=admin)).status_code == 400


async def test_cu05_baja_sin_motivo(cliente, admin):
    assert (await cliente.post(f"{P}/{MATEO}/baja", headers=admin, json={})).status_code == 422
    assert (await cliente.post(f"{P}/{MATEO}/baja", headers=admin, json={"motivo": "  "})).status_code == 422


async def test_cu05_no_puede_darse_de_baja_a_si_mismo(cliente, admin):
    r = await cliente.post(f"{P}/{DIRECCION}/baja", headers=admin, json={"motivo": "Prueba"})
    assert r.status_code == 400 and "sí mismo" in r.json()["detalle"]
    assert (await cliente.get(f"{P}/{DIRECCION}", headers=admin)).json()["estado_persona"] == "activo"


async def test_cu05_docente_con_materias_no_se_da_de_baja(cliente, admin):
    r = await cliente.post(f"{P}/2000001/baja", headers=admin, json={"motivo": "Renuncia"})
    assert r.status_code == 400 and "asignada" in r.json()["detalle"]


async def test_cu05_ci_inexistente(cliente, admin):
    assert (await cliente.get(f"{P}/{INEXISTENTE}", headers=admin)).status_code == 404
    assert (await cliente.patch(f"{P}/{INEXISTENTE}", headers=admin, json={"telefono": "70000000"})).status_code == 404
    assert (await cliente.post(f"{P}/{INEXISTENTE}/baja", headers=admin, json={"motivo": "Prueba"})).status_code == 404
    assert (await cliente.post(f"{P}/{INEXISTENTE}/reactivar", headers=admin)).status_code == 404

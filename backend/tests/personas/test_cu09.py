"""Pruebas del CU09: consultar estudiantes/tutores relacionados.

Datos de 08_datos_prueba.sql:
  - rflores (2000001) dicta Matemática en 1ro A Secundaria (estudiantes 4500001 a 4500006).
  - marioq (3000001) es tutor principal de Mateo (4500001) y Sofía (4500007); Rosa (3000002) es la madre.
  - mquispe (4500001) es estudiante.
"""
from tests.conftest import iniciar

URL = "/personas/relacionados"


async def test_cu09_sin_sesion(cliente):
    respuesta = await cliente.get(f"{URL}/4500001?tipo=estudiante")
    assert respuesta.status_code == 401


async def test_cu09_admin_ve_tutores_y_estudiantes(cliente, admin):
    r = await cliente.get(f"{URL}/4500001?tipo=estudiante", headers=admin)
    assert r.status_code == 200, r.text
    datos = r.json()
    assert datos["tipo"] == "estudiante" and datos["nombre_completo"]
    tutores = {t["ci"]: t for t in datos["relacionados"]}
    assert set(tutores) == {"3000001", "3000002"}
    assert tutores["3000001"]["es_principal"] and tutores["3000001"]["telefono"] == "72000001"
    assert not tutores["3000002"]["es_principal"]

    r = await cliente.get(f"{URL}/3000001?tipo=tutor", headers=admin)
    assert r.status_code == 200, r.text
    estudiantes = r.json()["relacionados"]
    assert {e["ci"] for e in estudiantes} == {"4500001", "4500007"}
    assert all(e["curso"] and e["estado"] == "activo" for e in estudiantes)


async def test_cu09_tipo_incorrecto(cliente, admin):
    """Si el CI no es del tipo consultado se avisa qué es (en vez de una lista vacía)."""
    r = await cliente.get(f"{URL}/3000001?tipo=estudiante", headers=admin)
    assert r.status_code == 400
    assert "es tutor" in r.json()["detalle"]

    r = await cliente.get(f"{URL}/4500001?tipo=tutor", headers=admin)
    assert r.status_code == 400
    assert "es estudiante" in r.json()["detalle"]

    r = await cliente.get(f"{URL}/2000001?tipo=estudiante", headers=admin)  # un docente
    assert r.status_code == 400


async def test_cu09_tutor(cliente):
    """El tutor ve a sus estudiantes y a los tutores de sus hijos; nada más."""
    tutor = await iniciar(cliente, "marioq")

    r = await cliente.get(f"{URL}/3000001?tipo=tutor", headers=tutor)
    assert r.status_code == 200, r.text
    assert {e["ci"] for e in r.json()["relacionados"]} == {"4500001", "4500007"}

    r = await cliente.get(f"{URL}/4500001?tipo=estudiante", headers=tutor)
    assert r.status_code == 200, r.text
    assert {t["ci"] for t in r.json()["relacionados"]} == {"3000001", "3000002"}

    assert (await cliente.get(f"{URL}/4500002?tipo=estudiante", headers=tutor)).status_code == 403
    assert (await cliente.get(f"{URL}/3000002?tipo=tutor", headers=tutor)).status_code == 403


async def test_cu09_estudiante(cliente):
    """El estudiante solo ve sus propios tutores."""
    estudiante = await iniciar(cliente, "mquispe")

    r = await cliente.get(f"{URL}/4500001?tipo=estudiante", headers=estudiante)
    assert r.status_code == 200, r.text
    assert {t["ci"] for t in r.json()["relacionados"]} == {"3000001", "3000002"}

    assert (await cliente.get(f"{URL}/4500002?tipo=estudiante", headers=estudiante)).status_code == 403
    assert (await cliente.get(f"{URL}/3000001?tipo=tutor", headers=estudiante)).status_code == 403


async def test_cu09_profesor(cliente, profesor):
    """El profesor ve los tutores de los estudiantes de sus clases, no los de otros ni a un tutor."""
    r = await cliente.get(f"{URL}/4500001?tipo=estudiante", headers=profesor)
    assert r.status_code == 200, r.text
    assert {t["ci"] for t in r.json()["relacionados"]} == {"3000001", "3000002"}

    assert (await cliente.get(f"{URL}/4500007?tipo=estudiante", headers=profesor)).status_code == 403
    assert (await cliente.get(f"{URL}/3000001?tipo=tutor", headers=profesor)).status_code == 403


async def test_cu09_ci_inexistente(cliente, admin):
    """Un CI inexistente: 404 para el administrador y 403 para los demás (no se revela si existe)."""
    assert (await cliente.get(f"{URL}/9999999?tipo=estudiante", headers=admin)).status_code == 404
    estudiante = await iniciar(cliente, "mquispe")
    assert (await cliente.get(f"{URL}/9999999?tipo=estudiante", headers=estudiante)).status_code == 403

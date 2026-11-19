"""Pruebas del CU09: consultar estudiantes/tutores relacionados.

backend/tests/personas/test_cu09.py
Datos de 08_datos_prueba.sql:
  - rflores (2000001) dicta Matemática en 1ro A Secundaria (estudiantes 4500001 a 4500006).
  - marioq (3000001) es tutor de Mateo (4500001) y Sofía (4500007).
  - mquispe (4500001) es estudiante.
"""
from tests.conftest import iniciar

URL = "/personas/relacionados"


async def test_cu09_sin_sesion(cliente):
    """Sin sesión debe responder 401."""
    respuesta = await cliente.get(f"{URL}/4500001?tipo=estudiante")
    assert respuesta.status_code == 401


async def test_cu09_admin_ve_todo(cliente, admin):
    """El administrador ve los tutores de un estudiante y los estudiantes de un tutor."""
    # Admin consulta tutores de un estudiante
    r = await cliente.get(f"{URL}/4500001?tipo=estudiante", headers=admin)
    assert r.status_code == 200, r.text
    tutores = r.json()
    assert len(tutores) > 0
    assert any(t["ci_relacionado"] == "3000001" for t in tutores)

    # Admin consulta estudiantes de un tutor (Mario Quispe, CI 3000001)
    r = await cliente.get(f"{URL}/3000001?tipo=tutor", headers=admin)
    assert r.status_code == 200, r.text
    estudiantes = r.json()
    assert len(estudiantes) == 2
    assert {e["ci_relacionado"] for e in estudiantes} == {"4500001", "4500007"}


async def test_cu09_tutor_ve_sus_estudiantes(cliente):
    """El tutor ve solo sus estudiantes y recibe 403 con uno ajeno."""
    tutor = await iniciar(cliente, "marioq")
    
    # El tutor se consulta a sí mismo (debería ver a sus estudiantes)
    r = await cliente.get(f"{URL}/3000001?tipo=tutor", headers=tutor)
    assert r.status_code == 200, r.text
    estudiantes = r.json()
    assert {e["ci_relacionado"] for e in estudiantes} == {"4500001", "4500007"}
    
    # El tutor intenta ver a un estudiante que NO es suyo (ej. 4500002)
    r = await cliente.get(f"{URL}/4500002?tipo=estudiante", headers=tutor)
    assert r.status_code == 403


async def test_cu09_estudiante_ve_sus_tutores(cliente):
    """El estudiante ve solo sus propios tutores."""
    estudiante = await iniciar(cliente, "mquispe")
    
    # El estudiante se consulta a sí mismo
    r = await cliente.get(f"{URL}/4500001?tipo=estudiante", headers=estudiante)
    assert r.status_code == 200, r.text
    tutores = r.json()
    assert any(t["ci_relacionado"] == "3000001" for t in tutores)
    
    # El estudiante intenta consultar a otro (debería dar 403)
    r = await cliente.get(f"{URL}/4500002?tipo=estudiante", headers=estudiante)
    assert r.status_code == 403


async def test_cu09_profesor_ve_sus_estudiantes(cliente, profesor):
    """El profesor ve solo los tutores de sus estudiantes."""
    # El profesor (rflores) dicta clases a 4500001
    r = await cliente.get(f"{URL}/4500001?tipo=estudiante", headers=profesor)
    assert r.status_code == 200, r.text
    
    # El profesor intenta ver a un estudiante al que NO le dicta clases (4500007)
    r = await cliente.get(f"{URL}/4500007?tipo=estudiante", headers=profesor)
    assert r.status_code == 403


async def test_cu09_ci_inexistente(cliente, admin):
    """Un CI inexistente responde 404."""
    r = await cliente.get(f"{URL}/9999999?tipo=estudiante", headers=admin)
    assert r.status_code == 404
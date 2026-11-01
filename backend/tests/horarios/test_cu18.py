"""
Pruebas del CU18: Gestionar aulas (paquete horarios).

Casos mínimos exigidos:
- Solo administrador (profesor u otro rol no puede -> 403).
- Crear aula exitosamente.
- Número repetido -> 409 conflicto.
- Capacidad <= 0 -> error (422 o 400).
- Editar aula.
- Cambiar estado de aula (disponible / mantenimiento / inactiva).
- Eliminar aula sin asignaciones -> 204.
- Eliminar aula con asignaciones -> 409 conflicto con mensaje:
  "El aula tiene clases asignadas: márquela como inactiva".
"""
import pytest
from tests.conftest import USUARIOS, iniciar


@pytest.mark.asyncio
async def test_cu18_profesor_no_puede_403(cliente, profesor):
    """Un profesor u otro rol no administrador recibe 403."""
    r_get = await cliente.get("/horarios/aulas", headers=profesor)
    assert r_get.status_code == 403

    r_post = await cliente.post(
        "/horarios/aulas",
        headers=profesor,
        json={"numero": "TEST-403", "capacidad": 30, "tipo_aula": "Teoría", "estado_aula": "disponible"},
    )
    assert r_post.status_code == 403

    r_patch = await cliente.patch(
        "/horarios/aulas/1",
        headers=profesor,
        json={"estado_aula": "mantenimiento"},
    )
    assert r_patch.status_code == 403

    r_delete = await cliente.delete("/horarios/aulas/1", headers=profesor)
    assert r_delete.status_code == 403


@pytest.mark.asyncio
async def test_cu18_listar_aulas(cliente, admin):
    """El administrador puede listar aulas y ver el total de clases asignadas."""
    r = await cliente.get("/horarios/aulas", headers=admin)
    assert r.status_code == 200, r.text
    aulas = r.json()
    assert isinstance(aulas, list)
    assert len(aulas) > 0
    primera = aulas[0]
    assert "id_aula" in primera
    assert "numero" in primera
    assert "capacidad" in primera
    assert "estado_aula" in primera
    assert "total_clases_asignadas" in primera


@pytest.mark.asyncio
async def test_cu18_crear_aula(cliente, admin):
    """Crear aula nueva con datos válidos."""
    datos = {
        "numero": "LAB-X1",
        "capacidad": 25,
        "tipo_aula": "Laboratorio de Computación",
        "estado_aula": "disponible",
    }
    r = await cliente.post("/horarios/aulas", headers=admin, json=datos)
    assert r.status_code == 201, r.text
    creada = r.json()
    assert creada["numero"] == "LAB-X1"
    assert creada["capacidad"] == 25
    assert creada["tipo_aula"] == "Laboratorio de Computación"
    assert creada["estado_aula"] == "disponible"
    assert creada["total_clases_asignadas"] == 0


@pytest.mark.asyncio
async def test_cu18_numero_repetido_409(cliente, admin):
    """Número de aula repetido produce conflicto 409."""
    # En 08_datos_prueba.sql existe B-201 o A-101
    r_get = await cliente.get("/horarios/aulas", headers=admin)
    existente = r_get.json()[0]
    num_existente = existente["numero"]

    r = await cliente.post(
        "/horarios/aulas",
        headers=admin,
        json={"numero": num_existente, "capacidad": 40, "estado_aula": "disponible"},
    )
    assert r.status_code == 409, f"Se esperaba 409 pero se obtuvo {r.status_code}: {r.text}"
    assert "Ya existe un aula con ese número" in r.json()["detalle"]


@pytest.mark.asyncio
async def test_cu18_capacidad_cero_o_menor_error(cliente, admin):
    """Capacidad 0 o negativa genera error (422 o 400)."""
    r_cero = await cliente.post(
        "/horarios/aulas",
        headers=admin,
        json={"numero": "AULA-0", "capacidad": 0, "estado_aula": "disponible"},
    )
    assert r_cero.status_code in (400, 422), f"Se esperaba error pero se obtuvo {r_cero.status_code}"

    r_neg = await cliente.post(
        "/horarios/aulas",
        headers=admin,
        json={"numero": "AULA-NEG", "capacidad": -5, "estado_aula": "disponible"},
    )
    assert r_neg.status_code in (400, 422), f"Se esperaba error pero se obtuvo {r_neg.status_code}"


@pytest.mark.asyncio
async def test_cu18_editar_aula(cliente, admin):
    """Editar capacidad y tipo de un aula recién creada."""
    r_crear = await cliente.post(
        "/horarios/aulas",
        headers=admin,
        json={"numero": "EDIT-01", "capacidad": 30, "tipo_aula": "Normal", "estado_aula": "disponible"},
    )
    assert r_crear.status_code == 201
    id_aula = r_crear.json()["id_aula"]

    r_edit = await cliente.patch(
        f"/horarios/aulas/{id_aula}",
        headers=admin,
        json={"numero": "EDIT-01B", "capacidad": 35, "tipo_aula": "Polivalente"},
    )
    assert r_edit.status_code == 200, r_edit.text
    modificada = r_edit.json()
    assert modificada["numero"] == "EDIT-01B"
    assert modificada["capacidad"] == 35
    assert modificada["tipo_aula"] == "Polivalente"


@pytest.mark.asyncio
async def test_cu18_cambiar_estado_aula(cliente, admin):
    """Cambiar el estado de un aula (disponible -> mantenimiento -> inactiva)."""
    r_crear = await cliente.post(
        "/horarios/aulas",
        headers=admin,
        json={"numero": "ESTADO-01", "capacidad": 20, "estado_aula": "disponible"},
    )
    assert r_crear.status_code == 201
    id_aula = r_crear.json()["id_aula"]

    # Cambiar a mantenimiento
    r_mant = await cliente.patch(
        f"/horarios/aulas/{id_aula}",
        headers=admin,
        json={"estado_aula": "mantenimiento"},
    )
    assert r_mant.status_code == 200
    assert r_mant.json()["estado_aula"] == "mantenimiento"

    # Cambiar a inactiva
    r_inac = await cliente.patch(
        f"/horarios/aulas/{id_aula}",
        headers=admin,
        json={"estado_aula": "inactiva"},
    )
    assert r_inac.status_code == 200
    assert r_inac.json()["estado_aula"] == "inactiva"


@pytest.mark.asyncio
async def test_cu18_eliminar_aula_sin_asignaciones(cliente, admin):
    """Eliminar aula sin asignaciones funciona (204)."""
    r_crear = await cliente.post(
        "/horarios/aulas",
        headers=admin,
        json={"numero": "DEL-01", "capacidad": 20, "estado_aula": "disponible"},
    )
    assert r_crear.status_code == 201
    id_aula = r_crear.json()["id_aula"]

    r_del = await cliente.delete(f"/horarios/aulas/{id_aula}", headers=admin)
    assert r_del.status_code == 204

    # Verificar que ya no existe
    r_get = await cliente.get("/horarios/aulas", headers=admin)
    assert not any(a["id_aula"] == id_aula for a in r_get.json())


@pytest.mark.asyncio
async def test_cu18_eliminar_aula_con_asignaciones_409(cliente, admin):
    """No se puede eliminar un aula con asignaciones; debe devolver 409 con el mensaje solicitado."""
    r_get = await cliente.get("/horarios/aulas", headers=admin)
    aulas = r_get.json()
    aula_con_clases = next((a for a in aulas if a["total_clases_asignadas"] > 0), None)
    assert aula_con_clases is not None, "Debe existir un aula de prueba con clases asignadas"

    r_del = await cliente.delete(f"/horarios/aulas/{aula_con_clases['id_aula']}", headers=admin)
    assert r_del.status_code == 409, f"Se esperaba 409 pero se obtuvo {r_del.status_code}: {r_del.text}"
    detalle = r_del.json()["detalle"]
    assert "El aula tiene clases asignadas: márquela como inactiva" in detalle

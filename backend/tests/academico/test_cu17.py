"""
Pruebas del CU17: Consultar historial de inscripciones.

Casos mínimos exigidos:
- Estudiante ve el suyo directo.
- Estudiante no ve a otro (403).
- Tutor ve a su hijo/tutelado.
- Tutor no ve a un ajeno (403).
- Admin ve a cualquiera.
- CI inexistente (404).
- El promedio coincide con el promedio de v_nota_final para esa gestión.
- Profesor u otro rol no permitido -> 403.
"""
import pytest
from sqlalchemy import text

from app.nucleo import bd
from tests.conftest import USUARIOS, iniciar


@pytest.mark.asyncio
async def test_cu17_estudiante_ve_el_suyo(cliente):
    """El estudiante autenticado puede consultar su propio historial de inscripciones."""
    cabecera = await iniciar(cliente, USUARIOS["estudiante"])
    r = await cliente.get("/academico/inscripciones/historial/4500001", headers=cabecera)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["ci"] == "4500001"
    assert "inscripciones" in data
    assert len(data["inscripciones"]) > 0
    primera = data["inscripciones"][0]
    assert "anio" in primera
    assert "curso" in primera
    assert "estado_inscripcion" in primera


@pytest.mark.asyncio
async def test_cu17_estudiante_no_ve_a_otro_403(cliente):
    """Un estudiante no puede consultar el historial de otro estudiante (403)."""
    cabecera = await iniciar(cliente, USUARIOS["estudiante"])
    # Intentar ver a otro estudiante (4500002)
    r = await cliente.get("/academico/inscripciones/historial/4500002", headers=cabecera)
    assert r.status_code == 403, f"Se esperaba 403 pero se obtuvo {r.status_code}: {r.text}"


@pytest.mark.asyncio
async def test_cu17_tutor_ve_a_su_hijo(cliente):
    """El tutor puede consultar el historial de su hijo asignado en tutor_estudiante."""
    cabecera = await iniciar(cliente, USUARIOS["tutor"])
    # marioq es tutor de mquispe (4500001)
    r = await cliente.get("/academico/inscripciones/historial/4500001", headers=cabecera)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["ci"] == "4500001"
    assert len(data["inscripciones"]) > 0


@pytest.mark.asyncio
async def test_cu17_tutor_no_ve_a_ajeno_403(cliente):
    """El tutor no puede consultar un estudiante ajeno que no tiene asignado (403)."""
    cabecera = await iniciar(cliente, USUARIOS["tutor"])
    # 4500002 no es hijo de marioq
    r = await cliente.get("/academico/inscripciones/historial/4500002", headers=cabecera)
    assert r.status_code == 403, f"Se esperaba 403 pero se obtuvo {r.status_code}: {r.text}"


@pytest.mark.asyncio
async def test_cu17_admin_ve_a_cualquiera(cliente, admin):
    """El administrador puede consultar a cualquier estudiante."""
    r1 = await cliente.get("/academico/inscripciones/historial/4500001", headers=admin)
    assert r1.status_code == 200, r1.text

    r2 = await cliente.get("/academico/inscripciones/historial/4500002", headers=admin)
    assert r2.status_code == 200, r2.text


@pytest.mark.asyncio
async def test_cu17_ci_inexistente_404(cliente, admin):
    """Si el estudiante no existe en la BD, retorna 404."""
    r = await cliente.get("/academico/inscripciones/historial/99999999", headers=admin)
    assert r.status_code == 404, f"Se esperaba 404 pero se obtuvo {r.status_code}: {r.text}"


@pytest.mark.asyncio
async def test_cu17_profesor_rol_no_permitido_403(cliente):
    """Un profesor no tiene acceso a consultar el historial de inscripciones (403)."""
    cabecera = await iniciar(cliente, USUARIOS["profesor"])
    r = await cliente.get("/academico/inscripciones/historial/4500001", headers=cabecera)
    assert r.status_code == 403, f"Se esperaba 403 pero se obtuvo {r.status_code}: {r.text}"


@pytest.mark.asyncio
async def test_cu17_promedio_coincide_con_v_nota_final(cliente, admin):
    """El promedio anual del historial coincide con el cálculo directo de v_nota_final."""
    ci = "4500001"
    r = await cliente.get(f"/academico/inscripciones/historial/{ci}", headers=admin)
    assert r.status_code == 200, r.text
    data = r.json()

    async with bd._fabrica() as sesion:
        for insc in data["inscripciones"]:
            id_g = insc["id_gestion"]
            prom_db = await sesion.scalar(
                text("""SELECT ROUND(AVG(nota_final), 2)
                          FROM v_nota_final
                         WHERE ci_estudiante = :ci AND id_gestion = :g"""),
                {"ci": ci, "g": id_g},
            )
            prom_retornado = insc["promedio_anual"]
            if prom_db is not None:
                assert prom_retornado is not None
                assert float(prom_retornado) == float(prom_db)
            else:
                assert prom_retornado is None


@pytest.mark.asyncio
async def test_cu17_listar_estudiantes_segun_rol(cliente, admin):
    """El endpoint /inscripciones/historial/estudiantes filtra según rol."""
    # Estudiante solo ve su CI
    cab_est = await iniciar(cliente, USUARIOS["estudiante"])
    r_est = await cliente.get("/academico/inscripciones/historial/estudiantes", headers=cab_est)
    assert r_est.status_code == 200
    lista_est = r_est.json()
    assert len(lista_est) == 1
    assert lista_est[0]["ci"] == "4500001"

    # Tutor solo ve sus tutelados
    cab_tutor = await iniciar(cliente, USUARIOS["tutor"])
    r_tut = await cliente.get("/academico/inscripciones/historial/estudiantes", headers=cab_tutor)
    assert r_tut.status_code == 200
    lista_tut = r_tut.json()
    assert len(lista_tut) >= 1
    cis_tut = [e["ci"] for e in lista_tut]
    assert "4500001" in cis_tut
    assert "4500002" not in cis_tut  # 4500002 no es de marioq

    # Admin ve todos
    r_admin = await cliente.get("/academico/inscripciones/historial/estudiantes", headers=admin)
    assert r_admin.status_code == 200
    lista_admin = r_admin.json()
    assert len(lista_admin) > len(lista_tut)


@pytest.mark.asyncio
async def test_cu17_admin_encuentra_estudiantes_dados_de_baja(cliente, admin):
    """Un estudiante dado de baja sigue apareciendo en el buscador (marcado como inactivo) y su historial se consulta."""
    async with bd._fabrica() as sesion:
        await sesion.execute(text("UPDATE persona SET estado_persona = 'inactivo' WHERE ci = '4500002'"))
        await sesion.commit()

    r = await cliente.get("/academico/inscripciones/historial/estudiantes", headers=admin,
                          params={"buscar": "4500002"})
    assert r.status_code == 200
    encontrados = {e["ci"]: e for e in r.json()}
    assert "4500002" in encontrados
    assert encontrados["4500002"]["activo"] is False

    r = await cliente.get("/academico/inscripciones/historial/4500002", headers=admin)
    assert r.status_code == 200
    assert all("nota_minima" in i for i in r.json()["inscripciones"])

"""Pruebas del CU24: generar y consultar boletín/libreta.

Datos de 08_datos_prueba: Boletines emitidos para el 1er trimestre (cerrado).
Calificaciones existentes para 1er y 2do trimestre. El 3er trimestre está abierto.
Estudiantes: mquispe (4500001), con tutor marioq.
"""
import pytest
from sqlalchemy import text

from app.nucleo import bd
from tests.conftest import USUARIOS, iniciar


async def _sql(consulta: str, **params):
    """Ejecuta SQL directo dentro de la transacción de la prueba (se deshace al terminar)."""
    async with bd._fabrica() as sesion:
        await sesion.execute(text(consulta), params)
        await sesion.commit()


async def test_cu24_solo_administrador_puede_emitir(cliente):
    """Solo administrador puede emitir boletines."""
    for usuario in ("mquispe", "marioq", "rflores"):  # estudiante, tutor, profesor
        cabecera = await iniciar(cliente, usuario)
        r = await cliente.post("/evaluacion/boletines/emitir", headers=cabecera,
                              params={"id_periodo": 1})
        assert r.status_code == 403, f"Usuario {usuario} no debería poder emitir: {r.text}"


async def test_cu24_administrador_emite_boletines(cliente, admin):
    """Administrador emite boletines de un periodo."""
    # El 1er trimestre ya tiene boletines (08_datos_prueba), así que reemitimos
    r = await cliente.post("/evaluacion/boletines/emitir", headers=admin,
                          params={"id_periodo": 1})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["cantidad"] > 0
    assert data["periodo"] == "1er Trimestre"
    assert "fecha_emision" in data


async def test_cu24_estudiante_consulta_su_boletin(cliente, admin):
    """Estudiante consulta su propio boletín."""
    # Primero asegurarse de que existe el boletín (ya está en 08_datos_prueba)
    r = await cliente.post("/evaluacion/boletines/emitir", headers=admin,
                          params={"id_periodo": 1})
    assert r.status_code == 200

    # Ahora el estudiante consulta su boletín
    cabecera_est = await iniciar(cliente, USUARIOS["estudiante"])
    r = await cliente.get(f"/evaluacion/boletines/4500001", headers=cabecera_est,
                         params={"id_periodo": 1})
    assert r.status_code == 200, r.text
    boletin = r.json()
    assert boletin["ci"] == "4500001"
    assert boletin["promedio_general_b"] > 0
    assert len(boletin["notas_por_materia"]) > 0


async def test_cu24_estudiante_no_ve_otro_boletin(cliente, admin):
    """Estudiante no puede consultar boletín de otro estudiante."""
    # Asegurar que existe el boletín
    await cliente.post("/evaluacion/boletines/emitir", headers=admin,
                      params={"id_periodo": 1})

    cabecera_est = await iniciar(cliente, USUARIOS["estudiante"])
    # Intentar ver otro estudiante
    r = await cliente.get(f"/evaluacion/boletines/4500002", headers=cabecera_est,
                         params={"id_periodo": 1})
    assert r.status_code == 403, f"Estudiante no debería ver otro boletín: {r.text}"


async def test_cu24_tutor_ve_sus_estudiantes(cliente, admin):
    """Tutor consulta boletín de sus estudiantes."""
    await cliente.post("/evaluacion/boletines/emitir", headers=admin,
                      params={"id_periodo": 1})

    cabecera_tutor = await iniciar(cliente, USUARIOS["tutor"])
    # marioq es tutor de mquispe (4500001)
    r = await cliente.get(f"/evaluacion/boletines/4500001", headers=cabecera_tutor,
                         params={"id_periodo": 1})
    assert r.status_code == 200, r.text


async def test_cu24_tutor_no_ve_estudiante_ajeno(cliente, admin):
    """Tutor no puede consultar boletín de estudiante ajeno."""
    await cliente.post("/evaluacion/boletines/emitir", headers=admin,
                      params={"id_periodo": 1})

    cabecera_tutor = await iniciar(cliente, USUARIOS["tutor"])
    # marioq no es tutor de 4500002
    r = await cliente.get(f"/evaluacion/boletines/4500002", headers=cabecera_tutor,
                         params={"id_periodo": 1})
    assert r.status_code == 403, f"Tutor no debería ver estudiante ajeno: {r.text}"


async def test_cu24_boletin_no_emitido_404(cliente):
    """Si el boletín no ha sido emitido, retorna 404."""
    cabecera_est = await iniciar(cliente, USUARIOS["estudiante"])
    # El 2do trimestre no tiene boletines emitidos aún
    r = await cliente.get(f"/evaluacion/boletines/4500001", headers=cabecera_est,
                         params={"id_periodo": 2})
    assert r.status_code == 404, f"Debería retornar 404: {r.text}"


async def test_cu24_administrador_consulta_centralizador(cliente, admin):
    """Administrador consulta el centralizador de un curso."""
    # Asegurar que existe el boletín
    await cliente.post("/evaluacion/boletines/emitir", headers=admin,
                      params={"id_periodo": 1, "id_curso": None})

    # Consultar centralizador de 1ro A - Secundaria (id_curso = 14, según los datos de prueba)
    r = await cliente.get("/evaluacion/centralizador", headers=admin,
                         params={"id_curso": 14, "id_periodo": 1})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["curso"]
    assert data["periodo"] == "1er Trimestre"
    assert len(data["filas"]) > 0
    assert all("notas" in fila for fila in data["filas"])


async def test_cu24_estudiante_no_ve_centralizador(cliente):
    """Estudiante no puede consultar el centralizador."""
    cabecera_est = await iniciar(cliente, USUARIOS["estudiante"])
    r = await cliente.get("/evaluacion/centralizador", headers=cabecera_est,
                         params={"id_curso": 1, "id_periodo": 1})
    assert r.status_code == 403, f"Estudiante no debería ver centralizador: {r.text}"


async def test_cu24_periodo_inexistente_404(cliente, admin):
    """Emitir boletines de un periodo inexistente retorna 404."""
    r = await cliente.post("/evaluacion/boletines/emitir", headers=admin,
                          params={"id_periodo": 999999})
    assert r.status_code == 404, r.text


async def test_cu24_curso_inexistente_404_en_centralizador(cliente, admin):
    """Centralizador con curso inexistente retorna 404."""
    r = await cliente.get("/evaluacion/centralizador", headers=admin,
                         params={"id_curso": 999999, "id_periodo": 1})
    assert r.status_code == 404, r.text


async def test_cu24_opciones_periodos_accesible(cliente, admin):
    """Opciones de períodos es accesible para admin, tutor y estudiante."""
    for usuario_key in ("administrador", "tutor", "estudiante"):
        cabecera = await iniciar(cliente, USUARIOS[usuario_key])
        r = await cliente.get("/evaluacion/boletines/opciones/periodos", headers=cabecera)
        assert r.status_code == 200, f"Usuario {usuario_key}: {r.text}"
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert all("id_periodo" in p and "nombre_periodo" in p for p in data)


async def test_cu24_opciones_periodos_profesor_403(cliente):
    """Profesor no puede acceder a opciones de períodos."""
    cabecera = await iniciar(cliente, USUARIOS["profesor"])
    r = await cliente.get("/evaluacion/boletines/opciones/periodos", headers=cabecera)
    assert r.status_code == 403, r.text


async def test_cu24_opciones_cursos_accesible(cliente, admin):
    """Opciones de cursos es accesible para admin, tutor y estudiante."""
    for usuario_key in ("administrador", "tutor", "estudiante"):
        cabecera = await iniciar(cliente, USUARIOS[usuario_key])
        r = await cliente.get("/evaluacion/boletines/opciones/cursos", headers=cabecera)
        assert r.status_code == 200, f"Usuario {usuario_key}: {r.text}"
        data = r.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert all("id_curso" in c and "nombre_curso" in c for c in data)


async def test_cu24_opciones_cursos_profesor_403(cliente):
    """Profesor no puede acceder a opciones de cursos."""
    cabecera = await iniciar(cliente, USUARIOS["profesor"])
    r = await cliente.get("/evaluacion/boletines/opciones/cursos", headers=cabecera)
    assert r.status_code == 403, r.text

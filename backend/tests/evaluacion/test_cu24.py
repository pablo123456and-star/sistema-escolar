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


# ------------------------------------------------------------
# Correcciones del PR #18 y decisiones del grupo
# ------------------------------------------------------------

async def _valor(consulta: str, **params):
    """Devuelve un valor de la base de pruebas (dentro de la misma transacción)."""
    async with bd._fabrica() as sesion:
        return await sesion.scalar(text(consulta), params)


async def test_cu24_emitir_un_curso_informa_solo_ese_curso(cliente, admin):
    """La cantidad es la que devuelve sp_emitir_boletines (INOUT), no el total de boletines del periodo."""
    r = await cliente.post("/evaluacion/boletines/emitir", headers=admin, params={"id_periodo": 1})
    total = r.json()["cantidad"]
    r = await cliente.post("/evaluacion/boletines/emitir", headers=admin, params={"id_periodo": 1, "id_curso": 14})
    assert r.status_code == 200, r.text
    esperado = await _valor("""
        SELECT count(DISTINCT nf.ci_estudiante) FROM v_nota_final nf
          JOIN inscripcion i ON i.ci_estudiante_inscripcion = nf.ci_estudiante
                            AND i.id_gestion_inscripcion = nf.id_gestion
         WHERE nf.id_periodo = 1 AND i.id_curso_inscripcion = 14 AND i.estado_inscripcion <> 'retirada'""")
    assert r.json()["cantidad"] == esperado
    assert esperado <= total


async def test_cu24_emitir_curso_inexistente_404(cliente, admin):
    """Emitir para un curso que no existe responde 404 (antes devolvía 200 con 0)."""
    r = await cliente.post("/evaluacion/boletines/emitir", headers=admin,
                           params={"id_periodo": 1, "id_curso": 999999})
    assert r.status_code == 404, r.text


async def test_cu24_centralizador_columnas_son_las_materias_del_curso(cliente, admin):
    """Las columnas vienen del backend y cubren las materias de todas las filas."""
    r = await cliente.get("/evaluacion/centralizador", headers=admin, params={"id_curso": 14, "id_periodo": 1})
    assert r.status_code == 200, r.text
    data = r.json()
    columnas = {m["id_materia"] for m in data["materias"]}
    assert columnas
    con_nota = {n["id_materia"] for fila in data["filas"] for n in fila["notas"]}
    assert con_nota <= columnas
    assert data["anio"] == 2026 and data["nota_minima"] == 51


async def test_cu24_periodos_incluyen_gestiones_anteriores(cliente, admin):
    """Las opciones de periodo traen todas las gestiones, la más reciente primero."""
    await _sql("""INSERT INTO gestion (anio, fecha_inicio_g, fecha_final_g, nota_minima_aprobacion, estado_gestion)
                  VALUES (2025, '2025-02-03', '2025-12-05', 51, 'cerrada')""")
    await _sql("""INSERT INTO periodo (nombre_periodo, tipo, fecha_inicio_p, fecha_final_p, estado_periodo, id_gestion_periodo)
                  SELECT '1er Trimestre', 'trimestre', '2025-02-03', '2025-05-09', 'cerrado', id_gestion
                    FROM gestion WHERE anio = 2025""")
    r = await cliente.get("/evaluacion/boletines/opciones/periodos", headers=admin)
    assert r.status_code == 200, r.text
    anios = [p["anio"] for p in r.json()]
    assert 2025 in anios
    assert anios == sorted(anios, reverse=True)


async def test_cu24_opciones_estudiantes_segun_rol(cliente, admin):
    """Tutor: solo sus estudiantes; estudiante: solo él; administrador: el curso pedido."""
    cabecera_tutor = await iniciar(cliente, USUARIOS["tutor"])
    r = await cliente.get("/evaluacion/boletines/opciones/estudiantes", headers=cabecera_tutor,
                          params={"id_periodo": 1})
    assert r.status_code == 200, r.text
    cis = {e["ci"] for e in r.json()}
    assert "4500001" in cis
    ajenos = await _valor("""SELECT count(*) FROM unnest(CAST(:cis AS text[])) ci
                              WHERE NOT EXISTS (SELECT 1 FROM tutor_estudiante te
                                                 WHERE te.ci_estudiante_tutorestudiante = ci
                                                   AND te.ci_tutor_tutorestudiante =
                                                       (SELECT ci_persona FROM usuario WHERE nombre_usuario = 'marioq'))""",
                          cis=list(cis))
    assert ajenos == 0

    cabecera_est = await iniciar(cliente, USUARIOS["estudiante"])
    r = await cliente.get("/evaluacion/boletines/opciones/estudiantes", headers=cabecera_est,
                          params={"id_periodo": 1})
    assert [e["ci"] for e in r.json()] == ["4500001"]

    r = await cliente.get("/evaluacion/boletines/opciones/estudiantes", headers=admin,
                          params={"id_periodo": 1, "id_curso": 14})
    assert r.status_code == 200 and len(r.json()) > 0
    assert len({e["nombre_curso"] for e in r.json()}) == 1


async def test_cu24_estudiante_ajeno_403_aunque_no_haya_boletin(cliente):
    """El permiso se valida antes de buscar: no se revela si existe el boletín de otro."""
    cabecera_est = await iniciar(cliente, USUARIOS["estudiante"])
    r = await cliente.get("/evaluacion/boletines/4500002", headers=cabecera_est, params={"id_periodo": 2})
    assert r.status_code == 403, r.text

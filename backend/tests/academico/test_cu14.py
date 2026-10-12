"""
Pruebas automáticas del CU14.
Asignar profesor a materia/curso.
Unidad Educativa Mariscal Sucre G.

Estas pruebas utilizan exclusivamente escuela_prueba.
Los cambios se revierten al finalizar cada prueba.
"""

import os
from uuid import uuid4

import pytest
from sqlalchemy import text

from sqlalchemy.engine import make_url

from app.nucleo import bd

from app.nucleo.errores import (
    ErrorNegocio,
    NoEncontrado,
    Conflicto,
)

from app.paquetes.academico import repository as repo

from app.paquetes.academico.models import (
    Materia,
    MateriaGrado,
)

from app.paquetes.academico.schemas import (
    AsignacionCrear,
    AsignacionActualizar,
)

from app.paquetes.academico.casos_uso import (
    cu13_gestionar_materias as cu13,
    cu14_asignar_profesor as cu14,
)


# ============================================================
# PREPARAR DATOS DE PRUEBA
# ============================================================

@pytest.fixture
async def escenario_cu14(cliente):
    """
    Prepara un curso, profesor, aula y materia.

    La materia se crea temporalmente para garantizar
    que todavía no tenga una asignación.

    Se utiliza la conexión de prueba configurada
    en conftest.py.
    """

    url = os.environ.get("TEST_DATABASE_URL")

    if not url:
        pytest.skip("No está configurada TEST_DATABASE_URL.")

    nombre_bd = make_url(url).database

    if nombre_bd != "escuela_prueba":
        pytest.fail(
            "SEGURIDAD: Las pruebas del CU14 solamente "
            "pueden ejecutarse en escuela_prueba."
        )

    async with bd._fabrica() as sesion:

        gestion = await cu14.exigir_gestion_abierta(sesion)

        cursos = await repo.listar_cursos_cu14(sesion)

        profesores = await repo.listar_profesores_activos_cu14(
            sesion
        )

        aulas = await repo.listar_aulas_disponibles_cu14(
            sesion
        )

        assert cursos, "No existen cursos de prueba."
        assert profesores, "No existen profesores activos."
        assert aulas, "No existen aulas disponibles."

        curso = cursos[0]

        # Crear una materia temporal.

        materia = Materia(
            nombre_materia=(
                f"Materia temporal CU14 {uuid4().hex[:8]}"
            ),
            carga_horaria=4,
        )

        sesion.add(materia)

        await sesion.flush()

        # Asociar la materia al grado del curso.

        relacion = MateriaGrado(
            id_grado_mg=curso["id_grado"],
            id_materia_mg=materia.id_materia,
        )

        sesion.add(relacion)

        await sesion.flush()

        # Preparar datos de asignación.

        datos = AsignacionCrear(
            id_curso=curso["id_curso"],
            id_materia=materia.id_materia,
            ci_profesor=profesores[0]["ci_profesor"],
            id_aula=aulas[0]["id_aula"],
        )

        yield {
            "sesion": sesion,
            "gestion": gestion,
            "curso": curso,
            "materia": materia,
            "profesores": profesores,
            "aulas": aulas,
            "datos": datos,
        }


# ============================================================
# PRUEBA 1: CONSULTAR OPCIONES Y MATERIAS
# ============================================================

async def test_cu14_consultar_opciones(escenario_cu14):

    e = escenario_cu14

    opciones = await cu14.opciones(e["sesion"])

    assert opciones.id_gestion == e["gestion"].id_gestion
    assert opciones.cursos
    assert opciones.profesores
    assert opciones.aulas

    resultado = await cu14.consultar_materias(
        e["sesion"],
        e["curso"]["id_curso"],
    )

    ids_materias = [
        materia.id_materia
        for materia in resultado.materias
    ]

    assert e["materia"].id_materia in ids_materias


# ============================================================
# PRUEBA 2: REGISTRAR Y CONSULTAR ASIGNACIÓN
# ============================================================

async def test_cu14_registrar_asignacion(escenario_cu14):

    e = escenario_cu14

    asignacion = await cu14.registrar(
        e["sesion"],
        e["datos"],
    )

    assert asignacion.id_asignacion > 0

    assert (
        asignacion.id_materia_asignacion
        == e["materia"].id_materia
    )

    assert (
        asignacion.id_gestion_asignacion
        == e["gestion"].id_gestion
    )

    consultada = await cu14.obtener(
        e["sesion"],
        asignacion.id_asignacion,
    )

    assert consultada.id_asignacion == asignacion.id_asignacion


# ============================================================
# PRUEBA 3: IMPEDIR ASIGNACIONES DUPLICADAS
# ============================================================

async def test_cu14_asignacion_duplicada(escenario_cu14):

    e = escenario_cu14

    await cu14.registrar(
        e["sesion"],
        e["datos"],
    )

    with pytest.raises(Conflicto):

        await cu14.registrar(
            e["sesion"],
            e["datos"],
        )


# ============================================================
# PRUEBA 4: RECHAZAR PROFESOR INEXISTENTE
# ============================================================

async def test_cu14_profesor_inactivo(escenario_cu14):

    e = escenario_cu14

    datos = e["datos"].model_copy(
        update={
            "ci_profesor": "999999999999999"
        }
    )

    with pytest.raises(ErrorNegocio):

        await cu14.registrar(
            e["sesion"],
            datos,
        )


# ============================================================
# PRUEBA 5: RECHAZAR AULA NO DISPONIBLE
# ============================================================

async def test_cu14_aula_no_disponible(escenario_cu14):

    e = escenario_cu14

    datos = e["datos"].model_copy(
        update={
            "id_aula": 999999
        }
    )

    with pytest.raises(ErrorNegocio):

        await cu14.registrar(
            e["sesion"],
            datos,
        )


# ============================================================
# PRUEBA 6: RECHAZAR MATERIA FUERA DEL PLAN
# ============================================================

async def test_cu14_materia_fuera_del_plan(escenario_cu14):

    e = escenario_cu14

    # Crear una materia sin asociarla al grado.

    materia = Materia(
        nombre_materia=(
            f"Materia fuera del plan {uuid4().hex[:8]}"
        ),
        carga_horaria=4,
    )

    e["sesion"].add(materia)

    await e["sesion"].flush()

    datos = e["datos"].model_copy(
        update={
            "id_materia": materia.id_materia
        }
    )

    with pytest.raises(ErrorNegocio):

        await cu14.registrar(
            e["sesion"],
            datos,
        )


# ============================================================
# PRUEBA 7: MODIFICAR PROFESOR Y AULA
# ============================================================

async def test_cu14_modificar_asignacion(escenario_cu14):

    e = escenario_cu14

    asignacion = await cu14.registrar(
        e["sesion"],
        e["datos"],
    )

    assert len(e["profesores"]) >= 2
    assert len(e["aulas"]) >= 2

    nuevo_profesor = e["profesores"][1]["ci_profesor"]
    nueva_aula = e["aulas"][1]["id_aula"]

    cambios = AsignacionActualizar(
        ci_profesor=nuevo_profesor,
        id_aula=nueva_aula,
    )

    actualizada = await cu14.actualizar(
        e["sesion"],
        asignacion.id_asignacion,
        cambios,
    )

    assert actualizada.ci_profesor_asignacion == nuevo_profesor

    assert actualizada.id_aula_asignacion == nueva_aula


# ============================================================
# PRUEBA 8: ELIMINAR ASIGNACIÓN SIN BLOQUEOS
# ============================================================

async def test_cu14_eliminar_asignacion(escenario_cu14):

    e = escenario_cu14

    asignacion = await cu14.registrar(
        e["sesion"],
        e["datos"],
    )

    await cu14.eliminar(
        e["sesion"],
        asignacion.id_asignacion,
    )

    with pytest.raises(NoEncontrado):

        await cu14.obtener(
            e["sesion"],
            asignacion.id_asignacion,
        )


# ============================================================
# PRUEBA 9: IMPEDIR ELIMINAR CON ASISTENCIAS
# ============================================================

async def test_cu14_no_eliminar_con_asistencias(
    escenario_cu14,
    monkeypatch,
):

    e = escenario_cu14

    asignacion = await cu14.registrar(
        e["sesion"],
        e["datos"],
    )

    # Simular que la asignación tiene asistencias.

    async def tiene_asistencias(*args, **kwargs):
        return True

    monkeypatch.setattr(
        repo,
        "asignacion_con_asistencias_cu14",
        tiene_asistencias,
    )

    with pytest.raises(Conflicto, match="asistencias"):

        await cu14.eliminar(
            e["sesion"],
            asignacion.id_asignacion,
        )

    # Comprobar que no se eliminó.

    consultada = await cu14.obtener(
        e["sesion"],
        asignacion.id_asignacion,
    )

    assert consultada.id_asignacion == asignacion.id_asignacion


# ============================================================
# PRUEBA 10: IMPEDIR ELIMINAR CON CALIFICACIONES
# ============================================================

async def test_cu14_no_eliminar_con_calificaciones(
    escenario_cu14,
    monkeypatch,
):

    e = escenario_cu14

    asignacion = await cu14.registrar(
        e["sesion"],
        e["datos"],
    )

    # Simular que la asignación tiene calificaciones.

    async def tiene_calificaciones(*args, **kwargs):
        return True

    monkeypatch.setattr(
        repo,
        "asignacion_con_calificaciones_cu14",
        tiene_calificaciones,
    )

    with pytest.raises(Conflicto, match="calificaciones"):

        await cu14.eliminar(
            e["sesion"],
            asignacion.id_asignacion,
        )

    # Comprobar que no se eliminó.

    consultada = await cu14.obtener(
        e["sesion"],
        asignacion.id_asignacion,
    )

    assert consultada.id_asignacion == asignacion.id_asignacion

# ============================================================
# CU14 - PRUEBAS HTTP DE LOS ENDPOINTS FASTAPI
# ============================================================


# ------------------------------------------------------------
# PRUEBA 11: CONSULTAR OPCIONES Y MATERIAS DESDE LA API
# ------------------------------------------------------------

async def test_cu14_http_consultar(cliente, admin, escenario_cu14):

    e = escenario_cu14

    # Consultar cursos, profesores y aulas

    respuesta = await cliente.get(
        "/academico/asignaciones/opciones",
        headers=admin,
    )

    assert respuesta.status_code == 200, respuesta.text

    datos = respuesta.json()

    assert "cursos" in datos
    assert "profesores" in datos
    assert "aulas" in datos

    # Consultar las materias de un curso

    respuesta = await cliente.get(
        f"/academico/cursos/{e['curso']['id_curso']}/asignaciones",
        headers=admin,
    )

    assert respuesta.status_code == 200, respuesta.text

    materias = respuesta.json()["materias"]

    assert any(
        materia["id_materia"] == e["materia"].id_materia
        for materia in materias
    )


# ------------------------------------------------------------
# PRUEBA 12: REGISTRAR, MODIFICAR Y ELIMINAR POR HTTP
# ------------------------------------------------------------

async def test_cu14_http_operaciones(cliente, admin, escenario_cu14):

    e = escenario_cu14

    # Registrar una asignacion

    respuesta = await cliente.post(
        "/academico/asignaciones",
        headers=admin,
        json=e["datos"].model_dump(),
    )

    assert respuesta.status_code == 201, respuesta.text

    id_asignacion = respuesta.json()["id_asignacion"]

    # Consultar la asignacion registrada

    respuesta = await cliente.get(
        f"/academico/asignaciones/{id_asignacion}",
        headers=admin,
    )

    assert respuesta.status_code == 200, respuesta.text

    # Modificar el aula

    nueva_aula = e["aulas"][1]["id_aula"]

    respuesta = await cliente.patch(
        f"/academico/asignaciones/{id_asignacion}",
        headers=admin,
        json={"id_aula": nueva_aula},
    )

    assert respuesta.status_code == 200, respuesta.text

    assert (
        respuesta.json()["id_aula_asignacion"]
        == nueva_aula
    )

    # Eliminar la asignacion

    respuesta = await cliente.delete(
        f"/academico/asignaciones/{id_asignacion}",
        headers=admin,
    )

    assert respuesta.status_code == 204, respuesta.text

    # Comprobar que ya no existe

    respuesta = await cliente.get(
        f"/academico/asignaciones/{id_asignacion}",
        headers=admin,
    )

    assert respuesta.status_code == 404, respuesta.text


# ------------------------------------------------------------
# PRUEBA 13: IMPEDIR DUPLICADOS DESDE LA API
# ------------------------------------------------------------

async def test_cu14_http_duplicados(cliente, admin, escenario_cu14):

    e = escenario_cu14

    # Primera asignacion

    respuesta = await cliente.post(
        "/academico/asignaciones",
        headers=admin,
        json=e["datos"].model_dump(),
    )

    assert respuesta.status_code == 201, respuesta.text

    # Intentar registrar nuevamente

    respuesta = await cliente.post(
        "/academico/asignaciones",
        headers=admin,
        json=e["datos"].model_dump(),
    )

    assert respuesta.status_code == 409, respuesta.text


# ------------------------------------------------------------
# PRUEBA 14: SOLO ADMINISTRADOR
# ------------------------------------------------------------

async def test_cu14_http_solo_administrador(
    cliente,
    profesor,
    escenario_cu14,
):

    e = escenario_cu14

    # Un profesor no puede consultar las opciones

    respuesta = await cliente.get(
        "/academico/asignaciones/opciones",
        headers=profesor,
    )

    assert respuesta.status_code == 403, respuesta.text

    # Un profesor tampoco puede registrar asignaciones

    respuesta = await cliente.post(
        "/academico/asignaciones",
        headers=profesor,
        json=e["datos"].model_dump(),
    )

    assert respuesta.status_code == 403, respuesta.text

    # Sin iniciar sesion

    respuesta = await cliente.get(
        "/academico/asignaciones/opciones",
    )

    assert respuesta.status_code == 401, respuesta.text

# ============================================================
# PRUEBAS DE RESTRICCIONES CON DATOS REALES
# CU13 Y CU14
# ============================================================


async def verificar_base_pruebas(sesion):
    """Impide ejecutar estas comprobaciones fuera de escuela_prueba."""

    nombre_bd = await sesion.scalar(
        text("SELECT current_database()")
    )

    assert nombre_bd == "escuela_prueba", (
        "SEGURIDAD: Estas pruebas solo pueden ejecutarse "
        "en escuela_prueba."
    )


# ============================================================
# PRUEBA 15: CU13 - NO QUITAR MATERIA CON ASIGNACION
# ============================================================

async def test_cu13_no_quitar_materia_con_asignacion_real(cliente):

    async with bd._fabrica() as sesion:

        await verificar_base_pruebas(sesion)

        consulta = text("""
            SELECT
                c.id_grado_curso AS id_grado,
                a.id_materia_asignacion AS id_materia

            FROM asignacion_profesor_clase a

            JOIN curso c
                ON c.id_curso = a.id_curso_asignacion

            JOIN gestion g
                ON g.id_gestion = a.id_gestion_asignacion

            JOIN materia_grado mg
                ON mg.id_grado_mg = c.id_grado_curso
                AND mg.id_materia_mg = a.id_materia_asignacion

            WHERE g.estado_gestion = 'abierta'

            ORDER BY a.id_asignacion
            LIMIT 1
        """)

        resultado = await sesion.execute(consulta)
        fila = resultado.mappings().first()

        assert fila is not None, (
            "No hay asignaciones en la gestion abierta."
        )

        # Debe rechazar quitar la materia del plan.

        with pytest.raises(Conflicto):

            await cu13.quitar_del_plan(
                sesion,
                fila["id_grado"],
                fila["id_materia"],
            )

        # La materia debe continuar en el plan.

        existe = await repo.materia_en_plan(
            sesion,
            fila["id_grado"],
            fila["id_materia"],
        )

        assert existe


# ============================================================
# PRUEBA 16: CU14 - NO ELIMINAR CON ASISTENCIAS REALES
# ============================================================

async def test_cu14_no_eliminar_asistencias_reales(cliente):

    async with bd._fabrica() as sesion:

        await verificar_base_pruebas(sesion)

        consulta = text("""
            SELECT a.id_asignacion

            FROM asignacion_profesor_clase a

            JOIN asistencia asi
                ON asi.id_asignacion_asistencia = a.id_asignacion

            JOIN gestion g
                ON g.id_gestion = a.id_gestion_asignacion

            WHERE g.estado_gestion = 'abierta'

            ORDER BY a.id_asignacion
            LIMIT 1
        """)

        id_asignacion = await sesion.scalar(consulta)

        assert id_asignacion is not None, (
            "No hay asignaciones con asistencias."
        )

        # Debe rechazar la eliminacion.

        with pytest.raises(Conflicto, match="asistencias"):

            await cu14.eliminar(
                sesion,
                id_asignacion,
            )

        # La asignacion debe continuar existiendo.

        asignacion = await cu14.obtener(
            sesion,
            id_asignacion,
        )

        assert asignacion.id_asignacion == id_asignacion


# ============================================================
# PRUEBA 17: CU14 - NO ELIMINAR CON CALIFICACIONES REALES
# ============================================================

async def test_cu14_no_eliminar_calificaciones_reales(
    cliente,
    monkeypatch,
):

    async with bd._fabrica() as sesion:

        await verificar_base_pruebas(sesion)

        consulta = text("""
            SELECT a.id_asignacion

            FROM asignacion_profesor_clase a

            JOIN gestion g
                ON g.id_gestion = a.id_gestion_asignacion

            WHERE g.estado_gestion = 'abierta'

            ORDER BY a.id_asignacion
        """)

        resultado = await sesion.scalars(consulta)

        id_asignacion = None

        for identificador in resultado.all():

            tiene_notas = (
                await repo.asignacion_con_calificaciones_cu14(
                    sesion,
                    identificador,
                )
            )

            if tiene_notas:
                id_asignacion = identificador
                break

        assert id_asignacion is not None, (
            "No hay asignaciones con calificaciones."
        )

        # Se omite SOLO la comprobacion de asistencias
        # para verificar el bloqueo por calificaciones.
        # La consulta de calificaciones sigue siendo real.

        async def sin_asistencias(*args, **kwargs):
            return False

        monkeypatch.setattr(
            repo,
            "asignacion_con_asistencias_cu14",
            sin_asistencias,
        )

        # Debe rechazar la eliminacion por las notas.

        with pytest.raises(Conflicto, match="calificaciones"):

            await cu14.eliminar(
                sesion,
                id_asignacion,
            )

        # La asignacion debe continuar existiendo.

        asignacion = await cu14.obtener(
            sesion,
            id_asignacion,
        )

        assert asignacion.id_asignacion == id_asignacion
"""
Pruebas automáticas del CU13.
Gestionar materias y plan de estudios.
Unidad Educativa Mariscal Sucre G.
"""


# ============================================================
# FUNCIONES AUXILIARES PARA LAS PRUEBAS
# ============================================================

async def crear_materia(cliente, admin, nombre):
    respuesta = await cliente.post(
        "/academico/materias",
        headers=admin,
        json={
            "nombre_materia": nombre,
            "carga_horaria": 4,
        },
    )

    assert respuesta.status_code == 201, respuesta.text

    return respuesta.json()


async def obtener_primer_grado(cliente, admin):
    respuesta = await cliente.get(
        "/academico/niveles-grados",
        headers=admin,
    )

    assert respuesta.status_code == 200, respuesta.text

    grados = respuesta.json()["grados"]

    return next(
        grado["id_grado"]
        for grado in grados
        if grado["id_nivel_educativo_grado"] == 2
        and grado["orden_grado"] == 1
    )


# ============================================================
# PRUEBA 1: LISTAR MATERIAS
# ============================================================

async def test_cu13_listar_materias(cliente, admin):

    respuesta = await cliente.get(
        "/academico/materias",
        headers=admin,
    )

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert "items" in datos
    assert "total" in datos
    assert datos["total"] >= 15


# ============================================================
# PRUEBA 2: REGISTRAR Y CONSULTAR MATERIA
# ============================================================

async def test_cu13_registrar_materia(cliente, admin):

    materia = await crear_materia(
        cliente,
        admin,
        "Materia automatica CU13",
    )

    assert materia["nombre_materia"] == "Materia automatica CU13"
    assert materia["carga_horaria"] == 4

    respuesta = await cliente.get(
        f"/academico/materias/{materia['id_materia']}",
        headers=admin,
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["id_materia"] == materia["id_materia"]


# ============================================================
# PRUEBA 3: IMPEDIR MATERIAS DUPLICADAS
# ============================================================

async def test_cu13_materia_duplicada(cliente, admin):

    await crear_materia(
        cliente,
        admin,
        "Materia duplicada CU13",
    )

    respuesta = await cliente.post(
        "/academico/materias",
        headers=admin,
        json={
            "nombre_materia": "Materia duplicada CU13",
            "carga_horaria": 4,
        },
    )

    assert respuesta.status_code == 409


# ============================================================
# PRUEBA 4: VALIDAR CARGA HORARIA
# ============================================================

async def test_cu13_carga_horaria_invalida(cliente, admin):

    respuesta = await cliente.post(
        "/academico/materias",
        headers=admin,
        json={
            "nombre_materia": "Materia invalida CU13",
            "carga_horaria": -2,
        },
    )

    assert respuesta.status_code == 422


# ============================================================
# PRUEBA 5: MODIFICAR MATERIA
# ============================================================

async def test_cu13_modificar_materia(cliente, admin):

    materia = await crear_materia(
        cliente,
        admin,
        "Materia para modificar CU13",
    )

    respuesta = await cliente.patch(
        f"/academico/materias/{materia['id_materia']}",
        headers=admin,
        json={
            "nombre_materia": "Materia modificada CU13",
            "carga_horaria": 6,
        },
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["carga_horaria"] == 6
    assert respuesta.json()["nombre_materia"] == "Materia modificada CU13"


# ============================================================
# PRUEBA 6: CONSULTAR NIVELES Y GRADOS
# ============================================================

async def test_cu13_niveles_grados(cliente, admin):

    respuesta = await cliente.get(
        "/academico/niveles-grados",
        headers=admin,
    )

    assert respuesta.status_code == 200

    datos = respuesta.json()

    assert len(datos["niveles"]) == 3
    assert len(datos["grados"]) == 14


# ============================================================
# PRUEBA 7: AGREGAR Y QUITAR MATERIA DEL PLAN
# ============================================================

async def test_cu13_plan_estudios(cliente, admin):

    materia = await crear_materia(
        cliente,
        admin,
        "Materia para plan CU13",
    )

    id_materia = materia["id_materia"]
    id_grado = await obtener_primer_grado(cliente, admin)

    # Agregar materia al plan

    respuesta = await cliente.post(
        f"/academico/grados/{id_grado}/materias",
        headers=admin,
        json={"id_materia": id_materia},
    )

    assert respuesta.status_code == 201

    ids_plan = [
        m["id_materia"]
        for m in respuesta.json()["materias_plan"]
    ]

    assert id_materia in ids_plan

    # Intentar agregar la misma materia nuevamente

    respuesta = await cliente.post(
        f"/academico/grados/{id_grado}/materias",
        headers=admin,
        json={"id_materia": id_materia},
    )

    assert respuesta.status_code == 409

    # Intentar eliminar materia vinculada

    respuesta = await cliente.delete(
        f"/academico/materias/{id_materia}",
        headers=admin,
    )

    assert respuesta.status_code == 409

    # Quitar materia del plan

    respuesta = await cliente.delete(
        f"/academico/grados/{id_grado}/materias/{id_materia}",
        headers=admin,
    )

    assert respuesta.status_code == 200

    ids_plan = [
        m["id_materia"]
        for m in respuesta.json()["materias_plan"]
    ]

    assert id_materia not in ids_plan


# ============================================================
# PRUEBA 8: ELIMINAR MATERIA
# ============================================================

async def test_cu13_eliminar_materia(cliente, admin):

    materia = await crear_materia(
        cliente,
        admin,
        "Materia para eliminar CU13",
    )

    id_materia = materia["id_materia"]

    respuesta = await cliente.delete(
        f"/academico/materias/{id_materia}",
        headers=admin,
    )

    assert respuesta.status_code == 204

    respuesta = await cliente.get(
        f"/academico/materias/{id_materia}",
        headers=admin,
    )

    assert respuesta.status_code == 404


# ============================================================
# PRUEBA 9: SOLO ADMINISTRADOR
# ============================================================

async def test_cu13_solo_administrador(cliente, profesor):

    respuesta = await cliente.get(
        "/academico/materias",
        headers=profesor,
    )

    assert respuesta.status_code == 403
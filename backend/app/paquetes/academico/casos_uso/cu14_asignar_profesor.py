"""
CU14 - Asignar profesor a materia/curso
Paquete: academico

Actores ........: Admin. académico
Rol del sistema : administrador
Tablas .........: asignacion_profesor_clase, materia_grado, aula, profesor, persona
Usa de la BD ...: —

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - La materia debe estar en el plan de estudios del grado del curso.
    - El aula debe estar 'disponible'; el profesor debe estar activo.
    - Una asignación por curso + materia + gestión (lo asegura la BD).
    - Consulta: materias del plan que aún no tienen profesor.

Precondición:
    La materia está en el plan del grado del curso, el aula está disponible, el profesor está activo y la gestión existe.

Postcondición:
    La asignación (profesor + materia + curso + aula + gestión) queda creada y lista para recibir horarios.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
# ============================================================
# CU14 - ASIGNAR PROFESOR A MATERIA/CURSO
# ============================================================

from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.errores import (
    ErrorNegocio,
    NoEncontrado,
    Conflicto,
)

from app.paquetes.academico import repository as repo

from app.paquetes.academico.politicas import gestion_abierta

from app.paquetes.academico.models import (
    Gestion,
    AsignacionProfesorClase,
)

from app.paquetes.academico.schemas import (
    CursoOpcionAsignacion,
    ProfesorOpcionAsignacion,
    AulaOpcionAsignacion,
    OpcionesAsignacionSalida,
    MateriaCursoAsignacionSalida,
    MateriasCursoAsignacionSalida,
    AsignacionCrear,
    AsignacionActualizar,
    AsignacionSalida,
)


# ============================================================
# 1. COMPROBAR QUE EXISTA UNA GESTION ABIERTA
# ============================================================

async def exigir_gestion_abierta(
    sesion: AsyncSession,
) -> Gestion:
    """
    Obtiene la gestion abierta.

    Si no existe, impide realizar asignaciones.
    """

    gestion = await gestion_abierta(sesion)

    if gestion is None:
        raise ErrorNegocio(
            "No existe una gestion academica abierta "
            "para realizar asignaciones."
        )

    return gestion


# ============================================================
# 2. CONSULTAR OPCIONES PARA ASIGNAR
# ============================================================

async def opciones(
    sesion: AsyncSession,
) -> OpcionesAsignacionSalida:
    """
    Obtiene:
    - Gestion abierta.
    - Cursos.
    - Profesores activos.
    - Aulas disponibles.
    """

    gestion = await exigir_gestion_abierta(sesion)

    cursos = await repo.listar_cursos_cu14(sesion)

    profesores = await repo.listar_profesores_activos_cu14(
        sesion
    )

    aulas = await repo.listar_aulas_disponibles_cu14(
        sesion
    )

    return OpcionesAsignacionSalida(
        id_gestion=gestion.id_gestion,
        anio_gestion=gestion.anio,

        cursos=[
            CursoOpcionAsignacion.model_validate(curso)
            for curso in cursos
        ],

        profesores=[
            ProfesorOpcionAsignacion.model_validate(profesor)
            for profesor in profesores
        ],

        aulas=[
            AulaOpcionAsignacion.model_validate(aula)
            for aula in aulas
        ],
    )


# ============================================================
# 3. CONSULTAR MATERIAS Y ASIGNACIONES DE UN CURSO
# ============================================================

async def consultar_materias(
    sesion: AsyncSession,
    id_curso: int,
) -> MateriasCursoAsignacionSalida:
    """
    Consulta las materias del curso e identifica
    cuales tienen profesor y aula asignados.
    """

    gestion = await exigir_gestion_abierta(sesion)

    curso = await repo.obtener_curso_cu14(
        sesion,
        id_curso,
    )

    if curso is None:
        raise NoEncontrado(
            "El curso seleccionado no existe."
        )

    materias = await repo.listar_materias_curso_cu14(
        sesion,
        id_curso,
        gestion.id_gestion,
    )

    return MateriasCursoAsignacionSalida(
        id_curso=curso["id_curso"],
        nombre_curso=curso["nombre_curso"],

        id_gestion=gestion.id_gestion,
        anio_gestion=gestion.anio,

        materias=[
            MateriaCursoAsignacionSalida.model_validate(
                materia
            )
            for materia in materias
        ],
    )


# ============================================================
# 4. OBTENER UNA ASIGNACION
# ============================================================

async def obtener(
    sesion: AsyncSession,
    id_asignacion: int,
) -> AsignacionSalida:
    """
    Busca una asignacion mediante su identificador.
    """

    asignacion = await sesion.get(
        AsignacionProfesorClase,
        id_asignacion,
    )

    if asignacion is None:
        raise NoEncontrado(
            "La asignacion seleccionada no existe."
        )

    return AsignacionSalida.model_validate(asignacion)


# ============================================================
# 5. REGISTRAR ASIGNACION
# ============================================================

async def registrar(
    sesion: AsyncSession,
    datos: AsignacionCrear,
) -> AsignacionSalida:
    """
    Registra un profesor y un aula para una materia
    de un curso en la gestion abierta.
    """

    # 1. Comprobar gestion abierta

    gestion = await exigir_gestion_abierta(sesion)

    # 2. Verificar que el curso exista

    curso = await repo.obtener_curso_cu14(
        sesion,
        datos.id_curso,
    )

    if curso is None:
        raise NoEncontrado(
            "El curso seleccionado no existe."
        )

    # 3. Verificar que la materia pertenezca al grado

    materia_valida = (
        await repo.materia_habilitada_en_curso_cu14(
            sesion,
            datos.id_curso,
            datos.id_materia,
        )
    )

    if not materia_valida:
        raise ErrorNegocio(
            "La materia seleccionada no pertenece "
            "al plan de estudios del grado de este curso."
        )

    # 4. Verificar que el profesor este activo

    profesor_valido = await repo.profesor_activo_cu14(
        sesion,
        datos.ci_profesor,
    )

    if not profesor_valido:
        raise ErrorNegocio(
            "El profesor seleccionado no existe "
            "o no se encuentra activo."
        )

    # 5. Verificar que el aula este disponible

    aula_valida = await repo.aula_disponible_cu14(
        sesion,
        datos.id_aula,
    )

    if not aula_valida:
        raise ErrorNegocio(
            "El aula seleccionada no existe "
            "o no se encuentra disponible."
        )

    # 6. Impedir asignaciones duplicadas

    existente = await repo.buscar_asignacion_duplicada_cu14(
        sesion,
        datos.id_curso,
        datos.id_materia,
        gestion.id_gestion,
    )

    if existente is not None:
        raise Conflicto(
            "Esta materia ya tiene una asignacion "
            "registrada para el curso y la gestion actual."
        )

    # 7. Crear la asignacion

    asignacion = AsignacionProfesorClase(
        ci_profesor_asignacion=datos.ci_profesor,
        id_materia_asignacion=datos.id_materia,
        id_curso_asignacion=datos.id_curso,
        id_aula_asignacion=datos.id_aula,
        id_gestion_asignacion=gestion.id_gestion,
    )

    sesion.add(asignacion)

    await sesion.flush()

    return AsignacionSalida.model_validate(asignacion)


# ============================================================
# 6. MODIFICAR ASIGNACION
# ============================================================

async def actualizar(
    sesion: AsyncSession,
    id_asignacion: int,
    datos: AsignacionActualizar,
) -> AsignacionSalida:
    """
    Permite cambiar el profesor, el aula o ambos.

    Solo se pueden modificar asignaciones
    de la gestion abierta.
    """

    # 1. Buscar asignacion

    asignacion = await sesion.get(
        AsignacionProfesorClase,
        id_asignacion,
    )

    if asignacion is None:
        raise NoEncontrado(
            "La asignacion que deseas modificar no existe."
        )

    # 2. Comprobar gestion

    gestion = await exigir_gestion_abierta(sesion)

    if asignacion.id_gestion_asignacion != gestion.id_gestion:
        raise Conflicto(
            "No se puede modificar una asignacion "
            "que pertenece a una gestion diferente "
            "de la gestion abierta."
        )

    # 3. Obtener cambios enviados

    cambios = datos.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    if not cambios:
        raise ErrorNegocio(
            "Debes proporcionar al menos un dato "
            "para modificar la asignacion."
        )

    # 4. Validar nuevo profesor

    if "ci_profesor" in cambios:

        profesor_valido = await repo.profesor_activo_cu14(
            sesion,
            cambios["ci_profesor"],
        )

        if not profesor_valido:
            raise ErrorNegocio(
                "El profesor seleccionado no existe "
                "o no se encuentra activo."
            )

        asignacion.ci_profesor_asignacion = (
            cambios["ci_profesor"]
        )

    # 5. Validar nueva aula

    if "id_aula" in cambios:

        aula_valida = await repo.aula_disponible_cu14(
            sesion,
            cambios["id_aula"],
        )

        if not aula_valida:
            raise ErrorNegocio(
                "El aula seleccionada no existe "
                "o no se encuentra disponible."
            )

        asignacion.id_aula_asignacion = cambios["id_aula"]

    # 6. Guardar cambios

    await sesion.flush()

    return AsignacionSalida.model_validate(asignacion)


# ============================================================
# 7. ELIMINAR ASIGNACION
# ============================================================

async def eliminar(
    sesion: AsyncSession,
    id_asignacion: int,
) -> None:
    """
    Elimina una asignacion solamente si:

    - Pertenece a la gestion abierta.
    - No tiene asistencias.
    - No tiene calificaciones relacionadas.
    """

    # 1. Buscar asignacion

    asignacion = await sesion.get(
        AsignacionProfesorClase,
        id_asignacion,
    )

    if asignacion is None:
        raise NoEncontrado(
            "La asignacion que deseas eliminar no existe."
        )

    # 2. Verificar gestion abierta

    gestion = await exigir_gestion_abierta(sesion)

    if asignacion.id_gestion_asignacion != gestion.id_gestion:
        raise Conflicto(
            "No se puede eliminar una asignacion "
            "de una gestion diferente de la abierta."
        )

    # 3. Comprobar asistencias

    tiene_asistencias = (
        await repo.asignacion_con_asistencias_cu14(
            sesion,
            id_asignacion,
        )
    )

    if tiene_asistencias:
        raise Conflicto(
            "No se puede eliminar la asignacion "
            "porque tiene asistencias registradas."
        )

    # 4. Comprobar calificaciones

    tiene_calificaciones = (
        await repo.asignacion_con_calificaciones_cu14(
            sesion,
            id_asignacion,
        )
    )

    if tiene_calificaciones:
        raise Conflicto(
            "No se puede eliminar la asignacion "
            "porque tiene calificaciones registradas."
        )

    # 5. Eliminar asignacion

    await sesion.delete(asignacion)

    await sesion.flush()
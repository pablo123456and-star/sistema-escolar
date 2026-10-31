"""
Endpoints del paquete academico: /api/v1/academico/...

Cada endpoint llama a su caso de uso en casos_uso/.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/academico", tags=["academico"])

# PENDIENTE: endpoints de
#   cu12_gestionar_niveles_cursos
#   cu13_gestionar_materias
#   cu14_asignar_profesor
#   cu16_inscribir_estudiante
#   cu17_consultar_historial_inscripciones

# ============================================================
# CU13 - GESTIONAR MATERIAS Y PLAN DE ESTUDIOS
# ============================================================

from fastapi import status

from app.nucleo.dependencias import Administrador, Sesion

from app.nucleo.esquemas import (
    NumeroPagina,
    Pagina,
    TamanoPagina,
)

from app.paquetes.academico.casos_uso import (
    cu13_gestionar_materias as cu13,
)

from app.paquetes.academico.schemas import (
    MateriaCrear,
    MateriaActualizar,
    MateriaSalida,
    OpcionesPlanSalida,
    MateriaPlanEntrada,
    PlanEstudiosSalida,
)


# ------------------------------------------------------------
# 1. LISTAR Y BUSCAR MATERIAS
# ------------------------------------------------------------

@router.get(
    "/materias",
    response_model=Pagina[MateriaSalida],
    summary="CU13 - Listar y buscar materias",
)
async def listar_materias(
    _: Administrador,
    sesion: Sesion,
    q: str | None = None,
    pagina: NumeroPagina = 1,
    tamano: TamanoPagina = 10,
):
    return await cu13.listar(
        sesion,
        q=q,
        pagina=pagina,
        tamano=tamano,
    )


# ------------------------------------------------------------
# 2. CONSULTAR NIVELES Y GRADOS
# ------------------------------------------------------------

@router.get(
    "/niveles-grados",
    response_model=OpcionesPlanSalida,
    summary="CU13 - Consultar niveles educativos y grados",
)
async def opciones_plan_estudios(
    _: Administrador,
    sesion: Sesion,
):
    return await cu13.opciones(sesion)


# ------------------------------------------------------------
# 3. CONSULTAR UNA MATERIA
# ------------------------------------------------------------

@router.get(
    "/materias/{id_materia}",
    response_model=MateriaSalida,
    summary="CU13 - Consultar materia",
)
async def obtener_materia(
    _: Administrador,
    sesion: Sesion,
    id_materia: int,
):
    return await cu13.obtener(
        sesion,
        id_materia,
    )


# ------------------------------------------------------------
# 4. REGISTRAR MATERIA
# ------------------------------------------------------------

@router.post(
    "/materias",
    response_model=MateriaSalida,
    status_code=status.HTTP_201_CREATED,
    summary="CU13 - Registrar materia",
)
async def registrar_materia(
    datos: MateriaCrear,
    _: Administrador,
    sesion: Sesion,
):
    return await cu13.registrar(
        sesion,
        datos,
    )


# ------------------------------------------------------------
# 5. MODIFICAR MATERIA
# ------------------------------------------------------------

@router.patch(
    "/materias/{id_materia}",
    response_model=MateriaSalida,
    summary="CU13 - Modificar materia",
)
async def actualizar_materia(
    datos: MateriaActualizar,
    _: Administrador,
    sesion: Sesion,
    id_materia: int,
):
    return await cu13.actualizar(
        sesion,
        id_materia,
        datos,
    )


# ------------------------------------------------------------
# 6. ELIMINAR MATERIA
# ------------------------------------------------------------

@router.delete(
    "/materias/{id_materia}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="CU13 - Eliminar materia",
)
async def eliminar_materia(
    _: Administrador,
    sesion: Sesion,
    id_materia: int,
):
    await cu13.eliminar(
        sesion,
        id_materia,
    )


# ------------------------------------------------------------
# 7. CONSULTAR PLAN DE ESTUDIOS
# ------------------------------------------------------------

@router.get(
    "/grados/{id_grado}/materias",
    response_model=PlanEstudiosSalida,
    summary="CU13 - Consultar plan de estudios",
)
async def consultar_plan_estudios(
    _: Administrador,
    sesion: Sesion,
    id_grado: int,
):
    return await cu13.consultar_plan(
        sesion,
        id_grado,
    )


# ------------------------------------------------------------
# 8. AGREGAR MATERIA AL PLAN
# ------------------------------------------------------------

@router.post(
    "/grados/{id_grado}/materias",
    response_model=PlanEstudiosSalida,
    status_code=status.HTTP_201_CREATED,
    summary="CU13 - Agregar materia al plan",
)
async def agregar_materia_plan(
    datos: MateriaPlanEntrada,
    _: Administrador,
    sesion: Sesion,
    id_grado: int,
):
    return await cu13.agregar_al_plan(
        sesion,
        id_grado,
        datos,
    )


# ------------------------------------------------------------
# 9. QUITAR MATERIA DEL PLAN
# ------------------------------------------------------------

@router.delete(
    "/grados/{id_grado}/materias/{id_materia}",
    response_model=PlanEstudiosSalida,
    summary="CU13 - Quitar materia del plan",
)
async def quitar_materia_plan(
    _: Administrador,
    sesion: Sesion,
    id_grado: int,
    id_materia: int,
):
    return await cu13.quitar_del_plan(
        sesion,
        id_grado,
        id_materia,
    )

# ============================================================
# CU14 - ASIGNAR PROFESOR A MATERIA/CURSO
# ============================================================

from app.paquetes.academico.casos_uso import (
    cu14_asignar_profesor as cu14,
)

from app.paquetes.academico.schemas import (
    AsignacionCrear,
    AsignacionActualizar,
    AsignacionSalida,
    OpcionesAsignacionSalida,
    MateriasCursoAsignacionSalida,
)


# ------------------------------------------------------------
# 1. CONSULTAR OPCIONES PARA REALIZAR ASIGNACIONES
# ------------------------------------------------------------

@router.get(
    "/asignaciones/opciones",
    response_model=OpcionesAsignacionSalida,
    summary="CU14 - Consultar cursos, profesores y aulas",
)
async def opciones_asignacion(
    _: Administrador,
    sesion: Sesion,
):
    return await cu14.opciones(sesion)


# ------------------------------------------------------------
# 2. CONSULTAR MATERIAS Y ASIGNACIONES DE UN CURSO
# ------------------------------------------------------------

@router.get(
    "/cursos/{id_curso}/asignaciones",
    response_model=MateriasCursoAsignacionSalida,
    summary="CU14 - Consultar materias y asignaciones del curso",
)
async def consultar_asignaciones_curso(
    _: Administrador,
    sesion: Sesion,
    id_curso: int,
):
    return await cu14.consultar_materias(
        sesion,
        id_curso,
    )


# ------------------------------------------------------------
# 3. CONSULTAR UNA ASIGNACION
# ------------------------------------------------------------

@router.get(
    "/asignaciones/{id_asignacion}",
    response_model=AsignacionSalida,
    summary="CU14 - Consultar una asignacion",
)
async def obtener_asignacion(
    _: Administrador,
    sesion: Sesion,
    id_asignacion: int,
):
    return await cu14.obtener(
        sesion,
        id_asignacion,
    )


# ------------------------------------------------------------
# 4. REGISTRAR UNA ASIGNACION
# ------------------------------------------------------------

@router.post(
    "/asignaciones",
    response_model=AsignacionSalida,
    status_code=status.HTTP_201_CREATED,
    summary="CU14 - Registrar asignacion de profesor",
)
async def registrar_asignacion(
    datos: AsignacionCrear,
    _: Administrador,
    sesion: Sesion,
):
    return await cu14.registrar(
        sesion,
        datos,
    )


# ------------------------------------------------------------
# 5. MODIFICAR UNA ASIGNACION
# ------------------------------------------------------------

@router.patch(
    "/asignaciones/{id_asignacion}",
    response_model=AsignacionSalida,
    summary="CU14 - Modificar asignacion de profesor",
)
async def actualizar_asignacion(
    datos: AsignacionActualizar,
    _: Administrador,
    sesion: Sesion,
    id_asignacion: int,
):
    return await cu14.actualizar(
        sesion,
        id_asignacion,
        datos,
    )


# ------------------------------------------------------------
# 6. ELIMINAR UNA ASIGNACION
# ------------------------------------------------------------

@router.delete(
    "/asignaciones/{id_asignacion}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="CU14 - Eliminar asignacion de profesor",
)
async def eliminar_asignacion(
    _: Administrador,
    sesion: Sesion,
    id_asignacion: int,
):
    await cu14.eliminar(
        sesion,
        id_asignacion,
    )

# ============================================================
# CU16 - INSCRIBIR ESTUDIANTE EN GESTIÓN ACADÉMICA
# ============================================================

from app.paquetes.academico.casos_uso import cu16_inscribir_estudiante as cu16
from app.paquetes.academico.schemas import BoletaSalida, EstudianteInscripcionSalida, InscripcionCrear


@router.get("/inscripciones/estudiantes", response_model=Pagina[EstudianteInscripcionSalida],
            summary="CU16 - Buscar estudiante (CI, RUDE o nombre)")
async def buscar_estudiantes_inscripcion(
    _: Administrador, sesion: Sesion, q: str | None = None, pagina: NumeroPagina = 1, tamano: TamanoPagina = 10,
):
    return await cu16.buscar_estudiantes(sesion, q=q, pagina=pagina, tamano=tamano)


@router.post("/inscripciones", response_model=BoletaSalida, status_code=status.HTTP_201_CREATED,
             summary="CU16 - Inscribir estudiante en la gestión abierta")
async def inscribir_estudiante(datos: InscripcionCrear, _: Administrador, sesion: Sesion):
    return await cu16.inscribir(sesion, datos)


@router.get("/inscripciones/{id_inscripcion}/boleta", response_model=BoletaSalida,
            summary="CU16 - Emitir boleta de inscripción")
async def boleta_inscripcion(_: Administrador, sesion: Sesion, id_inscripcion: int):
    return await cu16.emitir_boleta(sesion, id_inscripcion)

# ============================================================
# CU12 - GESTIONAR NIVELES EDUCATIVOS Y CURSOS
# ============================================================

from app.paquetes.academico.casos_uso import cu12_gestionar_niveles_cursos as cu12
from app.paquetes.academico.schemas import (
    CursoActualizar, CursoCrear, CursoSalida, EstructuraSalida, GradoActualizar, GradoCrear, GradoSalida,
    NivelEducativoSalida, NivelEntrada,
)


@router.get("/estructura", response_model=EstructuraSalida,
            summary="CU12 - Consultar niveles, grados y paralelos con sus inscritos")
async def consultar_estructura(_: Administrador, sesion: Sesion):
    return await cu12.estructura(sesion)


@router.post("/niveles", response_model=NivelEducativoSalida, status_code=status.HTTP_201_CREATED,
             summary="CU12 - Registrar nivel educativo")
async def registrar_nivel(datos: NivelEntrada, _: Administrador, sesion: Sesion):
    return await cu12.registrar_nivel(sesion, datos)


@router.patch("/niveles/{id_nivel}", response_model=NivelEducativoSalida, summary="CU12 - Renombrar nivel educativo")
async def actualizar_nivel(datos: NivelEntrada, _: Administrador, sesion: Sesion, id_nivel: int):
    return await cu12.actualizar_nivel(sesion, id_nivel, datos)


@router.delete("/niveles/{id_nivel}", status_code=status.HTTP_204_NO_CONTENT, summary="CU12 - Eliminar nivel educativo")
async def eliminar_nivel(_: Administrador, sesion: Sesion, id_nivel: int):
    await cu12.eliminar_nivel(sesion, id_nivel)


@router.post("/grados", response_model=GradoSalida, status_code=status.HTTP_201_CREATED, summary="CU12 - Registrar grado")
async def registrar_grado(datos: GradoCrear, _: Administrador, sesion: Sesion):
    return await cu12.registrar_grado(sesion, datos)


@router.patch("/grados/{id_grado}", response_model=GradoSalida, summary="CU12 - Modificar grado")
async def actualizar_grado(datos: GradoActualizar, _: Administrador, sesion: Sesion, id_grado: int):
    return await cu12.actualizar_grado(sesion, id_grado, datos)


@router.delete("/grados/{id_grado}", status_code=status.HTTP_204_NO_CONTENT, summary="CU12 - Eliminar grado")
async def eliminar_grado(_: Administrador, sesion: Sesion, id_grado: int):
    await cu12.eliminar_grado(sesion, id_grado)


@router.post("/cursos", response_model=CursoSalida, status_code=status.HTTP_201_CREATED,
             summary="CU12 - Registrar paralelo")
async def registrar_curso(datos: CursoCrear, _: Administrador, sesion: Sesion):
    return await cu12.registrar_curso(sesion, datos)


@router.patch("/cursos/{id_curso}", response_model=CursoSalida, summary="CU12 - Modificar paralelo o cupo")
async def actualizar_curso(datos: CursoActualizar, _: Administrador, sesion: Sesion, id_curso: int):
    return await cu12.actualizar_curso(sesion, id_curso, datos)


@router.delete("/cursos/{id_curso}", status_code=status.HTTP_204_NO_CONTENT, summary="CU12 - Eliminar paralelo")
async def eliminar_curso(_: Administrador, sesion: Sesion, id_curso: int):
    await cu12.eliminar_curso(sesion, id_curso)


# ============================================================
# CU15 - GESTIONAR GESTIÓN ACADÉMICA (AÑO LECTIVO)
# ============================================================

from app.paquetes.academico.casos_uso import cu15_gestionar_gestion_academica as cu15
from app.paquetes.academico.schemas import (
    CierreGestionSalida, DimensionesGuardar, DimensionesSalida, GestionActualizar, GestionCrear, GestionSalida,
    PeriodoActualizar, PeriodoCrear, PeriodoSalida, ResumenGestionSalida,
)


@router.get("/gestiones", response_model=list[GestionSalida], summary="CU15 - Listar gestiones académicas")
async def listar_gestiones(_: Administrador, sesion: Sesion):
    return await cu15.listar_gestiones(sesion)


@router.post("/gestiones", response_model=GestionSalida, status_code=status.HTTP_201_CREATED,
             summary="CU15 - Crear gestión académica")
async def crear_gestion(datos: GestionCrear, _: Administrador, sesion: Sesion):
    return await cu15.crear_gestion(sesion, datos)


@router.get("/gestiones/{id_gestion}", response_model=GestionSalida, summary="CU15 - Consultar gestión")
async def consultar_gestion(_: Administrador, sesion: Sesion, id_gestion: int):
    return await cu15.obtener_gestion(sesion, id_gestion)


@router.patch("/gestiones/{id_gestion}", response_model=GestionSalida, summary="CU15 - Modificar gestión abierta")
async def actualizar_gestion(datos: GestionActualizar, _: Administrador, sesion: Sesion, id_gestion: int):
    return await cu15.actualizar_gestion(sesion, id_gestion, datos)


@router.get("/gestiones/{id_gestion}/resumen", response_model=ResumenGestionSalida,
            summary="CU15 - Resumen de la gestión para el panel")
async def resumen_gestion(_: Administrador, sesion: Sesion, id_gestion: int):
    return await cu15.resumen(sesion, id_gestion)


@router.post("/gestiones/{id_gestion}/cerrar", response_model=CierreGestionSalida,
             summary="CU15 - Cerrar gestión (promovidos y reprobados)")
async def cerrar_gestion(_: Administrador, sesion: Sesion, id_gestion: int):
    return await cu15.cerrar_gestion(sesion, id_gestion)


@router.get("/gestiones/{id_gestion}/periodos", response_model=list[PeriodoSalida], summary="CU15 - Listar periodos")
async def listar_periodos(_: Administrador, sesion: Sesion, id_gestion: int):
    return await cu15.listar_periodos(sesion, id_gestion)


@router.post("/gestiones/{id_gestion}/periodos", response_model=PeriodoSalida, status_code=status.HTTP_201_CREATED,
             summary="CU15 - Registrar periodo")
async def crear_periodo(datos: PeriodoCrear, _: Administrador, sesion: Sesion, id_gestion: int):
    return await cu15.crear_periodo(sesion, id_gestion, datos)


@router.patch("/periodos/{id_periodo}", response_model=PeriodoSalida, summary="CU15 - Modificar periodo")
async def actualizar_periodo(datos: PeriodoActualizar, _: Administrador, sesion: Sesion, id_periodo: int):
    return await cu15.actualizar_periodo(sesion, id_periodo, datos)


@router.delete("/periodos/{id_periodo}", status_code=status.HTTP_204_NO_CONTENT, summary="CU15 - Eliminar periodo")
async def eliminar_periodo(_: Administrador, sesion: Sesion, id_periodo: int):
    await cu15.eliminar_periodo(sesion, id_periodo)


@router.get("/gestiones/{id_gestion}/dimensiones", response_model=DimensionesSalida,
            summary="CU15 - Consultar dimensiones de evaluación")
async def consultar_dimensiones(_: Administrador, sesion: Sesion, id_gestion: int):
    return await cu15.consultar_dimensiones(sesion, id_gestion)


@router.put("/gestiones/{id_gestion}/dimensiones", response_model=DimensionesSalida,
            summary="CU15 - Guardar dimensiones de evaluación")
async def guardar_dimensiones(datos: DimensionesGuardar, _: Administrador, sesion: Sesion, id_gestion: int):
    return await cu15.guardar_dimensiones(sesion, id_gestion, datos)

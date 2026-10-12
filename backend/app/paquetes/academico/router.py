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
#   cu15_gestionar_gestion_academica
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
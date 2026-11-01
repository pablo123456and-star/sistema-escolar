"""
Endpoints del paquete horarios: /api/v1/horarios/...

Cada endpoint llama a su caso de uso en casos_uso/.
"""
from fastapi import APIRouter, status

from app.nucleo.dependencias import Administrador, Sesion, Usuario
from app.paquetes.horarios.casos_uso import cu18_gestionar_aulas as cu18
from app.paquetes.horarios.casos_uso import cu19_generar_horario as cu19
from app.paquetes.horarios.casos_uso import cu20_consultar_horarios as cu20
from app.paquetes.horarios.schemas import (
    AulaActualizar, AulaCrear, AulaSalida,
    CursoHorarioSalida, HorarioActualizar, HorarioConsultaSalida, HorarioCrear, HorarioCursoSalida, HorarioSalida,
    OpcionesConsultaSalida,
)

router = APIRouter(prefix="/horarios", tags=["horarios"])


# ---- CU18: gestionar aulas -------------------------------------------------------
@router.get("/aulas", response_model=list[AulaSalida], summary="CU18 - Listar aulas con número de clases asignadas")
async def listar_aulas(_: Administrador, sesion: Sesion):
    return await cu18.listar_aulas(sesion)


@router.post("/aulas", response_model=AulaSalida, status_code=status.HTTP_201_CREATED,
             summary="CU18 - Registrar una nueva aula")
async def crear_aula(datos: AulaCrear, _: Administrador, sesion: Sesion):
    return await cu18.crear_aula(sesion, datos)


@router.patch("/aulas/{id_aula}", response_model=AulaSalida, summary="CU18 - Modificar o cambiar estado de un aula")
async def editar_aula(id_aula: int, datos: AulaActualizar, _: Administrador, sesion: Sesion):
    return await cu18.editar_aula(sesion, id_aula, datos)


@router.delete("/aulas/{id_aula}", status_code=status.HTTP_204_NO_CONTENT,
               summary="CU18 - Eliminar aula sin clases asignadas")
async def eliminar_aula(id_aula: int, _: Administrador, sesion: Sesion):
    await cu18.eliminar_aula(sesion, id_aula)


# ---- CU19: generar horario -------------------------------------------------------
@router.get("/cursos", response_model=list[CursoHorarioSalida], summary="CU19 - Cursos de la gestión abierta")
async def listar_cursos(_: Administrador, sesion: Sesion):
    return await cu19.cursos(sesion)


@router.get("/cursos/{id_curso}", response_model=HorarioCursoSalida,
            summary="CU19 - Horario del curso y sus asignaciones")
async def horario_curso(_: Administrador, sesion: Sesion, id_curso: int):
    return await cu19.horario_curso(sesion, id_curso)


@router.post("/cursos/{id_curso}/bloques", response_model=HorarioSalida, status_code=status.HTTP_201_CREATED,
             summary="CU19 - Agregar bloque de horario")
async def agregar_bloque(datos: HorarioCrear, _: Administrador, sesion: Sesion, id_curso: int):
    return await cu19.agregar(sesion, id_curso, datos)


@router.patch("/bloques/{id_horario}", response_model=HorarioSalida, summary="CU19 - Modificar bloque de horario")
async def modificar_bloque(datos: HorarioActualizar, _: Administrador, sesion: Sesion, id_horario: int):
    return await cu19.modificar(sesion, id_horario, datos)


@router.delete("/bloques/{id_horario}", status_code=status.HTTP_204_NO_CONTENT,
               summary="CU19 - Eliminar bloque de horario")
async def eliminar_bloque(_: Administrador, sesion: Sesion, id_horario: int):
    await cu19.eliminar(sesion, id_horario)


# ---- CU20: consultar horarios ----------------------------------------------------
@router.get("/consulta/opciones", response_model=OpcionesConsultaSalida,
            summary="CU20 - Horarios que el usuario puede consultar según su rol")
async def opciones_consulta(usuario: Usuario, sesion: Sesion):
    return await cu20.opciones(sesion, usuario)


@router.get("/consulta", response_model=HorarioConsultaSalida, summary="CU20 - Horario de un curso o de un docente")
async def consultar_horario(usuario: Usuario, sesion: Sesion, id_curso: int | None = None,
                            ci_profesor: str | None = None):
    return await cu20.consultar(sesion, usuario, id_curso=id_curso, ci_profesor=ci_profesor)

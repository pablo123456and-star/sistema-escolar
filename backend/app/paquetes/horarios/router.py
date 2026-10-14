"""
Endpoints del paquete horarios: /api/v1/horarios/...

Cada endpoint llama a su caso de uso en casos_uso/.
"""
from fastapi import APIRouter, status

from app.nucleo.dependencias import Administrador, Sesion, Usuario
from app.paquetes.horarios.casos_uso import cu19_generar_horario as cu19
from app.paquetes.horarios.casos_uso import cu20_consultar_horarios as cu20
from app.paquetes.horarios.schemas import (
    CursoHorarioSalida, HorarioActualizar, HorarioConsultaSalida, HorarioCrear, HorarioCursoSalida, HorarioSalida,
    OpcionesConsultaSalida,
)

router = APIRouter(prefix="/horarios", tags=["horarios"])

# PENDIENTE: endpoints de
#   cu18_gestionar_aulas


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

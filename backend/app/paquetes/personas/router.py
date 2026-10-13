"""
Endpoints del paquete personas: /api/v1/personas/...

Cada endpoint llama a su caso de uso en casos_uso/.
"""
from typing import Annotated, Literal

from fastapi import APIRouter, Path, status

from app.nucleo.dependencias import Administrador, Sesion
from app.nucleo.errores import NoEncontrado
from app.nucleo.esquemas import NumeroPagina, Pagina, TamanoPagina
from app.paquetes.personas import repository as repo
from app.paquetes.personas.casos_uso import cu06_gestionar_estudiante as cu06
from app.paquetes.personas.casos_uso import cu08_registrar_asociar_tutor as cu08
from app.paquetes.personas.casos_uso import cu10_registrar_docente as cu10
from app.paquetes.personas.schemas import (
    PATRON_CI, BajaEntrada, EstudianteActualizar, EstudianteCrear, EstudianteDetalleSalida, EstudianteSalida,
    OpcionesEstudianteSalida, PersonaBuscadaSalida, PersonaSalida, TutorActualizar, TutorCrear, TutorDetalleSalida,
    TutorSalida, VinculoActualizar, VinculoConEstudianteEntrada, VinculoEntrada, VinculoSalida,
    DocenteActualizar, DocenteCrear, DocenteDetalleSalida, DocenteSalida,
)

router = APIRouter(prefix="/personas", tags=["personas"])

CiRuta = Annotated[str, Path(pattern=PATRON_CI)]
Estado = Literal["activo", "inactivo"]


@router.get("/buscar/{ci}", response_model=PersonaBuscadaSalida,
            summary="Buscar persona por CI (para reutilizarla al registrar)")
async def buscar_persona(_: Administrador, sesion: Sesion, ci: CiRuta):
    fila = await repo.buscar_persona(sesion, ci)
    if fila is None:
        raise NoEncontrado("No existe una persona con ese CI.")
    return PersonaBuscadaSalida(
        **PersonaSalida.model_validate(fila.Persona, from_attributes=True).model_dump(),
        es_estudiante=fila.es_estudiante, es_tutor=fila.es_tutor,
        es_profesor=fila.es_profesor, es_administrativo=fila.es_administrativo,
    )


# ---- CU06: estudiantes -----------------------------------------------------------
@router.get("/estudiantes", response_model=Pagina[EstudianteSalida], summary="CU06 - Listar estudiantes")
async def listar_estudiantes(
    _: Administrador, sesion: Sesion,
    q: str | None = None, id_grado: int | None = None, paralelo: str | None = None, estado: Estado | None = None,
    pagina: NumeroPagina = 1, tamano: TamanoPagina = 10,
):
    return await cu06.listar(sesion, q=q, id_grado=id_grado, paralelo=paralelo, estado=estado,
                             pagina=pagina, tamano=tamano)


@router.get("/estudiantes/opciones", response_model=OpcionesEstudianteSalida,
            summary="CU06 - Cursos de la gestión abierta (filtros e inscripción)")
async def opciones_estudiantes(_: Administrador, sesion: Sesion):
    return await cu06.opciones(sesion)


@router.get("/estudiantes/{ci}", response_model=EstudianteDetalleSalida, summary="CU06 - Ver estudiante")
async def obtener_estudiante(_: Administrador, sesion: Sesion, ci: CiRuta):
    return await cu06.obtener(sesion, ci)


@router.post("/estudiantes", response_model=EstudianteDetalleSalida, status_code=status.HTTP_201_CREATED,
             summary="CU06 - Registrar estudiante (con tutor e inscripción opcionales)")
async def registrar_estudiante(datos: EstudianteCrear, _: Administrador, sesion: Sesion):
    return await cu06.registrar(sesion, datos)


@router.patch("/estudiantes/{ci}", response_model=EstudianteDetalleSalida, summary="CU06 - Actualizar estudiante")
async def actualizar_estudiante(datos: EstudianteActualizar, _: Administrador, sesion: Sesion, ci: CiRuta):
    return await cu06.actualizar(sesion, ci, datos)


@router.post("/estudiantes/{ci}/baja", response_model=EstudianteDetalleSalida, summary="CU06 - Dar de baja (lógica)")
async def baja_estudiante(datos: BajaEntrada, _: Administrador, sesion: Sesion, ci: CiRuta):
    return await cu06.dar_baja(sesion, ci, datos.motivo)


@router.post("/estudiantes/{ci}/reactivar", response_model=EstudianteDetalleSalida, summary="CU06 - Reactivar")
async def reactivar_estudiante(_: Administrador, sesion: Sesion, ci: CiRuta):
    return await cu06.reactivar(sesion, ci)


# ---- CU08: tutores y vínculos ------------------------------------------------------
@router.get("/tutores", response_model=Pagina[TutorSalida], summary="CU08 - Listar tutores")
async def listar_tutores(
    _: Administrador, sesion: Sesion, q: str | None = None, estado: Estado | None = None,
    pagina: NumeroPagina = 1, tamano: TamanoPagina = 10,
):
    return await cu08.listar(sesion, q, estado, pagina, tamano)


@router.get("/tutores/{ci}", response_model=TutorDetalleSalida, summary="CU08 - Ver tutor y sus estudiantes")
async def obtener_tutor(_: Administrador, sesion: Sesion, ci: CiRuta):
    return await cu08.obtener(sesion, ci)


@router.post("/tutores", response_model=TutorDetalleSalida, status_code=status.HTTP_201_CREATED,
             summary="CU08 - Registrar tutor")
async def registrar_tutor(datos: TutorCrear, _: Administrador, sesion: Sesion):
    return await cu08.registrar(sesion, datos)


@router.patch("/tutores/{ci}", response_model=TutorDetalleSalida, summary="CU08 - Actualizar tutor")
async def actualizar_tutor(datos: TutorActualizar, _: Administrador, sesion: Sesion, ci: CiRuta):
    return await cu08.actualizar(sesion, ci, datos)


@router.post("/tutores/{ci}/estudiantes", response_model=VinculoSalida, status_code=status.HTTP_201_CREATED,
             summary="CU08 - Asociar estudiante al tutor")
async def vincular(datos: VinculoConEstudianteEntrada, _: Administrador, sesion: Sesion, ci: CiRuta):
    vinculo = VinculoEntrada.model_validate(datos.model_dump(exclude={"ci_estudiante"}))
    return await cu08.vincular(sesion, ci, datos.ci_estudiante, vinculo)


@router.patch("/tutores/{ci}/estudiantes/{ci_estudiante}", response_model=VinculoSalida,
              summary="CU08 - Modificar el vínculo")
async def actualizar_vinculo(datos: VinculoActualizar, _: Administrador, sesion: Sesion,
                             ci: CiRuta, ci_estudiante: CiRuta):
    return await cu08.actualizar_vinculo(sesion, ci, ci_estudiante, datos)


@router.delete("/tutores/{ci}/estudiantes/{ci_estudiante}", status_code=status.HTTP_204_NO_CONTENT,
               summary="CU08 - Desvincular estudiante")
async def desvincular(_: Administrador, sesion: Sesion, ci: CiRuta, ci_estudiante: CiRuta):
    await cu08.desvincular(sesion, ci, ci_estudiante)


# ---- CU10: docentes ------------------------------------------------------------------
@router.get("/docentes", response_model=Pagina[DocenteSalida], summary="CU10 - Listar docentes")
async def listar_docentes(
    _: Administrador, sesion: Sesion, q: str | None = None, estado: Estado | None = None,
    pagina: NumeroPagina = 1, tamano: TamanoPagina = 10,
):
    return await cu10.listar(sesion, q, estado, pagina, tamano)


@router.get("/docentes/{ci}", response_model=DocenteDetalleSalida, summary="CU10 - Ver docente y sus materias")
async def obtener_docente(_: Administrador, sesion: Sesion, ci: CiRuta):
    return await cu10.obtener(sesion, ci)


@router.post("/docentes", response_model=DocenteDetalleSalida, status_code=status.HTTP_201_CREATED,
             summary="CU10 - Registrar docente")
async def registrar_docente(datos: DocenteCrear, _: Administrador, sesion: Sesion):
    return await cu10.registrar(sesion, datos)


@router.patch("/docentes/{ci}", response_model=DocenteDetalleSalida, summary="CU10 - Actualizar docente")
async def actualizar_docente(datos: DocenteActualizar, _: Administrador, sesion: Sesion, ci: CiRuta):
    return await cu10.actualizar(sesion, ci, datos)


@router.post("/docentes/{ci}/baja", response_model=DocenteDetalleSalida, summary="CU10 - Dar de baja (lógica)")
async def baja_docente(datos: BajaEntrada, _: Administrador, sesion: Sesion, ci: CiRuta):
    return await cu10.dar_baja(sesion, ci, datos.motivo)


@router.post("/docentes/{ci}/reactivar", response_model=DocenteDetalleSalida, summary="CU10 - Reactivar")
async def reactivar_docente(_: Administrador, sesion: Sesion, ci: CiRuta):
    return await cu10.reactivar(sesion, ci)

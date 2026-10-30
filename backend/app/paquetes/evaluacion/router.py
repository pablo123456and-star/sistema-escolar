"""
Endpoints del paquete evaluacion: /api/v1/evaluacion/...

Cada endpoint llama a su caso de uso en casos_uso/.
"""
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends

from app.nucleo.dependencias import Sesion, UsuarioActual, requiere_rol

router = APIRouter(prefix="/evaluacion", tags=["evaluacion"])

# PENDIENTE: endpoints de
#   cu22_consultar_historial_asistencia
#   cu23_registrar_calificaciones
#   cu24_generar_consultar_boletin

# ============================================================
# CU21 - REGISTRAR ASISTENCIA DE ESTUDIANTES
# ============================================================

from app.paquetes.evaluacion.casos_uso import cu21_registrar_asistencia as cu21
from app.paquetes.evaluacion.schemas import AsistenciaGuardar, ClasesAsistenciaSalida, ListaAsistenciaSalida

AdministradorOProfesor = Annotated[UsuarioActual, Depends(requiere_rol("administrador", "profesor"))]


@router.get("/asistencia/clases", response_model=ClasesAsistenciaSalida,
            summary="CU21 - Clases en las que el usuario registra asistencia")
async def clases_asistencia(usuario: AdministradorOProfesor, sesion: Sesion):
    return await cu21.clases(sesion, usuario)


@router.get("/asistencia/{id_asignacion}", response_model=ListaAsistenciaSalida,
            summary="CU21 - Lista de la clase en una fecha (hoy por defecto)")
async def lista_asistencia(usuario: AdministradorOProfesor, sesion: Sesion, id_asignacion: int,
                           fecha: date | None = None):
    return await cu21.lista(sesion, usuario, id_asignacion, fecha)


@router.put("/asistencia/{id_asignacion}", response_model=ListaAsistenciaSalida,
            summary="CU21 - Registrar o corregir la asistencia de toda la clase")
async def guardar_asistencia(datos: AsistenciaGuardar, usuario: AdministradorOProfesor, sesion: Sesion,
                             id_asignacion: int):
    return await cu21.guardar(sesion, usuario, id_asignacion, datos)

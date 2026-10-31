"""
Endpoints del paquete administracion: /api/v1/administracion/...

Cada endpoint llama a su caso de uso en casos_uso/.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.nucleo.dependencias import Administrador, Sesion, UsuarioActual, requiere_rol

router = APIRouter(prefix="/administracion", tags=["administracion"])

# PENDIENTE: endpoints de
#   cu26_gestionar_inventario
#   cu27_gestionar_comunicados

# ============================================================
# CU25 - REGISTRAR PAGO DE MENSUALIDAD
# ============================================================

from app.paquetes.administracion.casos_uso import cu25_registrar_pago_mensualidad as cu25
from app.paquetes.administracion.schemas import (
    ArancelActualizar, ArancelCrear, ArancelesSalida, ArancelNivelSalida, BecaActualizar, BecaCrear, BecaSalida,
    BecasSalida, CobroEntrada, EstadoCuentaSalida, EstudiantesPagoSalida, GenerarCuotasEntrada, GenerarCuotasSalida,
    MorososSalida, MotivoEntrada, ReciboSalida,
)

EstudianteOTutor = Annotated[UsuarioActual, Depends(requiere_rol("estudiante", "tutor"))]
ConsultaPagos = Annotated[UsuarioActual, Depends(requiere_rol("administrador", "estudiante", "tutor"))]


@router.get("/aranceles", response_model=ArancelesSalida, summary="CU25 - Aranceles de la gestión abierta por nivel")
async def aranceles(_: Administrador, sesion: Sesion):
    return await cu25.aranceles(sesion)


@router.post("/aranceles", response_model=ArancelNivelSalida, status_code=status.HTTP_201_CREATED,
             summary="CU25 - Registrar arancel de un nivel")
async def registrar_arancel(datos: ArancelCrear, _: Administrador, sesion: Sesion):
    return await cu25.registrar_arancel(sesion, datos)


@router.patch("/aranceles/{id_arancel}", response_model=ArancelNivelSalida, summary="CU25 - Modificar arancel")
async def actualizar_arancel(datos: ArancelActualizar, _: Administrador, sesion: Sesion, id_arancel: int):
    return await cu25.actualizar_arancel(sesion, id_arancel, datos)


@router.get("/becas", response_model=BecasSalida, summary="CU25 - Becas de la gestión abierta")
async def becas(_: Administrador, sesion: Sesion):
    return await cu25.becas(sesion)


@router.post("/becas", response_model=BecaSalida, status_code=status.HTTP_201_CREATED,
             summary="CU25 - Registrar beca de un estudiante")
async def registrar_beca(datos: BecaCrear, _: Administrador, sesion: Sesion):
    return await cu25.registrar_beca(sesion, datos)


@router.patch("/becas/{id_beca}", response_model=BecaSalida, summary="CU25 - Modificar beca")
async def actualizar_beca(datos: BecaActualizar, _: Administrador, sesion: Sesion, id_beca: int):
    return await cu25.actualizar_beca(sesion, id_beca, datos)


@router.post("/cuotas/generar", response_model=GenerarCuotasSalida,
             summary="CU25 - Generar las cuotas de un mes (CALL sp_generar_cuotas_mes)")
async def generar_cuotas(datos: GenerarCuotasEntrada, _: Administrador, sesion: Sesion):
    return await cu25.generar_cuotas(sesion, datos)


@router.get("/pagos/estudiantes", response_model=EstudiantesPagoSalida,
            summary="CU25 - Buscar estudiantes para cobrar (con sus cuotas pendientes)")
async def estudiantes_pago(_: Administrador, sesion: Sesion, buscar: str | None = None):
    return await cu25.estudiantes(sesion, buscar)


@router.get("/cuotas", response_model=EstadoCuentaSalida, summary="CU25 - Cuotas de un estudiante y sus tutores")
async def cuotas(usuario: Administrador, sesion: Sesion, ci_estudiante: str):
    return await cu25.estado_cuenta(sesion, usuario, ci_estudiante.strip())


@router.get("/mis-cuotas", response_model=list[EstadoCuentaSalida],
            summary="CU25 - Cuotas del estudiante o de los estudiantes del tutor")
async def mis_cuotas(usuario: EstudianteOTutor, sesion: Sesion):
    return await cu25.mis_cuotas(sesion, usuario)


@router.post("/pagos/{id_pago}/cobrar", response_model=ReciboSalida, summary="CU25 - Cobrar una cuota pendiente")
async def cobrar(datos: CobroEntrada, usuario: Administrador, sesion: Sesion, id_pago: int):
    return await cu25.cobrar(sesion, usuario, id_pago, datos)


@router.get("/pagos/{id_pago}/recibo", response_model=ReciboSalida, summary="CU25 - Recibo de pago de una cuota pagada")
async def recibo(usuario: ConsultaPagos, sesion: Sesion, id_pago: int):
    return await cu25.recibo(sesion, usuario, id_pago)


@router.post("/pagos/{id_pago}/revertir", response_model=EstadoCuentaSalida,
             summary="CU25 - Revertir un cobro mal hecho (la cuota vuelve a pendiente)")
async def revertir_cobro(datos: MotivoEntrada, usuario: Administrador, sesion: Sesion, id_pago: int):
    return await cu25.revertir_cobro(sesion, usuario, id_pago, datos)


@router.post("/pagos/{id_pago}/anular", response_model=EstadoCuentaSalida, summary="CU25 - Anular una cuota pendiente")
async def anular(datos: MotivoEntrada, usuario: Administrador, sesion: Sesion, id_pago: int):
    return await cu25.anular(sesion, usuario, id_pago, datos)


@router.get("/morosos", response_model=MorososSalida, summary="CU25 - Estudiantes con cuotas atrasadas")
async def morosos(_: Administrador, sesion: Sesion):
    return await cu25.morosos(sesion)

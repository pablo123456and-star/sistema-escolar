"""
Endpoints del paquete reportes: /api/v1/reportes/...

?formato=json devuelve la vista previa; pdf o xlsx devuelve el archivo para descargar
(y la descarga queda en la bitácora).
"""
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.nucleo.dependencias import Sesion, UsuarioActual, requiere_rol
from app.nucleo.exportar import Tabla, a_excel, a_pdf
from app.paquetes.reportes import repository as repo
from app.paquetes.reportes.casos_uso import reporte_dinamico, reportes_estaticos
from app.paquetes.reportes.schemas import (
    ColumnaSalida,
    Formato,
    FuenteSalida,
    OpcionesSalida,
    ReporteDinamicoEntrada,
    ReporteEstaticoInfo,
    ReporteSalida,
)

router = APIRouter(prefix="/reportes", tags=["reportes"])
Administrador = Annotated[UsuarioActual, Depends(requiere_rol("administrador"))]

_TIPOS = {"pdf": "application/pdf",
          "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}


def _vista_previa(tabla: Tabla, total: int) -> ReporteSalida:
    def limpio(v):
        return float(v) if isinstance(v, Decimal) else v

    return ReporteSalida(
        titulo=tabla.titulo, filtros=tabla.filtros,
        columnas=[ColumnaSalida(clave=c.clave, titulo=c.titulo, tipo=c.tipo) for c in tabla.columnas],
        filas=[{k: limpio(v) for k, v in f.items()} for f in tabla.filas],
        total=total, mostradas=len(tabla.filas), resumen=tabla.resumen, generado_en=tabla.generado_en,
    )


async def _archivo(sesion, tabla: Tabla, formato: str, nombre: str) -> Response:
    contenido = a_pdf(tabla) if formato == "pdf" else a_excel(tabla)
    await repo.registrar_bitacora(sesion, f"Generó el reporte «{tabla.titulo}» en {formato.upper()}")
    archivo = f"reporte_{nombre}_{tabla.generado_en:%Y%m%d_%H%M}.{formato}"
    return Response(contenido, media_type=_TIPOS[formato],
                    headers={"Content-Disposition": f'attachment; filename="{archivo}"'})


@router.get("/opciones", response_model=OpcionesSalida, summary="Reportes - Listas para los filtros")
async def opciones(usuario: Administrador, sesion: Sesion):
    return await repo.opciones(sesion)


@router.get("/estaticos", response_model=list[ReporteEstaticoInfo], summary="Reportes - Catálogo de reportes fijos")
async def catalogo(usuario: Administrador):
    return reportes_estaticos.catalogo()


@router.get("/estaticos/{clave}", response_model=ReporteSalida,
            summary="Reportes - Reporte fijo (formato json, pdf o xlsx)")
async def estatico(usuario: Administrador, sesion: Sesion, clave: str, formato: Formato = "json",
                   id_gestion: int | None = None, id_curso: int | None = None, id_periodo: int | None = None):
    tabla = await reportes_estaticos.generar(sesion, usuario, clave, id_gestion, id_curso, id_periodo)
    if formato == "json":
        return _vista_previa(tabla, len(tabla.filas))
    return await _archivo(sesion, tabla, formato, clave)


@router.get("/dinamico/fuentes", response_model=list[FuenteSalida],
            summary="Reportes - Fuentes, columnas y filtros del reporte personalizado")
async def fuentes(usuario: Administrador):
    return reporte_dinamico.fuentes()


@router.post("/dinamico", response_model=ReporteSalida,
             summary="Reportes - Reporte personalizado (formato json, pdf o xlsx)")
async def dinamico(datos: ReporteDinamicoEntrada, usuario: Administrador, sesion: Sesion, formato: Formato = "json"):
    tabla, total = await reporte_dinamico.generar(sesion, usuario, datos, para_archivo=formato != "json")
    if formato == "json":
        return _vista_previa(tabla, total)
    return await _archivo(sesion, tabla, formato, datos.fuente)

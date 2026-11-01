"""
DTO de entrada y salida (Pydantic) del paquete reportes.
"""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

Formato = Literal["json", "pdf", "xlsx"]
TipoColumna = Literal["texto", "entero", "decimal", "porcentaje", "fecha"]


class GestionOpcion(BaseModel):
    id_gestion: int
    anio: int
    estado_gestion: str


class NivelOpcion(BaseModel):
    id_nivel: int
    nombre_nivel: str


class CursoOpcion(BaseModel):
    id_curso: int
    nombre_curso: str
    id_nivel: int


class PeriodoOpcion(BaseModel):
    id_periodo: int
    nombre_periodo: str
    id_gestion: int
    anio: int


class MateriaOpcion(BaseModel):
    id_materia: int
    nombre_materia: str


class OpcionesSalida(BaseModel):
    """Listas para los filtros de la pantalla de reportes."""

    gestiones: list[GestionOpcion]
    niveles: list[NivelOpcion]
    cursos: list[CursoOpcion]
    periodos: list[PeriodoOpcion]
    materias: list[MateriaOpcion]


class ReporteEstaticoInfo(BaseModel):
    """Un reporte fijo del catálogo y los datos que pide."""

    clave: str
    nombre: str
    descripcion: str
    parametros: list[Literal["gestion", "curso", "periodo"]]


class ColumnaSalida(BaseModel):
    clave: str
    titulo: str
    tipo: TipoColumna


class ReporteSalida(BaseModel):
    """Vista previa del reporte en pantalla (los mismos datos que van al PDF y al Excel)."""

    titulo: str
    filtros: list[str]
    columnas: list[ColumnaSalida]
    filas: list[dict[str, Any]]
    total: int            # registros que cumplen los filtros
    mostradas: int        # registros incluidos (la vista previa muestra hasta 200)
    resumen: list[str]
    generado_en: datetime


class ColumnaFuente(ColumnaSalida):
    por_defecto: bool


class OpcionFiltro(BaseModel):
    valor: str
    etiqueta: str


class FiltroFuente(BaseModel):
    clave: str
    titulo: str
    tipo: Literal["gestion", "nivel", "curso", "periodo", "materia", "opcion", "fecha", "numero"]
    opciones: list[OpcionFiltro]


class FuenteSalida(BaseModel):
    """Fuente de datos del reporte dinámico con sus columnas y filtros permitidos."""

    clave: str
    nombre: str
    descripcion: str
    columnas: list[ColumnaFuente]
    filtros: list[FiltroFuente]


class ReporteDinamicoEntrada(BaseModel):
    fuente: str = Field(min_length=1, max_length=30)
    columnas: list[str] = Field(min_length=1, max_length=20)
    filtros: dict[str, str | int | float | None] = Field(default_factory=dict)
    orden: str | None = Field(default=None, max_length=30)
    descendente: bool = False

    @field_validator("columnas")
    @classmethod
    def sin_repetidas(cls, valor: list[str]) -> list[str]:
        return list(dict.fromkeys(valor))

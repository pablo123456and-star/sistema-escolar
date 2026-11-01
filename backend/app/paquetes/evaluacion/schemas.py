"""
DTO de entrada y salida (Pydantic) del paquete evaluacion (compartido).
"""
# ============================================================
# CU21 - REGISTRAR ASISTENCIA DE ESTUDIANTES
# ============================================================

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

EstadoAsistencia = Literal["presente", "ausente", "tardanza", "justificado"]


class ClaseAsistenciaSalida(BaseModel):
    """Asignación (materia + curso + profesor) en la que se toma asistencia."""

    id_asignacion: int
    id_curso: int
    curso: str
    materia: str
    ci_profesor: str
    profesor: str
    dias: list[str]            # días de clase según el horario (CU19)
    registrada_hoy: bool


class ClasesAsistenciaSalida(BaseModel):
    """Clases que el usuario puede registrar en la gestión abierta (profesor: las suyas)."""

    gestion: int | None
    fecha_inicio: date | None  # primer día de la gestión: no se registra antes
    hoy: date                  # hora de Bolivia
    clases: list[ClaseAsistenciaSalida]


class EstudianteAsistenciaSalida(BaseModel):
    ci: str
    nombre_persona: str
    apellidos: str
    estado: EstadoAsistencia | None   # None = aún sin registrar ese día
    observacion: str | None


class ListaAsistenciaSalida(BaseModel):
    """Lista de la clase en una fecha, con lo ya registrado (si existe)."""

    clase: ClaseAsistenciaSalida
    fecha: date
    registrada: bool
    dia_con_clase: bool        # False: ese día no figura en el horario (solo aviso)
    periodo: str | None
    editable: bool             # False: periodo cerrado y el usuario no es administrador
    motivo_no_editable: str | None
    estudiantes: list[EstudianteAsistenciaSalida]


class RegistroAsistenciaEntrada(BaseModel):
    ci_estudiante: str = Field(min_length=1, max_length=20)
    estado: EstadoAsistencia
    observacion: str | None = Field(default=None, max_length=300)

    @field_validator("ci_estudiante", mode="before")
    @classmethod
    def limpiar_ci(cls, valor):
        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("observacion", mode="before")
    @classmethod
    def limpiar_observacion(cls, valor):
        if isinstance(valor, str):
            return " ".join(valor.split()) or None
        return valor


class AsistenciaGuardar(BaseModel):
    """Asistencia de toda la clase en una fecha (se guarda en una sola operación)."""

    fecha: date
    registros: list[RegistroAsistenciaEntrada] = Field(min_length=1)

    @model_validator(mode="after")
    def sin_repetidos(self):
        cis = [r.ci_estudiante for r in self.registros]
        if len(cis) != len(set(cis)):
            raise ValueError("Un estudiante aparece más de una vez en la lista.")
        return self


# ============================================================
# CU22 - CONSULTAR HISTORIAL DE ASISTENCIA
# ============================================================


class EstudianteHistorialSalida(BaseModel):
    ci: str
    nombre_persona: str
    apellidos: str
    curso: str
    estado_inscripcion: str


class EstudiantesHistorialSalida(BaseModel):
    """Estudiantes cuyo historial puede consultar el usuario (estudiante: él mismo; tutor: sus hijos)."""

    gestion: int | None
    estudiantes: list[EstudianteHistorialSalida]


class GestionHistorialSalida(BaseModel):
    id_gestion: int
    anio: int


class ConteoAsistenciaSalida(BaseModel):
    total: int                 # clases registradas
    presente: int
    ausente: int
    tardanza: int
    justificado: int
    porcentaje: float | None   # (presente + tardanza) / total * 100; None = sin registros


class MateriaHistorialSalida(ConteoAsistenciaSalida):
    id_materia: int
    materia: str


class RegistroHistorialSalida(BaseModel):
    fecha: date
    id_materia: int
    materia: str
    estado: EstadoAsistencia
    observacion: str | None


class HistorialAsistenciaSalida(BaseModel):
    """Asistencia del estudiante en una gestión: resumen general, porcentaje por materia y detalle por fecha."""

    estudiante: EstudianteHistorialSalida
    id_gestion: int
    gestion: int
    gestiones: list[GestionHistorialSalida]   # gestiones en las que estuvo inscrito
    desde: date | None
    hasta: date | None
    general: ConteoAsistenciaSalida
    materias: list[MateriaHistorialSalida]
    detalle: list[RegistroHistorialSalida]


# ============================================================
# CU24 - GENERAR Y CONSULTAR BOLETÍN/LIBRETA
# ============================================================


class NotaMateriaSalida(BaseModel):
    """Nota de una materia (de v_nota_final)."""

    id_materia: int
    materia: str
    nota_final: float
    dimensiones_registradas: int
    dimensiones_totales: int


class BoletinSalida(BaseModel):
    """Boletín completo de un estudiante en un periodo."""

    id_boletin: int
    fecha_emision_b: date
    promedio_general_b: float
    observaciones_generales_boletin: str | None
    ci: str
    nombre_persona: str
    apellidos: str
    nombre_periodo: str
    id_gestion_periodo: int
    anio: int
    id_curso_inscripcion: int | None
    nombre_curso: str | None
    notas_por_materia: list[NotaMateriaSalida]


class EmitirBoletinesSalida(BaseModel):
    """Resultado de emitir boletines."""

    cantidad: int
    periodo: str
    fecha_emision: date


class CentralizadorFilaSalida(BaseModel):
    """Una fila del centralizador: un estudiante con sus notas por materia."""

    ci: str
    nombre_persona: str
    apellidos: str
    notas: list[NotaMateriaSalida]
    promedio_estudiante: float | None


class CentralizadorSalida(BaseModel):
    """Centralizador académico: notas de un curso en un periodo."""

    curso: str
    periodo: str
    filas: list[CentralizadorFilaSalida]


class PeriodoOpcionCU24(BaseModel):
    """Opción de período para las listas desplegables del CU24."""

    id_periodo: int
    nombre_periodo: str


class CursoOpcionCU24(BaseModel):
    """Opción de curso para las listas desplegables del CU24."""

    id_curso: int
    nombre_curso: str

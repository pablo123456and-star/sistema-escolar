"""
DTO de entrada y salida (Pydantic) del paquete horarios (compartido).
"""
from datetime import time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

EstadoAula = Literal["disponible", "mantenimiento", "inactiva"]
Dia = Literal["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]


# ---- CU18: gestionar aulas -------------------------------------------------------
class AulaCrear(BaseModel):
    numero: str = Field(min_length=1, max_length=10, description="Número o identificador del aula")
    capacidad: int = Field(gt=0, description="Capacidad máxima de estudiantes (mayor a 0)")
    tipo_aula: str | None = Field(default=None, max_length=30, description="Tipo de aula (teoría, laboratorio, etc.)")
    estado_aula: EstadoAula = Field(default="disponible", description="Estado inicial del aula")


class AulaActualizar(BaseModel):
    numero: str | None = Field(default=None, min_length=1, max_length=10)
    capacidad: int | None = Field(default=None, gt=0)
    tipo_aula: str | None = Field(default=None, max_length=30)
    estado_aula: EstadoAula | None = None

    @model_validator(mode="after")
    def _algun_cambio(self):
        if not self.model_fields_set:
            raise ValueError("Indique al menos un dato a modificar.")
        return self


class AulaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_aula: int
    numero: str
    capacidad: int | None
    tipo_aula: str | None
    estado_aula: str
    total_clases_asignadas: int = 0


class HorarioCrear(BaseModel):
    """Datos para crear un bloque de horario."""
    id_asignacion: int = Field(gt=0, description="Id de la asignación profesor–materia–curso–aula")
    dia: Dia
    hora_inicio: time
    hora_final: time

    @model_validator(mode="after")
    def _horas_coherentes(self):
        if self.hora_final <= self.hora_inicio:
            raise ValueError("La hora final debe ser posterior a la hora inicial.")
        return self


class HorarioSalida(BaseModel):
    """Bloque de horario tal como lo devuelve v_horario."""
    model_config = ConfigDict(from_attributes=True)

    id_horario: int
    dia: str
    dia_orden: int
    hora_inicio: time
    hora_final: time
    id_asignacion: int
    id_gestion: int
    id_curso: int
    nombre_curso: str
    id_materia: int
    nombre_materia: str
    ci_profesor: str
    profesor: str
    id_aula: int
    aula: str


class HorarioActualizar(BaseModel):
    """Cambios de un bloque (actualización parcial). Las horas se validan juntas en el caso de uso."""
    id_asignacion: int | None = Field(default=None, gt=0)
    dia: Dia | None = None
    hora_inicio: time | None = None
    hora_final: time | None = None

    @model_validator(mode="after")
    def _algun_cambio(self):
        if not self.model_fields_set:
            raise ValueError("Indique al menos un dato a modificar.")
        return self


# ---- CU19: generar horario -------------------------------------------------------
class CursoHorarioSalida(BaseModel):
    """Curso de la gestión abierta con el avance de su horario."""
    id_curso: int
    nombre_curso: str
    id_grado: int
    nombre_grado: str
    paralelo: str
    nivel: str
    asignaciones: int
    bloques: int


class AsignacionBloqueSalida(BaseModel):
    """Asignación del curso (materia + docente + aula) que se puede poner en el horario."""
    id_asignacion: int
    id_materia: int
    nombre_materia: str
    carga_horaria: int | None
    ci_profesor: str
    profesor: str
    aula: str
    bloques: int


class HorarioCursoSalida(BaseModel):
    id_curso: int
    nombre_curso: str
    gestion: int
    asignaciones: list[AsignacionBloqueSalida]
    bloques: list[HorarioSalida]


# ---- CU20: consultar horarios ----------------------------------------------------
class CursoOpcionConsulta(BaseModel):
    id_curso: int
    nombre_curso: str


class DocenteOpcionConsulta(BaseModel):
    ci: str
    nombre: str


class EstudianteOpcionConsulta(BaseModel):
    ci: str
    nombre: str
    id_curso: int | None
    nombre_curso: str | None


class OpcionesConsultaSalida(BaseModel):
    """Qué horarios puede consultar el usuario según su rol."""
    rol: str
    gestion: int | None
    cursos: list[CursoOpcionConsulta]
    docentes: list[DocenteOpcionConsulta]
    estudiantes: list[EstudianteOpcionConsulta]


class HorarioConsultaSalida(BaseModel):
    tipo: Literal["curso", "docente"]
    titulo: str
    gestion: int
    bloques: list[HorarioSalida]

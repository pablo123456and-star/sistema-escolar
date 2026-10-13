"""
DTO de entrada y salida (Pydantic) del paquete horarios (compartido).

"""
DTO de entrada y salida (Pydantic) del paquete horarios (compartido).
"""
from datetime import time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Dia = Literal["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]


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

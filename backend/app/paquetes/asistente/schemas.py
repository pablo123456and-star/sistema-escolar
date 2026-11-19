"""Esquemas del asistente por voz (CU28)."""
from pydantic import BaseModel, Field, field_validator


class TurnoAnterior(BaseModel):
    """Pregunta y respuesta anteriores, para entender preguntas de seguimiento ("¿y el martes?")."""
    pregunta: str = Field(max_length=500)
    respuesta: str = Field(max_length=2000)


class ConsultaEntrada(BaseModel):
    pregunta: str = Field(min_length=2, max_length=500)
    historial: list[TurnoAnterior] = Field(default_factory=list, max_length=6)

    @field_validator("pregunta", mode="before")
    @classmethod
    def _limpiar(cls, v):
        return " ".join(v.split()) if isinstance(v, str) else v


class RespuestaAsistente(BaseModel):
    pregunta: str
    respuesta: str
    consultas: list[str] = Field(description="Rutas que consultó el asistente para responder")


class EstadoAsistente(BaseModel):
    habilitado: bool

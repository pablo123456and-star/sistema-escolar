"""
Esquemas comunes a todos los paquetes: respuesta paginada y mensaje simple.
"""
from typing import Annotated, Generic, TypeVar

from pydantic import AfterValidator, BaseModel, Field

T = TypeVar("T")


class Pagina(BaseModel, Generic[T]):
    items: list[T]
    total: int
    pagina: int
    tamano: int


class Mensaje(BaseModel):
    mensaje: str


def _contrasena_segura(valor: str) -> str:
    if not any(c.isalpha() for c in valor) or not any(c.isdigit() for c in valor):
        raise ValueError("La contraseña debe tener letras y números")
    return valor


# bcrypt usa como máximo 72 bytes: se limita a 64 caracteres
ContrasenaNueva = Annotated[str, Field(min_length=8, max_length=64), AfterValidator(_contrasena_segura)]

# Parámetros de paginación comunes
NumeroPagina = Annotated[int, Field(ge=1)]
TamanoPagina = Annotated[int, Field(ge=1, le=100)]

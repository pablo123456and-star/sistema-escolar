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


CARACTERES_ESPECIALES = set("!@#$%^&*()_+-=[]{}|;:,.<>?/~`'\"\\/")


def _contrasena_segura(valor: str) -> str:
    errores = []
    if len(valor) < 8:
        errores.append("mínimo 8 caracteres")
    if not any(c.isupper() for c in valor):
        errores.append("al menos una letra mayúscula")
    if not any(c.islower() for c in valor):
        errores.append("al menos una letra minúscula")
    if not any(c.isdigit() for c in valor):
        errores.append("al menos un número")
    if not any(c in CARACTERES_ESPECIALES for c in valor):
        errores.append("al menos un carácter especial (ej. !@#$%^&*)")
    if errores:
        raise ValueError(f"La contraseña debe cumplir: {', '.join(errores)}")
    return valor


# bcrypt usa como máximo 72 bytes: se limita a 64 caracteres
ContrasenaNueva = Annotated[str, Field(min_length=8, max_length=64), AfterValidator(_contrasena_segura)]

# Parámetros de paginación comunes
NumeroPagina = Annotated[int, Field(ge=1)]
TamanoPagina = Annotated[int, Field(ge=1, le=100)]

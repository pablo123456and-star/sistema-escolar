"""
DTO de entrada y salida (Pydantic) del paquete seguridad (compartido).
"""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.nucleo.esquemas import ContrasenaNueva

PATRON_USUARIO = r"^[A-Za-z0-9._-]+$"  # sin espacios ni tildes


# ---- CU01: sesión y recuperación de contraseña ------------------------------
class IniciarSesionEntrada(BaseModel):
    identificador: str = Field(min_length=1, max_length=100, description="Nombre de usuario o correo")
    contrasena: str = Field(min_length=1, max_length=64)
    recordar: bool = False


class PerfilSalida(BaseModel):
    id_usuario: int
    nombre_usuario: str
    rol: str
    ci: str
    nombres: str
    apellidos: str
    email: str | None
    cargo: str | None
    ultimo_acceso: datetime | None


class SesionSalida(BaseModel):
    token: str
    expira: datetime
    usuario: PerfilSalida


class CambiarContrasenaEntrada(BaseModel):
    actual: str = Field(min_length=1, max_length=64)
    nueva: ContrasenaNueva


class RecuperarContrasenaEntrada(BaseModel):
    identificador: str = Field(min_length=1, max_length=100, description="Nombre de usuario o correo")


class ActividadSalida(BaseModel):
    fecha_hora: datetime
    accion: str
    modulo: str | None
    nombre_usuario: str | None


class ResumenInicioSalida(BaseModel):
    usuarios_activos: int
    estudiantes_activos: int
    tutores: int
    cursos: int
    gestion: str | None
    actividades: list[ActividadSalida]


# ---- CU02: usuarios -----------------------------------------------------------
class UsuarioSalida(BaseModel):
    id_usuario: int
    nombre_usuario: str
    estado_usuario: str
    ultimo_acceso: datetime | None
    creado_en: datetime
    id_rol: int
    nombre_rol: str
    ci: str
    expedido: str | None
    nombres: str
    apellidos: str
    email: str | None


class UsuarioCrear(BaseModel):
    ci_persona: str = Field(min_length=1, max_length=20)
    id_rol: int
    nombre_usuario: str = Field(min_length=3, max_length=50, pattern=PATRON_USUARIO)
    contrasena: ContrasenaNueva


class UsuarioActualizar(BaseModel):
    nombre_usuario: str | None = Field(None, min_length=3, max_length=50, pattern=PATRON_USUARIO)
    estado_usuario: Literal["activo", "inactivo", "bloqueado"] | None = None
    id_rol: int | None = None


class PersonaSinCuentaSalida(BaseModel):
    ci: str
    nombres: str
    apellidos: str
    email: str | None


class ContrasenaTemporalSalida(BaseModel):
    contrasena_temporal: str
    mensaje: str


class SolicitudRecuperacionSalida(BaseModel):
    id_bitacora: int
    fecha_hora: datetime
    id_usuario: int
    nombre_usuario: str
    nombres: str
    apellidos: str
    ip: str | None


# ---- CU03: roles y permisos ---------------------------------------------------
class RolSalida(BaseModel):
    id_rol: int
    nombre_rol: str
    descripcion_rol: str | None
    usuarios_activos: int
    usuarios_total: int


class RolActualizar(BaseModel):
    descripcion_rol: str = Field(min_length=1, max_length=150)


class AsignarRolEntrada(BaseModel):
    id_rol: int


class PermisoSalida(BaseModel):
    paquete: str
    codigo: str
    caso_uso: str
    roles: list[str]


# ---- CU04: bitácora -----------------------------------------------------------
class BitacoraSalida(BaseModel):
    id_bitacora: int
    fecha_hora: datetime
    accion: str
    operacion: str | None
    tabla_afectada: str | None
    registro_id: str | None
    modulo: str | None
    ip: str | None
    id_usuario: int | None
    nombre_usuario: str | None
    datos_anteriores: dict[str, Any] | None
    datos_nuevos: dict[str, Any] | None


class OpcionesBitacoraSalida(BaseModel):
    modulos: list[str]
    tablas: list[str]
    operaciones: list[str]

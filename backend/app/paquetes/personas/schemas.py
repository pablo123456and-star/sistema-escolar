"""
DTO de entrada y salida (Pydantic) del paquete personas (compartido).
"""
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Expedido = Literal["LP", "CB", "SC", "OR", "PT", "CH", "TJ", "BE", "PD"]
PATRON_CI = r"^[0-9]{4,12}(-[0-9][A-Z])?$"          # ej. 1234567 o 1234567-1B
PATRON_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
PATRON_TELEFONO = r"^[0-9+ -]{6,20}$"


def _limpiar(valor):
    """Quita espacios sobrantes; una cadena vacía se guarda como NULL."""
    if isinstance(valor, str):
        valor = " ".join(valor.split())
        return valor or None
    return valor


class _Base(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def _normalizar(cls, v):
        return _limpiar(v)


# ---- Persona (datos comunes) -------------------------------------------------
class PersonaEntrada(_Base):
    ci: str = Field(pattern=PATRON_CI, description="Número de CI con complemento si tiene (1234567-1B)")
    expedido: Expedido | None = None
    nombre_persona: str = Field(min_length=2, max_length=100)
    apellidos: str = Field(min_length=2, max_length=100)
    sexo: Literal["M", "F"] | None = None
    fecha_nacimiento: date | None = None
    direccion: str | None = Field(None, max_length=150)
    telefono: str | None = Field(None, pattern=PATRON_TELEFONO)
    email: str | None = Field(None, max_length=100, pattern=PATRON_EMAIL)

    @field_validator("fecha_nacimiento")
    @classmethod
    def _no_futura(cls, v: date | None):
        if v and v > date.today():
            raise ValueError("La fecha de nacimiento no puede ser futura")
        return v


class PersonaActualizar(_Base):
    expedido: Expedido | None = None
    nombre_persona: str | None = Field(None, min_length=2, max_length=100)
    apellidos: str | None = Field(None, min_length=2, max_length=100)
    sexo: Literal["M", "F"] | None = None
    fecha_nacimiento: date | None = None
    direccion: str | None = Field(None, max_length=150)
    telefono: str | None = Field(None, pattern=PATRON_TELEFONO)
    email: str | None = Field(None, max_length=100, pattern=PATRON_EMAIL)


class PersonaSalida(BaseModel):
    ci: str
    expedido: str | None
    nombre_persona: str
    apellidos: str
    sexo: str | None
    fecha_nacimiento: date | None
    direccion: str | None
    telefono: str | None
    email: str | None
    estado_persona: str


class PersonaBuscadaSalida(PersonaSalida):
    """Persona encontrada por CI y los papeles que ya tiene en la institución."""
    es_estudiante: bool
    es_tutor: bool
    es_profesor: bool
    es_administrativo: bool


class BajaEntrada(_Base):
    motivo: str = Field(min_length=3, max_length=300)


# ---- Vínculo tutor–estudiante (CU08) -----------------------------------------
Parentesco = Field(min_length=3, max_length=30, description="Padre, Madre, Abuelo(a), Tío(a), Hermano(a), Tutor legal...")


class VinculoEntrada(_Base):
    parentesco: str = Parentesco
    es_principal: bool = False
    es_responsable_pago: bool = False
    autorizado_recoger: bool = True


class VinculoConTutorEntrada(VinculoEntrada):
    ci_tutor: str = Field(pattern=PATRON_CI)


class VinculoConEstudianteEntrada(VinculoEntrada):
    ci_estudiante: str = Field(pattern=PATRON_CI)


class VinculoActualizar(_Base):
    parentesco: str | None = Field(None, min_length=3, max_length=30)
    es_principal: bool | None = None
    es_responsable_pago: bool | None = None
    autorizado_recoger: bool | None = None


class VinculoSalida(BaseModel):
    ci_tutor: str
    ci_estudiante: str
    nombre_tutor: str
    nombre_estudiante: str
    telefono_tutor: str | None
    parentesco: str
    es_principal: bool
    es_responsable_pago: bool
    autorizado_recoger: bool
    estado_estudiante: str
    curso_estudiante: str | None


# ---- Estudiante (CU06) --------------------------------------------------------
class EstudianteCrear(_Base):
    persona: PersonaEntrada
    rude: str | None = Field(None, min_length=4, max_length=20)
    antecedentes_academicos: str | None = Field(None, max_length=1000)
    tutor: VinculoConTutorEntrada | None = None
    id_curso: int | None = Field(None, description="Si se indica, se inscribe en la gestión abierta")


class EstudianteActualizar(_Base):
    persona: PersonaActualizar | None = None
    rude: str | None = Field(None, min_length=4, max_length=20)
    antecedentes_academicos: str | None = Field(None, max_length=1000)


class EstudianteSalida(BaseModel):
    ci: str
    expedido: str | None
    nombre_persona: str
    apellidos: str
    sexo: str | None
    fecha_nacimiento: date | None
    rude: str | None
    estado_persona: str
    id_curso: int | None
    curso: str | None
    grado: str | None
    paralelo: str | None
    nivel: str | None
    tutor_principal: str | None


class InscripcionActualSalida(BaseModel):
    id_inscripcion: int
    gestion: int
    curso: str
    estado_inscripcion: str
    fecha_inscripcion: date


class EstudianteDetalleSalida(PersonaSalida):
    rude: str | None
    antecedentes_academicos: str | None
    inscripcion: InscripcionActualSalida | None
    tutores: list[VinculoSalida]
    tiene_usuario: bool


class CursoOpcion(BaseModel):
    id_curso: int
    nombre_curso: str
    id_grado: int
    nombre_grado: str
    paralelo: str
    nivel: str
    cupo_maximo: int
    inscritos: int


class OpcionesEstudianteSalida(BaseModel):
    gestion: int | None
    cursos: list[CursoOpcion]
    paralelos: list[str]


# ---- Tutor (CU08) ---------------------------------------------------------------
class TutorCrear(_Base):
    persona: PersonaEntrada
    ocupacion: str | None = Field(None, max_length=50)


class TutorActualizar(_Base):
    persona: PersonaActualizar | None = None
    ocupacion: str | None = Field(None, max_length=50)


class TutorSalida(BaseModel):
    ci: str
    expedido: str | None
    nombre_persona: str
    apellidos: str
    telefono: str | None
    email: str | None
    ocupacion: str | None
    estado_persona: str
    cantidad_estudiantes: int


class TutorDetalleSalida(PersonaSalida):
    ocupacion: str | None
    estudiantes: list[VinculoSalida]
    tiene_usuario: bool


# ---- Docente (CU10) -------------------------------------------------------------
class DocenteCrear(_Base):
    persona: PersonaEntrada
    titulo_academico: str | None = Field(None, max_length=100)
    fecha_contrato: date | None = None
    antecedentes_laborales: str | None = Field(None, max_length=1000)
    anios_experiencia: int | None = Field(None, ge=0, le=60)


class DocenteActualizar(_Base):
    persona: PersonaActualizar | None = None
    titulo_academico: str | None = Field(None, max_length=100)
    fecha_contrato: date | None = None
    antecedentes_laborales: str | None = Field(None, max_length=1000)
    anios_experiencia: int | None = Field(None, ge=0, le=60)


class DocenteSalida(BaseModel):
    ci: str
    expedido: str | None
    nombre_persona: str
    apellidos: str
    sexo: str | None
    telefono: str | None
    email: str | None
    titulo_academico: str | None
    anios_experiencia: int | None
    estado_persona: str
    cantidad_asignaciones: int


class AsignacionDocenteSalida(BaseModel):
    id_asignacion: int
    materia: str
    curso: str
    aula: str


class DocenteDetalleSalida(PersonaSalida):
    titulo_academico: str | None
    fecha_contrato: date | None
    antecedentes_laborales: str | None
    anios_experiencia: int | None
    gestion: int | None
    asignaciones: list[AsignacionDocenteSalida]
    tiene_usuario: bool


# ---- Administrativo (CU11) ------------------------------------------------------
class AdministrativoCrear(_Base):
    persona: PersonaEntrada
    cargo: str | None = Field(None, max_length=50)


class AdministrativoActualizar(_Base):
    persona: PersonaActualizar | None = None
    cargo: str | None = Field(None, max_length=50)


class AdministrativoSalida(BaseModel):
    ci: str
    expedido: str | None
    nombre_persona: str
    apellidos: str
    sexo: str | None
    telefono: str | None
    email: str | None
    cargo: str | None
    estado_persona: str


class AdministrativoDetalleSalida(PersonaSalida):
    cargo: str | None
    tiene_usuario: bool


# ---- CU07: antecedentes médicos y seguimiento ----------------------------------------
TipoSeguimiento = Literal["conducta", "academico", "salud", "merito", "otro"]
Gravedad = Literal["leve", "grave", "muy_grave"]


def _texto_largo(valor):
    """Como _limpiar, pero conserva los saltos de línea (párrafos) de los textos largos."""
    if isinstance(valor, str):
        lineas = [" ".join(linea.split()) for linea in valor.strip().splitlines()]
        valor = "\n".join(lineas).strip()
        while "\n\n\n" in valor:
            valor = valor.replace("\n\n\n", "\n\n")
        return valor or None
    return valor


class _BaseTexto(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def _normalizar(cls, v):
        return _texto_largo(v)


class AntecedentesActualizar(_BaseTexto):
    observacion_medica: str | None = Field(
        None, max_length=1000, description="Alergias, enfermedades, medicación... (vacío = sin observaciones)"
    )


class SeguimientoCrear(_BaseTexto):
    tipo: TipoSeguimiento
    gravedad: Gravedad | None = Field(None, description="Obligatoria solo para conducta")
    fecha: date | None = Field(None, description="Por defecto, hoy. No puede ser futura")
    descripcion: str = Field(min_length=5, max_length=2000)
    accion_tomada: str | None = Field(None, max_length=1000)


class SeguimientoSalida(BaseModel):
    id_seguimiento: int
    fecha: date
    tipo: TipoSeguimiento
    gravedad: Gravedad | None
    descripcion: str
    accion_tomada: str | None
    registrado_por: str
    rol_registrado_por: str | None
    es_mio: bool


class EstudianteSeguimientoSalida(BaseModel):
    """Fila de la lista de estudiantes que el usuario puede consultar en el CU07."""
    ci: str
    nombre_persona: str
    apellidos: str
    sexo: str | None
    estado_persona: str
    curso: str | None
    tiene_observacion_medica: bool
    cantidad_seguimientos: int
    ultimo_seguimiento: date | None


class FichaSeguimientoSalida(BaseModel):
    ci: str
    expedido: str | None
    nombre_persona: str
    apellidos: str
    sexo: str | None
    fecha_nacimiento: date | None
    rude: str | None
    estado_persona: str
    curso: str | None
    gestion: int | None
    observacion_medica: str | None
    antecedentes_academicos: str | None
    puede_editar_antecedentes: bool
    puede_registrar_seguimiento: bool
    seguimientos: list[SeguimientoSalida]


# ============================================================
# CU05 - REGISTRAR Y ACTUALIZAR DATOS DE PERSONA
# ============================================================
class PersonaListaSalida(BaseModel):
    """Fila del buscador de personas: datos básicos, roles y cuenta de usuario."""
    ci: str
    expedido: str | None
    nombre_persona: str
    apellidos: str
    sexo: str | None
    telefono: str | None
    email: str | None
    estado_persona: str
    es_estudiante: bool
    es_tutor: bool
    es_profesor: bool
    es_administrativo: bool
    nombre_usuario: str | None
    estado_usuario: str | None


class UsuarioPersonaSalida(BaseModel):
    """Cuenta de usuario de la persona (nunca la contraseña ni su hash)."""
    nombre_usuario: str
    rol: str
    estado_usuario: str


class PersonaFichaSalida(PersonaBuscadaSalida):
    usuario: UsuarioPersonaSalida | None
    inscripcion: InscripcionActualSalida | None
    es_usuario_actual: bool

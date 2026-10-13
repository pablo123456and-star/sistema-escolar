"""
DTO de entrada y salida (Pydantic) del paquete academico (compartido).

PENDIENTE.
"""
# ============================================================
# CU13 - GESTIONAR MATERIAS Y PLAN DE ESTUDIOS
# ============================================================

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# MATERIAS

class MateriaCrear(BaseModel):
    """Datos necesarios para registrar una materia."""

    nombre_materia: str = Field(
        min_length=1,
        max_length=100
    )

    carga_horaria: int = Field(gt=0)

    @field_validator("nombre_materia", mode="before")
    @classmethod
    def limpiar_nombre(cls, valor):
        if isinstance(valor, str):
            return " ".join(valor.split())
        return valor


class MateriaActualizar(BaseModel):
    """Datos que pueden modificarse de una materia."""

    nombre_materia: str | None = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    carga_horaria: int | None = Field(
        default=None,
        gt=0
    )

    @field_validator("nombre_materia", mode="before")
    @classmethod
    def limpiar_nombre(cls, valor):
        if isinstance(valor, str):
            return " ".join(valor.split())
        return valor

    @model_validator(mode="after")
    def validar_cambios(self):
        if self.nombre_materia is None and self.carga_horaria is None:
            raise ValueError("Debes proporcionar al menos un dato para modificar.")
        return self


class MateriaSalida(BaseModel):
    """Información de una materia registrada."""

    model_config = ConfigDict(from_attributes=True)

    id_materia: int
    nombre_materia: str
    carga_horaria: int | None


# NIVELES EDUCATIVOS

class NivelEducativoSalida(BaseModel):
    """Información de un nivel educativo."""

    model_config = ConfigDict(from_attributes=True)

    id_nivel: int
    nombre_nivel: str


# GRADOS

class GradoSalida(BaseModel):
    """Información de un grado."""

    model_config = ConfigDict(from_attributes=True)

    id_grado: int
    nombre_grado: str
    orden_grado: int
    id_nivel_educativo_grado: int


class OpcionesPlanSalida(BaseModel):
    """Niveles y grados disponibles para los selectores."""

    niveles: list[NivelEducativoSalida]
    grados: list[GradoSalida]


# PLAN DE ESTUDIOS

class MateriaPlanEntrada(BaseModel):
    """Materia que se agregará al plan de un grado."""

    id_materia: int = Field(gt=0)


class PlanEstudiosSalida(BaseModel):
    """Materias asignadas y disponibles para un grado."""

    id_grado: int
    nombre_grado: str

    materias_plan: list[MateriaSalida]
    materias_disponibles: list[MateriaSalida]

# ============================================================
# CU14 - ASIGNAR PROFESOR A MATERIA/CURSO
# ============================================================


# ------------------------------------------------------------
# 1. CURSOS DISPONIBLES
# ------------------------------------------------------------

class CursoOpcionAsignacion(BaseModel):
    """Curso que puede seleccionarse para asignar profesores."""

    id_curso: int
    nombre_curso: str
    id_grado: int
    nombre_grado: str
    paralelo: str


# ------------------------------------------------------------
# 2. PROFESORES DISPONIBLES
# ------------------------------------------------------------

class ProfesorOpcionAsignacion(BaseModel):
    """Profesor activo disponible para una asignación."""

    ci_profesor: str
    nombre_profesor: str


# ------------------------------------------------------------
# 3. AULAS DISPONIBLES
# ------------------------------------------------------------

class AulaOpcionAsignacion(BaseModel):
    """Aula disponible para asignar una materia."""

    id_aula: int
    numero: str
    capacidad: int | None = None
    tipo_aula: str | None = None


# ------------------------------------------------------------
# 4. OPCIONES PARA REALIZAR ASIGNACIONES
# ------------------------------------------------------------

class OpcionesAsignacionSalida(BaseModel):
    """Opciones necesarias para los selectores del CU14."""

    id_gestion: int | None
    anio_gestion: int | None

    cursos: list[CursoOpcionAsignacion]
    profesores: list[ProfesorOpcionAsignacion]
    aulas: list[AulaOpcionAsignacion]


# ------------------------------------------------------------
# 5. MATERIAS DEL CURSO
# ------------------------------------------------------------

class MateriaCursoAsignacionSalida(BaseModel):
    """Materia del curso con su asignación actual, si existe."""

    id_materia: int
    nombre_materia: str
    carga_horaria: int | None

    id_asignacion: int | None = None

    ci_profesor: str | None = None
    nombre_profesor: str | None = None

    id_aula: int | None = None
    numero_aula: str | None = None


class MateriasCursoAsignacionSalida(BaseModel):
    """Materias y asignaciones de un curso."""

    id_curso: int
    nombre_curso: str

    id_gestion: int
    anio_gestion: int

    materias: list[MateriaCursoAsignacionSalida]


# ------------------------------------------------------------
# 6. REGISTRAR UNA ASIGNACIÓN
# ------------------------------------------------------------

class AsignacionCrear(BaseModel):
    """Datos necesarios para asignar profesor y aula."""

    id_curso: int = Field(gt=0)

    id_materia: int = Field(gt=0)

    ci_profesor: str = Field(
        min_length=1,
        max_length=20
    )

    id_aula: int = Field(gt=0)

    @field_validator("ci_profesor", mode="before")
    @classmethod
    def limpiar_ci_profesor(cls, valor):
        if isinstance(valor, str):
            return valor.strip()
        return valor


# ------------------------------------------------------------
# 7. MODIFICAR UNA ASIGNACIÓN
# ------------------------------------------------------------

class AsignacionActualizar(BaseModel):
    """Permite modificar el profesor o el aula."""

    ci_profesor: str | None = Field(
        default=None,
        min_length=1,
        max_length=20
    )

    id_aula: int | None = Field(
        default=None,
        gt=0
    )

    @field_validator("ci_profesor", mode="before")
    @classmethod
    def limpiar_ci_profesor(cls, valor):
        if isinstance(valor, str):
            return valor.strip()
        return valor

    @model_validator(mode="after")
    def validar_cambios(self):

        if self.ci_profesor is None and self.id_aula is None:
            raise ValueError(
                "Debes proporcionar un profesor o un aula "
                "para modificar la asignación."
            )

        return self


# ------------------------------------------------------------
# 8. RESPUESTA DE UNA ASIGNACIÓN
# ------------------------------------------------------------

class AsignacionSalida(BaseModel):
    """Información de la asignación registrada."""

    model_config = ConfigDict(from_attributes=True)

    id_asignacion: int

    ci_profesor_asignacion: str

    id_materia_asignacion: int

    id_curso_asignacion: int

    id_aula_asignacion: int

    id_gestion_asignacion: int

# ============================================================
# CU16 - INSCRIBIR ESTUDIANTE EN GESTIÓN ACADÉMICA
# ============================================================

from datetime import date, time


class EstudianteInscripcionSalida(BaseModel):
    """Estudiante encontrado, con su inscripción en la gestión abierta (si tiene)."""

    ci: str
    expedido: str | None
    nombre_persona: str
    apellidos: str
    rude: str | None
    estado_persona: str
    id_inscripcion: int | None
    estado_inscripcion: str | None
    curso: str | None


class InscripcionCrear(BaseModel):
    ci_estudiante: str = Field(min_length=1, max_length=20)
    id_curso: int = Field(gt=0)

    @field_validator("ci_estudiante", mode="before")
    @classmethod
    def limpiar_ci(cls, valor):
        return valor.strip() if isinstance(valor, str) else valor


class MateriaBoletaSalida(BaseModel):
    materia: str
    carga_horaria: int | None
    docente: str | None
    aula: str | None


class BloqueBoletaSalida(BaseModel):
    dia: str
    hora_inicio: time
    hora_final: time
    materia: str
    docente: str
    aula: str


class BoletaSalida(BaseModel):
    """Boleta de inscripción: estudiante, gestión, curso, materias y horario semanal."""

    id_inscripcion: int
    fecha_inscripcion: date
    estado_inscripcion: str
    ci: str
    expedido: str | None
    nombre_persona: str
    apellidos: str
    fecha_nacimiento: date | None
    rude: str | None
    gestion: int
    curso: str
    grado: str
    paralelo: str
    nivel: str
    materias: list[MateriaBoletaSalida]
    horario: list[BloqueBoletaSalida]

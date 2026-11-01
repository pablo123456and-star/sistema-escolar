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

# ============================================================
# CU12 - GESTIONAR NIVELES EDUCATIVOS Y CURSOS
# ============================================================


def _limpiar_texto(valor):
    """Quita espacios repetidos y en los extremos."""
    return " ".join(valor.split()) if isinstance(valor, str) else valor


def _limpiar_paralelo(valor):
    """El paralelo se guarda sin espacios y en mayúsculas ("a" -> "A")."""
    return valor.strip().upper() if isinstance(valor, str) else valor


class NivelEntrada(BaseModel):
    """Datos para registrar o renombrar un nivel educativo."""

    nombre_nivel: str = Field(min_length=1, max_length=50)

    limpiar_nombre = field_validator("nombre_nivel", mode="before")(_limpiar_texto)


class GradoCrear(BaseModel):
    """Datos para registrar un grado dentro de un nivel."""

    id_nivel: int = Field(gt=0)
    nombre_grado: str = Field(min_length=1, max_length=50)
    orden_grado: int = Field(gt=0, le=99)

    limpiar_nombre = field_validator("nombre_grado", mode="before")(_limpiar_texto)


class GradoActualizar(BaseModel):
    """Datos que pueden modificarse de un grado (el nivel no cambia)."""

    nombre_grado: str | None = Field(default=None, min_length=1, max_length=50)
    orden_grado: int | None = Field(default=None, gt=0, le=99)

    limpiar_nombre = field_validator("nombre_grado", mode="before")(_limpiar_texto)

    @model_validator(mode="after")
    def validar_cambios(self):
        if self.nombre_grado is None and self.orden_grado is None:
            raise ValueError("Debe indicar el nombre o el orden del grado.")
        return self


class CursoCrear(BaseModel):
    """Datos para registrar un paralelo de un grado."""

    id_grado: int = Field(gt=0)
    paralelo: str = Field(min_length=1, max_length=5, pattern=r"^[A-Z0-9]+$")
    cupo_maximo: int = Field(gt=0, le=100)

    limpiar_paralelo = field_validator("paralelo", mode="before")(_limpiar_paralelo)


class CursoActualizar(BaseModel):
    """Datos que pueden modificarse de un paralelo (el grado no cambia)."""

    paralelo: str | None = Field(default=None, min_length=1, max_length=5, pattern=r"^[A-Z0-9]+$")
    cupo_maximo: int | None = Field(default=None, gt=0, le=100)

    limpiar_paralelo = field_validator("paralelo", mode="before")(_limpiar_paralelo)

    @model_validator(mode="after")
    def validar_cambios(self):
        if self.paralelo is None and self.cupo_maximo is None:
            raise ValueError("Debe indicar el paralelo o el cupo.")
        return self


class CursoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_curso: int
    paralelo: str
    cupo_maximo: int
    id_grado_curso: int


class CursoEstructuraSalida(BaseModel):
    """Paralelo con sus inscritos activos en la gestión abierta."""

    id_curso: int
    paralelo: str
    cupo_maximo: int
    inscritos: int


class GradoEstructuraSalida(BaseModel):
    id_grado: int
    nombre_grado: str
    orden_grado: int
    materias: int
    cursos: list[CursoEstructuraSalida]


class NivelEstructuraSalida(BaseModel):
    id_nivel: int
    nombre_nivel: str
    grados: list[GradoEstructuraSalida]


class EstructuraSalida(BaseModel):
    """Niveles -> grados -> paralelos. Los inscritos son de la gestión abierta (si hay)."""

    gestion: int | None
    niveles: list[NivelEstructuraSalida]


# ============================================================
# CU15 - GESTIONAR GESTIÓN ACADÉMICA (AÑO LECTIVO)
# ============================================================

from datetime import date as _date
from decimal import Decimal as _Decimal
from typing import Literal as _Literal


class GestionCrear(BaseModel):
    anio: int = Field(ge=2000, le=2100)
    fecha_inicio_g: _date
    fecha_final_g: _date
    nota_minima_aprobacion: _Decimal = Field(default=_Decimal("51"), ge=0, le=100)

    @model_validator(mode="after")
    def validar_fechas(self):
        if self.fecha_final_g <= self.fecha_inicio_g:
            raise ValueError("La fecha final debe ser posterior a la fecha de inicio.")
        if self.fecha_inicio_g.year != self.anio:
            raise ValueError("El año debe coincidir con el año de la fecha de inicio.")
        return self


class GestionActualizar(BaseModel):
    anio: int | None = Field(default=None, ge=2000, le=2100)
    fecha_inicio_g: _date | None = None
    fecha_final_g: _date | None = None
    nota_minima_aprobacion: _Decimal | None = Field(default=None, ge=0, le=100)


class GestionSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_gestion: int
    anio: int
    fecha_inicio_g: _date
    fecha_final_g: _date
    nota_minima_aprobacion: _Decimal
    estado_gestion: str
    periodos: int = 0
    inscritos: int = 0


class PeriodoCrear(BaseModel):
    nombre_periodo: str = Field(min_length=1, max_length=50)
    tipo: _Literal["trimestre", "bimestre", "semestre"] | None = None
    fecha_inicio_p: _date
    fecha_final_p: _date
    observaciones_periodo: str | None = Field(default=None, max_length=500)

    @field_validator("nombre_periodo", mode="before")
    @classmethod
    def limpiar_nombre_periodo(cls, valor):
        return " ".join(valor.split()) if isinstance(valor, str) else valor

    @model_validator(mode="after")
    def validar_fechas(self):
        if self.fecha_final_p <= self.fecha_inicio_p:
            raise ValueError("La fecha final del periodo debe ser posterior a la de inicio.")
        return self


class PeriodoActualizar(BaseModel):
    nombre_periodo: str | None = Field(default=None, min_length=1, max_length=50)
    tipo: _Literal["trimestre", "bimestre", "semestre"] | None = None
    fecha_inicio_p: _date | None = None
    fecha_final_p: _date | None = None
    observaciones_periodo: str | None = Field(default=None, max_length=500)

    @field_validator("nombre_periodo", "fecha_inicio_p", "fecha_final_p", mode="before")
    @classmethod
    def no_nulo(cls, valor, info):
        # Omitir el campo deja el valor actual; enviarlo vacío (null) no se permite: son obligatorios en la BD.
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            raise ValueError(f"{info.field_name} no puede quedar vacío.")
        if info.field_name == "nombre_periodo":
            return " ".join(valor.split())
        return valor


class PeriodoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_periodo: int
    nombre_periodo: str
    tipo: str | None
    fecha_inicio_p: _date
    fecha_final_p: _date
    estado_periodo: str
    observaciones_periodo: str | None
    id_gestion_periodo: int


class DimensionEntrada(BaseModel):
    nombre_dimension: str = Field(min_length=1, max_length=30)
    puntaje_maximo: _Decimal = Field(gt=0, le=100)
    es_autoevaluacion: bool = False

    @field_validator("nombre_dimension", mode="before")
    @classmethod
    def limpiar_nombre_dimension(cls, valor):
        return " ".join(valor.split()) if isinstance(valor, str) else valor


class DimensionesGuardar(BaseModel):
    """Reemplaza todas las dimensiones de la gestión; el orden de la lista es el orden de la dimensión."""

    dimensiones: list[DimensionEntrada] = Field(min_length=1, max_length=10)

    @model_validator(mode="after")
    def validar_lista(self):
        nombres = [d.nombre_dimension.lower() for d in self.dimensiones]
        if len(set(nombres)) != len(nombres):
            raise ValueError("Los nombres de las dimensiones no pueden repetirse.")
        if sum(d.es_autoevaluacion for d in self.dimensiones) > 1:
            raise ValueError("Solo una dimensión puede ser la autoevaluación.")
        return self


class DimensionSalida(BaseModel):
    id_dimension: int
    nombre_dimension: str
    puntaje_maximo: _Decimal
    es_autoevaluacion: bool
    orden_dimension: int


class DimensionesSalida(BaseModel):
    dimensiones: list[DimensionSalida]
    suma_puntajes: _Decimal
    completa: bool


class ResumenGestionSalida(BaseModel):
    id_gestion: int
    anio: int
    inscritos_activos: int
    retirados: int
    finalizados: int
    promedio_general: _Decimal | None
    total_cobrado: _Decimal
    total_vencido: _Decimal


class CierreGestionSalida(BaseModel):
    id_gestion: int
    promovidos: int
    reprobados: int


# ============================================================
# CU17 - CONSULTAR HISTORIAL DE INSCRIPCIONES
# ============================================================

from datetime import date
from typing import Literal

class EstudianteHistorialItem(BaseModel):
    ci: str
    nombre_completo: str
    nombre_persona: str
    apellidos: str
    codigo_rude: str | None = None
    curso_actual: str | None = None


class HistorialInscripcionItem(BaseModel):
    id_inscripcion: int
    id_gestion: int
    anio: int
    curso: str
    estado_inscripcion: Literal["activa", "retirada", "finalizada"]
    fecha_inscripcion: date
    fecha_retiro: date | None = None
    motivo_retiro: str | None = None
    resultado_final: Literal["promovido", "reprobado"] | None = None
    promedio_anual: _Decimal | None = None


class HistorialEstudianteSalida(BaseModel):
    ci: str
    nombre_completo: str
    codigo_rude: str | None = None
    inscripciones: list[HistorialInscripcionItem]


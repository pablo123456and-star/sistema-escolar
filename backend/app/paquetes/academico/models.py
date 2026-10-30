"""
Modelos SQLAlchemy (ORM) del paquete academico (compartido).

Tablas (lectura y escritura): nivel_educativo, grado, curso, materia, materia_grado, asignacion_profesor_clase, gestion, periodo, dimension_evaluacion, inscripcion.
Vistas (solo lectura): v_curso.

Gestion, curso e inscripcion los usa también el CU06 para inscribir al
estudiante en el mismo paso. Nivel, grado y curso los administra el CU12.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.bd import Base


class Gestion(Base):
    __tablename__ = "gestion"

    id_gestion: Mapped[int] = mapped_column(Integer, primary_key=True)
    anio: Mapped[int]
    fecha_inicio_g: Mapped[date]
    fecha_final_g: Mapped[date]
    nota_minima_aprobacion: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    estado_gestion: Mapped[str] = mapped_column(String(20))


class Curso(Base):
    __tablename__ = "curso"

    id_curso: Mapped[int] = mapped_column(Integer, primary_key=True)
    paralelo: Mapped[str] = mapped_column(String(5))
    cupo_maximo: Mapped[int]
    id_grado_curso: Mapped[int] = mapped_column(ForeignKey("grado.id_grado"))


class Inscripcion(Base):
    __tablename__ = "inscripcion"

    id_inscripcion: Mapped[int] = mapped_column(Integer, primary_key=True)
    fecha_inscripcion: Mapped[date] = mapped_column(server_default="CURRENT_DATE")
    estado_inscripcion: Mapped[str] = mapped_column(String(20), server_default="activa")
    fecha_retiro: Mapped[date | None]
    motivo_retiro: Mapped[str | None] = mapped_column(Text)
    resultado_final: Mapped[str | None] = mapped_column(String(20))
    ci_estudiante_inscripcion: Mapped[str] = mapped_column(ForeignKey("estudiante.ci_estudiante"))
    id_gestion_inscripcion: Mapped[int] = mapped_column(ForeignKey("gestion.id_gestion"))
    id_curso_inscripcion: Mapped[int] = mapped_column(ForeignKey("curso.id_curso"))
    creado_en: Mapped[datetime] = mapped_column(server_default="now()")
    actualizado_en: Mapped[datetime] = mapped_column(server_default="now()")


# ============================================================
# CU13 - GESTIONAR MATERIAS Y PLAN DE ESTUDIOS
# ============================================================

from sqlalchemy import SmallInteger


# Modelo de niveles educativos
class NivelEducativo(Base):
    __tablename__ = "nivel_educativo"

    id_nivel: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_nivel: Mapped[str] = mapped_column(String(50), nullable=False)


# Modelo de grados
class Grado(Base):
    __tablename__ = "grado"

    id_grado: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_grado: Mapped[str] = mapped_column(String(50), nullable=False)
    orden_grado: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    id_nivel_educativo_grado: Mapped[int] = mapped_column(ForeignKey("nivel_educativo.id_nivel"), nullable=False)


# Modelo de materias
class Materia(Base):
    __tablename__ = "materia"

    id_materia: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_materia: Mapped[str] = mapped_column(String(100), nullable=False)
    carga_horaria: Mapped[int | None] = mapped_column(Integer)


# Modelo del plan de estudios
class MateriaGrado(Base):
    __tablename__ = "materia_grado"

    id_grado_mg: Mapped[int] = mapped_column(ForeignKey("grado.id_grado", ondelete="CASCADE"), primary_key=True)
    id_materia_mg: Mapped[int] = mapped_column(ForeignKey("materia.id_materia", ondelete="CASCADE"), primary_key=True)

# ============================================================
# CU14 - ASIGNAR PROFESOR A MATERIA/CURSO
# ============================================================

from sqlalchemy import DateTime, func


class AsignacionProfesorClase(Base):
    """Representa la asignación de un profesor a una materia y curso."""

    __tablename__ = "asignacion_profesor_clase"

    id_asignacion: Mapped[int] = mapped_column(Integer, primary_key=True)
    ci_profesor_asignacion: Mapped[str] = mapped_column(ForeignKey("profesor.ci_profesor", onupdate="CASCADE"), nullable=False)
    id_materia_asignacion: Mapped[int] = mapped_column(ForeignKey("materia.id_materia"), nullable=False)
    id_curso_asignacion: Mapped[int] = mapped_column(ForeignKey("curso.id_curso"), nullable=False)
    id_aula_asignacion: Mapped[int] = mapped_column(Integer, nullable=False)
    id_gestion_asignacion: Mapped[int] = mapped_column(ForeignKey("gestion.id_gestion"), nullable=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

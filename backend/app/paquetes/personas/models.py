"""
Modelos SQLAlchemy (ORM) del paquete personas (compartido).

Tablas (lectura y escritura): persona, estudiante, tutor, tutor_estudiante,
profesor, administrativo. (seguimiento_estudiante se agrega con el CU07.)
"""
from datetime import date, datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.bd import Base


class Persona(Base):
    __tablename__ = "persona"

    ci: Mapped[str] = mapped_column(String(20), primary_key=True)
    expedido: Mapped[str | None] = mapped_column(String(2))
    nombre_persona: Mapped[str] = mapped_column(String(100))
    apellidos: Mapped[str] = mapped_column(String(100))
    sexo: Mapped[str | None] = mapped_column(String(1))
    fecha_nacimiento: Mapped[date | None]
    direccion: Mapped[str | None] = mapped_column(String(150))
    telefono: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(100))
    estado_persona: Mapped[str] = mapped_column(String(20), server_default="activo")
    creado_en: Mapped[datetime] = mapped_column(server_default="now()")
    actualizado_en: Mapped[datetime] = mapped_column(server_default="now()")


class Estudiante(Base):
    __tablename__ = "estudiante"

    ci_estudiante: Mapped[str] = mapped_column(ForeignKey("persona.ci"), primary_key=True)
    rude: Mapped[str | None] = mapped_column(String(20))
    observacion_medica: Mapped[str | None] = mapped_column(Text)
    antecedentes_academicos: Mapped[str | None] = mapped_column(Text)


class Tutor(Base):
    __tablename__ = "tutor"

    ci_tutor: Mapped[str] = mapped_column(ForeignKey("persona.ci"), primary_key=True)
    ocupacion: Mapped[str | None] = mapped_column(String(50))


class TutorEstudiante(Base):
    __tablename__ = "tutor_estudiante"

    ci_tutor_tutorestudiante: Mapped[str] = mapped_column(ForeignKey("tutor.ci_tutor"), primary_key=True)
    ci_estudiante_tutorestudiante: Mapped[str] = mapped_column(
        ForeignKey("estudiante.ci_estudiante"), primary_key=True
    )
    parentesco: Mapped[str] = mapped_column(String(30))
    es_principal: Mapped[bool] = mapped_column(Boolean, default=False)
    es_responsable_pago: Mapped[bool] = mapped_column(Boolean, default=False)
    autorizado_recoger: Mapped[bool] = mapped_column(Boolean, default=True)


class Profesor(Base):
    __tablename__ = "profesor"

    ci_profesor: Mapped[str] = mapped_column(ForeignKey("persona.ci"), primary_key=True)
    titulo_academico: Mapped[str | None] = mapped_column(String(100))
    fecha_contrato: Mapped[date | None]
    antecedentes_laborales: Mapped[str | None] = mapped_column(Text)
    anios_experiencia: Mapped[int | None] = mapped_column(Integer)


class Administrativo(Base):
    __tablename__ = "administrativo"

    ci_administrativo: Mapped[str] = mapped_column(ForeignKey("persona.ci"), primary_key=True)
    cargo: Mapped[str | None] = mapped_column(String(50))

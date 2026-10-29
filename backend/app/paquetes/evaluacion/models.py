"""
Modelos SQLAlchemy (ORM) del paquete evaluacion (compartido).

Tablas (lectura y escritura): asistencia, calificacion, calificacion_detalle, boletin, libreta.
Vistas (solo lectura): v_nota_final.

Implementado por ahora: asistencia (CU21). El resto se agrega con los CU22-CU24.
"""
from datetime import date

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.bd import Base


class Asistencia(Base):
    """Un registro por estudiante, clase (asignación) y día (UNIQUE en la BD)."""

    __tablename__ = "asistencia"

    id_asistencia: Mapped[int] = mapped_column(Integer, primary_key=True)
    fecha_asistencia: Mapped[date] = mapped_column(server_default="CURRENT_DATE")
    estado_asistencia: Mapped[str] = mapped_column(String(20))
    observacion_asistencia: Mapped[str | None] = mapped_column(Text)
    id_asignacion_asistencia: Mapped[int] = mapped_column(ForeignKey("asignacion_profesor_clase.id_asignacion"))
    ci_estudiante_asistencia: Mapped[str] = mapped_column(ForeignKey("estudiante.ci_estudiante"))

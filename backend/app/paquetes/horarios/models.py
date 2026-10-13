"""
Modelos SQLAlchemy (ORM) del paquete horarios (compartido).

Tablas (lectura y escritura): aula, horario.
Vistas (solo lectura): v_horario.

"""
Modelos SQLAlchemy (ORM) del paquete horarios (compartido).

Tablas (lectura y escritura): aula, horario, asignacion_profesor_clase.
Vistas (solo lectura): v_horario.
"""
from datetime import time

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.bd import Base


class Aula(Base):
    __tablename__ = "aula"

    id_aula: Mapped[int] = mapped_column(Integer, primary_key=True)
    numero: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    capacidad: Mapped[int | None] = mapped_column(Integer)
    tipo_aula: Mapped[str | None] = mapped_column(String(30))
    estado_aula: Mapped[str] = mapped_column(String(20), nullable=False, default="disponible")


class Horario(Base):
    __tablename__ = "horario"
    __table_args__ = (
        CheckConstraint("hora_final_f > hora_inicio_h", name="horario_check"),
        CheckConstraint(
            "dia IN ('lunes','martes','miercoles','jueves','viernes','sabado','domingo')",
            name="horario_dia_check",
        ),
    )

    id_horario: Mapped[int] = mapped_column(Integer, primary_key=True)
    dia: Mapped[str] = mapped_column(String(10), nullable=False)
    hora_inicio_h: Mapped[time] = mapped_column(Time, nullable=False)
    hora_final_f: Mapped[time] = mapped_column(Time, nullable=False)
    id_asignacion_horario: Mapped[int] = mapped_column(
        ForeignKey("asignacion_profesor_clase.id_asignacion", ondelete="CASCADE"), nullable=False
    )

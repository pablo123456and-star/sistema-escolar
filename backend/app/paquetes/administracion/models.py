"""
Modelos SQLAlchemy (ORM) del paquete administracion (compartido).

Tablas (lectura y escritura): arancel, beca, pago_mensualidad, inventario, movimiento_inventario, comunicado, comunicado_lectura.
Vistas (solo lectura): v_estado_pagos.

Implementado por ahora: arancel, beca y pago_mensualidad (CU25). El resto se agrega con los CU26 y CU27.
"""
# ============================================================
# CU25 - REGISTRAR PAGO DE MENSUALIDAD
# ============================================================

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.bd import Base


class Arancel(Base):
    """Monto mensual de un nivel en una gestión (UNIQUE gestión + nivel en la BD)."""

    __tablename__ = "arancel"

    id_arancel: Mapped[int] = mapped_column(Integer, primary_key=True)
    monto_mensual: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    dia_vencimiento: Mapped[int] = mapped_column(SmallInteger)
    id_gestion_arancel: Mapped[int] = mapped_column(ForeignKey("gestion.id_gestion"))
    id_nivel_arancel: Mapped[int] = mapped_column(ForeignKey("nivel_educativo.id_nivel"))


class Beca(Base):
    """Descuento de un estudiante en una gestión (UNIQUE estudiante + gestión en la BD)."""

    __tablename__ = "beca"

    id_beca: Mapped[int] = mapped_column(Integer, primary_key=True)
    porcentaje_descuento: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    motivo_beca: Mapped[str | None] = mapped_column(String(150))
    ci_estudiante_beca: Mapped[str] = mapped_column(ForeignKey("estudiante.ci_estudiante"))
    id_gestion_beca: Mapped[int] = mapped_column(ForeignKey("gestion.id_gestion"))
    creado_en: Mapped[datetime] = mapped_column(server_default="now()")


class PagoMensualidad(Base):
    """Cuota de un mes (la genera sp_generar_cuotas_mes); al cobrarla pasa a 'pagado' con su recibo."""

    __tablename__ = "pago_mensualidad"

    id_pago: Mapped[int] = mapped_column(Integer, primary_key=True)
    mes: Mapped[int] = mapped_column(SmallInteger)
    monto: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    descuento_aplicado: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    fecha_vencimiento: Mapped[date]
    fecha_pago: Mapped[date | None]
    metodo_pago: Mapped[str | None] = mapped_column(String(30))
    estado_pago: Mapped[str] = mapped_column(String(20), server_default="pendiente")
    numero_recibo: Mapped[int | None]
    observacion_pago: Mapped[str | None] = mapped_column(Text)
    ci_administrativo_pago: Mapped[str | None] = mapped_column(ForeignKey("administrativo.ci_administrativo"))
    ci_estudiante_pago: Mapped[str] = mapped_column(ForeignKey("estudiante.ci_estudiante"))
    ci_tutor_pago: Mapped[str | None] = mapped_column(String(20))
    id_gestion_pago: Mapped[int] = mapped_column(ForeignKey("gestion.id_gestion"))
    creado_en: Mapped[datetime] = mapped_column(server_default="now()")
    actualizado_en: Mapped[datetime] = mapped_column(server_default="now()")

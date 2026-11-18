"""
Modelos SQLAlchemy (ORM) del paquete administracion (compartido).

Tablas (lectura y escritura): arancel, beca, pago_mensualidad, inventario, movimiento_inventario, comunicado, comunicado_lectura.
Vistas (solo lectura): v_estado_pagos.

Implementado: arancel, beca y pago_mensualidad (CU25); inventario y movimiento_inventario (CU26);
comunicado y comunicado_lectura (CU27).
"""
# ============================================================
# CU25 - REGISTRAR PAGO DE MENSUALIDAD
# ============================================================

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, SmallInteger, String, Text
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


# ============================================================
# CU26 - GESTIONAR INVENTARIO
# ============================================================


class Inventario(Base):
    """Bien del colegio. cantidad_inventario la mantiene el trigger fn_tg_aplicar_movimiento:
    el backend nunca la edita directamente (solo registra movimientos)."""

    __tablename__ = "inventario"

    id_inventario: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_inventario: Mapped[str] = mapped_column(String(100))
    cantidad_inventario: Mapped[int] = mapped_column(Integer, server_default="0")
    stock_minimo: Mapped[int] = mapped_column(Integer, server_default="0")   # script 11
    observacion_inventario: Mapped[str | None] = mapped_column(Text)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class MovimientoInventario(Base):
    """Entrada o salida de un bien. No se edita ni se borra: se corrige con un movimiento contrario."""

    __tablename__ = "movimiento_inventario"

    id_movimiento: Mapped[int] = mapped_column(Integer, primary_key=True)
    fecha_acceso_inventario: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
    tipo_accion_inventario: Mapped[str] = mapped_column(String(20))
    cantidad_movimiento: Mapped[int]
    motivo_movimiento: Mapped[str | None] = mapped_column(Text)
    destino_movimiento: Mapped[str | None] = mapped_column(String(100))
    ci_administrativo_movimiento: Mapped[str] = mapped_column(ForeignKey("administrativo.ci_administrativo"))
    id_inventario_movimiento: Mapped[int] = mapped_column(ForeignKey("inventario.id_inventario"))


# ============================================================
# CU27 - GESTIONAR COMUNICADOS Y CITACIONES
# ============================================================


class Comunicado(Base):
    """Aviso del colegio. Alcance: 'todos', un 'curso' o un 'estudiante' (sus tutores).
    Una citación siempre es para un estudiante y tiene fecha (lo aseguran los CHECK de la BD)."""

    __tablename__ = "comunicado"

    id_comunicado: Mapped[int] = mapped_column(Integer, primary_key=True)
    titulo: Mapped[str] = mapped_column(String(150))
    contenido: Mapped[str] = mapped_column(Text)
    tipo_comunicado: Mapped[str] = mapped_column(String(20), server_default="general")
    alcance: Mapped[str] = mapped_column(String(20))
    fecha_publicacion: Mapped[datetime] = mapped_column(server_default="now()")
    fecha_citacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    id_gestion_comunicado: Mapped[int] = mapped_column(ForeignKey("gestion.id_gestion"))
    id_curso_comunicado: Mapped[int | None] = mapped_column(ForeignKey("curso.id_curso"))
    ci_estudiante_comunicado: Mapped[str | None] = mapped_column(ForeignKey("estudiante.ci_estudiante"))
    ci_autor: Mapped[str] = mapped_column(ForeignKey("persona.ci"))
    creado_en: Mapped[datetime] = mapped_column(server_default="now()")


class ComunicadoLectura(Base):
    """Quién leyó un comunicado y cuándo (PK comunicado + persona: una sola vez por persona)."""

    __tablename__ = "comunicado_lectura"

    id_comunicado_lectura: Mapped[int] = mapped_column(
        ForeignKey("comunicado.id_comunicado", ondelete="CASCADE"), primary_key=True
    )
    ci_persona_lectura: Mapped[str] = mapped_column(ForeignKey("persona.ci"), primary_key=True)
    leido_en: Mapped[datetime] = mapped_column(server_default="now()")

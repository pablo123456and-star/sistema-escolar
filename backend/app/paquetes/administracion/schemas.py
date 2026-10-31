"""
DTO de entrada y salida (Pydantic) del paquete administracion (compartido).
"""
# ============================================================
# CU25 - REGISTRAR PAGO DE MENSUALIDAD
# ============================================================

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

MetodoPago = Literal["efectivo", "transferencia", "qr", "tarjeta"]
MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre",
         "Noviembre", "Diciembre"]


def _limpiar_texto(valor):
    """Quita espacios repetidos y en los extremos ("" -> None)."""
    if isinstance(valor, str):
        return " ".join(valor.split()) or None
    return valor


def _limpiar_ci(valor):
    return valor.strip() if isinstance(valor, str) else valor


# ---------- Aranceles ----------

class ArancelNivelSalida(BaseModel):
    """Nivel educativo con su arancel en la gestión (None si todavía no tiene)."""

    id_nivel: int
    nivel: str
    id_arancel: int | None
    monto_mensual: float | None
    dia_vencimiento: int | None


class ArancelesSalida(BaseModel):
    gestion: int | None
    niveles: list[ArancelNivelSalida]


class ArancelCrear(BaseModel):
    id_nivel: int = Field(gt=0)
    monto_mensual: Decimal = Field(gt=0, le=100000, decimal_places=2)
    dia_vencimiento: int = Field(default=10, ge=1, le=28)


class ArancelActualizar(BaseModel):
    """Nuevo monto o día de vencimiento (rige para las cuotas que se generen después)."""

    monto_mensual: Decimal | None = Field(default=None, gt=0, le=100000, decimal_places=2)
    dia_vencimiento: int | None = Field(default=None, ge=1, le=28)

    @model_validator(mode="after")
    def algo_que_cambiar(self):
        if self.monto_mensual is None and self.dia_vencimiento is None:
            raise ValueError("Indique el monto o el día de vencimiento.")
        return self


# ---------- Becas ----------

class BecaSalida(BaseModel):
    id_beca: int
    ci_estudiante: str
    nombre_persona: str
    apellidos: str
    curso: str | None
    porcentaje_descuento: float
    motivo_beca: str | None


class BecasSalida(BaseModel):
    gestion: int | None
    becas: list[BecaSalida]


class BecaCrear(BaseModel):
    ci_estudiante: str = Field(min_length=1, max_length=20)
    porcentaje_descuento: Decimal = Field(gt=0, le=100, decimal_places=2)
    motivo_beca: str | None = Field(default=None, max_length=150)

    limpiar_ci = field_validator("ci_estudiante", mode="before")(_limpiar_ci)
    limpiar_motivo = field_validator("motivo_beca", mode="before")(_limpiar_texto)


class BecaActualizar(BaseModel):
    porcentaje_descuento: Decimal | None = Field(default=None, gt=0, le=100, decimal_places=2)
    motivo_beca: str | None = Field(default=None, max_length=150)

    limpiar_motivo = field_validator("motivo_beca", mode="before")(_limpiar_texto)

    @model_validator(mode="after")
    def algo_que_cambiar(self):
        if not self.model_fields_set:
            raise ValueError("Indique el porcentaje o el motivo.")
        return self


# ---------- Cuotas ----------

class GenerarCuotasEntrada(BaseModel):
    mes: int = Field(ge=1, le=12)


class GenerarCuotasSalida(BaseModel):
    gestion: int
    mes: int
    cuotas_creadas: int   # 0 si ya estaban generadas (no se duplican)


class EstudiantePagoSalida(BaseModel):
    """Inscrito con el resumen de sus cuotas (para buscarlo y cobrar)."""

    ci: str
    nombre_persona: str
    apellidos: str
    curso: str
    pendientes: int
    atrasadas: int
    deuda: float          # suma de las cuotas atrasadas


class EstudiantesPagoSalida(BaseModel):
    gestion: int | None
    estudiantes: list[EstudiantePagoSalida]


class TutorPagoSalida(BaseModel):
    ci: str
    nombre_persona: str
    apellidos: str
    parentesco: str
    es_responsable_pago: bool


class CuotaSalida(BaseModel):
    id_pago: int
    anio: int
    mes: int
    monto: float                  # lo que se cobra (ya con la beca descontada)
    descuento_aplicado: float
    fecha_vencimiento: date
    fecha_pago: date | None
    metodo_pago: str | None
    numero_recibo: int | None
    estado_pago: str              # pendiente | pagado | anulado (lo guardado)
    estado_actual: str            # además 'atrasado': pendiente y vencida (v_estado_pagos)
    dias_atraso: int
    observacion_pago: str | None


class EstudianteCuentaSalida(BaseModel):
    ci: str
    nombre_persona: str
    apellidos: str
    curso: str | None             # de su última inscripción


class EstadoCuentaSalida(BaseModel):
    """Cuotas de un estudiante (todas sus gestiones) y los tutores que pueden pagar."""

    estudiante: EstudianteCuentaSalida
    tutores: list[TutorPagoSalida]
    cuotas: list[CuotaSalida]
    total_pendiente: float        # cuotas pendientes (incluye las atrasadas)
    total_atrasado: float


class CobroEntrada(BaseModel):
    metodo_pago: MetodoPago
    ci_tutor: str | None = Field(default=None, max_length=20)   # None = el responsable de pago

    @field_validator("ci_tutor", mode="before")
    @classmethod
    def limpiar_tutor(cls, valor):
        return _limpiar_ci(valor) or None


class MotivoEntrada(BaseModel):
    """Motivo obligatorio para revertir un cobro o anular una cuota (queda en la observación)."""

    motivo: str = Field(min_length=5, max_length=300)

    limpiar_motivo = field_validator("motivo", mode="before")(_limpiar_texto)


class ReciboSalida(BaseModel):
    """Recibo de pago (comprobante interno del colegio, no es factura)."""

    id_pago: int
    numero_recibo: int
    fecha_pago: date
    ci_estudiante: str
    estudiante: str
    curso: str | None
    gestion: int
    mes: int
    monto_mensual: float          # arancel del mes, antes de la beca
    descuento: float
    porcentaje_beca: float | None
    total: float
    metodo_pago: str
    tutor: str | None
    parentesco: str | None
    cajero: str
    cargo: str | None


# ---------- Pago en línea (Stripe, modo de prueba) ----------

class PagoEnLineaEstadoSalida(BaseModel):
    habilitado: bool              # False si no hay clave de prueba de Stripe configurada


class PagoEnLineaSalida(BaseModel):
    url: str                      # página de pago de Stripe a la que se redirige


class ConfirmarPagoEnLineaEntrada(BaseModel):
    id_sesion: str = Field(min_length=10, max_length=255, pattern=r"^cs_[A-Za-z0-9_]+$")


# ---------- Morosos ----------

class CuotaAtrasadaSalida(BaseModel):
    id_pago: int
    anio: int
    mes: int
    monto: float
    dias_atraso: int


class MorosoSalida(BaseModel):
    ci_estudiante: str
    estudiante: str
    curso: str | None
    tutor: str | None             # responsable de pago (o el principal)
    telefono: str | None
    cuotas: list[CuotaAtrasadaSalida]
    deuda: float
    dias_atraso: int              # el mayor


class MorososSalida(BaseModel):
    total_deuda: float
    morosos: list[MorosoSalida]

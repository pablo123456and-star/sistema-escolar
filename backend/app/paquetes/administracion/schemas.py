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


# ============================================================
# CU26 - GESTIONAR INVENTARIO
# ============================================================

from datetime import datetime  # noqa: E402

from pydantic import ConfigDict  # noqa: E402

TipoMovimiento = Literal["entrada", "salida"]
EstadoStock = Literal["normal", "bajo", "sin_stock"]


class BienCrear(BaseModel):
    """Bien nuevo: siempre empieza con cantidad 0 (el stock solo cambia con movimientos)."""

    model_config = ConfigDict(extra="forbid")   # la cantidad no se envía: si llega, 422

    nombre: str = Field(min_length=2, max_length=100)
    stock_minimo: int = Field(default=0, ge=0, le=100000)
    observacion: str | None = Field(default=None, max_length=500)

    _limpiar = field_validator("nombre", "observacion", mode="before")(_limpiar_texto)


class BienActualizar(BaseModel):
    """Datos que se pueden corregir de un bien. La cantidad NUNCA: se corrige con un movimiento."""

    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, min_length=2, max_length=100)
    stock_minimo: int | None = Field(default=None, ge=0, le=100000)
    observacion: str | None = Field(default=None, max_length=500)   # null o "" la borra

    _limpiar = field_validator("nombre", "observacion", mode="before")(_limpiar_texto)

    @model_validator(mode="after")
    def algo_que_cambiar(self):
        if not self.model_fields_set:
            raise ValueError("Indique el nombre, el stock mínimo o la observación.")
        if "nombre" in self.model_fields_set and self.nombre is None:
            raise ValueError("El nombre del bien no puede quedar vacío.")
        if "stock_minimo" in self.model_fields_set and self.stock_minimo is None:
            raise ValueError("Indique el stock mínimo (0 = sin alerta).")
        return self


class BienSalida(BaseModel):
    id_inventario: int
    nombre: str
    cantidad: int
    stock_minimo: int
    estado: EstadoStock           # lo calcula el backend (politicas.estado_stock)
    observacion: str | None
    movimientos: int
    ultimo_movimiento: datetime | None


class InventarioSalida(BaseModel):
    bienes: list[BienSalida]
    total: int
    sin_stock: int
    stock_bajo: int


class MovimientoCrear(BaseModel):
    """Entrada o salida. Motivo obligatorio; la salida además indica a dónde va."""

    tipo: TipoMovimiento
    cantidad: int = Field(gt=0, le=100000)
    motivo: str = Field(min_length=3, max_length=300)
    destino: str | None = Field(default=None, max_length=100)

    _limpiar = field_validator("motivo", "destino", mode="before")(_limpiar_texto)

    @model_validator(mode="after")
    def destino_de_salida(self):
        if self.tipo == "salida" and not self.destino:
            raise ValueError("Indique el destino de la salida (a dónde o a quién se entrega).")
        if self.tipo == "entrada":
            self.destino = None
        return self


class MovimientoSalida(BaseModel):
    id_movimiento: int
    fecha: datetime
    tipo: TipoMovimiento
    cantidad: int
    motivo: str | None
    destino: str | None
    ci_responsable: str
    responsable: str
    saldo: int                    # stock del bien después de este movimiento


class MovimientosSalida(BaseModel):
    bien: BienSalida
    movimientos: list[MovimientoSalida]   # del más reciente al más antiguo


class MovimientoRegistradoSalida(BaseModel):
    bien: BienSalida              # con el stock ya actualizado
    movimiento: MovimientoSalida
    aviso: str | None             # "stock bajo" o "sin stock" tras una salida


# ============================================================
# CU27 - GESTIONAR COMUNICADOS Y CITACIONES
# ============================================================

from datetime import datetime, timedelta, timezone  # noqa: E402

TipoComunicado = Literal["general", "citacion"]
Alcance = Literal["todos", "curso", "estudiante"]

# Bolivia no tiene horario de verano: siempre UTC-4
HORA_BOLIVIA = timezone(timedelta(hours=-4))


class ComunicadoCrear(BaseModel):
    """Comunicado o citación a publicar. Solo se usa el destinatario que corresponde al alcance."""

    titulo: str = Field(min_length=3, max_length=150)
    contenido: str = Field(min_length=5, max_length=5000)
    tipo_comunicado: TipoComunicado = "general"
    alcance: Alcance
    id_curso: int | None = None
    ci_estudiante: str | None = Field(default=None, max_length=20)
    fecha_citacion: datetime | None = None

    _limpiar_titulo = field_validator("titulo", mode="before")(_limpiar_texto)
    _limpiar_ci_est = field_validator("ci_estudiante", mode="before")(_limpiar_ci)

    @field_validator("contenido", mode="before")
    @classmethod
    def _limpiar_contenido(cls, valor):
        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("fecha_citacion")
    @classmethod
    def _con_zona(cls, valor: datetime | None):
        """Una fecha sin zona horaria (ej. '2026-11-20T10:00' de un formulario) es hora de Bolivia."""
        if valor is not None and valor.tzinfo is None:
            return valor.replace(tzinfo=HORA_BOLIVIA)
        return valor

    @model_validator(mode="after")
    def _destinatario_segun_alcance(self):
        if self.tipo_comunicado == "citacion":
            if self.alcance != "estudiante":
                raise ValueError("Una citación siempre se dirige a un estudiante (a sus tutores).")
            if self.fecha_citacion is None:
                raise ValueError("Indique la fecha y hora de la citación.")
        else:
            self.fecha_citacion = None
        if self.alcance == "curso":
            if self.id_curso is None:
                raise ValueError("Elija el curso al que va dirigido el comunicado.")
            self.ci_estudiante = None
        elif self.alcance == "estudiante":
            if not self.ci_estudiante:
                raise ValueError("Elija el estudiante al que va dirigido el comunicado.")
            self.id_curso = None
        else:
            self.id_curso = None
            self.ci_estudiante = None
        return self


class ComunicadoSalida(BaseModel):
    id_comunicado: int
    titulo: str
    contenido: str
    tipo_comunicado: TipoComunicado
    alcance: Alcance
    destinatario: str             # "Toda la comunidad", el curso o el estudiante
    id_curso: int | None
    ci_estudiante: str | None
    gestion: int
    fecha_publicacion: datetime
    fecha_citacion: datetime | None
    ci_autor: str
    autor: str
    rol_autor: str | None
    es_mio: bool                  # el usuario conectado es el autor
    es_destinatario: bool         # le llegó al usuario conectado (puede marcarlo como leído)
    leido_en: datetime | None     # cuándo lo leyó el usuario conectado
    lecturas: int | None          # cuántos lo leyeron (solo para el autor y el administrador)


class BandejaSalida(BaseModel):
    comunicados: list[ComunicadoSalida]
    no_leidos: int


class CursoDestinoSalida(BaseModel):
    id_curso: int
    nombre_curso: str


class EstudianteDestinoSalida(BaseModel):
    ci: str
    nombre: str
    curso: str


class DestinosSalida(BaseModel):
    """A quién puede publicar el usuario conectado en la gestión abierta."""

    gestion: int | None
    puede_todos: bool
    cursos: list[CursoDestinoSalida]
    estudiantes: list[EstudianteDestinoSalida]


class LectorSalida(BaseModel):
    ci: str
    nombre: str
    relacion: str                 # "Estudiante", "Tutor de ...", o el rol si el alcance es 'todos'
    tiene_cuenta: bool            # sin cuenta de usuario no puede leerlo en el sistema
    leido_en: datetime | None


class LecturasSalida(BaseModel):
    id_comunicado: int
    titulo: str
    total_destinatarios: int
    total_leidos: int
    destinatarios: list[LectorSalida]

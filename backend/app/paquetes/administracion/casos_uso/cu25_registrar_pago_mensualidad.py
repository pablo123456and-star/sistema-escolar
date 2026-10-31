"""
CU25 - Registrar pago de mensualidad (incluye aranceles, becas, cuotas y morosos)
Paquete: administracion

Actores ........: Administrativo
Rol del sistema : administrador (tutor y estudiante consultan)
Tablas .........: arancel, beca, pago_mensualidad, tutor_estudiante, administrativo
Usa de la BD ...: Procedimiento sp_generar_cuotas_mes, vista v_estado_pagos, secuencia seq_numero_recibo,
                  trigger de auditoría

Reglas de negocio que implementa este caso de uso (backend):
    - Aranceles y becas: solo administrador y solo de la gestión abierta (uno por nivel / por estudiante;
      beca entre 0 y 100 %: lo asegura la BD). Un cambio rige para las cuotas que se generen después.
    - Beca: el estudiante debe tener inscripción activa en la gestión.
    - Generar cuotas del mes: CALL sp_generar_cuotas_mes (el mes debe estar dentro de la gestión;
      no duplica cuotas ya generadas).
    - Cobrar: solo una cuota 'pendiente'; el cajero es el administrativo conectado.
    - Tutor que paga: debe ser tutor de ese estudiante; por defecto el responsable de pago.
    - Fecha de pago = hoy (hora de Bolivia); número de recibo = nextval('seq_numero_recibo').
    - Recibo de pago: comprobante interno del colegio (no es factura); lo ven el administrador,
      el estudiante y sus tutores.
    - Revertir cobro (corregir un cobro mal hecho): la cuota pagada vuelve a 'pendiente' con motivo
      obligatorio; el número de recibo no se reutiliza y queda anotado en la observación.
    - Anular (dar de baja la cuota, ej. retiro): solo una cuota pendiente, con motivo obligatorio;
      un pago anulado ya no se modifica.
    - Morosos: cuotas atrasadas de v_estado_pagos con el teléfono del tutor responsable.
    - Tutor y estudiante solo consultan las cuotas de sus estudiantes / las suyas.
    - Pago en línea (Stripe, MODO DE PRUEBA): el tutor o el estudiante paga una cuota pendiente con
      tarjeta de prueba. La cuota se da por pagada solo si Stripe confirma la sesión (no se confía en
      el navegador) y el monto coincide; queda con método 'tarjeta', su recibo y como cajero el
      administrativo "Pagos en línea" (script 10). Confirmar dos veces no cobra dos veces.

Precondición:
    La cuota está pendiente y quien cobra es un administrativo.

Postcondición:
    La cuota queda pagada con número de recibo único y fecha; queda registrado en la bitácora.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
import calendar
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo import pasarela_pago
from app.nucleo.config import obtener_config
from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import Conflicto, ErrorNegocio, NoEncontrado
from app.paquetes.academico.politicas import gestion_abierta
from app.paquetes.administracion import politicas
from app.paquetes.administracion import repository as repo
from app.paquetes.administracion.models import Arancel, Beca, PagoMensualidad
from app.paquetes.administracion.schemas import (
    ArancelActualizar, ArancelCrear, ArancelesSalida, ArancelNivelSalida, BecaActualizar, BecaCrear, BecaSalida,
    BecasSalida, CobroEntrada, ConfirmarPagoEnLineaEntrada, CuotaAtrasadaSalida, CuotaSalida, EstadoCuentaSalida,
    EstudianteCuentaSalida, EstudiantePagoSalida, EstudiantesPagoSalida, GenerarCuotasEntrada, GenerarCuotasSalida,
    MESES, MorosoSalida, MorososSalida, MotivoEntrada, PagoEnLineaEstadoSalida, PagoEnLineaSalida, ReciboSalida,
    TutorPagoSalida,
)


async def _gestion_abierta(sesion: AsyncSession):
    gestion = await gestion_abierta(sesion)
    if gestion is None:
        raise ErrorNegocio("No hay una gestión abierta.")
    return gestion


# ------------------------------------------------------------
# 1. ARANCELES
# ------------------------------------------------------------

async def aranceles(sesion: AsyncSession) -> ArancelesSalida:
    gestion = await gestion_abierta(sesion)
    filas = await repo.aranceles_cu25(sesion, gestion.id_gestion) if gestion else []
    return ArancelesSalida(
        gestion=gestion.anio if gestion else None,
        niveles=[ArancelNivelSalida.model_validate(f._asdict()) for f in filas],
    )


async def _arancel_salida(sesion: AsyncSession, arancel: Arancel) -> ArancelNivelSalida:
    return ArancelNivelSalida(
        id_nivel=arancel.id_nivel_arancel, nivel=await repo.nombre_nivel_cu25(sesion, arancel.id_nivel_arancel),
        id_arancel=arancel.id_arancel, monto_mensual=arancel.monto_mensual, dia_vencimiento=arancel.dia_vencimiento,
    )


async def registrar_arancel(sesion: AsyncSession, datos: ArancelCrear) -> ArancelNivelSalida:
    gestion = await _gestion_abierta(sesion)
    nivel = await repo.nombre_nivel_cu25(sesion, datos.id_nivel)
    if nivel is None:
        raise NoEncontrado("No existe ese nivel educativo.")
    if await repo.arancel_de_nivel_cu25(sesion, gestion.id_gestion, datos.id_nivel):
        raise Conflicto(f"{nivel} ya tiene arancel en la gestión {gestion.anio}: modifíquelo.")
    arancel = Arancel(monto_mensual=datos.monto_mensual, dia_vencimiento=datos.dia_vencimiento,
                      id_gestion_arancel=gestion.id_gestion, id_nivel_arancel=datos.id_nivel)
    sesion.add(arancel)
    await sesion.flush()
    return await _arancel_salida(sesion, arancel)


async def actualizar_arancel(sesion: AsyncSession, id_arancel: int, datos: ArancelActualizar) -> ArancelNivelSalida:
    arancel = await sesion.get(Arancel, id_arancel)
    if arancel is None:
        raise NoEncontrado("No existe ese arancel.")
    gestion = await _gestion_abierta(sesion)
    if arancel.id_gestion_arancel != gestion.id_gestion:
        raise ErrorNegocio("Solo se modifican los aranceles de la gestión abierta.")
    if datos.monto_mensual is not None:
        arancel.monto_mensual = datos.monto_mensual
    if datos.dia_vencimiento is not None:
        arancel.dia_vencimiento = datos.dia_vencimiento
    await sesion.flush()
    return await _arancel_salida(sesion, arancel)


# ------------------------------------------------------------
# 2. BECAS
# ------------------------------------------------------------

async def becas(sesion: AsyncSession) -> BecasSalida:
    gestion = await gestion_abierta(sesion)
    filas = await repo.becas_cu25(sesion, gestion.id_gestion) if gestion else []
    return BecasSalida(
        gestion=gestion.anio if gestion else None,
        becas=[BecaSalida.model_validate(f._asdict()) for f in filas],
    )


async def _beca_salida(sesion: AsyncSession, beca: Beca) -> BecaSalida:
    fila = (await repo.becas_cu25(sesion, beca.id_gestion_beca, beca.id_beca))[0]
    return BecaSalida.model_validate(fila._asdict())


async def registrar_beca(sesion: AsyncSession, datos: BecaCrear) -> BecaSalida:
    gestion = await _gestion_abierta(sesion)
    if not await repo.inscripcion_activa_cu25(sesion, datos.ci_estudiante, gestion.id_gestion):
        raise ErrorNegocio(f"El estudiante {datos.ci_estudiante} no tiene una inscripción activa en la gestión {gestion.anio}.")
    if await repo.beca_de_estudiante_cu25(sesion, gestion.id_gestion, datos.ci_estudiante):
        raise Conflicto(f"El estudiante ya tiene una beca en la gestión {gestion.anio}: modifíquela.")
    beca = Beca(porcentaje_descuento=datos.porcentaje_descuento, motivo_beca=datos.motivo_beca,
                ci_estudiante_beca=datos.ci_estudiante, id_gestion_beca=gestion.id_gestion)
    sesion.add(beca)
    await sesion.flush()
    return await _beca_salida(sesion, beca)


async def actualizar_beca(sesion: AsyncSession, id_beca: int, datos: BecaActualizar) -> BecaSalida:
    beca = await sesion.get(Beca, id_beca)
    if beca is None:
        raise NoEncontrado("No existe esa beca.")
    gestion = await _gestion_abierta(sesion)
    if beca.id_gestion_beca != gestion.id_gestion:
        raise ErrorNegocio("Solo se modifican las becas de la gestión abierta.")
    if datos.porcentaje_descuento is not None:
        beca.porcentaje_descuento = datos.porcentaje_descuento
    if "motivo_beca" in datos.model_fields_set:
        beca.motivo_beca = datos.motivo_beca
    await sesion.flush()
    return await _beca_salida(sesion, beca)


# ------------------------------------------------------------
# 3. GENERAR CUOTAS Y CONSULTAR ESTADO DE CUENTA
# ------------------------------------------------------------

async def generar_cuotas(sesion: AsyncSession, datos: GenerarCuotasEntrada) -> GenerarCuotasSalida:
    gestion = await _gestion_abierta(sesion)
    primer_dia = date(gestion.anio, datos.mes, 1)
    ultimo_dia = date(gestion.anio, datos.mes, calendar.monthrange(gestion.anio, datos.mes)[1])
    if ultimo_dia < gestion.fecha_inicio_g or primer_dia > gestion.fecha_final_g:
        raise ErrorNegocio(
            f"El mes debe estar dentro de la gestión {gestion.anio} "
            f"({gestion.fecha_inicio_g:%d/%m/%Y} al {gestion.fecha_final_g:%d/%m/%Y})."
        )
    creadas = await repo.generar_cuotas_cu25(sesion, gestion.id_gestion, datos.mes)
    return GenerarCuotasSalida(gestion=gestion.anio, mes=datos.mes, cuotas_creadas=creadas or 0)


async def estudiantes(sesion: AsyncSession, buscar: str | None) -> EstudiantesPagoSalida:
    """Inscritos de la gestión abierta (con sus cuotas pendientes) para elegir a quién cobrar."""
    gestion = await gestion_abierta(sesion)
    buscar = " ".join((buscar or "").split()) or None
    filas = await repo.estudiantes_pago_cu25(sesion, gestion.id_gestion, buscar) if gestion else []
    return EstudiantesPagoSalida(
        gestion=gestion.anio if gestion else None,
        estudiantes=[EstudiantePagoSalida.model_validate(f._asdict()) for f in filas],
    )


async def estado_cuenta(sesion: AsyncSession, usuario: UsuarioActual, ci_estudiante: str) -> EstadoCuentaSalida:
    await politicas.pagos_visibles(sesion, usuario, ci_estudiante)
    estudiante = await repo.estudiante_cu25(sesion, ci_estudiante)
    if estudiante is None:
        raise NoEncontrado("No existe un estudiante con ese CI.")
    cuotas = [CuotaSalida.model_validate(c._asdict()) for c in await repo.cuotas_cu25(sesion, ci_estudiante)]
    return EstadoCuentaSalida(
        estudiante=EstudianteCuentaSalida.model_validate(estudiante._asdict()),
        tutores=[TutorPagoSalida.model_validate(t._asdict()) for t in await repo.tutores_cu25(sesion, ci_estudiante)],
        cuotas=cuotas,
        total_pendiente=round(sum(c.monto for c in cuotas if c.estado_pago == "pendiente"), 2),
        total_atrasado=round(sum(c.monto for c in cuotas if c.estado_actual == "atrasado"), 2),
    )


async def mis_cuotas(sesion: AsyncSession, usuario: UsuarioActual) -> list[EstadoCuentaSalida]:
    """Estudiante: sus cuotas. Tutor: las de cada uno de sus estudiantes."""
    cis = [usuario.ci] if usuario.rol == "estudiante" else await repo.estudiantes_de_tutor_cu25(sesion, usuario.ci)
    return [await estado_cuenta(sesion, usuario, ci) for ci in cis]


# ------------------------------------------------------------
# 4. COBRAR, RECIBO, REVERTIR Y ANULAR
# ------------------------------------------------------------

async def _cuota(sesion: AsyncSession, id_pago: int) -> PagoMensualidad:
    pago = await repo.cuota_para_cambiar_cu25(sesion, id_pago)
    if pago is None:
        raise NoEncontrado("No existe esa cuota.")
    if pago.estado_pago == "anulado":
        raise ErrorNegocio("La cuota está anulada y ya no se puede modificar.")
    return pago


def _recibo_salida(fila) -> ReciboSalida:
    base = fila.monto + fila.descuento_aplicado
    return ReciboSalida(
        id_pago=fila.id_pago, numero_recibo=fila.numero_recibo, fecha_pago=fila.fecha_pago,
        ci_estudiante=fila.ci_estudiante, estudiante=fila.estudiante, curso=fila.curso, gestion=fila.gestion,
        mes=fila.mes, monto_mensual=base, descuento=fila.descuento_aplicado,
        porcentaje_beca=round(fila.descuento_aplicado * 100 / base, 2) if fila.descuento_aplicado else None,
        total=fila.monto, metodo_pago=fila.metodo_pago, tutor=fila.tutor, parentesco=fila.parentesco,
        cajero=fila.cajero, cargo=fila.cargo,
    )


async def cobrar(sesion: AsyncSession, usuario: UsuarioActual, id_pago: int, datos: CobroEntrada) -> ReciboSalida:
    ci_cajero = await politicas.cajero(sesion, usuario)
    pago = await _cuota(sesion, id_pago)
    if pago.estado_pago != "pendiente":
        raise ErrorNegocio(f"La cuota ya está {pago.estado_pago} (recibo N° {pago.numero_recibo}): solo se cobran cuotas pendientes.")

    tutores = await repo.tutores_cu25(sesion, pago.ci_estudiante_pago)
    if datos.ci_tutor:
        if datos.ci_tutor not in {t.ci for t in tutores}:
            raise ErrorNegocio("La persona indicada no es tutor de ese estudiante.")
        ci_tutor = datos.ci_tutor
    else:
        ci_tutor = tutores[0].ci if tutores else None   # el responsable de pago (o el principal)

    # Se consultan antes de tocar la cuota: una consulta en medio guardaría el cambio a medias (autoflush)
    hoy, numero = await repo.hoy_cu25(sesion), await repo.siguiente_recibo_cu25(sesion)
    pago.estado_pago = "pagado"
    pago.fecha_pago = hoy
    pago.numero_recibo = numero
    pago.metodo_pago = datos.metodo_pago
    pago.ci_administrativo_pago = ci_cajero
    pago.ci_tutor_pago = ci_tutor
    await sesion.flush()
    return _recibo_salida(await repo.recibo_cu25(sesion, id_pago))


async def recibo(sesion: AsyncSession, usuario: UsuarioActual, id_pago: int) -> ReciboSalida:
    fila = await repo.recibo_cu25(sesion, id_pago)
    if fila is None:
        raise NoEncontrado("No existe esa cuota.")
    await politicas.pagos_visibles(sesion, usuario, fila.ci_estudiante)
    if fila.estado_pago != "pagado":
        raise ErrorNegocio("La cuota no está pagada: no tiene recibo.")
    return _recibo_salida(fila)


def _anotar(pago: PagoMensualidad, nota: str) -> None:
    """Agrega la nota a la observación sin borrar las anteriores (queda el historial)."""
    pago.observacion_pago = f"{pago.observacion_pago}\n{nota}" if pago.observacion_pago else nota


async def revertir_cobro(sesion: AsyncSession, usuario: UsuarioActual, id_pago: int,
                         datos: MotivoEntrada) -> EstadoCuentaSalida:
    await politicas.cajero(sesion, usuario)
    pago = await _cuota(sesion, id_pago)
    if pago.estado_pago != "pagado":
        raise ErrorNegocio("Solo se revierte el cobro de una cuota pagada.")
    _anotar(pago, f"Cobro revertido (recibo N° {pago.numero_recibo} del {pago.fecha_pago:%d/%m/%Y}): {datos.motivo}")
    pago.estado_pago = "pendiente"
    pago.fecha_pago = pago.numero_recibo = pago.metodo_pago = None
    pago.ci_administrativo_pago = pago.ci_tutor_pago = None
    await sesion.flush()
    return await estado_cuenta(sesion, usuario, pago.ci_estudiante_pago)


async def anular(sesion: AsyncSession, usuario: UsuarioActual, id_pago: int, datos: MotivoEntrada) -> EstadoCuentaSalida:
    await politicas.cajero(sesion, usuario)
    pago = await _cuota(sesion, id_pago)
    if pago.estado_pago == "pagado":
        raise ErrorNegocio("La cuota está pagada: primero revierta el cobro.")
    _anotar(pago, f"Cuota anulada: {datos.motivo}")
    pago.estado_pago = "anulado"
    await sesion.flush()
    return await estado_cuenta(sesion, usuario, pago.ci_estudiante_pago)


# ------------------------------------------------------------
# 5. MOROSOS
# ------------------------------------------------------------

async def morosos(sesion: AsyncSession) -> MorososSalida:
    por_estudiante: dict[str, MorosoSalida] = {}
    for f in await repo.morosos_cu25(sesion):
        m = por_estudiante.setdefault(f.ci_estudiante, MorosoSalida(
            ci_estudiante=f.ci_estudiante, estudiante=f.estudiante, curso=f.curso, tutor=f.tutor,
            telefono=f.telefono, cuotas=[], deuda=0, dias_atraso=0,
        ))
        m.cuotas.append(CuotaAtrasadaSalida(id_pago=f.id_pago, anio=f.anio, mes=f.mes, monto=f.monto,
                                            dias_atraso=f.dias_atraso))
        m.deuda = round(m.deuda + float(f.monto), 2)
        m.dias_atraso = max(m.dias_atraso, f.dias_atraso)
        m.curso = f.curso or m.curso
    lista = sorted(por_estudiante.values(), key=lambda m: (-m.dias_atraso, m.estudiante))
    return MorososSalida(total_deuda=round(sum(m.deuda for m in lista), 2), morosos=lista)


# ------------------------------------------------------------
# 6. PAGO EN LÍNEA (STRIPE, MODO DE PRUEBA)
# ------------------------------------------------------------

def estado_pago_en_linea() -> PagoEnLineaEstadoSalida:
    return PagoEnLineaEstadoSalida(habilitado=pasarela_pago.habilitada())


def _centavos(monto) -> int:
    return int(round(float(monto) * 100))


async def iniciar_pago_en_linea(sesion: AsyncSession, usuario: UsuarioActual, id_pago: int) -> PagoEnLineaSalida:
    """Crea la sesión de pago de Stripe para una cuota pendiente y devuelve la página de pago."""
    if not pasarela_pago.habilitada():
        raise ErrorNegocio("El pago en línea no está habilitado.")
    pago = await _cuota(sesion, id_pago)
    await politicas.pagos_visibles(sesion, usuario, pago.ci_estudiante_pago)
    if pago.estado_pago != "pendiente":
        raise ErrorNegocio("Solo se pagan en línea las cuotas pendientes.")
    estudiante = await repo.estudiante_cu25(sesion, pago.ci_estudiante_pago)
    anio = (await repo.recibo_cu25(sesion, id_pago)).gestion
    referencia = {"id_pago": pago.id_pago}
    if usuario.rol == "tutor":
        referencia["ci_tutor"] = usuario.ci
    frontend = obtener_config().FRONTEND_URL.rstrip("/")
    sesion_pago = await pasarela_pago.crear_sesion_pago(
        _centavos(pago.monto),
        f"Mensualidad de {MESES[pago.mes - 1].lower()} {anio} - {estudiante.nombre_persona} {estudiante.apellidos}",
        referencia,
        f"{frontend}/administracion/pagos?pago=exito&id_sesion={{CHECKOUT_SESSION_ID}}",
        f"{frontend}/administracion/pagos?pago=cancelado",
    )
    return PagoEnLineaSalida(url=sesion_pago["url"])


async def confirmar_pago_en_linea(sesion: AsyncSession, usuario: UsuarioActual,
                                  datos: ConfirmarPagoEnLineaEntrada) -> ReciboSalida:
    """Registra el cobro si Stripe confirma que la sesión está pagada (se puede llamar más de una vez)."""
    sesion_pago = await pasarela_pago.obtener_sesion(datos.id_sesion)
    try:
        id_pago = int(sesion_pago["referencia"].get("id_pago"))
    except (TypeError, ValueError):
        raise ErrorNegocio("La sesión de pago no corresponde a una cuota del colegio.")
    pago = await repo.cuota_para_cambiar_cu25(sesion, id_pago)
    if pago is None:
        raise NoEncontrado("No existe esa cuota.")
    await politicas.pagos_visibles(sesion, usuario, pago.ci_estudiante_pago)
    if not sesion_pago["pagado"]:
        raise ErrorNegocio("El pago todavía no fue aprobado por la pasarela.")

    nota = f"Pago en línea con tarjeta (Stripe, modo de prueba). Sesión {sesion_pago['id']}"
    if pago.estado_pago == "pagado" and pago.observacion_pago and sesion_pago["id"] in pago.observacion_pago:
        return await recibo(sesion, usuario, id_pago)          # ya registrado: no se cobra dos veces
    if pago.estado_pago != "pendiente":
        raise ErrorNegocio(f"La cuota ya está {pago.estado_pago}: comuníquese con la secretaría para la devolución.")
    if (sesion_pago["monto_centavos"] != _centavos(pago.monto)
            or (sesion_pago["moneda"] or "").lower() != obtener_config().STRIPE_MONEDA.lower()):
        raise ErrorNegocio("El monto pagado no coincide con el de la cuota: comuníquese con la secretaría.")
    cajero = obtener_config().PAGO_EN_LINEA_CI
    if not await repo.es_administrativo_cu25(sesion, cajero):
        raise ErrorNegocio("Falta registrar el administrativo de pagos en línea (script 10_pago_en_linea.sql).")

    tutores = await repo.tutores_cu25(sesion, pago.ci_estudiante_pago)
    ci_tutor = sesion_pago["referencia"].get("ci_tutor")
    if ci_tutor not in {t.ci for t in tutores}:
        ci_tutor = tutores[0].ci if tutores else None
    # Se consultan antes de tocar la cuota: una consulta en medio guardaría el cambio a medias (autoflush)
    hoy, numero = await repo.hoy_cu25(sesion), await repo.siguiente_recibo_cu25(sesion)
    _anotar(pago, nota)
    pago.estado_pago = "pagado"
    pago.fecha_pago = hoy
    pago.numero_recibo = numero
    pago.metodo_pago = "tarjeta"
    pago.ci_administrativo_pago = cajero
    pago.ci_tutor_pago = ci_tutor
    await sesion.flush()
    return _recibo_salida(await repo.recibo_cu25(sesion, id_pago))

/**
 * Tipos y validaciones (Zod) del paquete administracion. Espejo de backend/app/paquetes/administracion/schemas.py.
 * Compartido por todos sus casos de uso.
 */
import { z } from 'zod'

// ============================================================
// CU25 - REGISTRAR PAGO DE MENSUALIDAD
// ============================================================

export const METODOS_PAGO = ['efectivo', 'transferencia', 'qr', 'tarjeta'] as const
export type MetodoPago = (typeof METODOS_PAGO)[number]

export const MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre',
  'Octubre', 'Noviembre', 'Diciembre']

export type ArancelNivel = {
  id_nivel: number
  nivel: string
  id_arancel: number | null
  monto_mensual: number | null
  dia_vencimiento: number | null
}

export type Aranceles = { gestion: number | null; niveles: ArancelNivel[] }

export const esquemaArancel = z.object({
  monto_mensual: z.number('Ingrese el monto').positive('Debe ser mayor a 0').max(100000, 'Monto demasiado alto'),
  dia_vencimiento: z.number('Ingrese el día').int('Debe ser un número entero').min(1, 'Mínimo 1').max(28, 'Máximo 28'),
})
export type DatosArancel = z.infer<typeof esquemaArancel>

export type Beca = {
  id_beca: number
  ci_estudiante: string
  nombre_persona: string
  apellidos: string
  curso: string | null
  porcentaje_descuento: number
  motivo_beca: string | null
}

export type Becas = { gestion: number | null; becas: Beca[] }

export const esquemaBeca = z.object({
  ci_estudiante: z.string().trim().min(1, 'Elija el estudiante'),
  porcentaje_descuento: z.number('Ingrese el porcentaje').gt(0, 'Debe ser mayor a 0').max(100, 'Máximo 100 %'),
  motivo_beca: z.string().trim().max(150, 'Máximo 150 caracteres'),
})
export type DatosBeca = z.infer<typeof esquemaBeca>

export type CuotasGeneradas = { gestion: number; mes: number; cuotas_creadas: number }

export type EstudiantePago = {
  ci: string
  nombre_persona: string
  apellidos: string
  curso: string
  pendientes: number
  atrasadas: number
  deuda: number
}

export type EstudiantesPago = { gestion: number | null; estudiantes: EstudiantePago[] }

export type TutorPago = {
  ci: string
  nombre_persona: string
  apellidos: string
  parentesco: string
  es_responsable_pago: boolean
}

export type EstadoCuota = 'pendiente' | 'atrasado' | 'pagado' | 'anulado'

export type Cuota = {
  id_pago: number
  anio: number
  mes: number
  monto: number
  descuento_aplicado: number
  fecha_vencimiento: string
  fecha_pago: string | null
  metodo_pago: MetodoPago | null
  numero_recibo: number | null
  estado_pago: 'pendiente' | 'pagado' | 'anulado'
  estado_actual: EstadoCuota // 'atrasado' = pendiente y vencida
  dias_atraso: number
  observacion_pago: string | null
}

export type EstadoCuenta = {
  estudiante: { ci: string; nombre_persona: string; apellidos: string; curso: string | null }
  tutores: TutorPago[]
  cuotas: Cuota[]
  total_pendiente: number
  total_atrasado: number
}

export type DatosCobro = { metodo_pago: MetodoPago; ci_tutor: string | null }

export const esquemaMotivo = z.object({
  motivo: z.string().trim().min(5, 'Escriba el motivo (mínimo 5 caracteres)').max(300, 'Máximo 300 caracteres'),
})
export type DatosMotivo = z.infer<typeof esquemaMotivo>

/** Recibo de pago: comprobante interno del colegio (no es factura). */
export type Recibo = {
  id_pago: number
  numero_recibo: number
  fecha_pago: string
  ci_estudiante: string
  estudiante: string
  curso: string | null
  gestion: number
  mes: number
  monto_mensual: number
  descuento: number
  porcentaje_beca: number | null
  total: number
  metodo_pago: MetodoPago
  tutor: string | null
  parentesco: string | null
  cajero: string
  cargo: string | null
}

export type Moroso = {
  ci_estudiante: string
  estudiante: string
  curso: string | null
  tutor: string | null
  telefono: string | null
  cuotas: { id_pago: number; anio: number; mes: number; monto: number; dias_atraso: number }[]
  deuda: number
  dias_atraso: number
}

export type Morosos = { total_deuda: number; morosos: Moroso[] }

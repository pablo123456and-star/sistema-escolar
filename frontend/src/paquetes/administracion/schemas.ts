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

// ============================================================
// CU26 - GESTIONAR INVENTARIO
// ============================================================

export type TipoMovimiento = 'entrada' | 'salida'
/** Lo calcula el backend: 'bajo' = llegó a su stock mínimo; 'sin_stock' = cantidad 0. */
export type EstadoStock = 'normal' | 'bajo' | 'sin_stock'

export type Bien = {
  id_inventario: number
  nombre: string
  cantidad: number
  stock_minimo: number
  estado: EstadoStock
  observacion: string | null
  movimientos: number
  ultimo_movimiento: string | null
}

export type Inventario = { bienes: Bien[]; total: number; sin_stock: number; stock_bajo: number }

export type Movimiento = {
  id_movimiento: number
  fecha: string
  tipo: TipoMovimiento
  cantidad: number
  motivo: string | null
  destino: string | null
  ci_responsable: string
  responsable: string
  saldo: number
}

export type Movimientos = { bien: Bien; movimientos: Movimiento[] }
export type MovimientoRegistrado = { bien: Bien; movimiento: Movimiento; aviso: string | null }

// Un número entero escrito en un input (llega como texto)
const entero = (minimo: number, mensaje: string) =>
  z
    .string()
    .trim()
    .regex(/^\d+$/, 'Escriba un número entero')
    .refine((v) => Number(v) >= minimo, mensaje)
    .refine((v) => Number(v) <= 100000, 'Máximo 100000')

/** Registrar o corregir un bien. La cantidad no está: solo cambia con entradas y salidas. */
export const esquemaBien = z.object({
  nombre: z.string().trim().min(2, 'Mínimo 2 caracteres').max(100, 'Máximo 100 caracteres'),
  stock_minimo: entero(0, 'No puede ser negativo'),
  observacion: z.string().trim().max(500, 'Máximo 500 caracteres'),
})
export type DatosBien = z.infer<typeof esquemaBien>

export const esquemaMovimiento = z
  .object({
    tipo: z.enum(['entrada', 'salida']),
    cantidad: entero(1, 'Debe ser mayor a 0'),
    motivo: z.string().trim().min(3, 'Indique el motivo (mínimo 3 caracteres)').max(300, 'Máximo 300 caracteres'),
    destino: z.string().trim().max(100, 'Máximo 100 caracteres'),
  })
  .superRefine((d, ctx) => {
    if (d.tipo === 'salida' && !d.destino)
      ctx.addIssue({ code: 'custom', path: ['destino'], message: 'Indique a dónde o a quién se entrega' })
  })
export type DatosMovimiento = z.infer<typeof esquemaMovimiento>

// ============================================================
// CU27 - GESTIONAR COMUNICADOS Y CITACIONES
// ============================================================

export type TipoComunicado = 'general' | 'citacion'
export type Alcance = 'todos' | 'curso' | 'estudiante'

export type Comunicado = {
  id_comunicado: number
  titulo: string
  contenido: string
  tipo_comunicado: TipoComunicado
  alcance: Alcance
  destinatario: string
  id_curso: number | null
  ci_estudiante: string | null
  gestion: number
  fecha_publicacion: string
  fecha_citacion: string | null
  ci_autor: string
  autor: string
  rol_autor: string | null
  es_mio: boolean
  es_destinatario: boolean
  leido_en: string | null
  lecturas: number | null
}

export type Bandeja = { comunicados: Comunicado[]; no_leidos: number }

export type Destinos = {
  gestion: number | null
  puede_todos: boolean
  cursos: { id_curso: number; nombre_curso: string }[]
  estudiantes: { ci: string; nombre: string; curso: string }[]
}

export type Lector = { ci: string; nombre: string; relacion: string; tiene_cuenta: boolean; leido_en: string | null }

export type Lecturas = {
  id_comunicado: number
  titulo: string
  total_destinatarios: number
  total_leidos: number
  destinatarios: Lector[]
}

export const esquemaComunicado = z
  .object({
    titulo: z.string().trim().min(3, 'Mínimo 3 caracteres').max(150, 'Máximo 150 caracteres'),
    contenido: z.string().trim().min(5, 'Mínimo 5 caracteres').max(5000, 'Máximo 5000 caracteres'),
    tipo_comunicado: z.enum(['general', 'citacion']),
    alcance: z.enum(['todos', 'curso', 'estudiante']),
    id_curso: z.string(),
    ci_estudiante: z.string(),
    fecha_citacion: z.string(), // "2026-11-20T10:00" (input datetime-local, hora de Bolivia)
  })
  .superRefine((d, ctx) => {
    if (d.alcance === 'curso' && !d.id_curso) ctx.addIssue({ code: 'custom', path: ['id_curso'], message: 'Elija el curso' })
    if (d.alcance === 'estudiante' && !d.ci_estudiante)
      ctx.addIssue({ code: 'custom', path: ['ci_estudiante'], message: 'Elija el estudiante' })
    if (d.tipo_comunicado === 'citacion') {
      if (d.alcance !== 'estudiante')
        ctx.addIssue({ code: 'custom', path: ['alcance'], message: 'Una citación se dirige a un estudiante (sus tutores)' })
      if (!d.fecha_citacion)
        ctx.addIssue({ code: 'custom', path: ['fecha_citacion'], message: 'Indique la fecha y hora de la citación' })
      else if (new Date(`${d.fecha_citacion}:00-04:00`) <= new Date())
        ctx.addIssue({ code: 'custom', path: ['fecha_citacion'], message: 'La citación debe ser en una fecha futura' })
    }
  })
export type DatosComunicado = z.infer<typeof esquemaComunicado>

/** Cuerpo que espera el backend (POST /administracion/comunicados). */
export type ComunicadoNuevo = {
  titulo: string
  contenido: string
  tipo_comunicado: TipoComunicado
  alcance: Alcance
  id_curso: number | null
  ci_estudiante: string | null
  fecha_citacion: string | null
}

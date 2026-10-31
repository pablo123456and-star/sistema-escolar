/**
 * Llamadas al backend del paquete administracion (/api/v1/administracion/...) y hooks de TanStack Query.
 * Compartido por todos sus casos de uso.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/nucleo/api'
import type {
  Aranceles,
  ArancelNivel,
  Beca,
  Becas,
  CuotasGeneradas,
  DatosArancel,
  DatosCobro,
  EstadoCuenta,
  EstudiantesPago,
  Morosos,
  Recibo,
} from './schemas'

// ============================================================
// CU25 - REGISTRAR PAGO DE MENSUALIDAD
// ============================================================

const PAGOS = ['administracion', 'pagos'] as const

/** Tras cobrar, revertir, anular o configurar: se recargan cuotas, búsquedas y morosos. */
function useInvalidarPagos() {
  const cliente = useQueryClient()
  return () => cliente.invalidateQueries({ queryKey: PAGOS })
}

export function useAranceles() {
  return useQuery({ queryKey: [...PAGOS, 'aranceles'], queryFn: () => api<Aranceles>('/administracion/aranceles') })
}

export function useGuardarArancel() {
  const invalidar = useInvalidarPagos()
  return useMutation({
    mutationFn: ({ id_arancel, id_nivel, datos }: { id_arancel: number | null; id_nivel: number; datos: DatosArancel }) =>
      id_arancel
        ? api<ArancelNivel>(`/administracion/aranceles/${id_arancel}`, { metodo: 'PATCH', cuerpo: datos })
        : api<ArancelNivel>('/administracion/aranceles', { metodo: 'POST', cuerpo: { id_nivel, ...datos } }),
    onSuccess: invalidar,
  })
}

export function useBecas() {
  return useQuery({ queryKey: [...PAGOS, 'becas'], queryFn: () => api<Becas>('/administracion/becas') })
}

type DatosBecaApi = { ci_estudiante?: string; porcentaje_descuento: number; motivo_beca: string | null }

export function useGuardarBeca() {
  const invalidar = useInvalidarPagos()
  return useMutation({
    mutationFn: ({ id_beca, datos }: { id_beca?: number; datos: DatosBecaApi }) =>
      id_beca
        ? api<Beca>(`/administracion/becas/${id_beca}`, { metodo: 'PATCH', cuerpo: datos })
        : api<Beca>('/administracion/becas', { metodo: 'POST', cuerpo: datos }),
    onSuccess: invalidar,
  })
}

export function useGenerarCuotas() {
  const invalidar = useInvalidarPagos()
  return useMutation({
    mutationFn: (mes: number) => api<CuotasGeneradas>('/administracion/cuotas/generar', { metodo: 'POST', cuerpo: { mes } }),
    onSuccess: invalidar,
  })
}

export function useEstudiantesPago(buscar: string) {
  return useQuery({
    queryKey: [...PAGOS, 'estudiantes', buscar],
    queryFn: () => api<EstudiantesPago>('/administracion/pagos/estudiantes', { params: { buscar } }),
  })
}

export function useEstadoCuenta(ci_estudiante: string | null) {
  return useQuery({
    queryKey: [...PAGOS, 'cuotas', ci_estudiante],
    queryFn: () => api<EstadoCuenta>('/administracion/cuotas', { params: { ci_estudiante } }),
    enabled: !!ci_estudiante,
  })
}

export function useMisCuotas() {
  return useQuery({ queryKey: [...PAGOS, 'mis-cuotas'], queryFn: () => api<EstadoCuenta[]>('/administracion/mis-cuotas') })
}

export function useCobrar() {
  const invalidar = useInvalidarPagos()
  return useMutation({
    mutationFn: ({ id_pago, datos }: { id_pago: number; datos: DatosCobro }) =>
      api<Recibo>(`/administracion/pagos/${id_pago}/cobrar`, { metodo: 'POST', cuerpo: datos }),
    onSuccess: invalidar,
  })
}

export function useRecibo(id_pago: number | null) {
  return useQuery({
    queryKey: [...PAGOS, 'recibo', id_pago],
    queryFn: () => api<Recibo>(`/administracion/pagos/${id_pago}/recibo`),
    enabled: id_pago !== null,
  })
}

/** Revertir un cobro mal hecho o anular una cuota pendiente (ambos con motivo). */
export function useCorregirCuota() {
  const invalidar = useInvalidarPagos()
  return useMutation({
    mutationFn: ({ id_pago, accion, motivo }: { id_pago: number; accion: 'revertir' | 'anular'; motivo: string }) =>
      api<EstadoCuenta>(`/administracion/pagos/${id_pago}/${accion}`, { metodo: 'POST', cuerpo: { motivo } }),
    onSuccess: invalidar,
  })
}

export function useMorosos() {
  return useQuery({ queryKey: [...PAGOS, 'morosos'], queryFn: () => api<Morosos>('/administracion/morosos') })
}

// ---- Pago en línea (Stripe, modo de prueba) ----

export function useEstadoPagoEnLinea() {
  return useQuery({
    queryKey: [...PAGOS, 'en-linea'],
    queryFn: () => api<{ habilitado: boolean }>('/administracion/pagos/en-linea/estado'),
  })
}

/** Crea la sesión de pago en Stripe y devuelve la página de pago a la que se redirige. */
export function useIniciarPagoEnLinea() {
  return useMutation({
    mutationFn: (id_pago: number) =>
      api<{ url: string }>(`/administracion/pagos/${id_pago}/pagar-en-linea`, { metodo: 'POST' }),
  })
}

/** Al volver de Stripe: el backend consulta a Stripe y, si está pagado, registra el cobro y devuelve el recibo. */
export function useConfirmarPagoEnLinea() {
  const invalidar = useInvalidarPagos()
  return useMutation({
    mutationFn: (id_sesion: string) =>
      api<Recibo>('/administracion/pagos/en-linea/confirmar', { metodo: 'POST', cuerpo: { id_sesion } }),
    onSuccess: invalidar,
  })
}

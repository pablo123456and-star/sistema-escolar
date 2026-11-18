/**
 * Llamadas al backend del paquete administracion (/api/v1/administracion/...) y hooks de TanStack Query.
 * Compartido por todos sus casos de uso.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/nucleo/api'
import type {
  Aranceles,
  Bandeja,
  Bien,
  EstadoStock,
  Inventario,
  MovimientoRegistrado,
  Movimientos,
  TipoMovimiento,
  Comunicado,
  ComunicadoNuevo,
  Destinos,
  Lecturas,
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

// ============================================================
// CU26 - GESTIONAR INVENTARIO
// ============================================================

const INVENTARIO = ['administracion', 'inventario'] as const

/** Tras registrar, corregir, eliminar o mover stock: se recargan la lista y los historiales. */
function useInvalidarInventario() {
  const cliente = useQueryClient()
  return () => cliente.invalidateQueries({ queryKey: INVENTARIO })
}

/** Bienes con su stock y su estado (normal, bajo, sin_stock), con buscador y filtro por estado. */
export function useInventario(buscar: string, estado: EstadoStock | '') {
  return useQuery({
    queryKey: [...INVENTARIO, 'lista', buscar, estado],
    queryFn: () => api<Inventario>('/administracion/inventario', { params: { buscar, estado } }),
    placeholderData: (anterior) => anterior,
  })
}

/** Historial de entradas y salidas de un bien (null = no se pide). */
export function useMovimientos(id_inventario: number | null) {
  return useQuery({
    queryKey: [...INVENTARIO, 'movimientos', id_inventario],
    queryFn: () => api<Movimientos>(`/administracion/inventario/${id_inventario}/movimientos`),
    enabled: id_inventario !== null,
  })
}

type CuerpoBien = { nombre: string; stock_minimo: number; observacion: string | null }

export function useRegistrarBien() {
  const invalidar = useInvalidarInventario()
  return useMutation({
    mutationFn: (datos: CuerpoBien) => api<Bien>('/administracion/inventario', { metodo: 'POST', cuerpo: datos }),
    onSuccess: invalidar,
  })
}

export function useActualizarBien() {
  const invalidar = useInvalidarInventario()
  return useMutation({
    mutationFn: ({ id_inventario, ...datos }: CuerpoBien & { id_inventario: number }) =>
      api<Bien>(`/administracion/inventario/${id_inventario}`, { metodo: 'PATCH', cuerpo: datos }),
    onSuccess: invalidar,
  })
}

export function useEliminarBien() {
  const invalidar = useInvalidarInventario()
  return useMutation({
    mutationFn: (id_inventario: number) =>
      api<{ mensaje: string }>(`/administracion/inventario/${id_inventario}`, { metodo: 'DELETE' }),
    onSuccess: invalidar,
  })
}

export function useRegistrarMovimiento() {
  const invalidar = useInvalidarInventario()
  return useMutation({
    mutationFn: ({
      id_inventario,
      ...datos
    }: {
      id_inventario: number
      tipo: TipoMovimiento
      cantidad: number
      motivo: string
      destino: string | null
    }) =>
      api<MovimientoRegistrado>(`/administracion/inventario/${id_inventario}/movimientos`, {
        metodo: 'POST',
        cuerpo: datos,
      }),
    onSuccess: invalidar,
  })
}

// ============================================================
// CU27 - GESTIONAR COMUNICADOS Y CITACIONES
// ============================================================

const COMUNICADOS = ['administracion', 'comunicados'] as const

/** Tras publicar, leer o eliminar: se recargan la bandeja y los registros de lectura. */
function useInvalidarComunicados() {
  const cliente = useQueryClient()
  return () => cliente.invalidateQueries({ queryKey: COMUNICADOS })
}

/** Comunicados que ve el usuario conectado (con su estado de lectura y los no leídos). */
export function useBandeja() {
  return useQuery({ queryKey: [...COMUNICADOS, 'bandeja'], queryFn: () => api<Bandeja>('/administracion/comunicados') })
}

/** Cursos y estudiantes a los que puede publicar (solo administrador y profesor). */
export function useDestinosComunicado(habilitado: boolean) {
  return useQuery({
    queryKey: [...COMUNICADOS, 'destinos'],
    queryFn: () => api<Destinos>('/administracion/comunicados/destinos'),
    enabled: habilitado,
  })
}

export function usePublicarComunicado() {
  const invalidar = useInvalidarComunicados()
  return useMutation({
    mutationFn: (datos: ComunicadoNuevo) => api<Comunicado>('/administracion/comunicados', { metodo: 'POST', cuerpo: datos }),
    onSuccess: invalidar,
  })
}

export function useMarcarLeido() {
  const invalidar = useInvalidarComunicados()
  return useMutation({
    mutationFn: (id_comunicado: number) =>
      api<Comunicado>(`/administracion/comunicados/${id_comunicado}/leido`, { metodo: 'POST' }),
    onSuccess: invalidar,
  })
}

/** Registro de lectura (autor o administrador). */
export function useLecturas(id_comunicado: number | null) {
  return useQuery({
    queryKey: [...COMUNICADOS, 'lecturas', id_comunicado],
    queryFn: () => api<Lecturas>(`/administracion/comunicados/${id_comunicado}/lecturas`),
    enabled: id_comunicado !== null,
  })
}

export function useEliminarComunicado() {
  const invalidar = useInvalidarComunicados()
  return useMutation({
    mutationFn: (id_comunicado: number) =>
      api<{ mensaje: string }>(`/administracion/comunicados/${id_comunicado}`, { metodo: 'DELETE' }),
    onSuccess: invalidar,
  })
}

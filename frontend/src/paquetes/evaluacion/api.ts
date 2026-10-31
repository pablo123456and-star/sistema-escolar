/**
 * Llamadas al backend del paquete evaluacion (/api/v1/evaluacion/...) y hooks de TanStack Query.
 * Compartido por todos sus casos de uso.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/nucleo/api'
import type {
  ClasesAsistencia,
  DatosAsistencia,
  EstudiantesHistorial,
  FiltrosHistorial,
  HistorialAsistencia,
  ListaAsistencia,
} from './schemas'

// ============================================================
// CU21 - REGISTRAR ASISTENCIA DE ESTUDIANTES
// ============================================================

export function useClasesAsistencia() {
  return useQuery({
    queryKey: ['evaluacion', 'asistencia', 'clases'],
    queryFn: () => api<ClasesAsistencia>('/evaluacion/asistencia/clases'),
  })
}

export function useListaAsistencia(id_asignacion: number | null, fecha: string) {
  return useQuery({
    queryKey: ['evaluacion', 'asistencia', id_asignacion, fecha],
    queryFn: () => api<ListaAsistencia>(`/evaluacion/asistencia/${id_asignacion}`, { params: { fecha } }),
    enabled: id_asignacion !== null && !!fecha,
  })
}

export function useGuardarAsistencia(id_asignacion: number) {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (datos: DatosAsistencia) =>
      api<ListaAsistencia>(`/evaluacion/asistencia/${id_asignacion}`, { metodo: 'PUT', cuerpo: datos }),
    onSuccess: (lista) => {
      cliente.setQueryData(['evaluacion', 'asistencia', id_asignacion, lista.fecha], lista)
      return cliente.invalidateQueries({ queryKey: ['evaluacion', 'asistencia', 'clases'] })
    },
  })
}

// ============================================================
// CU22 - CONSULTAR HISTORIAL DE ASISTENCIA
// ============================================================

export function useEstudiantesHistorial() {
  return useQuery({
    queryKey: ['evaluacion', 'historial', 'estudiantes'],
    queryFn: () => api<EstudiantesHistorial>('/evaluacion/asistencia/historial/estudiantes'),
  })
}

export function useHistorialAsistencia(ci: string | null, filtros: FiltrosHistorial) {
  return useQuery({
    queryKey: ['evaluacion', 'historial', ci, filtros],
    queryFn: () => api<HistorialAsistencia>(`/evaluacion/asistencia/historial/${ci}`, { params: filtros }),
    enabled: !!ci,
  })
}

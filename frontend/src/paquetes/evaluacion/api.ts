/**
 * Llamadas al backend del paquete evaluacion (/api/v1/evaluacion/...) y hooks de TanStack Query.
 * Compartido por todos sus casos de uso.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/nucleo/api'
import type { ClasesAsistencia, DatosAsistencia, ListaAsistencia } from './schemas'

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

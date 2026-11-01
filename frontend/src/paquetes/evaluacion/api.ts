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


// ============================================================
// CU23 - REGISTRAR CALIFICACIONES Y EVALUACIONES
// ============================================================

import type {
  CambioPeriodo,
  ClasesCalificacion,
  DatosAutoevaluacion,
  DatosPlanilla,
  MisCalificaciones,
  PlanillaCU23,
} from './schemas'

export function useClasesCalificacion() {
  return useQuery({
    queryKey: ['evaluacion', 'calificaciones', 'clases'],
    queryFn: () => api<ClasesCalificacion>('/evaluacion/calificaciones/clases'),
  })
}

export function usePlanilla(id_asignacion: number | null, id_periodo: number | null) {
  return useQuery({
    queryKey: ['evaluacion', 'calificaciones', 'planilla', id_asignacion, id_periodo],
    queryFn: () => api<PlanillaCU23>(`/evaluacion/calificaciones/planilla/${id_asignacion}`, { params: { id_periodo } }),
    enabled: id_asignacion !== null && id_periodo !== null,
  })
}

export function useGuardarPlanilla(id_asignacion: number) {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (datos: DatosPlanilla) =>
      api<PlanillaCU23>(`/evaluacion/calificaciones/planilla/${id_asignacion}`, { metodo: 'PUT', cuerpo: datos }),
    onSuccess: (planilla) => {
      cliente.setQueryData(['evaluacion', 'calificaciones', 'planilla', id_asignacion, planilla.periodo.id_periodo], planilla)
      return cliente.invalidateQueries({ queryKey: ['evaluacion', 'calificaciones', 'clases'] })
    },
  })
}

export function useMisCalificaciones(id_periodo: number | null) {
  return useQuery({
    queryKey: ['evaluacion', 'calificaciones', 'mias', id_periodo],
    queryFn: () => api<MisCalificaciones>('/evaluacion/calificaciones/mias', { params: { id_periodo } }),
  })
}

export function useGuardarAutoevaluacion() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (datos: DatosAutoevaluacion) =>
      api<MisCalificaciones>('/evaluacion/calificaciones/autoevaluacion', { metodo: 'PUT', cuerpo: datos }),
    onSuccess: (datos) => {
      cliente.setQueryData(['evaluacion', 'calificaciones', 'mias', datos.periodo?.id_periodo ?? null], datos)
      return cliente.invalidateQueries({ queryKey: ['evaluacion', 'calificaciones', 'mias', null] })
    },
  })
}

export function useCambiarPeriodo() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: ({ id_periodo, accion }: { id_periodo: number; accion: 'cerrar' | 'reabrir' }) =>
      api<CambioPeriodo>(`/evaluacion/calificaciones/periodos/${id_periodo}/${accion}`, { metodo: 'POST' }),
    onSuccess: () =>
      Promise.all([
        cliente.invalidateQueries({ queryKey: ['evaluacion', 'calificaciones'] }),
        cliente.invalidateQueries({ queryKey: ['evaluacion', 'boletin'] }),
        cliente.invalidateQueries({ queryKey: ['evaluacion', 'centralizador'] }),
        cliente.invalidateQueries({ queryKey: ['evaluacion', 'boletines'] }),
      ]),
  })
}


// ============================================================
// CU24 - GENERAR Y CONSULTAR BOLETÍN/LIBRETA
// ============================================================

import type { Boletin, Centralizador, CursoOpcionCU24, EmitirBoletines, EstudianteOpcionCU24, PeriodoOpcionCU24 } from './schemas'

export function useOpcionesPeriodos() {
  return useQuery({
    queryKey: ['evaluacion', 'boletines', 'opciones', 'periodos'],
    queryFn: () => api<PeriodoOpcionCU24[]>('/evaluacion/boletines/opciones/periodos'),
  })
}

export function useOpcionesCursos() {
  return useQuery({
    queryKey: ['evaluacion', 'boletines', 'opciones', 'cursos'],
    queryFn: () => api<CursoOpcionCU24[]>('/evaluacion/boletines/opciones/cursos'),
  })
}

export function useEstudiantesBoletin(id_periodo: number | null, id_curso?: number | null) {
  return useQuery({
    queryKey: ['evaluacion', 'boletines', 'opciones', 'estudiantes', id_periodo, id_curso ?? null],
    queryFn: () =>
      api<EstudianteOpcionCU24[]>('/evaluacion/boletines/opciones/estudiantes', {
        params: { id_periodo, id_curso: id_curso ?? undefined },
      }),
    enabled: !!id_periodo,
  })
}

export function useEmitirBoletines() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (params: { id_periodo: number; id_curso?: number }) =>
      api<EmitirBoletines>('/evaluacion/boletines/emitir', {
        metodo: 'POST',
        params
      }),
    onSuccess: () =>
      Promise.all([
        cliente.invalidateQueries({ queryKey: ['evaluacion', 'boletin'] }),
        cliente.invalidateQueries({ queryKey: ['evaluacion', 'centralizador'] }),
      ]),
  })
}

export function useBoletin(ci_estudiante: string | null, id_periodo: number | null) {
  return useQuery({
    queryKey: ['evaluacion', 'boletin', ci_estudiante, id_periodo],
    queryFn: () => api<Boletin>(`/evaluacion/boletines/${ci_estudiante}`, { params: { id_periodo } }),
    enabled: !!ci_estudiante && !!id_periodo,
  })
}

export function useCentralizador(id_curso: number | null, id_periodo: number | null) {
  return useQuery({
    queryKey: ['evaluacion', 'centralizador', id_curso, id_periodo],
    queryFn: () => api<Centralizador>('/evaluacion/centralizador', { params: { id_curso, id_periodo } }),
    enabled: !!id_curso && !!id_periodo,
  })
}

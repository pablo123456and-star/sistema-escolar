/**
 * Llamadas al backend del paquete personas (/api/v1/personas/...) y hooks de TanStack Query.
 * Compartido por todos sus casos de uso.
 */
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type Pagina } from '@/nucleo/api'
import type {
  Docente,
  DocenteDetalle,
  Estudiante,
  EstudianteDetalle,
  OpcionesEstudiante,
  PersonaBuscada,
  Tutor,
  TutorDetalle,
  Vinculo,
} from './schemas'

const P = '/personas'

export const personasApi = {
  buscar: (ci: string) => api<PersonaBuscada>(`${P}/buscar/${encodeURIComponent(ci)}`),
}

function useInvalidar() {
  const cliente = useQueryClient()
  return () => cliente.invalidateQueries({ queryKey: ['personas'] })
}

// ---- CU06 -------------------------------------------------------------------
export type FiltrosEstudiantes = {
  q?: string
  id_grado?: string
  paralelo?: string
  estado?: string
  pagina: number
  tamano: number
}

export function useEstudiantes(f: FiltrosEstudiantes) {
  return useQuery({
    queryKey: ['personas', 'estudiantes', f],
    queryFn: () => api<Pagina<Estudiante>>(`${P}/estudiantes`, { params: f }),
    placeholderData: keepPreviousData,
  })
}

export function useOpcionesEstudiantes() {
  return useQuery({
    queryKey: ['personas', 'estudiantes-opciones'],
    queryFn: () => api<OpcionesEstudiante>(`${P}/estudiantes/opciones`),
  })
}

export function useEstudiante(ci: string | null) {
  return useQuery({
    queryKey: ['personas', 'estudiante', ci],
    queryFn: () => api<EstudianteDetalle>(`${P}/estudiantes/${ci}`),
    enabled: !!ci,
  })
}

export function useRegistrarEstudiante() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: (cuerpo: unknown) => api<EstudianteDetalle>(`${P}/estudiantes`, { metodo: 'POST', cuerpo }),
    onSuccess: invalidar,
  })
}

export function useActualizarEstudiante() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: ({ ci, cuerpo }: { ci: string; cuerpo: unknown }) =>
      api<EstudianteDetalle>(`${P}/estudiantes/${ci}`, { metodo: 'PATCH', cuerpo }),
    onSuccess: invalidar,
  })
}

export function useBajaEstudiante() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: ({ ci, motivo }: { ci: string; motivo: string }) =>
      api<EstudianteDetalle>(`${P}/estudiantes/${ci}/baja`, { metodo: 'POST', cuerpo: { motivo } }),
    onSuccess: invalidar,
  })
}

export function useReactivarEstudiante() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: (ci: string) => api<EstudianteDetalle>(`${P}/estudiantes/${ci}/reactivar`, { metodo: 'POST' }),
    onSuccess: invalidar,
  })
}

// ---- CU08 -------------------------------------------------------------------
export function useTutores(f: { q?: string; estado?: string; pagina: number; tamano: number }) {
  return useQuery({
    queryKey: ['personas', 'tutores', f],
    queryFn: () => api<Pagina<Tutor>>(`${P}/tutores`, { params: f }),
    placeholderData: keepPreviousData,
  })
}

export function useTutor(ci: string | null) {
  return useQuery({
    queryKey: ['personas', 'tutor', ci],
    queryFn: () => api<TutorDetalle>(`${P}/tutores/${ci}`),
    enabled: !!ci,
  })
}

export function useRegistrarTutor() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: (cuerpo: unknown) => api<TutorDetalle>(`${P}/tutores`, { metodo: 'POST', cuerpo }),
    onSuccess: invalidar,
  })
}

export function useActualizarTutor() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: ({ ci, cuerpo }: { ci: string; cuerpo: unknown }) =>
      api<TutorDetalle>(`${P}/tutores/${ci}`, { metodo: 'PATCH', cuerpo }),
    onSuccess: invalidar,
  })
}

export function useVincular() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: ({ ci_tutor, ...cuerpo }: { ci_tutor: string; ci_estudiante: string; parentesco: string;
      es_principal: boolean; es_responsable_pago: boolean; autorizado_recoger: boolean }) =>
      api<Vinculo>(`${P}/tutores/${ci_tutor}/estudiantes`, { metodo: 'POST', cuerpo }),
    onSuccess: invalidar,
  })
}

export function useActualizarVinculo() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: ({ ci_tutor, ci_estudiante, ...cuerpo }: { ci_tutor: string; ci_estudiante: string } & Partial<
      Pick<Vinculo, 'parentesco' | 'es_principal' | 'es_responsable_pago' | 'autorizado_recoger'>
    >) => api<Vinculo>(`${P}/tutores/${ci_tutor}/estudiantes/${ci_estudiante}`, { metodo: 'PATCH', cuerpo }),
    onSuccess: invalidar,
  })
}

export function useDesvincular() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: ({ ci_tutor, ci_estudiante }: { ci_tutor: string; ci_estudiante: string }) =>
      api<void>(`${P}/tutores/${ci_tutor}/estudiantes/${ci_estudiante}`, { metodo: 'DELETE' }),
    onSuccess: invalidar,
  })
}

// ---- CU10 -------------------------------------------------------------------
export function useDocentes(f: { q?: string; estado?: string; pagina: number; tamano: number }) {
  return useQuery({
    queryKey: ['personas', 'docentes', f],
    queryFn: () => api<Pagina<Docente>>(`${P}/docentes`, { params: f }),
    placeholderData: keepPreviousData,
  })
}

export function useDocente(ci: string | null) {
  return useQuery({
    queryKey: ['personas', 'docente', ci],
    queryFn: () => api<DocenteDetalle>(`${P}/docentes/${ci}`),
    enabled: !!ci,
  })
}

export function useRegistrarDocente() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: (cuerpo: unknown) => api<DocenteDetalle>(`${P}/docentes`, { metodo: 'POST', cuerpo }),
    onSuccess: invalidar,
  })
}

export function useActualizarDocente() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: ({ ci, cuerpo }: { ci: string; cuerpo: unknown }) =>
      api<DocenteDetalle>(`${P}/docentes/${ci}`, { metodo: 'PATCH', cuerpo }),
    onSuccess: invalidar,
  })
}

export function useBajaDocente() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: ({ ci, motivo }: { ci: string; motivo: string }) =>
      api<DocenteDetalle>(`${P}/docentes/${ci}/baja`, { metodo: 'POST', cuerpo: { motivo } }),
    onSuccess: invalidar,
  })
}

export function useReactivarDocente() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: (ci: string) => api<DocenteDetalle>(`${P}/docentes/${ci}/reactivar`, { metodo: 'POST' }),
    onSuccess: invalidar,
  })
}

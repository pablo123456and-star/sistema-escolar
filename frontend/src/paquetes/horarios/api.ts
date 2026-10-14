/**
 * Llamadas al backend del paquete horarios (/api/v1/horarios/...) y hooks de TanStack Query.
 * Compartido por todos sus casos de uso.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/nucleo/api'
import type { BloqueHorario } from '@/nucleo/inicio/datosEjemplo'
import type { Bloque, CursoHorario, FiltroConsulta, HorarioConsulta, HorarioCurso, OpcionesConsulta } from './schemas'

const H = '/horarios'

function useInvalidar() {
  const cliente = useQueryClient()
  return () => cliente.invalidateQueries({ queryKey: ['horarios'] })
}

// ---- CU19 -------------------------------------------------------------------
export function useCursosHorario() {
  return useQuery({ queryKey: ['horarios', 'cursos'], queryFn: () => api<CursoHorario[]>(`${H}/cursos`) })
}

export function useHorarioCurso(id_curso: number | null) {
  return useQuery({
    queryKey: ['horarios', 'curso', id_curso],
    queryFn: () => api<HorarioCurso>(`${H}/cursos/${id_curso}`),
    enabled: id_curso !== null,
  })
}

export type CuerpoBloque = { id_asignacion: number; dia: string; hora_inicio: string; hora_final: string }

export function useAgregarBloque() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: ({ id_curso, cuerpo }: { id_curso: number; cuerpo: CuerpoBloque }) =>
      api<Bloque>(`${H}/cursos/${id_curso}/bloques`, { metodo: 'POST', cuerpo }),
    onSuccess: invalidar,
  })
}

export function useModificarBloque() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: ({ id_horario, cuerpo }: { id_horario: number; cuerpo: Partial<CuerpoBloque> }) =>
      api<Bloque>(`${H}/bloques/${id_horario}`, { metodo: 'PATCH', cuerpo }),
    onSuccess: invalidar,
  })
}

export function useEliminarBloque() {
  const invalidar = useInvalidar()
  return useMutation({
    mutationFn: (id_horario: number) => api<void>(`${H}/bloques/${id_horario}`, { metodo: 'DELETE' }),
    onSuccess: invalidar,
  })
}

// ---- CU20 -------------------------------------------------------------------
export function useOpcionesConsulta() {
  return useQuery({ queryKey: ['horarios', 'opciones'], queryFn: () => api<OpcionesConsulta>(`${H}/consulta/opciones`) })
}

export function useHorarioConsulta(filtro: FiltroConsulta | null) {
  return useQuery({
    queryKey: ['horarios', 'consulta', filtro],
    queryFn: () => api<HorarioConsulta>(`${H}/consulta`, { params: filtro ?? {} }),
    enabled: filtro !== null,
  })
}

/** Horario real (CU20) en el formato de los paneles de inicio (solo lunes a viernes). */
export function useHorarioInicio(filtro: FiltroConsulta | null): BloqueHorario[] {
  const { data } = useHorarioConsulta(filtro)
  return (data?.bloques ?? []).flatMap((b) =>
    b.dia === 'sabado' || b.dia === 'domingo'
      ? []
      : [{
          dia: b.dia,
          inicio: b.hora_inicio.slice(0, 5),
          fin: b.hora_final.slice(0, 5),
          materia: b.nombre_materia,
          curso: b.nombre_curso,
          aula: b.aula,
          docente: b.profesor,
        }],
  )
}

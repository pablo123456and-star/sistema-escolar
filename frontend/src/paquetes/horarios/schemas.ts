/**
 * Tipos y validaciones (Zod) del paquete horarios. Espejo de backend/app/paquetes/horarios/schemas.py.
 * Compartido por todos sus casos de uso.
 */
import { z } from 'zod'

export const DIAS = [
  { dia: 'lunes', etiqueta: 'Lunes' },
  { dia: 'martes', etiqueta: 'Martes' },
  { dia: 'miercoles', etiqueta: 'Miércoles' },
  { dia: 'jueves', etiqueta: 'Jueves' },
  { dia: 'viernes', etiqueta: 'Viernes' },
  { dia: 'sabado', etiqueta: 'Sábado' },
  { dia: 'domingo', etiqueta: 'Domingo' },
] as const

export type Dia = (typeof DIAS)[number]['dia']

/** Bloque de horario tal como lo devuelve v_horario (horas en "HH:MM:SS"). */
export type Bloque = {
  id_horario: number
  dia: Dia
  dia_orden: number
  hora_inicio: string
  hora_final: string
  id_asignacion: number
  id_gestion: number
  id_curso: number
  nombre_curso: string
  id_materia: number
  nombre_materia: string
  ci_profesor: string
  profesor: string
  id_aula: number
  aula: string
}

// ---- CU19 -------------------------------------------------------------------
export type CursoHorario = {
  id_curso: number
  nombre_curso: string
  id_grado: number
  nombre_grado: string
  paralelo: string
  nivel: string
  asignaciones: number
  bloques: number
}

export type AsignacionBloque = {
  id_asignacion: number
  id_materia: number
  nombre_materia: string
  carga_horaria: number | null
  ci_profesor: string
  profesor: string
  aula: string
  bloques: number
}

export type HorarioCurso = {
  id_curso: number
  nombre_curso: string
  gestion: number
  asignaciones: AsignacionBloque[]
  bloques: Bloque[]
}

export const esquemaBloque = z
  .object({
    id_asignacion: z.string().min(1, 'Seleccione la materia'),
    dia: z.string().min(1, 'Seleccione el día'),
    hora_inicio: z.string().regex(/^\d{2}:\d{2}$/, 'Ingrese la hora de inicio'),
    hora_final: z.string().regex(/^\d{2}:\d{2}$/, 'Ingrese la hora de fin'),
  })
  .refine((d) => d.hora_final > d.hora_inicio, {
    message: 'La hora final debe ser posterior a la hora inicial',
    path: ['hora_final'],
  })

export type DatosBloque = z.infer<typeof esquemaBloque>

// ---- CU20 -------------------------------------------------------------------
export type OpcionesConsulta = {
  rol: string
  gestion: number | null
  cursos: { id_curso: number; nombre_curso: string }[]
  docentes: { ci: string; nombre: string }[]
  estudiantes: { ci: string; nombre: string; id_curso: number | null; nombre_curso: string | null }[]
}

export type FiltroConsulta = { id_curso: number } | { ci_profesor: string }

export type HorarioConsulta = {
  tipo: 'curso' | 'docente'
  titulo: string
  gestion: number
  bloques: Bloque[]
}

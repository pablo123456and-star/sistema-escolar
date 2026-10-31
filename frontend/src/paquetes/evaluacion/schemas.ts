/**
 * Tipos y validaciones (Zod) del paquete evaluacion. Espejo de backend/app/paquetes/evaluacion/schemas.py.
 * Compartido por todos sus casos de uso.
 */

// ============================================================
// CU21 - REGISTRAR ASISTENCIA DE ESTUDIANTES
// ============================================================

export const ESTADOS_ASISTENCIA = ['presente', 'ausente', 'tardanza', 'justificado'] as const
export type EstadoAsistencia = (typeof ESTADOS_ASISTENCIA)[number]

export type ClaseAsistencia = {
  id_asignacion: number
  id_curso: number
  curso: string
  materia: string
  ci_profesor: string
  profesor: string
  dias: string[]
  registrada_hoy: boolean
}

export type ClasesAsistencia = {
  gestion: number | null
  fecha_inicio: string | null
  hoy: string
  clases: ClaseAsistencia[]
}

export type EstudianteAsistencia = {
  ci: string
  nombre_persona: string
  apellidos: string
  estado: EstadoAsistencia | null
  observacion: string | null
}

export type ListaAsistencia = {
  clase: ClaseAsistencia
  fecha: string
  registrada: boolean
  dia_con_clase: boolean
  periodo: string | null
  editable: boolean
  motivo_no_editable: string | null
  estudiantes: EstudianteAsistencia[]
}

export type RegistroAsistencia = { ci_estudiante: string; estado: EstadoAsistencia; observacion?: string | null }

export type DatosAsistencia = { fecha: string; registros: RegistroAsistencia[] }

// ============================================================
// CU22 - CONSULTAR HISTORIAL DE ASISTENCIA
// ============================================================

export type EstudianteHistorial = {
  ci: string
  nombre_persona: string
  apellidos: string
  curso: string
  estado_inscripcion: string
}

export type EstudiantesHistorial = { gestion: number | null; estudiantes: EstudianteHistorial[] }

export type ConteoAsistencia = {
  total: number
  presente: number
  ausente: number
  tardanza: number
  justificado: number
  porcentaje: number | null // null = sin registros
}

export type MateriaHistorial = ConteoAsistencia & { id_materia: number; materia: string }

export type RegistroHistorial = {
  fecha: string
  id_materia: number
  materia: string
  estado: EstadoAsistencia
  observacion: string | null
}

export type HistorialAsistencia = {
  estudiante: EstudianteHistorial
  id_gestion: number
  gestion: number
  gestiones: { id_gestion: number; anio: number }[]
  desde: string | null
  hasta: string | null
  general: ConteoAsistencia
  materias: MateriaHistorial[]
  detalle: RegistroHistorial[]
}

export type FiltrosHistorial = { id_gestion?: number; desde?: string; hasta?: string }

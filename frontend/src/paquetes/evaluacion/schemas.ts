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


// ============================================================
// CU23 - REGISTRAR CALIFICACIONES Y EVALUACIONES
// ============================================================

export type DimensionCU23 = {
  id_dimension: number
  nombre_dimension: string
  puntaje_maximo: number
  es_autoevaluacion: boolean
}

export type PeriodoCU23 = {
  id_periodo: number
  nombre_periodo: string
  estado_periodo: 'abierto' | 'cerrado'
  fecha_inicio_p: string
  fecha_final_p: string
  /** false: el trimestre aún no empieza y no admite notas */
  iniciado: boolean
  /** (estudiante, materia) sin nota o con dimensiones vacías */
  notas_pendientes: number
}

export type ClaseCU23 = {
  id_asignacion: number
  curso: string
  materia: string
  profesor: string
}

export type ClasesCalificacion = {
  gestion: number | null
  nota_minima: number | null
  periodos: PeriodoCU23[]
  dimensiones: DimensionCU23[]
  clases: ClaseCU23[]
}

/** id_dimension -> puntaje (las claves llegan como texto en JSON) */
export type Puntajes = Record<string, number>

export type NotaEstudianteCU23 = {
  ci: string
  nombre_persona: string
  apellidos: string
  puntajes: Puntajes
  nota_final: number | null
  observacion: string | null
}

export type PlanillaCU23 = {
  clase: ClaseCU23
  periodo: PeriodoCU23
  nota_minima: number
  dimensiones: DimensionCU23[]
  editable: boolean
  motivo_no_editable: string | null
  estudiantes: NotaEstudianteCU23[]
}

export type DatosPlanilla = {
  id_periodo: number
  notas: { ci_estudiante: string; puntajes: Record<string, number | null>; observacion?: string | null }[]
}

export type MateriaNotasCU23 = {
  id_materia: number
  materia: string
  profesor: string
  puntajes: Puntajes
  nota_final: number | null
  observacion: string | null
}

export type MisCalificaciones = {
  gestion: number | null
  curso: string | null
  nota_minima: number | null
  periodos: PeriodoCU23[]
  periodo: PeriodoCU23 | null
  dimensiones: DimensionCU23[]
  autoevaluacion_editable: boolean
  motivo_no_editable: string | null
  materias: MateriaNotasCU23[]
}

export type DatosAutoevaluacion = {
  id_periodo: number
  autoevaluaciones: { id_materia: number; puntaje: number | null }[]
}

export type CambioPeriodo = {
  periodo: string
  estado_periodo: 'abierto' | 'cerrado'
  boletines: number | null
}

// ============================================================
// CU24 - GENERAR Y CONSULTAR BOLETÍN/LIBRETA
// ============================================================

export type PeriodoOpcionCU24 = {
  id_periodo: number
  nombre_periodo: string
  estado_periodo: 'abierto' | 'cerrado'
  anio: number
  estado_gestion: string
}

export type EstudianteOpcionCU24 = {
  ci: string
  nombre_persona: string
  apellidos: string
  nombre_curso: string
}

export type CursoOpcionCU24 = {
  id_curso: number
  nombre_curso: string
}

export type NotaMateria = {
  id_materia: number
  materia: string
  nota_final: number
  dimensiones_registradas: number
  dimensiones_totales: number
}

export type Boletin = {
  id_boletin: number
  fecha_emision_b: string
  promedio_general_b: number
  observaciones_generales_boletin: string | null
  ci: string
  nombre_persona: string
  apellidos: string
  nombre_periodo: string
  id_gestion_periodo: number
  anio: number
  id_curso_inscripcion: number | null
  nombre_curso: string | null
  notas_por_materia: NotaMateria[]
}

export type EmitirBoletines = {
  cantidad: number
  periodo: string
  fecha_emision: string
}

export type FilaCentralizador = {
  ci: string
  nombre_persona: string
  apellidos: string
  notas: NotaMateria[]
  promedio_estudiante: number | null
}

export type MateriaColumnaCU24 = {
  id_materia: number
  materia: string
}

export type Centralizador = {
  curso: string
  periodo: string
  anio: number
  nota_minima: number
  /** Columnas: todas las materias del curso (cada fila trae solo las notas que existen). */
  materias: MateriaColumnaCU24[]
  filas: FilaCentralizador[]
}

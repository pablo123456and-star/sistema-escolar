/**
 * Tipos y validaciones (Zod) del paquete academico. Espejo de backend/app/paquetes/academico/schemas.py.
 * Compartido por todos sus casos de uso.
 *
 * PENDIENTE.
 */


// ============================================================
// CU13 - GESTIONAR MATERIAS Y PLAN DE ESTUDIOS
// ============================================================

import { z } from 'zod'

// ------------------------------------------------------------
// MATERIAS
// ------------------------------------------------------------

export type Materia = {
  id_materia: number
  nombre_materia: string
  carga_horaria: number | null
}

// Esquema para registrar y modificar materias
export const esquemaMateria = z.object({
  nombre_materia: z
    .string()
    .trim()
    .min(1, 'Ingrese el nombre de la materia')
    .max(100, 'El nombre no puede superar 100 caracteres'),

  carga_horaria: z
    .number()
    .int('La carga horaria debe ser un número entero')
    .positive('La carga horaria debe ser mayor que cero'),
})

export type DatosMateria = z.infer<typeof esquemaMateria>

export type MateriaActualizacion = Partial<DatosMateria>

// ------------------------------------------------------------
// NIVELES EDUCATIVOS
// ------------------------------------------------------------

export type NivelEducativo = {
  id_nivel: number
  nombre_nivel: string
}

// ------------------------------------------------------------
// GRADOS
// ------------------------------------------------------------

export type Grado = {
  id_grado: number
  nombre_grado: string
  orden_grado: number
  id_nivel_educativo_grado: number
}

// ------------------------------------------------------------
// OPCIONES PARA EL PLAN DE ESTUDIOS
// ------------------------------------------------------------

export type OpcionesPlan = {
  niveles: NivelEducativo[]
  grados: Grado[]
}

// ------------------------------------------------------------
// PLAN DE ESTUDIOS
// ------------------------------------------------------------

export type PlanEstudios = {
  id_grado: number
  nombre_grado: string
  materias_plan: Materia[]
  materias_disponibles: Materia[]
}

// Datos para agregar una materia al plan
export const esquemaMateriaPlan = z.object({
  id_materia: z
    .number()
    .int()
    .positive('Seleccione una materia válida'),
})

export type DatosMateriaPlan = z.infer<typeof esquemaMateriaPlan>

// ============================================================
// CU14 - ASIGNAR PROFESOR A MATERIA/CURSO
// ============================================================

// ------------------------------------------------------------
// 1. CURSOS
// ------------------------------------------------------------

export type CursoOpcionAsignacion = {
  id_curso: number
  nombre_curso: string
  id_grado: number
  nombre_grado: string
  paralelo: string
}


// ------------------------------------------------------------
// 2. PROFESORES ACTIVOS
// ------------------------------------------------------------

export type ProfesorOpcionAsignacion = {
  ci_profesor: string
  nombre_profesor: string
}


// ------------------------------------------------------------
// 3. AULAS DISPONIBLES
// ------------------------------------------------------------

export type AulaOpcionAsignacion = {
  id_aula: number
  numero: string
  capacidad: number | null
  tipo_aula: string | null
}


// ------------------------------------------------------------
// 4. OPCIONES PARA ASIGNAR
// ------------------------------------------------------------

export type OpcionesAsignacion = {
  id_gestion: number | null
  anio_gestion: number | null
  cursos: CursoOpcionAsignacion[]
  profesores: ProfesorOpcionAsignacion[]
  aulas: AulaOpcionAsignacion[]
}


// ------------------------------------------------------------
// 5. MATERIAS DE UN CURSO
// ------------------------------------------------------------

export type MateriaCursoAsignacion = {
  id_materia: number
  nombre_materia: string
  carga_horaria: number | null

  id_asignacion: number | null

  ci_profesor: string | null
  nombre_profesor: string | null

  id_aula: number | null
  numero_aula: string | null
}


export type MateriasCursoAsignacion = {
  id_curso: number
  nombre_curso: string

  id_gestion: number
  anio_gestion: number

  materias: MateriaCursoAsignacion[]
}


// ------------------------------------------------------------
// 6. VALIDAR REGISTRO DE ASIGNACIONES
// ------------------------------------------------------------

export const esquemaAsignacionCrear = z.object({
  id_curso: z.number()
    .int()
    .positive('Seleccione un curso válido'),

  id_materia: z.number()
    .int()
    .positive('Seleccione una materia válida'),

  ci_profesor: z.string()
    .trim()
    .min(1, 'Seleccione un profesor')
    .max(20, 'El CI no puede superar 20 caracteres'),

  id_aula: z.number()
    .int()
    .positive('Seleccione un aula válida'),
})

export type DatosAsignacionCrear =
  z.infer<typeof esquemaAsignacionCrear>


// ------------------------------------------------------------
// 7. VALIDAR MODIFICACION DE ASIGNACIONES
// ------------------------------------------------------------

export const esquemaAsignacionActualizar = z.object({
  ci_profesor: z.string()
    .trim()
    .min(1, 'Seleccione un profesor')
    .max(20)
    .optional(),

  id_aula: z.number()
    .int()
    .positive('Seleccione un aula válida')
    .optional(),
}).refine(
  (datos) =>
    datos.ci_profesor !== undefined ||
    datos.id_aula !== undefined,
  {
    message: 'Debe modificar el profesor o el aula',
  }
)

export type DatosAsignacionActualizar =
  z.infer<typeof esquemaAsignacionActualizar>


// ------------------------------------------------------------
// 8. ASIGNACION REGISTRADA
// ------------------------------------------------------------

export type Asignacion = {
  id_asignacion: number

  ci_profesor_asignacion: string
  id_materia_asignacion: number
  id_curso_asignacion: number
  id_aula_asignacion: number
  id_gestion_asignacion: number
}

// ============================================================
// CU16 - INSCRIBIR ESTUDIANTE EN GESTIÓN ACADÉMICA
// ============================================================

export type EstudianteInscripcion = {
  ci: string
  expedido: string | null
  nombre_persona: string
  apellidos: string
  rude: string | null
  estado_persona: 'activo' | 'inactivo'
  id_inscripcion: number | null
  estado_inscripcion: 'activa' | 'retirada' | 'finalizada' | null
  curso: string | null
}

export type DatosInscripcion = { ci_estudiante: string; id_curso: number }

export type MateriaBoleta = {
  materia: string
  carga_horaria: number | null
  docente: string | null
  aula: string | null
}

export type BloqueBoleta = {
  dia: string
  hora_inicio: string
  hora_final: string
  materia: string
  docente: string
  aula: string
}

export type Boleta = {
  id_inscripcion: number
  fecha_inscripcion: string
  estado_inscripcion: string
  ci: string
  expedido: string | null
  nombre_persona: string
  apellidos: string
  fecha_nacimiento: string | null
  rude: string | null
  gestion: number
  curso: string
  grado: string
  paralelo: string
  nivel: string
  materias: MateriaBoleta[]
  horario: BloqueBoleta[]
}

// ============================================================
// CU12 - GESTIONAR NIVELES EDUCATIVOS Y CURSOS
// ============================================================

export type CursoEstructura = { id_curso: number; paralelo: string; cupo_maximo: number; inscritos: number }

export type GradoEstructura = {
  id_grado: number
  nombre_grado: string
  orden_grado: number
  materias: number
  cursos: CursoEstructura[]
}

export type NivelEstructura = { id_nivel: number; nombre_nivel: string; grados: GradoEstructura[] }

/** Niveles -> grados -> paralelos. Los inscritos son de la gestión abierta (null si no hay). */
export type Estructura = { gestion: number | null; niveles: NivelEstructura[] }

export const esquemaNivel = z.object({
  nombre_nivel: z.string().trim().min(1, 'Ingrese el nombre del nivel').max(50, 'Máximo 50 caracteres'),
})
export type DatosNivel = z.infer<typeof esquemaNivel>

export const esquemaGrado = z.object({
  nombre_grado: z.string().trim().min(1, 'Ingrese el nombre del grado').max(50, 'Máximo 50 caracteres'),
  orden_grado: z.number('Ingrese el orden').int('Debe ser un número entero').min(1, 'Mínimo 1').max(99, 'Máximo 99'),
})
export type DatosGrado = z.infer<typeof esquemaGrado>

export const esquemaCurso = z.object({
  paralelo: z
    .string()
    .trim()
    .toUpperCase()
    .min(1, 'Ingrese el paralelo')
    .max(5, 'Máximo 5 caracteres')
    .regex(/^[A-Z0-9]+$/, 'Solo letras y números (ej. A, B, C)'),
  cupo_maximo: z.number('Ingrese el cupo').int('Debe ser un número entero').min(1, 'Mínimo 1').max(100, 'Máximo 100'),
})
export type DatosCurso = z.infer<typeof esquemaCurso>


// ============================================================
// CU15 - GESTIONAR GESTIÓN ACADÉMICA (AÑO LECTIVO)
// ============================================================

/** Los montos y notas (Decimal) llegan del backend como texto, p. ej. "51.00". */
export type Gestion = {
  id_gestion: number
  anio: number
  fecha_inicio_g: string
  fecha_final_g: string
  nota_minima_aprobacion: string
  estado_gestion: 'abierta' | 'cerrada'
  periodos: number
  inscritos: number
}

export type Periodo = {
  id_periodo: number
  nombre_periodo: string
  tipo: 'trimestre' | 'bimestre' | 'semestre' | null
  fecha_inicio_p: string
  fecha_final_p: string
  estado_periodo: 'abierto' | 'cerrado'
  observaciones_periodo: string | null
  id_gestion_periodo: number
}

export type Dimension = {
  id_dimension: number
  nombre_dimension: string
  puntaje_maximo: string
  es_autoevaluacion: boolean
  orden_dimension: number
}

export type Dimensiones = { dimensiones: Dimension[]; suma_puntajes: string; completa: boolean }

export type ResumenGestion = {
  id_gestion: number
  anio: number
  inscritos_activos: number
  retirados: number
  finalizados: number
  promedio_general: string | null
  total_cobrado: string
  total_vencido: string
}

export type CierreGestion = { id_gestion: number; promovidos: number; reprobados: number }

export const esquemaGestion = z
  .object({
    anio: z.number('Ingrese el año').int('Debe ser un número entero').min(2000, 'Año no válido').max(2100, 'Año no válido'),
    fecha_inicio_g: z.string().min(1, 'Ingrese la fecha de inicio'),
    fecha_final_g: z.string().min(1, 'Ingrese la fecha final'),
    nota_minima_aprobacion: z.number('Ingrese la nota mínima').min(0, 'Mínimo 0').max(100, 'Máximo 100'),
  })
  .refine((d) => !d.fecha_inicio_g || !d.fecha_final_g || d.fecha_final_g > d.fecha_inicio_g, {
    path: ['fecha_final_g'],
    message: 'Debe ser posterior a la fecha de inicio',
  })
  .refine((d) => !d.fecha_inicio_g || d.fecha_inicio_g.startsWith(String(d.anio)), {
    path: ['anio'],
    message: 'Debe coincidir con el año de la fecha de inicio',
  })
export type DatosGestion = z.infer<typeof esquemaGestion>

export const esquemaPeriodo = z
  .object({
    nombre_periodo: z.string().trim().min(1, 'Ingrese el nombre').max(50, 'Máximo 50 caracteres'),
    tipo: z.enum(['trimestre', 'bimestre', 'semestre']),
    fecha_inicio_p: z.string().min(1, 'Ingrese la fecha de inicio'),
    fecha_final_p: z.string().min(1, 'Ingrese la fecha final'),
  })
  .refine((d) => !d.fecha_inicio_p || !d.fecha_final_p || d.fecha_final_p > d.fecha_inicio_p, {
    path: ['fecha_final_p'],
    message: 'Debe ser posterior a la fecha de inicio',
  })
export type DatosPeriodo = z.infer<typeof esquemaPeriodo>

export const esquemaDimension = z.object({
  nombre_dimension: z.string().trim().min(1, 'Ingrese el nombre').max(30, 'Máximo 30 caracteres'),
  puntaje_maximo: z.number('Ingrese el puntaje').gt(0, 'Debe ser mayor que 0').max(100, 'Máximo 100'),
  es_autoevaluacion: z.boolean(),
})
export type DatosDimension = z.infer<typeof esquemaDimension>

// ============================================================
// CU17 - CONSULTAR HISTORIAL DE INSCRIPCIONES
// ============================================================

export type EstudianteHistorialItem = {
  ci: string
  nombre_completo: string
  nombre_persona: string
  apellidos: string
  codigo_rude?: string | null
  curso_actual?: string | null
  activo: boolean
}

export type HistorialInscripcionItem = {
  id_inscripcion: number
  id_gestion: number
  anio: number
  curso: string
  estado_inscripcion: 'activa' | 'retirada' | 'finalizada'
  fecha_inscripcion: string
  fecha_retiro?: string | null
  motivo_retiro?: string | null
  resultado_final?: 'promovido' | 'reprobado' | null
  promedio_anual?: number | string | null
  nota_minima: number | string
}

export type HistorialEstudianteSalida = {
  ci: string
  nombre_completo: string
  codigo_rude?: string | null
  inscripciones: HistorialInscripcionItem[]
}


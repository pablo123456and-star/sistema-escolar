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

/**
 * Tipos y validaciones (Zod) del paquete personas. Espejo de backend/app/paquetes/personas/schemas.py.
 * Compartido por todos sus casos de uso.
 */
import { z } from 'zod'

export const EXPEDIDOS = ['LP', 'CB', 'SC', 'OR', 'PT', 'CH', 'TJ', 'BE', 'PD'] as const
export const PARENTESCOS = ['Padre', 'Madre', 'Abuelo(a)', 'Tío(a)', 'Hermano(a)', 'Tutor legal', 'Otro'] as const

export type Persona = {
  ci: string
  expedido: string | null
  nombre_persona: string
  apellidos: string
  sexo: 'M' | 'F' | null
  fecha_nacimiento: string | null
  direccion: string | null
  telefono: string | null
  email: string | null
  estado_persona: 'activo' | 'inactivo'
}

export type PersonaBuscada = Persona & {
  es_estudiante: boolean
  es_tutor: boolean
  es_profesor: boolean
  es_administrativo: boolean
}

export type Vinculo = {
  ci_tutor: string
  ci_estudiante: string
  nombre_tutor: string
  nombre_estudiante: string
  telefono_tutor: string | null
  parentesco: string
  es_principal: boolean
  es_responsable_pago: boolean
  autorizado_recoger: boolean
  estado_estudiante: string
  curso_estudiante: string | null
}

// ---- CU06 -------------------------------------------------------------------
export type Estudiante = {
  ci: string
  expedido: string | null
  nombre_persona: string
  apellidos: string
  sexo: 'M' | 'F' | null
  fecha_nacimiento: string | null
  rude: string | null
  estado_persona: 'activo' | 'inactivo'
  id_curso: number | null
  curso: string | null
  grado: string | null
  paralelo: string | null
  nivel: string | null
  tutor_principal: string | null
}

export type EstudianteDetalle = Persona & {
  rude: string | null
  antecedentes_academicos: string | null
  inscripcion: { id_inscripcion: number; gestion: number; curso: string; estado_inscripcion: string; fecha_inscripcion: string } | null
  tutores: Vinculo[]
  tiene_usuario: boolean
}

export type CursoOpcion = {
  id_curso: number
  nombre_curso: string
  id_grado: number
  nombre_grado: string
  paralelo: string
  nivel: string
  cupo_maximo: number
  inscritos: number
}

export type OpcionesEstudiante = { gestion: number | null; cursos: CursoOpcion[]; paralelos: string[] }

// ---- CU08 -------------------------------------------------------------------
export type Tutor = {
  ci: string
  expedido: string | null
  nombre_persona: string
  apellidos: string
  telefono: string | null
  email: string | null
  ocupacion: string | null
  estado_persona: 'activo' | 'inactivo'
  cantidad_estudiantes: number
}

export type TutorDetalle = Persona & { ocupacion: string | null; estudiantes: Vinculo[]; tiene_usuario: boolean }

// ---- Formularios ------------------------------------------------------------
const opcional = (max: number, mensaje = `Máximo ${max} caracteres`) => z.string().trim().max(max, mensaje)

export const esquemaPersona = z.object({
  ci: z
    .string()
    .trim()
    .toUpperCase()
    .regex(/^[0-9]{4,12}(-[0-9][A-Z])?$/, 'C.I. no válido (ej. 1234567 o 1234567-1B)'),
  expedido: z.string(),
  nombre_persona: z.string().trim().min(2, 'Ingrese los nombres').max(100),
  apellidos: z.string().trim().min(2, 'Ingrese los apellidos').max(100),
  sexo: z.string(),
  fecha_nacimiento: z
    .string()
    .refine((v) => !v || v <= new Date().toISOString().slice(0, 10), 'La fecha no puede ser futura'),
  direccion: opcional(150),
  telefono: z.string().trim().refine((v) => !v || /^[0-9+ -]{6,20}$/.test(v), 'Teléfono no válido'),
  email: z
    .string()
    .trim()
    .max(100)
    .refine((v) => !v || /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(v), 'Correo no válido'),
})

export const PERSONA_VACIA = {
  ci: '',
  expedido: '',
  nombre_persona: '',
  apellidos: '',
  sexo: '',
  fecha_nacimiento: '',
  direccion: '',
  telefono: '',
  email: '',
}

export const esquemaEstudiante = z
  .object({
    persona: esquemaPersona,
    rude: z.string().trim().refine((v) => !v || (v.length >= 4 && v.length <= 20), 'Entre 4 y 20 caracteres'),
    antecedentes_academicos: opcional(1000),
    ci_tutor: z.string().trim(),
    parentesco: z.string(),
    id_curso: z.string(),
  })
  .refine((d) => !d.ci_tutor || d.parentesco, { message: 'Seleccione el parentesco', path: ['parentesco'] })

export const esquemaTutor = z.object({ persona: esquemaPersona, ocupacion: opcional(50) })

export const esquemaVinculo = z.object({
  ci_estudiante: z.string().trim().min(1, 'Ingrese el C.I. del estudiante'),
  parentesco: z.string().min(1, 'Seleccione el parentesco'),
  es_principal: z.boolean(),
  es_responsable_pago: z.boolean(),
  autorizado_recoger: z.boolean(),
})

export const esquemaBaja = z.object({ motivo: z.string().trim().min(3, 'Indique el motivo').max(300) })

type DatosPersona = z.infer<typeof esquemaPersona>

/** Convierte el formulario de persona al cuerpo que espera el backend (vacíos -> null). */
export function personaParaApi(p: DatosPersona) {
  const nulo = (v: string) => (v ? v : null)
  return {
    ci: p.ci,
    expedido: nulo(p.expedido),
    nombre_persona: p.nombre_persona,
    apellidos: p.apellidos,
    sexo: nulo(p.sexo),
    fecha_nacimiento: nulo(p.fecha_nacimiento),
    direccion: nulo(p.direccion),
    telefono: nulo(p.telefono),
    email: nulo(p.email),
  }
}

/** Datos de una persona existente para llenar el formulario. */
export function personaAFormulario(p: Persona): DatosPersona {
  return {
    ci: p.ci,
    expedido: p.expedido ?? '',
    nombre_persona: p.nombre_persona,
    apellidos: p.apellidos,
    sexo: p.sexo ?? '',
    fecha_nacimiento: p.fecha_nacimiento ?? '',
    direccion: p.direccion ?? '',
    telefono: p.telefono ?? '',
    email: p.email ?? '',
  }
}

// ---- CU10 -------------------------------------------------------------------
export type Docente = {
  ci: string
  expedido: string | null
  nombre_persona: string
  apellidos: string
  sexo: 'M' | 'F' | null
  telefono: string | null
  email: string | null
  titulo_academico: string | null
  anios_experiencia: number | null
  estado_persona: 'activo' | 'inactivo'
  cantidad_asignaciones: number
}

export type AsignacionDocente = { id_asignacion: number; materia: string; curso: string; aula: string }

export type DocenteDetalle = Persona & {
  titulo_academico: string | null
  fecha_contrato: string | null
  antecedentes_laborales: string | null
  anios_experiencia: number | null
  gestion: number | null
  asignaciones: AsignacionDocente[]
  tiene_usuario: boolean
}

export const esquemaDocente = z.object({
  persona: esquemaPersona,
  titulo_academico: opcional(100),
  fecha_contrato: z.string(),
  anios_experiencia: z
    .string()
    .trim()
    .refine((v) => !v || (/^\d+$/.test(v) && Number(v) <= 60), 'Número entero entre 0 y 60'),
  antecedentes_laborales: opcional(1000),
})

// ---- CU07: antecedentes médicos y seguimiento ------------------------------------
export const TIPOS_SEGUIMIENTO = ['conducta', 'academico', 'salud', 'merito', 'otro'] as const
export type TipoSeguimiento = (typeof TIPOS_SEGUIMIENTO)[number]
export const ETIQUETA_TIPO: Record<TipoSeguimiento, string> = {
  conducta: 'Conducta',
  academico: 'Académico',
  salud: 'Salud',
  merito: 'Mérito',
  otro: 'Otro',
}

export const GRAVEDADES = ['leve', 'grave', 'muy_grave'] as const
export type Gravedad = (typeof GRAVEDADES)[number]
export const ETIQUETA_GRAVEDAD: Record<Gravedad, string> = { leve: 'Leve', grave: 'Grave', muy_grave: 'Muy grave' }

export type EstudianteSeguimiento = {
  ci: string
  nombre_persona: string
  apellidos: string
  sexo: 'M' | 'F' | null
  estado_persona: 'activo' | 'inactivo'
  curso: string | null
  tiene_observacion_medica: boolean
  cantidad_seguimientos: number
  ultimo_seguimiento: string | null
}

export type Seguimiento = {
  id_seguimiento: number
  fecha: string
  tipo: TipoSeguimiento
  gravedad: Gravedad | null
  descripcion: string
  accion_tomada: string | null
  registrado_por: string
  rol_registrado_por: string | null
  es_mio: boolean
}

export type FichaSeguimiento = {
  ci: string
  expedido: string | null
  nombre_persona: string
  apellidos: string
  sexo: 'M' | 'F' | null
  fecha_nacimiento: string | null
  rude: string | null
  estado_persona: 'activo' | 'inactivo'
  curso: string | null
  gestion: number | null
  observacion_medica: string | null
  antecedentes_academicos: string | null
  puede_editar_antecedentes: boolean
  puede_registrar_seguimiento: boolean
  seguimientos: Seguimiento[]
}

/** Fecha de hoy (Bolivia) en formato AAAA-MM-DD, para el valor por defecto y el máximo del campo fecha. */
export function hoyBolivia(): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/La_Paz' }).format(new Date())
}

export const esquemaSeguimiento = z
  .object({
    tipo: z.enum(TIPOS_SEGUIMIENTO, { error: 'Elija el tipo' }),
    gravedad: z.string(),
    fecha: z.string().min(1, 'Indique la fecha'),
    descripcion: z.string().trim().min(5, 'Describa lo ocurrido (mínimo 5 caracteres)').max(2000),
    accion_tomada: z.string().trim().max(1000),
  })
  .superRefine((d, ctx) => {
    if (d.tipo === 'conducta' && !d.gravedad) {
      ctx.addIssue({ code: 'custom', path: ['gravedad'], message: 'Indique la gravedad' })
    }
    if (d.fecha && d.fecha > hoyBolivia()) {
      ctx.addIssue({ code: 'custom', path: ['fecha'], message: 'La fecha no puede ser futura' })
    }
  })

export const esquemaAntecedentes = z.object({ observacion_medica: z.string().max(1000, 'Máximo 1000 caracteres') })

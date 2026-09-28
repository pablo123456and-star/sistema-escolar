/**
 * Tipos y validaciones (Zod) del paquete seguridad. Espejo de backend/app/paquetes/seguridad/schemas.py.
 * Compartido por todos sus casos de uso.
 */
import { z } from 'zod'

export type Rol = 'administrador' | 'profesor' | 'estudiante' | 'tutor'
export type EstadoUsuario = 'activo' | 'inactivo' | 'bloqueado'

// ---- CU01 -------------------------------------------------------------------
export type Perfil = {
  id_usuario: number
  nombre_usuario: string
  rol: Rol
  ci: string
  nombres: string
  apellidos: string
  email: string | null
  cargo: string | null
  ultimo_acceso: string | null
}

export type Sesion = { token: string; expira: string; usuario: Perfil }

export type ResumenInicio = {
  usuarios_activos: number
  estudiantes_activos: number
  tutores: number
  cursos: number
  gestion: string | null
  actividades: { fecha_hora: string; accion: string; modulo: string | null; nombre_usuario: string | null }[]
}

const contrasenaNueva = z
  .string()
  .min(8, 'Mínimo 8 caracteres')
  .max(64, 'Máximo 64 caracteres')
  .regex(/[A-Za-z]/, 'Debe tener letras')
  .regex(/[0-9]/, 'Debe tener números')

export const esquemaLogin = z.object({
  identificador: z.string().trim().min(1, 'Ingrese su usuario o correo'),
  contrasena: z.string().min(1, 'Ingrese su contraseña'),
  recordar: z.boolean(),
})
export type DatosLogin = z.infer<typeof esquemaLogin>

export const esquemaRecuperar = z.object({
  identificador: z.string().trim().min(1, 'Ingrese su usuario o correo electrónico'),
})

export const esquemaCambiarContrasena = z
  .object({
    actual: z.string().min(1, 'Ingrese su contraseña actual'),
    nueva: contrasenaNueva,
    confirmar: z.string(),
  })
  .refine((d) => d.nueva === d.confirmar, { message: 'Las contraseñas no coinciden', path: ['confirmar'] })

// ---- CU02 -------------------------------------------------------------------
export type Usuario = {
  id_usuario: number
  nombre_usuario: string
  estado_usuario: EstadoUsuario
  ultimo_acceso: string | null
  creado_en: string
  id_rol: number
  nombre_rol: Rol
  ci: string
  expedido: string | null
  nombres: string
  apellidos: string
  email: string | null
}

export type PersonaSinCuenta = { ci: string; nombres: string; apellidos: string; email: string | null }

export type SolicitudRecuperacion = {
  id_bitacora: number
  fecha_hora: string
  id_usuario: number
  nombre_usuario: string
  nombres: string
  apellidos: string
  ip: string | null
}

const nombreUsuario = z
  .string()
  .trim()
  .min(3, 'Mínimo 3 caracteres')
  .max(50, 'Máximo 50 caracteres')
  .regex(/^[A-Za-z0-9._-]+$/, 'Solo letras, números, punto, guion y guion bajo (sin espacios ni tildes)')

export const esquemaNuevoUsuario = z
  .object({
    id_rol: z.string().min(1, 'Seleccione el rol'),
    ci_persona: z.string().min(1, 'Seleccione la persona'),
    nombre_usuario: nombreUsuario,
    contrasena: contrasenaNueva,
    confirmar: z.string(),
  })
  .refine((d) => d.contrasena === d.confirmar, { message: 'Las contraseñas no coinciden', path: ['confirmar'] })

export const esquemaEditarUsuario = z.object({
  nombre_usuario: nombreUsuario,
  id_rol: z.string().min(1, 'Seleccione el rol'),
  estado_usuario: z.enum(['activo', 'inactivo', 'bloqueado']),
})

// ---- CU03 -------------------------------------------------------------------
export type RolDetalle = {
  id_rol: number
  nombre_rol: Rol
  descripcion_rol: string | null
  usuarios_activos: number
  usuarios_total: number
}

export type Permiso = { paquete: string; codigo: string; caso_uso: string; roles: Rol[] }

export const esquemaRol = z.object({
  descripcion_rol: z.string().trim().min(1, 'Ingrese la descripción').max(150, 'Máximo 150 caracteres'),
})

// ---- CU04 -------------------------------------------------------------------
export type RegistroBitacora = {
  id_bitacora: number
  fecha_hora: string
  accion: string
  operacion: string | null
  tabla_afectada: string | null
  registro_id: string | null
  modulo: string | null
  ip: string | null
  id_usuario: number | null
  nombre_usuario: string | null
  datos_anteriores: Record<string, unknown> | null
  datos_nuevos: Record<string, unknown> | null
}

export type OpcionesBitacora = { modulos: string[]; tablas: string[]; operaciones: string[] }

export type FiltrosBitacora = {
  desde?: string
  hasta?: string
  modulo?: string
  tabla?: string
  operacion?: string
  usuario?: string
  texto?: string
}

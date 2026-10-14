/**
 * Llamadas al backend del paquete seguridad (/api/v1/seguridad/...) y hooks de TanStack Query.
 * Compartido por todos sus casos de uso.
 */
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, type Pagina } from '@/nucleo/api'
import type {
  FiltrosBitacora,
  OpcionesBitacora,
  Perfil,
  Permiso,
  PersonaSinCuenta,
  RegistroBitacora,
  ResumenInicio,
  RolDetalle,
  Sesion,
  SolicitudRecuperacion,
  Usuario,
} from './schemas'

const S = '/seguridad'

// ---- CU01 -------------------------------------------------------------------
export const seguridadApi = {
  iniciarSesion: (d: { identificador: string; contrasena: string; recordar: boolean }) =>
    api<Sesion>(`${S}/sesion`, { metodo: 'POST', cuerpo: d }),
  perfil: () => api<Perfil>(`${S}/perfil`),
  recuperar: (correoOIdentificador: string) =>
    api<{ mensaje: string }>(`${S}/recuperar-contrasena`, {
      metodo: 'POST',
      cuerpo: { correo: correoOIdentificador, identificador: correoOIdentificador },
    }),
  validarToken: (token: string) =>
    api<{ valido: boolean; nombre_usuario?: string; nombre_completo?: string; mensaje: string }>(
      `${S}/recuperar-contrasena/validar`,
      { params: { token } }
    ),
  restablecerContrasena: (token: string, nueva: string) =>
    api<{ mensaje: string }>(`${S}/restablecer-contrasena`, {
      metodo: 'POST',
      cuerpo: { token, nueva },
    }),
  cambiarContrasena: (d: { actual: string; nueva: string }) =>
    api<{ mensaje: string }>(`${S}/perfil/contrasena`, { metodo: 'POST', cuerpo: d }),
}

export function useResumenInicio() {
  return useQuery({ queryKey: ['seguridad', 'inicio'], queryFn: () => api<ResumenInicio>(`${S}/inicio`) })
}

// ---- CU02 -------------------------------------------------------------------
export type FiltrosUsuarios = { q?: string; id_rol?: string; estado?: string; pagina: number; tamano: number }

export function useUsuarios(f: FiltrosUsuarios) {
  return useQuery({
    queryKey: ['seguridad', 'usuarios', f],
    queryFn: () => api<Pagina<Usuario>>(`${S}/usuarios`, { params: f }),
    placeholderData: keepPreviousData,
  })
}

export function usePersonasSinCuenta(idRol: string, q: string) {
  return useQuery({
    queryKey: ['seguridad', 'personas-sin-cuenta', idRol, q],
    queryFn: () => api<PersonaSinCuenta[]>(`${S}/usuarios/personas-sin-cuenta`, { params: { id_rol: idRol, q } }),
    enabled: !!idRol,
  })
}

export function useSolicitudesRecuperacion(habilitado = true) {
  return useQuery({
    queryKey: ['seguridad', 'solicitudes'],
    queryFn: () => api<SolicitudRecuperacion[]>(`${S}/usuarios/solicitudes-recuperacion`),
    enabled: habilitado,
    refetchInterval: 60_000,
  })
}

function useInvalidarSeguridad() {
  const cliente = useQueryClient()
  return () => cliente.invalidateQueries({ queryKey: ['seguridad'] })
}

export function useCrearUsuario() {
  const invalidar = useInvalidarSeguridad()
  return useMutation({
    mutationFn: (d: { ci_persona: string; id_rol: number; nombre_usuario: string; contrasena: string }) =>
      api<Usuario>(`${S}/usuarios`, { metodo: 'POST', cuerpo: d }),
    onSuccess: invalidar,
  })
}

export function useActualizarUsuario() {
  const invalidar = useInvalidarSeguridad()
  return useMutation({
    mutationFn: ({ id, ...d }: { id: number; nombre_usuario?: string; id_rol?: number; estado_usuario?: string }) =>
      api<Usuario>(`${S}/usuarios/${id}`, { metodo: 'PATCH', cuerpo: d }),
    onSuccess: invalidar,
  })
}

export function useDesactivarUsuario() {
  const invalidar = useInvalidarSeguridad()
  return useMutation({
    mutationFn: (id: number) => api<Usuario>(`${S}/usuarios/${id}`, { metodo: 'DELETE' }),
    onSuccess: invalidar,
  })
}

export function useRestablecerContrasena() {
  const invalidar = useInvalidarSeguridad()
  return useMutation({
    mutationFn: (id: number) =>
      api<{ contrasena_temporal: string; mensaje: string }>(`${S}/usuarios/${id}/restablecer-contrasena`, {
        metodo: 'POST',
      }),
    onSuccess: invalidar,
  })
}

// ---- CU03 -------------------------------------------------------------------
export function useRoles() {
  return useQuery({ queryKey: ['seguridad', 'roles'], queryFn: () => api<RolDetalle[]>(`${S}/roles`) })
}

export function usePermisos() {
  return useQuery({ queryKey: ['seguridad', 'permisos'], queryFn: () => api<Permiso[]>(`${S}/permisos`) })
}

export function useActualizarRol() {
  const invalidar = useInvalidarSeguridad()
  return useMutation({
    mutationFn: ({ id, descripcion_rol }: { id: number; descripcion_rol: string }) =>
      api<RolDetalle>(`${S}/roles/${id}`, { metodo: 'PATCH', cuerpo: { descripcion_rol } }),
    onSuccess: invalidar,
  })
}

// ---- CU04 -------------------------------------------------------------------
export function useBitacora(f: FiltrosBitacora & { pagina: number; tamano: number }) {
  return useQuery({
    queryKey: ['seguridad', 'bitacora', f],
    queryFn: () => api<Pagina<RegistroBitacora>>(`${S}/bitacora`, { params: f }),
    placeholderData: keepPreviousData,
  })
}

export function useOpcionesBitacora() {
  return useQuery({
    queryKey: ['seguridad', 'bitacora-opciones'],
    queryFn: () => api<OpcionesBitacora>(`${S}/bitacora/opciones`),
  })
}

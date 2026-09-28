/** Contexto de la sesión: quién está conectado y cómo entrar o salir. */
import { createContext, useContext } from 'react'
import type { DatosLogin, Perfil } from '@/paquetes/seguridad/schemas'

export type ContextoSesion = {
  usuario: Perfil | null
  cargando: boolean
  iniciarSesion: (datos: DatosLogin) => Promise<Perfil>
  cerrarSesion: () => void
  recargarPerfil: () => Promise<void>
}

export const Contexto = createContext<ContextoSesion | null>(null)

export function useSesion(): ContextoSesion {
  const valor = useContext(Contexto)
  if (!valor) throw new Error('useSesion debe usarse dentro de <ProveedorSesion>')
  return valor
}

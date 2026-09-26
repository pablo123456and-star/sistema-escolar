/**
 * Guarda la sesión del usuario (token, perfil y rol) y la comparte con toda la app.
 *
 * PENDIENTE (CU01): iniciar sesión con POST /api/v1/seguridad/sesion, guardar el
 * token que devuelve el backend, cargar el perfil (GET /api/v1/seguridad/perfil)
 * y cerrar sesión borrando el token.
 */
import type { ReactNode } from 'react'

export default function ProveedorSesion({ children }: { children: ReactNode }) {
  return <>{children}</>
}

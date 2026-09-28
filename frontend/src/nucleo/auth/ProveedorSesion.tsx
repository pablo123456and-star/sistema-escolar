/**
 * Guarda la sesión del usuario (token, perfil y rol) y la comparte con toda la app.
 *
 * CU01: inicia sesión con POST /api/v1/seguridad/sesion, guarda el token que devuelve
 * el backend, carga el perfil (GET /api/v1/seguridad/perfil) al abrir la app y
 * cierra sesión borrando el token. Si el backend avisa que la sesión venció, la cierra.
 */
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { EVENTO_SESION_VENCIDA } from '@/nucleo/api'
import { borrarToken, guardarToken, obtenerToken } from '@/nucleo/auth/almacen'
import { Contexto, type ContextoSesion } from '@/nucleo/auth/contexto'
import { seguridadApi } from '@/paquetes/seguridad/api'
import type { DatosLogin, Perfil } from '@/paquetes/seguridad/schemas'

export default function ProveedorSesion({ children }: { children: ReactNode }) {
  const clienteQuery = useQueryClient()
  const [usuario, setUsuario] = useState<Perfil | null>(null)
  const [cargando, setCargando] = useState(() => obtenerToken() !== null)

  const recargarPerfil = useCallback(async () => {
    if (!obtenerToken()) {
      setUsuario(null)
      return
    }
    try {
      setUsuario(await seguridadApi.perfil())
    } catch {
      setUsuario(null)
    }
  }, [])

  // Al abrir la app: si hay un token guardado, se recupera el perfil
  useEffect(() => {
    if (!obtenerToken()) return
    let vigente = true
    seguridadApi
      .perfil()
      .then((perfil) => vigente && setUsuario(perfil))
      .catch(() => vigente && setUsuario(null))
      .finally(() => vigente && setCargando(false))
    return () => {
      vigente = false
    }
  }, [])

  useEffect(() => {
    const alVencer = () => {
      setUsuario(null)
      clienteQuery.clear()
      toast.warning('Su sesión venció. Vuelva a iniciar sesión.')
    }
    window.addEventListener(EVENTO_SESION_VENCIDA, alVencer)
    return () => window.removeEventListener(EVENTO_SESION_VENCIDA, alVencer)
  }, [clienteQuery])

  const iniciarSesion = useCallback(async (datos: DatosLogin) => {
    const sesion = await seguridadApi.iniciarSesion(datos)
    guardarToken(sesion.token, datos.recordar)
    setUsuario(sesion.usuario)
    return sesion.usuario
  }, [])

  const cerrarSesion = useCallback(() => {
    borrarToken()
    setUsuario(null)
    clienteQuery.clear()
  }, [clienteQuery])

  const valor = useMemo<ContextoSesion>(
    () => ({ usuario, cargando, iniciarSesion, cerrarSesion, recargarPerfil }),
    [usuario, cargando, iniciarSesion, cerrarSesion, recargarPerfil],
  )

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>
}

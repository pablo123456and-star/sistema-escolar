/**
 * Cliente HTTP hacia el backend FastAPI. Por defecto usa "/api/v1" (el proxy de Vite lo
 * reenvía al backend); con VITE_API_URL se puede apuntar a otra dirección.
 * Toda la información (incluido el login) se pide al backend: el frontend
 * nunca se conecta a la base de datos.
 * Agrega el token de la sesión en la cabecera Authorization: Bearer <token>.
 * Si el backend responde 401 con un token enviado, la sesión venció: se borra
 * el token y se avisa a la app (evento "sesion-vencida").
 */
import { borrarToken, obtenerToken } from '@/nucleo/auth/almacen'

const URL_API = (import.meta.env.VITE_API_URL as string | undefined) || '/api/v1'

export const EVENTO_SESION_VENCIDA = 'sesion-vencida'

export class ErrorApi extends Error {
  estado: number
  codigo?: string

  constructor(estado: number, mensaje: string, codigo?: string) {
    super(mensaje)
    this.estado = estado
    this.codigo = codigo
  }
}

type Parametros = Record<string, string | number | boolean | null | undefined>

type Opciones = {
  metodo?: 'GET' | 'POST' | 'PATCH' | 'DELETE'
  cuerpo?: unknown
  params?: Parametros
}

function armarUrl(ruta: string, params?: Parametros) {
  const url = new URL(URL_API.replace(/\/$/, '') + ruta, window.location.origin)
  for (const [clave, valor] of Object.entries(params ?? {})) {
    if (valor !== undefined && valor !== null && valor !== '') url.searchParams.set(clave, String(valor))
  }
  return url
}

export async function api<T>(ruta: string, { metodo = 'GET', cuerpo, params }: Opciones = {}): Promise<T> {
  const token = obtenerToken()
  const cabeceras: Record<string, string> = { Accept: 'application/json' }
  if (cuerpo !== undefined) cabeceras['Content-Type'] = 'application/json'
  if (token) cabeceras.Authorization = `Bearer ${token}`

  let respuesta: Response
  try {
    respuesta = await fetch(armarUrl(ruta, params), {
      method: metodo,
      headers: cabeceras,
      body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
    })
  } catch {
    throw new ErrorApi(0, 'No se pudo conectar con el servidor (o tuvo un error interno). Verifique que el backend esté levantado y revise su consola.')
  }

  if (respuesta.status === 204) return undefined as T
  const datos = await respuesta.json().catch(() => null)

  if (!respuesta.ok) {
    if (respuesta.status === 401 && token) {
      borrarToken()
      window.dispatchEvent(new Event(EVENTO_SESION_VENCIDA))
    }
    const detalle = typeof datos?.detalle === 'string' ? datos.detalle : 'Ocurrió un error inesperado.'
    throw new ErrorApi(respuesta.status, detalle, datos?.codigo)
  }
  return datos as T
}

/** Mensaje legible de cualquier error (para mostrar en pantalla). */
export function mensajeError(error: unknown): string {
  if (error instanceof ErrorApi) return error.message
  if (error instanceof Error) return error.message
  return 'Ocurrió un error inesperado.'
}

/** Respuesta paginada del backend. */
export type Pagina<T> = { items: T[]; total: number; pagina: number; tamano: number }

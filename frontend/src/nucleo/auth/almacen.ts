/**
 * Dónde se guarda el token de la sesión.
 * "Recordar sesión" -> localStorage (sobrevive al cerrar el navegador);
 * si no -> sessionStorage (se borra al cerrar la pestaña).
 */
const CLAVE = 'sesion_token'

function leer(almacen: Storage): string | null {
  try {
    return almacen.getItem(CLAVE)
  } catch {
    return null
  }
}

export function obtenerToken(): string | null {
  return leer(sessionStorage) ?? leer(localStorage)
}

export function guardarToken(token: string, recordar: boolean) {
  borrarToken()
  try {
    ;(recordar ? localStorage : sessionStorage).setItem(CLAVE, token)
  } catch {
    // sin almacenamiento disponible: la sesión dura mientras la página esté abierta
  }
}

export function borrarToken() {
  for (const almacen of [localStorage, sessionStorage]) {
    try {
      almacen.removeItem(CLAVE)
    } catch {
      // nada que borrar
    }
  }
}

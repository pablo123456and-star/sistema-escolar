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

/**
 * Último usuario que tuvo sesión en esta pestaña. Al volver a iniciar sesión, solo se regresa
 * a la página donde se cortó la sesión si entra la misma persona; si entra otra, va a su inicio.
 */
const CLAVE_ULTIMO = 'ultimo_usuario'

export function guardarUltimoUsuario(id_usuario: number) {
  try {
    sessionStorage.setItem(CLAVE_ULTIMO, String(id_usuario))
  } catch {
    // sin almacenamiento disponible: siempre se entra al inicio
  }
}

export function leerUltimoUsuario(): number | null {
  try {
    const valor = sessionStorage.getItem(CLAVE_ULTIMO)
    return valor ? Number(valor) : null
  } catch {
    return null
  }
}

/** Al cerrar sesión con el botón se olvida quién estaba: el siguiente que entre va a su inicio. */
export function borrarUltimoUsuario() {
  try {
    sessionStorage.removeItem(CLAVE_ULTIMO)
  } catch {
    // nada que borrar
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

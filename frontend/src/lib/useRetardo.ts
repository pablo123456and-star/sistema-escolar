/** Devuelve el valor recién cuando dejó de cambiar por unos milisegundos (para búsquedas mientras se escribe). */
import { useEffect, useState } from 'react'

export function useRetardo<T>(valor: T, ms = 300): T {
  const [retardado, setRetardado] = useState(valor)
  useEffect(() => {
    const t = setTimeout(() => setRetardado(valor), ms)
    return () => clearTimeout(t)
  }, [valor, ms])
  return retardado
}

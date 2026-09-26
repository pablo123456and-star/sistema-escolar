/**
 * Protege una ruta: si no hay sesión, redirige al login; si el rol no está
 * permitido, muestra "sin acceso".
 *
 * PENDIENTE: validar sesión y rol (administrador, profesor, estudiante, tutor).
 */
import type { ReactNode } from 'react'

type Props = { roles?: string[]; children: ReactNode }

export default function RutaProtegida({ children }: Props) {
  return <>{children}</>
}

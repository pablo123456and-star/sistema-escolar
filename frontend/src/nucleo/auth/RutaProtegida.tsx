/**
 * Protege una ruta: si no hay sesión, redirige al login; si el rol no está
 * permitido, muestra "sin acceso". (El backend vuelve a validar el rol en cada petición.)
 */
import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router'
import { Loader2Icon, ShieldAlertIcon } from 'lucide-react'
import { useSesion } from '@/nucleo/auth/contexto'
import type { Rol } from '@/paquetes/seguridad/schemas'

type Props = { roles?: Rol[]; children: ReactNode }

export default function RutaProtegida({ roles, children }: Props) {
  const { usuario, cargando } = useSesion()
  const ubicacion = useLocation()

  if (cargando) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center text-muted-foreground">
        <Loader2Icon className="mr-2 size-5 animate-spin" /> Cargando...
      </div>
    )
  }
  if (!usuario) return <Navigate to="/login" replace state={{ desde: ubicacion.pathname }} />
  if (roles && !roles.includes(usuario.rol)) {
    return (
      <div className="mx-auto mt-16 max-w-md rounded-xl border bg-card p-8 text-center shadow-sm">
        <ShieldAlertIcon className="mx-auto size-10 text-amber-500" />
        <h1 className="mt-3 text-lg font-semibold">Sin acceso</h1>
        <p className="mt-1 text-sm text-muted-foreground">Su rol no tiene permiso para ver esta pantalla.</p>
      </div>
    )
  }
  return <>{children}</>
}

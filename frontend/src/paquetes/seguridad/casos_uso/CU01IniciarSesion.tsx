/**
 * CU01 - Iniciar sesión (incluye recuperar contraseña)
 * Paquete: seguridad
 *
 * Actores ........: Todos
 * Rol del sistema : administrador, profesor, estudiante, tutor
 * Backend ........: backend/app/paquetes/seguridad/casos_uso/cu01_iniciar_sesion.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Pantallas: iniciar sesión (/login) y recuperar contraseña (/recuperar-contrasena).
 * Cerrar sesión y "Mi perfil" (cambiar contraseña) están en el menú del usuario (LayoutPrincipal).
 *
 * Precondición:  El usuario existe, está 'activo' y su persona está 'activo'.
 * Postcondición: El usuario recibe un token válido; el sistema conoce su rol y le muestra el menú que le corresponde.
 *
 * Estado: IMPLEMENTADO.
 */
import { useState, type ReactNode } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router'
import { Controller, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeftIcon, CircleCheckIcon, EyeIcon, EyeOffIcon, LockIcon, MailIcon, UserIcon } from 'lucide-react'
import { Button } from '@/componentes/ui/button'
import { Checkbox } from '@/componentes/ui/checkbox'
import { Input } from '@/componentes/ui/input'
import { Label } from '@/componentes/ui/label'
import { mensajeError } from '@/nucleo/api'
import { useSesion } from '@/nucleo/auth/contexto'
import { seguridadApi } from '../api'
import MarcoAcceso from '../componentes/MarcoAcceso'
import { esquemaLogin, esquemaRecuperar, type DatosLogin } from '../schemas'

function CampoConIcono({ icono, error, children }: { icono: ReactNode; error?: string; children: ReactNode }) {
  return (
    <div className="grid gap-1">
      <div className="relative">
        <span className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-slate-400">{icono}</span>
        {children}
      </div>
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  )
}

export default function CU01IniciarSesion() {
  const { usuario, iniciarSesion } = useSesion()
  const navegar = useNavigate()
  const ubicacion = useLocation()
  const [verContrasena, setVerContrasena] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const form = useForm<DatosLogin>({
    resolver: zodResolver(esquemaLogin),
    defaultValues: { identificador: '', contrasena: '', recordar: false },
  })

  const destino = (ubicacion.state as { desde?: string } | null)?.desde ?? '/'
  if (usuario) return <Navigate to={destino} replace />

  const enviar = form.handleSubmit(async (datos) => {
    setError(null)
    try {
      await iniciarSesion(datos)
      navegar(destino, { replace: true })
    } catch (e) {
      setError(mensajeError(e))
    }
  })

  const e = form.formState.errors
  return (
    <MarcoAcceso>
      <form onSubmit={enviar} className="w-full max-w-sm space-y-5" noValidate>
        <div className="text-center">
          <h1 className="text-3xl font-bold text-[#12306B]">Iniciar sesión</h1>
          <p className="mt-1 text-slate-500">Ingrese sus credenciales para continuar</p>
        </div>

        {error && <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 ring-1 ring-rose-200">{error}</p>}

        <CampoConIcono icono={<UserIcon className="size-5" />} error={e.identificador?.message}>
          <Input
            placeholder="Usuario o correo electrónico"
            autoComplete="username"
            autoFocus
            className="h-11 pl-10"
            aria-label="Usuario o correo electrónico"
            {...form.register('identificador')}
          />
        </CampoConIcono>

        <CampoConIcono icono={<LockIcon className="size-5" />} error={e.contrasena?.message}>
          <Input
            type={verContrasena ? 'text' : 'password'}
            placeholder="Contraseña"
            autoComplete="current-password"
            className="h-11 pr-10 pl-10"
            aria-label="Contraseña"
            {...form.register('contrasena')}
          />
          <button
            type="button"
            className="absolute top-1/2 right-3 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            onClick={() => setVerContrasena((v) => !v)}
            aria-label={verContrasena ? 'Ocultar contraseña' : 'Mostrar contraseña'}
          >
            {verContrasena ? <EyeOffIcon className="size-5" /> : <EyeIcon className="size-5" />}
          </button>
        </CampoConIcono>

        <Controller
          control={form.control}
          name="recordar"
          render={({ field }) => (
            <div className="flex items-center gap-2">
              <Checkbox id="recordar" checked={field.value} onCheckedChange={(v) => field.onChange(v === true)} />
              <Label htmlFor="recordar" className="font-normal">Recordar sesión</Label>
            </div>
          )}
        />

        <Button type="submit" className="h-11 w-full text-base" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? 'Ingresando...' : 'Iniciar sesión'}
        </Button>

        <p className="text-center">
          <Link to="/recuperar-contrasena" className="text-sm text-blue-600 hover:underline">
            ¿Olvidó su contraseña?
          </Link>
        </p>
      </form>
    </MarcoAcceso>
  )
}

/** CU01 - flujo alternativo: recuperar contraseña. */
export function CU01RecuperarContrasena() {
  const [mensaje, setMensaje] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const form = useForm<{ identificador: string }>({
    resolver: zodResolver(esquemaRecuperar),
    defaultValues: { identificador: '' },
  })

  const enviar = form.handleSubmit(async ({ identificador }) => {
    setError(null)
    try {
      setMensaje((await seguridadApi.recuperar(identificador)).mensaje)
    } catch (e) {
      setError(mensajeError(e))
    }
  })

  return (
    <MarcoAcceso>
      <div className="w-full max-w-sm space-y-5">
        <Link to="/login" className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline">
          <ArrowLeftIcon className="size-4" /> Volver al inicio de sesión
        </Link>
        <div className="text-center">
          <h1 className="text-3xl font-bold text-[#12306B]">Recuperar contraseña</h1>
          <p className="mt-1 text-slate-500">
            Ingrese su usuario o correo electrónico institucional para solicitar el restablecimiento.
          </p>
        </div>

        {mensaje ? (
          <div className="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-800 ring-1 ring-emerald-200">
            <CircleCheckIcon className="mb-2 size-6 text-emerald-600" />
            {mensaje}
          </div>
        ) : (
          <form onSubmit={enviar} className="space-y-5" noValidate>
            {error && <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 ring-1 ring-rose-200">{error}</p>}
            <div className="grid gap-1.5">
              <Label htmlFor="identificador">Usuario o correo electrónico institucional</Label>
              <CampoConIcono icono={<MailIcon className="size-5" />} error={form.formState.errors.identificador?.message}>
                <Input
                  id="identificador"
                  placeholder="usuario@mariscalsucreg.edu.bo"
                  className="h-11 pl-10"
                  autoFocus
                  {...form.register('identificador')}
                />
              </CampoConIcono>
            </div>
            <Button type="submit" className="h-11 w-full text-base" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? 'Enviando...' : 'Enviar solicitud'}
            </Button>
          </form>
        )}
      </div>
    </MarcoAcceso>
  )
}

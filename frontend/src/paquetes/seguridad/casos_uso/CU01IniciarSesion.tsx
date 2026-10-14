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
import {
  ArrowLeftIcon,
  CircleCheckIcon,
  ClockIcon,
  EyeIcon,
  EyeOffIcon,
  LockIcon,
  MailIcon,
  UserIcon,
} from 'lucide-react'
import { Button } from '@/componentes/ui/button'
import { Checkbox } from '@/componentes/ui/checkbox'
import { Input } from '@/componentes/ui/input'
import { Label } from '@/componentes/ui/label'
import { mensajeError } from '@/nucleo/api'
import { useSesion } from '@/nucleo/auth/contexto'
import { seguridadApi } from '../api'
import MarcoAcceso from '../componentes/MarcoAcceso'
import { esquemaLogin, esquemaRecuperar, type DatosLogin, type DatosRecuperar } from '../schemas'

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
  const esBloqueo =
    error &&
    (error.toLowerCase().includes('bloquead') ||
      error.toLowerCase().includes('intentos fallidos') ||
      error.toLowerCase().includes('esperar'))

  return (
    <MarcoAcceso>
      <form onSubmit={enviar} className="w-full max-w-sm space-y-5" noValidate>
        <div className="text-center">
          <h1 className="text-3xl font-bold text-[#12306B]">Iniciar sesión</h1>
          <p className="mt-1 text-slate-500">Ingrese sus credenciales para continuar</p>
        </div>

        {error && (
          esBloqueo ? (
            <div className="rounded-xl bg-amber-50 p-4 text-sm text-amber-900 ring-1 ring-amber-300 space-y-1.5 shadow-sm">
              <div className="flex items-center gap-2 font-semibold text-amber-800">
                <ClockIcon className="size-5 text-amber-600 shrink-0" />
                <span>Acceso bloqueado temporalmente</span>
              </div>
              <p className="text-xs text-amber-700 leading-relaxed">{error}</p>
            </div>
          ) : (
            <div className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 ring-1 ring-rose-200">
              {error}
            </div>
          )
        )}

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
              <Label htmlFor="recordar" className="font-normal cursor-pointer">
                Recordar sesión
              </Label>
            </div>
          )}
        />

        <Button type="submit" className="h-11 w-full text-base font-semibold" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? 'Ingresando...' : 'Iniciar sesión'}
        </Button>

        <p className="text-center">
          <Link to="/recuperar-contrasena" className="text-sm text-blue-600 hover:underline font-medium">
            ¿Olvidaste tu contraseña?
          </Link>
        </p>
      </form>
    </MarcoAcceso>
  )
}

/** CU01 - flujo alternativo: recuperar contraseña por correo. */
export function CU01RecuperarContrasena() {
  const [mensaje, setMensaje] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const form = useForm<DatosRecuperar>({
    resolver: zodResolver(esquemaRecuperar),
    defaultValues: { correo: '' },
  })

  const enviar = form.handleSubmit(async ({ correo }) => {
    setError(null)
    try {
      setMensaje((await seguridadApi.recuperar(correo)).mensaje)
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
          <p className="mt-1 text-slate-500 text-sm">
            Introduzca el correo electrónico vinculado a su cuenta para recibir las instrucciones y un enlace seguro de recuperación.
          </p>
        </div>

        {mensaje ? (
          <div className="space-y-4">
            <div className="rounded-xl bg-emerald-50 p-4 text-sm text-emerald-800 ring-1 ring-emerald-200 space-y-2">
              <div className="flex items-center gap-2 font-semibold">
                <CircleCheckIcon className="size-5 text-emerald-600 shrink-0" />
                <span>Instrucciones enviadas</span>
              </div>
              <p className="text-xs leading-relaxed text-emerald-700">{mensaje}</p>
              <p className="text-xs text-emerald-600 italic">
                El enlace es de un solo uso y caduca en 15 minutos.
              </p>
            </div>
            <Button asChild variant="outline" className="w-full">
              <Link to="/login">Regresar al inicio de sesión</Link>
            </Button>
          </div>
        ) : (
          <form onSubmit={enviar} className="space-y-5" noValidate>
            {error && <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 ring-1 ring-rose-200">{error}</p>}
            <div className="grid gap-1.5">
              <Label htmlFor="correo">Correo electrónico vinculado a la cuenta</Label>
              <CampoConIcono icono={<MailIcon className="size-5" />} error={form.formState.errors.correo?.message}>
                <Input
                  id="correo"
                  type="email"
                  placeholder="usuario@mariscalsucreg.edu.bo"
                  className="h-11 pl-10"
                  autoComplete="email"
                  autoFocus
                  {...form.register('correo')}
                />
              </CampoConIcono>
            </div>
            <Button type="submit" className="h-11 w-full text-base font-semibold" disabled={form.formState.isSubmitting}>
              {form.formState.isSubmitting ? 'Enviando...' : 'Enviar instrucciones'}
            </Button>
          </form>
        )}
      </div>
    </MarcoAcceso>
  )
}

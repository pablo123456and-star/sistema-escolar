/**
 * CU01 - Restablecer contraseña con token seguro de recuperación.
 * Paquete: seguridad
 *
 * Flujo: El usuario recibe un enlace por correo -> abre /restablecer-contrasena?token=...
 * -> se valida el token en el servidor -> establece su nueva contraseña cumpliendo
 * requisitos de seguridad -> token se invalida y se retorna al login.
 */
import { useEffect, useState, type ReactNode } from 'react'
import { Link, useSearchParams } from 'react-router'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import {
  ArrowLeftIcon,
  CheckCircle2Icon,
  CircleAlertIcon,
  CircleCheckIcon,
  EyeIcon,
  EyeOffIcon,
  KeyRoundIcon,
  Loader2Icon,
  LockIcon,
  ShieldCheckIcon,
  XCircleIcon,
} from 'lucide-react'
import { Button } from '@/componentes/ui/button'
import { Input } from '@/componentes/ui/input'
import { Label } from '@/componentes/ui/label'
import { mensajeError } from '@/nucleo/api'
import { seguridadApi } from '../api'
import MarcoAcceso from '../componentes/MarcoAcceso'
import {
  esquemaRestablecer,
  REQUISITOS_CONTRASENA,
  type DatosRestablecer,
} from '../schemas'

function CampoConIcono({
  icono,
  error,
  children,
}: {
  icono: ReactNode
  error?: string
  children: ReactNode
}) {
  return (
    <div className="grid gap-1">
      <div className="relative">
        <span className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-slate-400">
          {icono}
        </span>
        {children}
      </div>
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  )
}

export default function RestablecerContrasena() {
  const [params] = useSearchParams()
  const token = params.get('token') ?? ''

  const [cargandoToken, setCargandoToken] = useState(true)
  const [tokenValido, setTokenValido] = useState(false)
  const [datosUsuario, setDatosUsuario] = useState<{ usuario?: string; nombre?: string } | null>(null)
  const [errorToken, setErrorToken] = useState<string | null>(null)

  const [verNueva, setVerNueva] = useState(false)
  const [verConfirmar, setVerConfirmar] = useState(false)
  const [exito, setExito] = useState(false)
  const [errorGuardar, setErrorGuardar] = useState<string | null>(null)

  const form = useForm<DatosRestablecer>({
    resolver: zodResolver(esquemaRestablecer),
    defaultValues: { nueva: '', confirmar: '' },
    mode: 'onChange',
  })

  const valorNueva = form.watch('nueva') ?? ''

  useEffect(() => {
    if (!token) {
      setCargandoToken(false)
      setErrorToken('No se proporcionó un enlace válido o falta el token de recuperación.')
      return
    }

    let activo = true
    seguridadApi
      .validarToken(token)
      .then((res) => {
        if (!activo) return
        if (res.valido) {
          setTokenValido(true)
          setDatosUsuario({ usuario: res.nombre_usuario, nombre: res.nombre_completo })
        } else {
          setTokenValido(false)
          setErrorToken(res.mensaje)
        }
      })
      .catch((e) => {
        if (!activo) return
        setTokenValido(false)
        setErrorToken(mensajeError(e))
      })
      .finally(() => {
        if (activo) setCargandoToken(false)
      })

    return () => {
      activo = false
    }
  }, [token])

  const guardar = form.handleSubmit(async (datos) => {
    setErrorGuardar(null)
    try {
      await seguridadApi.restablecerContrasena(token, datos.nueva)
      setExito(true)
    } catch (e) {
      setErrorGuardar(mensajeError(e))
    }
  })

  return (
    <MarcoAcceso>
      <div className="w-full max-w-sm space-y-5">
        <Link to="/login" className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline">
          <ArrowLeftIcon className="size-4" /> Volver al inicio de sesión
        </Link>

        <div className="text-center">
          <h1 className="text-3xl font-bold text-[#12306B]">Nueva contraseña</h1>
          <p className="mt-1 text-slate-500">
            Establezca una nueva contraseña segura para su cuenta escolar.
          </p>
        </div>

        {cargandoToken && (
          <div className="flex flex-col items-center justify-center gap-3 py-10 text-slate-500">
            <Loader2Icon className="size-8 animate-spin text-blue-600" />
            <p className="text-sm">Verificando enlace de recuperación...</p>
          </div>
        )}

        {!cargandoToken && !tokenValido && (
          <div className="space-y-4">
            <div className="rounded-xl bg-rose-50 p-4 text-sm text-rose-800 ring-1 ring-rose-200">
              <CircleAlertIcon className="mb-2 size-6 text-rose-600" />
              <p className="font-semibold">Enlace inválido o caducado</p>
              <p className="mt-1">{errorToken}</p>
            </div>
            <p className="text-xs text-slate-500 text-center">
              Los enlaces de recuperación caducan a los 15 minutos y solo pueden usarse una vez.
            </p>
            <Button asChild className="w-full" variant="outline">
              <Link to="/recuperar-contrasena">Solicitar un nuevo enlace</Link>
            </Button>
          </div>
        )}

        {!cargandoToken && tokenValido && exito && (
          <div className="space-y-5">
            <div className="rounded-xl bg-emerald-50 p-5 text-emerald-800 ring-1 ring-emerald-200 text-center space-y-2">
              <CircleCheckIcon className="mx-auto size-10 text-emerald-600" />
              <p className="text-base font-semibold">¡Contraseña actualizada!</p>
              <p className="text-sm text-emerald-700">
                Su contraseña ha sido restablecida exitosamente. Ya puede iniciar sesión con su nueva clave.
              </p>
            </div>
            <Button asChild className="w-full h-11 text-base">
              <Link to="/login">Ir a iniciar sesión</Link>
            </Button>
          </div>
        )}

        {!cargandoToken && tokenValido && !exito && (
          <form onSubmit={guardar} className="space-y-5" noValidate>
            {datosUsuario?.nombre && (
              <div className="rounded-lg bg-blue-50/60 p-3 text-xs text-blue-900 border border-blue-100 flex items-center gap-2">
                <ShieldCheckIcon className="size-4 text-blue-600 shrink-0" />
                <span>
                  Restableciendo cuenta de <strong>{datosUsuario.nombre}</strong> ({datosUsuario.usuario})
                </span>
              </div>
            )}

            {errorGuardar && (
              <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700 ring-1 ring-rose-200">
                {errorGuardar}
              </p>
            )}

            <div className="grid gap-1.5">
              <Label htmlFor="nueva">Nueva contraseña</Label>
              <CampoConIcono icono={<LockIcon className="size-5" />} error={form.formState.errors.nueva?.message}>
                <Input
                  id="nueva"
                  type={verNueva ? 'text' : 'password'}
                  placeholder="Ingrese nueva contraseña"
                  autoComplete="new-password"
                  autoFocus
                  className="h-11 pr-10 pl-10"
                  {...form.register('nueva')}
                />
                <button
                  type="button"
                  className="absolute top-1/2 right-3 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  onClick={() => setVerNueva((v) => !v)}
                  aria-label={verNueva ? 'Ocultar' : 'Mostrar'}
                >
                  {verNueva ? <EyeOffIcon className="size-5" /> : <EyeIcon className="size-5" />}
                </button>
              </CampoConIcono>
            </div>

            <div className="grid gap-1.5">
              <Label htmlFor="confirmar">Confirmar nueva contraseña</Label>
              <CampoConIcono icono={<LockIcon className="size-5" />} error={form.formState.errors.confirmar?.message}>
                <Input
                  id="confirmar"
                  type={verConfirmar ? 'text' : 'password'}
                  placeholder="Repita la nueva contraseña"
                  autoComplete="new-password"
                  className="h-11 pr-10 pl-10"
                  {...form.register('confirmar')}
                />
                <button
                  type="button"
                  className="absolute top-1/2 right-3 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  onClick={() => setVerConfirmar((v) => !v)}
                  aria-label={verConfirmar ? 'Ocultar' : 'Mostrar'}
                >
                  {verConfirmar ? <EyeOffIcon className="size-5" /> : <EyeIcon className="size-5" />}
                </button>
              </CampoConIcono>
            </div>

            {/* Checklist interactivo de requisitos de seguridad (debajo de ambos campos) */}
            <div className="rounded-lg bg-slate-50 p-3 border border-slate-200/80 space-y-1.5 text-xs">
              <p className="font-semibold text-slate-700 mb-1 flex items-center gap-1.5">
                <KeyRoundIcon className="size-3.5 text-slate-500" />
                Requisitos de seguridad:
              </p>
              {REQUISITOS_CONTRASENA.map((req) => {
                const cumplido = req.test(valorNueva)
                return (
                  <div
                    key={req.id}
                    className={`flex items-center gap-1.5 transition-colors ${
                      cumplido ? 'text-emerald-700 font-medium' : 'text-slate-500'
                    }`}
                  >
                    {cumplido ? (
                      <CheckCircle2Icon className="size-3.5 text-emerald-600 shrink-0" />
                    ) : (
                      <XCircleIcon className="size-3.5 text-slate-300 shrink-0" />
                    )}
                    <span>{req.etiqueta}</span>
                  </div>
                )
              })}
            </div>

            <Button
              type="submit"
              className="h-11 w-full text-base"
              disabled={form.formState.isSubmitting}
            >
              {form.formState.isSubmitting ? 'Guardando contraseña...' : 'Guardar nueva contraseña'}
            </Button>
          </form>
        )}
      </div>
    </MarcoAcceso>
  )
}

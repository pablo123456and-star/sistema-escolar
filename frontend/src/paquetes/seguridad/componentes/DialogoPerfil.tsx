import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { CheckCircle2Icon, EyeIcon, EyeOffIcon, KeyRoundIcon, XCircleIcon } from 'lucide-react'
import { toast } from 'sonner'
import type { z } from 'zod'
import { Campo, InsigniaRol } from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/componentes/ui/dialog'
import { Input } from '@/componentes/ui/input'
import { Separator } from '@/componentes/ui/separator'
import { fechaHora } from '@/lib/formato'
import { mensajeError } from '@/nucleo/api'
import { useSesion } from '@/nucleo/auth/contexto'
import { seguridadApi } from '../api'
import { esquemaCambiarContrasena, REQUISITOS_CONTRASENA } from '../schemas'

type Datos = z.infer<typeof esquemaCambiarContrasena>

export default function DialogoPerfil({ abierto, onCambiar }: { abierto: boolean; onCambiar: (v: boolean) => void }) {
  const { usuario } = useSesion()
  const [guardando, setGuardando] = useState(false)
  const [verActual, setVerActual] = useState(false)
  const [verNueva, setVerNueva] = useState(false)
  const [verConfirmar, setVerConfirmar] = useState(false)

  const form = useForm<Datos>({
    resolver: zodResolver(esquemaCambiarContrasena),
    defaultValues: { actual: '', nueva: '', confirmar: '' },
    mode: 'onChange',
  })

  const valorNueva = form.watch('nueva') ?? ''

  if (!usuario) return null

  const guardar = form.handleSubmit(async ({ actual, nueva }) => {
    setGuardando(true)
    try {
      await seguridadApi.cambiarContrasena({ actual, nueva })
      toast.success('Contraseña actualizada.')
      form.reset()
      onCambiar(false)
    } catch (e) {
      toast.error(mensajeError(e))
    } finally {
      setGuardando(false)
    }
  })

  const e = form.formState.errors
  return (
    <Dialog open={abierto} onOpenChange={(v) => { if (!v) form.reset(); onCambiar(v) }}>
      <DialogContent className="sm:max-w-md max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Mi perfil</DialogTitle>
          <DialogDescription>Datos de su cuenta y cambio de contraseña.</DialogDescription>
        </DialogHeader>
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1.5 text-sm">
          <dt className="text-slate-500">Nombre</dt>
          <dd className="font-medium">{usuario.nombres} {usuario.apellidos}</dd>
          <dt className="text-slate-500">Usuario</dt>
          <dd>{usuario.nombre_usuario}</dd>
          <dt className="text-slate-500">Rol</dt>
          <dd><InsigniaRol rol={usuario.rol} /> {usuario.cargo && <span className="text-slate-500">· {usuario.cargo}</span>}</dd>
          <dt className="text-slate-500">C.I.</dt>
          <dd>{usuario.ci}</dd>
          <dt className="text-slate-500">Correo</dt>
          <dd>{usuario.email ?? '—'}</dd>
          <dt className="text-slate-500">Último acceso</dt>
          <dd>{fechaHora(usuario.ultimo_acceso)}</dd>
        </dl>
        <Separator />
        <form id="form-contrasena" onSubmit={guardar} className="grid gap-3">
          <p className="text-sm font-medium">Cambiar contraseña</p>
          <Campo etiqueta="Contraseña actual" error={e.actual?.message} htmlFor="actual">
            <div className="relative">
              <Input
                id="actual"
                type={verActual ? 'text' : 'password'}
                autoComplete="current-password"
                className="pr-10"
                {...form.register('actual')}
              />
              <button
                type="button"
                className="absolute top-1/2 right-3 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                onClick={() => setVerActual((v) => !v)}
                aria-label={verActual ? 'Ocultar' : 'Mostrar'}
              >
                {verActual ? <EyeOffIcon className="size-4" /> : <EyeIcon className="size-4" />}
              </button>
            </div>
          </Campo>

          <Campo etiqueta="Nueva contraseña" error={e.nueva?.message} htmlFor="nueva">
            <div className="relative">
              <Input
                id="nueva"
                type={verNueva ? 'text' : 'password'}
                autoComplete="new-password"
                className="pr-10"
                {...form.register('nueva')}
              />
              <button
                type="button"
                className="absolute top-1/2 right-3 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                onClick={() => setVerNueva((v) => !v)}
                aria-label={verNueva ? 'Ocultar' : 'Mostrar'}
              >
                {verNueva ? <EyeOffIcon className="size-4" /> : <EyeIcon className="size-4" />}
              </button>
            </div>
          </Campo>

          <Campo etiqueta="Repetir nueva contraseña" error={e.confirmar?.message} htmlFor="confirmar">
            <div className="relative">
              <Input
                id="confirmar"
                type={verConfirmar ? 'text' : 'password'}
                autoComplete="new-password"
                className="pr-10"
                {...form.register('confirmar')}
              />
              <button
                type="button"
                className="absolute top-1/2 right-3 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                onClick={() => setVerConfirmar((v) => !v)}
                aria-label={verConfirmar ? 'Ocultar' : 'Mostrar'}
              >
                {verConfirmar ? <EyeOffIcon className="size-4" /> : <EyeIcon className="size-4" />}
              </button>
            </div>
          </Campo>

          {/* Checklist de requisitos de seguridad (debajo de ambos campos) */}
          <div className="rounded-lg bg-slate-50 p-2.5 border border-slate-200/80 space-y-1 text-xs">
            <p className="font-semibold text-slate-700 flex items-center gap-1">
              <KeyRoundIcon className="size-3 text-slate-500" />
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
                    <CheckCircle2Icon className="size-3 text-emerald-600 shrink-0" />
                  ) : (
                    <XCircleIcon className="size-3 text-slate-300 shrink-0" />
                  )}
                  <span>{req.etiqueta}</span>
                </div>
              )
            })}
          </div>
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={() => onCambiar(false)}>Cerrar</Button>
          <Button type="submit" form="form-contrasena" disabled={guardando}>Guardar contraseña</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/** CU01 - "Mi perfil": datos del usuario conectado y cambio de su propia contraseña. */
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
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
import { esquemaCambiarContrasena } from '../schemas'

type Datos = z.infer<typeof esquemaCambiarContrasena>

export default function DialogoPerfil({ abierto, onCambiar }: { abierto: boolean; onCambiar: (v: boolean) => void }) {
  const { usuario } = useSesion()
  const [guardando, setGuardando] = useState(false)
  const form = useForm<Datos>({
    resolver: zodResolver(esquemaCambiarContrasena),
    defaultValues: { actual: '', nueva: '', confirmar: '' },
  })

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
      <DialogContent className="sm:max-w-md">
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
            <Input id="actual" type="password" autoComplete="current-password" {...form.register('actual')} />
          </Campo>
          <Campo etiqueta="Nueva contraseña" error={e.nueva?.message} htmlFor="nueva">
            <Input id="nueva" type="password" autoComplete="new-password" {...form.register('nueva')} />
          </Campo>
          <Campo etiqueta="Repetir nueva contraseña" error={e.confirmar?.message} htmlFor="confirmar">
            <Input id="confirmar" type="password" autoComplete="new-password" {...form.register('confirmar')} />
          </Campo>
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={() => onCambiar(false)}>Cerrar</Button>
          <Button type="submit" form="form-contrasena" disabled={guardando}>Guardar contraseña</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

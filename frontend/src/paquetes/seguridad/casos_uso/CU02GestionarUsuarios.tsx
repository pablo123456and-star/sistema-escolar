/**
 * CU02 - Gestionar usuarios (CRUD)
 * Paquete: seguridad
 *
 * Actores ........: Administrador
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/seguridad/casos_uso/cu02_gestionar_usuarios.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Listar con filtros (búsqueda, rol, estado), crear, editar, desactivar y restablecer la
 * contraseña (atiende las solicitudes de recuperación del CU01).
 *
 * Precondición:  Sesión iniciada como administrador. La persona está registrada con la especialización del rol.
 * Postcondición: El usuario queda creado, actualizado o desactivado, y la acción queda en la bitácora.
 *
 * Estado: IMPLEMENTADO.
 */
import { useState } from 'react'
import { Controller, useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import type { z } from 'zod'
import { CopyIcon, KeyRoundIcon, PencilIcon, PlusIcon, RotateCcwIcon, SearchIcon, TrashIcon, TriangleAlertIcon } from 'lucide-react'
import Confirmar from '@/componentes/Confirmar'
import {
  AvatarIniciales,
  BotonAccion,
  Campo,
  EncabezadoPagina,
  FilaMensaje,
  InsigniaEstado,
  InsigniaRol,
  Paginacion,
} from '@/componentes/comunes'
import { TODOS, sinTodos } from '@/lib/filtros'
import { Button } from '@/componentes/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/componentes/ui/dialog'
import { Input } from '@/componentes/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { ETIQUETA_ROL, documento, fecha, fechaHora, hora } from '@/lib/formato'
import { useRetardo } from '@/lib/useRetardo'
import { mensajeError } from '@/nucleo/api'
import { useSesion } from '@/nucleo/auth/contexto'
import {
  useActualizarUsuario,
  useCrearUsuario,
  useDesactivarUsuario,
  usePersonasSinCuenta,
  useRestablecerContrasena,
  useRoles,
  useSolicitudesRecuperacion,
  useUsuarios,
} from '../api'
import { esquemaEditarUsuario, esquemaNuevoUsuario, type Usuario } from '../schemas'

const TAMANO = 10

export default function CU02GestionarUsuarios() {
  const { usuario: yo } = useSesion()
  const [busqueda, setBusqueda] = useState('')
  const [rol, setRol] = useState(TODOS)
  const [estado, setEstado] = useState(TODOS)
  const [pagina, setPagina] = useState(1)
  const q = useRetardo(busqueda)

  const roles = useRoles()
  const lista = useUsuarios({ q, id_rol: sinTodos(rol), estado: sinTodos(estado), pagina, tamano: TAMANO })
  const solicitudes = useSolicitudesRecuperacion()

  const [nuevo, setNuevo] = useState(false)
  const [editando, setEditando] = useState<Usuario | null>(null)
  const [aDesactivar, setADesactivar] = useState<Usuario | null>(null)
  const [aRestablecer, setARestablecer] = useState<{ id: number; nombre: string } | null>(null)
  const [temporal, setTemporal] = useState<{ contrasena: string; mensaje: string } | null>(null)

  const desactivar = useDesactivarUsuario()
  const reactivar = useActualizarUsuario()
  const restablecer = useRestablecerContrasena()

  const limpiar = () => {
    setBusqueda('')
    setRol(TODOS)
    setEstado(TODOS)
    setPagina(1)
  }

  const confirmarRestablecer = async () => {
    if (!aRestablecer) return
    try {
      const r = await restablecer.mutateAsync(aRestablecer.id)
      setTemporal({ contrasena: r.contrasena_temporal, mensaje: r.mensaje })
      setARestablecer(null)
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  const confirmarDesactivar = async () => {
    if (!aDesactivar) return
    try {
      await desactivar.mutateAsync(aDesactivar.id_usuario)
      toast.success(`Usuario ${aDesactivar.nombre_usuario} desactivado.`)
      setADesactivar(null)
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  const reactivarUsuario = async (u: Usuario) => {
    try {
      await reactivar.mutateAsync({ id: u.id_usuario, estado_usuario: 'activo' })
      toast.success(`Usuario ${u.nombre_usuario} activado.`)
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  return (
    <div className="space-y-5">
      <EncabezadoPagina
        titulo="Gestión de usuarios"
        descripcion="Administre los usuarios del sistema, sus roles y estado de acceso."
        accion={
          <Button size="lg" onClick={() => setNuevo(true)}>
            <PlusIcon /> Nuevo usuario
          </Button>
        }
      />

      {!!solicitudes.data?.length && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
          <p className="flex items-center gap-2 font-medium text-amber-800">
            <TriangleAlertIcon className="size-5" /> Solicitudes de recuperación de contraseña
          </p>
          <ul className="mt-2 divide-y divide-amber-200">
            {solicitudes.data.map((s) => (
              <li key={s.id_bitacora} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
                <span>
                  <b>{s.nombres} {s.apellidos}</b> ({s.nombre_usuario}) · {fechaHora(s.fecha_hora)}
                </span>
                <Button size="sm" variant="outline" onClick={() => setARestablecer({ id: s.id_usuario, nombre: s.nombre_usuario })}>
                  <KeyRoundIcon /> Restablecer contraseña
                </Button>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="rounded-xl border bg-white shadow-sm">
        <div className="grid gap-3 p-4 md:grid-cols-[1fr_180px_180px_auto] md:items-end">
          <div className="relative">
            <SearchIcon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" />
            <Input
              value={busqueda}
              onChange={(e) => { setBusqueda(e.target.value); setPagina(1) }}
              placeholder="Buscar usuario por nombre, correo o cédula..."
              className="h-9 pl-9"
            />
          </div>
          <Campo etiqueta="Rol">
            <Select value={rol} onValueChange={(v) => { setRol(v); setPagina(1) }}>
              <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value={TODOS}>Todos</SelectItem>
                {roles.data?.map((r) => (
                  <SelectItem key={r.id_rol} value={String(r.id_rol)}>{ETIQUETA_ROL[r.nombre_rol]}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Campo>
          <Campo etiqueta="Estado">
            <Select value={estado} onValueChange={(v) => { setEstado(v); setPagina(1) }}>
              <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value={TODOS}>Todos</SelectItem>
                <SelectItem value="activo">Activo</SelectItem>
                <SelectItem value="inactivo">Inactivo</SelectItem>
                <SelectItem value="bloqueado">Bloqueado</SelectItem>
              </SelectContent>
            </Select>
          </Campo>
          <Button variant="outline" onClick={limpiar}>
            <RotateCcwIcon /> Limpiar
          </Button>
        </div>

        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50">
              <TableHead className="w-10 pl-4">#</TableHead>
              <TableHead>Nombre completo</TableHead>
              <TableHead>Usuario / Correo</TableHead>
              <TableHead>Rol</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Último acceso</TableHead>
              <TableHead className="pr-4 text-center">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {lista.isLoading ? (
              <FilaMensaje columnas={7} cargando />
            ) : lista.isError ? (
              <FilaMensaje columnas={7} mensaje={mensajeError(lista.error)} />
            ) : !lista.data?.items.length ? (
              <FilaMensaje columnas={7} mensaje="No se encontraron usuarios." />
            ) : (
              lista.data.items.map((u, i) => (
                <TableRow key={u.id_usuario}>
                  <TableCell className="pl-4 text-slate-500">{(pagina - 1) * TAMANO + i + 1}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <AvatarIniciales nombre={`${u.nombres} ${u.apellidos}`} />
                      <div>
                        <p className="font-medium">{u.nombres} {u.apellidos}</p>
                        <p className="text-xs text-slate-500">C.I. {documento(u.ci, u.expedido)}</p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <p>{u.nombre_usuario}</p>
                    <p className="text-xs text-slate-500">{u.email ?? '—'}</p>
                  </TableCell>
                  <TableCell><InsigniaRol rol={u.nombre_rol} /></TableCell>
                  <TableCell><InsigniaEstado estado={u.estado_usuario} /></TableCell>
                  <TableCell className="text-sm">
                    {u.ultimo_acceso ? (
                      <>
                        <p>{fecha(u.ultimo_acceso)}</p>
                        <p className="text-xs text-slate-500">{hora(u.ultimo_acceso)}</p>
                      </>
                    ) : (
                      <span className="text-slate-400">Nunca</span>
                    )}
                  </TableCell>
                  <TableCell className="pr-4">
                    <div className="flex justify-center gap-1.5">
                      <BotonAccion etiqueta="Editar" tono="azul" onClick={() => setEditando(u)}>
                        <PencilIcon />
                      </BotonAccion>
                      <BotonAccion
                        etiqueta="Restablecer contraseña"
                        tono="ambar"
                        onClick={() => setARestablecer({ id: u.id_usuario, nombre: u.nombre_usuario })}
                      >
                        <KeyRoundIcon />
                      </BotonAccion>
                      {u.estado_usuario === 'activo' ? (
                        <BotonAccion
                          etiqueta="Desactivar"
                          tono="rojo"
                          disabled={u.id_usuario === yo?.id_usuario}
                          onClick={() => setADesactivar(u)}
                        >
                          <TrashIcon />
                        </BotonAccion>
                      ) : (
                        <BotonAccion etiqueta="Activar" tono="verde" onClick={() => reactivarUsuario(u)}>
                          <RotateCcwIcon />
                        </BotonAccion>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <Paginacion pagina={pagina} tamano={TAMANO} total={lista.data?.total ?? 0} etiqueta="usuarios" onCambiar={setPagina} />
      </div>

      <DialogoNuevoUsuario abierto={nuevo} onCambiar={setNuevo} />
      {editando && <DialogoEditarUsuario usuario={editando} onCerrar={() => setEditando(null)} />}

      <Confirmar
        abierto={!!aDesactivar}
        onCambiar={(v) => !v && setADesactivar(null)}
        titulo="Desactivar usuario"
        descripcion={`El usuario ${aDesactivar?.nombre_usuario} ya no podrá iniciar sesión. Podrá activarlo nuevamente.`}
        textoConfirmar="Desactivar"
        icono={<TrashIcon />}
        peligro
        ocupado={desactivar.isPending}
        onConfirmar={confirmarDesactivar}
      />
      <Confirmar
        abierto={!!aRestablecer}
        onCambiar={(v) => !v && setARestablecer(null)}
        titulo="Restablecer contraseña"
        descripcion={`Se generará una contraseña temporal para ${aRestablecer?.nombre}. La anterior dejará de funcionar.`}
        textoConfirmar="Restablecer"
        icono={<KeyRoundIcon />}
        ocupado={restablecer.isPending}
        onConfirmar={confirmarRestablecer}
      />
      <Dialog open={!!temporal} onOpenChange={(v) => !v && setTemporal(null)}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Contraseña temporal</DialogTitle>
            <DialogDescription>{temporal?.mensaje}</DialogDescription>
          </DialogHeader>
          <div className="flex items-center gap-2 rounded-lg bg-slate-100 p-3">
            <code className="flex-1 text-lg font-semibold tracking-wider">{temporal?.contrasena}</code>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                navigator.clipboard?.writeText(temporal?.contrasena ?? '')
                toast.success('Copiada al portapapeles.')
              }}
            >
              <CopyIcon /> Copiar
            </Button>
          </div>
          <DialogFooter>
            <Button onClick={() => setTemporal(null)}>Listo</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

type DatosNuevo = z.infer<typeof esquemaNuevoUsuario>

function DialogoNuevoUsuario({ abierto, onCambiar }: { abierto: boolean; onCambiar: (v: boolean) => void }) {
  const roles = useRoles()
  const crear = useCrearUsuario()
  const [buscar, setBuscar] = useState('')
  const form = useForm<DatosNuevo>({
    resolver: zodResolver(esquemaNuevoUsuario),
    defaultValues: { id_rol: '', ci_persona: '', nombre_usuario: '', contrasena: '', confirmar: '' },
  })
  const idRol = useWatch({ control: form.control, name: 'id_rol' })
  const ciElegida = useWatch({ control: form.control, name: 'ci_persona' })
  const personas = usePersonasSinCuenta(idRol, useRetardo(buscar))

  const cerrar = () => {
    form.reset()
    setBuscar('')
    onCambiar(false)
  }

  const guardar = form.handleSubmit(async (d) => {
    try {
      const u = await crear.mutateAsync({
        ci_persona: d.ci_persona,
        id_rol: Number(d.id_rol),
        nombre_usuario: d.nombre_usuario,
        contrasena: d.contrasena,
      })
      toast.success(`Usuario ${u.nombre_usuario} creado.`)
      cerrar()
    } catch (e) {
      toast.error(mensajeError(e))
    }
  })

  const e = form.formState.errors
  return (
    <Dialog open={abierto} onOpenChange={(v) => (v ? onCambiar(true) : cerrar())}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Nuevo usuario</DialogTitle>
          <DialogDescription>
            La persona debe estar registrada con el tipo que corresponde al rol (por ejemplo, un docente para el rol Docente).
          </DialogDescription>
        </DialogHeader>
        <form id="form-nuevo-usuario" onSubmit={guardar} className="grid gap-4">
          <Campo etiqueta="Rol" error={e.id_rol?.message}>
            <Controller
              control={form.control}
              name="id_rol"
              render={({ field }) => (
                <Select value={field.value} onValueChange={(v) => { field.onChange(v); form.setValue('ci_persona', '') }}>
                  <SelectTrigger className="w-full"><SelectValue placeholder="Seleccione el rol" /></SelectTrigger>
                  <SelectContent>
                    {roles.data?.map((r) => (
                      <SelectItem key={r.id_rol} value={String(r.id_rol)}>{ETIQUETA_ROL[r.nombre_rol]}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </Campo>
          {idRol && (
            <Campo etiqueta="Persona (sin cuenta de usuario)" error={e.ci_persona?.message}>
              <Input placeholder="Buscar por nombre o C.I." value={buscar} onChange={(ev) => setBuscar(ev.target.value)} />
              <div className="max-h-40 overflow-y-auto rounded-lg border">
                {personas.isLoading ? (
                  <p className="p-3 text-sm text-slate-500">Buscando...</p>
                ) : !personas.data?.length ? (
                  <p className="p-3 text-sm text-slate-500">No hay personas disponibles para este rol.</p>
                ) : (
                  personas.data.map((p) => (
                    <button
                      type="button"
                      key={p.ci}
                      onClick={() => form.setValue('ci_persona', p.ci, { shouldValidate: true })}
                      className={`flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-slate-50 ${ciElegida === p.ci ? 'bg-blue-50 font-medium text-blue-700' : ''}`}
                    >
                      <span>{p.nombres} {p.apellidos}</span>
                      <span className="text-xs text-slate-500">C.I. {p.ci}</span>
                    </button>
                  ))
                )}
              </div>
            </Campo>
          )}
          <Campo etiqueta="Nombre de usuario" error={e.nombre_usuario?.message} htmlFor="nombre_usuario">
            <Input id="nombre_usuario" autoComplete="off" {...form.register('nombre_usuario')} />
          </Campo>
          <div className="grid gap-4 sm:grid-cols-2">
            <Campo etiqueta="Contraseña inicial" error={e.contrasena?.message} htmlFor="contrasena">
              <Input id="contrasena" type="password" autoComplete="new-password" {...form.register('contrasena')} />
            </Campo>
            <Campo etiqueta="Repetir contraseña" error={e.confirmar?.message} htmlFor="confirmar_nuevo">
              <Input id="confirmar_nuevo" type="password" autoComplete="new-password" {...form.register('confirmar')} />
            </Campo>
          </div>
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={cerrar}>Cancelar</Button>
          <Button type="submit" form="form-nuevo-usuario" disabled={crear.isPending}>Crear usuario</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

type DatosEditar = z.infer<typeof esquemaEditarUsuario>

function DialogoEditarUsuario({ usuario, onCerrar }: { usuario: Usuario; onCerrar: () => void }) {
  const { usuario: yo } = useSesion()
  const roles = useRoles()
  const actualizar = useActualizarUsuario()
  const soyYo = yo?.id_usuario === usuario.id_usuario
  const form = useForm<DatosEditar>({
    resolver: zodResolver(esquemaEditarUsuario),
    defaultValues: {
      nombre_usuario: usuario.nombre_usuario,
      id_rol: String(usuario.id_rol),
      estado_usuario: usuario.estado_usuario,
    },
  })

  const guardar = form.handleSubmit(async (d) => {
    try {
      await actualizar.mutateAsync({
        id: usuario.id_usuario,
        nombre_usuario: d.nombre_usuario,
        id_rol: Number(d.id_rol),
        estado_usuario: d.estado_usuario,
      })
      toast.success('Usuario actualizado.')
      onCerrar()
    } catch (e) {
      toast.error(mensajeError(e))
    }
  })

  const e = form.formState.errors
  return (
    <Dialog open onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Editar usuario</DialogTitle>
          <DialogDescription>
            {usuario.nombres} {usuario.apellidos} · C.I. {documento(usuario.ci, usuario.expedido)}
          </DialogDescription>
        </DialogHeader>
        <form id="form-editar-usuario" onSubmit={guardar} className="grid gap-4">
          <Campo etiqueta="Nombre de usuario" error={e.nombre_usuario?.message} htmlFor="editar_nombre">
            <Input id="editar_nombre" {...form.register('nombre_usuario')} />
          </Campo>
          <Campo etiqueta="Rol" error={e.id_rol?.message}>
            <Controller
              control={form.control}
              name="id_rol"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange} disabled={soyYo}>
                  <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {roles.data?.map((r) => (
                      <SelectItem key={r.id_rol} value={String(r.id_rol)}>{ETIQUETA_ROL[r.nombre_rol]}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </Campo>
          <Campo etiqueta="Estado">
            <Controller
              control={form.control}
              name="estado_usuario"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange} disabled={soyYo}>
                  <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="activo">Activo</SelectItem>
                    <SelectItem value="inactivo">Inactivo</SelectItem>
                    <SelectItem value="bloqueado">Bloqueado</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
          </Campo>
          {soyYo && <p className="text-xs text-slate-500">No puede cambiar el rol ni el estado de su propia cuenta.</p>}
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={onCerrar}>Cancelar</Button>
          <Button type="submit" form="form-editar-usuario" disabled={actualizar.isPending}>Guardar cambios</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

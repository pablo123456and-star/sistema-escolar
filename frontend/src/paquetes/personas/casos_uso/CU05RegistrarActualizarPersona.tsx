/**
 * CU05 - Registrar y actualizar datos de persona
 * Paquete: personas
 *
 * Actores ........: Administrativo
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/personas/casos_uso/cu05_registrar_actualizar_persona.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Buscar personas (C.I., nombre o apellido), ver su ficha (roles, cuenta de usuario e inscripción),
 * editar sus datos (solo se envían los campos cambiados; el C.I. no cambia), dar de baja con motivo
 * y reactivar. El registro de personas nuevas se hace en Estudiantes (CU06), Tutores (CU08) y Docentes (CU10).
 *
 * Precondición:  Sesión iniciada como administrador. Para actualizar o dar de baja: la persona existe.
 * Postcondición: Los datos quedan actualizados, o la persona queda inactiva con su usuario desactivado. Queda en la bitácora.
 *
 * Estado: IMPLEMENTADO.
 */
import { useState, type ReactNode } from 'react'
import { FormProvider, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import type { z } from 'zod'
import { EyeIcon, InfoIcon, RotateCcwIcon, SearchIcon, TrashIcon, UserCheckIcon } from 'lucide-react'
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
import { Separator } from '@/componentes/ui/separator'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { Textarea } from '@/componentes/ui/textarea'
import { documento, fecha, nombreCompleto } from '@/lib/formato'
import { useRetardo } from '@/lib/useRetardo'
import { mensajeError } from '@/nucleo/api'
import { useSesion } from '@/nucleo/auth/contexto'
import { useActualizarPersona, useBajaPersona, usePersona, usePersonas, useReactivarPersona } from '../api'
import CamposPersona from '../componentes/CamposPersona'
import {
  PERSONA_VACIA,
  esquemaBaja,
  esquemaEdicionPersona,
  personaAFormulario,
  personaParaApi,
  rolesPersona,
  type PersonaFicha,
} from '../schemas'

const TAMANO = 10

/** Persona elegida para dar de baja o reactivar (desde la tabla o desde la ficha). */
type Elegida = { ci: string; nombre_persona: string; apellidos: string; tiene_usuario: boolean }

function Roles({ roles }: { roles: string[] }) {
  if (!roles.length) return <span className="text-xs text-slate-400">Sin rol</span>
  return (
    <div className="flex flex-wrap gap-1">
      {roles.map((r) => (
        <span key={r} className="rounded-md bg-slate-100 px-1.5 py-0.5 text-xs font-medium text-slate-700">
          {r}
        </span>
      ))}
    </div>
  )
}

export default function CU05RegistrarActualizarPersona() {
  const { usuario } = useSesion()
  const [busqueda, setBusqueda] = useState('')
  const [estado, setEstado] = useState(TODOS)
  const [pagina, setPagina] = useState(1)
  const buscar = useRetardo(busqueda)
  const lista = usePersonas({ buscar, estado: sinTodos(estado), pagina, tamano: TAMANO })

  const [viendo, setViendo] = useState<string | null>(null)
  const [aBaja, setABaja] = useState<Elegida | null>(null)
  const [aReactivar, setAReactivar] = useState<Elegida | null>(null)
  const reactivar = useReactivarPersona()

  const confirmarReactivar = async () => {
    if (!aReactivar) return
    try {
      await reactivar.mutateAsync(aReactivar.ci)
      toast.success(`${nombreCompleto(aReactivar)} fue reactivado(a).`)
      setAReactivar(null)
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  // Desde la ficha: se cierra la ficha y se abre la confirmación
  const desdeFicha = (accion: (p: Elegida) => void) => (p: Elegida) => {
    setViendo(null)
    accion(p)
  }

  return (
    <div className="space-y-5">
      <EncabezadoPagina
        titulo="Personas"
        descripcion="Busque a cualquier persona de la institución, actualice sus datos o dele de baja. Las personas nuevas se registran en Estudiantes, Padres y tutores o Docentes."
      />

      <div className="rounded-xl border bg-white shadow-sm">
        <div className="grid gap-3 p-4 md:grid-cols-[1fr_180px_auto] md:items-end">
          <Campo etiqueta="Buscar persona">
            <div className="relative">
              <SearchIcon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" />
              <Input
                value={busqueda}
                onChange={(e) => { setBusqueda(e.target.value); setPagina(1) }}
                placeholder="C.I., nombre o apellido..."
                className="pl-9"
              />
            </div>
          </Campo>
          <Campo etiqueta="Estado">
            <Select value={estado} onValueChange={(v) => { setEstado(v); setPagina(1) }}>
              <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value={TODOS}>Todos</SelectItem>
                <SelectItem value="activo">Activo</SelectItem>
                <SelectItem value="inactivo">Inactivo</SelectItem>
              </SelectContent>
            </Select>
          </Campo>
          <Button variant="outline" onClick={() => { setBusqueda(''); setEstado(TODOS); setPagina(1) }}>
            <RotateCcwIcon /> Limpiar
          </Button>
        </div>

        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50">
              <TableHead className="w-10 pl-4">#</TableHead>
              <TableHead>Nombre completo</TableHead>
              <TableHead>Roles</TableHead>
              <TableHead>Contacto</TableHead>
              <TableHead>Usuario</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="pr-4 text-center">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {lista.isLoading ? (
              <FilaMensaje columnas={7} cargando />
            ) : lista.isError ? (
              <FilaMensaje columnas={7} mensaje={mensajeError(lista.error)} />
            ) : !lista.data?.items.length ? (
              <FilaMensaje columnas={7} mensaje="No se encontraron personas." />
            ) : (
              lista.data.items.map((p, i) => {
                const elegida: Elegida = { ...p, tiene_usuario: p.nombre_usuario !== null }
                return (
                  <TableRow key={p.ci}>
                    <TableCell className="pl-4 text-slate-500">{(pagina - 1) * TAMANO + i + 1}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <AvatarIniciales
                          nombre={nombreCompleto(p)}
                          className={p.sexo === 'F' ? 'bg-rose-100 text-rose-700' : p.sexo === 'M' ? 'bg-sky-100 text-sky-700' : undefined}
                        />
                        <div>
                          <p className="font-medium">{p.apellidos}, {p.nombre_persona}</p>
                          <p className="text-xs text-slate-500">C.I. {documento(p.ci, p.expedido)}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell><Roles roles={rolesPersona(p)} /></TableCell>
                    <TableCell>
                      <p>{p.telefono ?? '—'}</p>
                      <p className="text-xs text-slate-500">{p.email ?? ''}</p>
                    </TableCell>
                    <TableCell>
                      {p.nombre_usuario ? (
                        <div className="space-y-1">
                          <p className="text-sm">{p.nombre_usuario}</p>
                          {p.estado_usuario && <InsigniaEstado estado={p.estado_usuario} />}
                        </div>
                      ) : (
                        <span className="text-xs text-slate-400">Sin cuenta</span>
                      )}
                    </TableCell>
                    <TableCell><InsigniaEstado estado={p.estado_persona} /></TableCell>
                    <TableCell className="pr-4">
                      <div className="flex justify-center gap-1.5">
                        <BotonAccion etiqueta="Ver ficha" tono="azul" onClick={() => setViendo(p.ci)}>
                          <EyeIcon />
                        </BotonAccion>
                        {p.estado_persona === 'inactivo' ? (
                          <BotonAccion etiqueta="Reactivar" tono="verde" onClick={() => setAReactivar(elegida)}>
                            <UserCheckIcon />
                          </BotonAccion>
                        ) : (
                          p.ci !== usuario?.ci && (
                            <BotonAccion etiqueta="Dar de baja" tono="rojo" onClick={() => setABaja(elegida)}>
                              <TrashIcon />
                            </BotonAccion>
                          )
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
        <Paginacion pagina={pagina} tamano={TAMANO} total={lista.data?.total ?? 0} etiqueta="personas" onCambiar={setPagina} />
      </div>

      {viendo && (
        <DialogoFicha
          ci={viendo}
          onCerrar={() => setViendo(null)}
          onBaja={desdeFicha(setABaja)}
          onReactivar={desdeFicha(setAReactivar)}
        />
      )}
      {aBaja && <DialogoBaja persona={aBaja} onCerrar={() => setABaja(null)} />}
      <Confirmar
        abierto={!!aReactivar}
        onCambiar={(v) => !v && setAReactivar(null)}
        titulo="Reactivar persona"
        descripcion={
          aReactivar
            ? `${nombreCompleto(aReactivar)} volverá a estar activo(a)${aReactivar.tiene_usuario ? ' y podrá volver a ingresar con su cuenta' : ''}. Sus inscripciones retiradas no se restauran.`
            : ''
        }
        textoConfirmar="Reactivar"
        icono={<UserCheckIcon />}
        ocupado={reactivar.isPending}
        onConfirmar={confirmarReactivar}
      />
    </div>
  )
}

function Dato({ etiqueta, valor }: { etiqueta: string; valor: ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-slate-500">{etiqueta}</dt>
      <dd className="text-sm">{valor || '—'}</dd>
    </div>
  )
}

type DatosEdicion = z.infer<typeof esquemaEdicionPersona>

function DialogoFicha({
  ci,
  onCerrar,
  onBaja,
  onReactivar,
}: {
  ci: string
  onCerrar: () => void
  onBaja: (p: Elegida) => void
  onReactivar: (p: Elegida) => void
}) {
  const ficha = usePersona(ci)
  const actualizar = useActualizarPersona()
  const d: PersonaFicha | undefined = ficha.data

  const form = useForm<DatosEdicion>({
    resolver: zodResolver(esquemaEdicionPersona),
    defaultValues: { persona: PERSONA_VACIA },
    values: d ? { persona: personaAFormulario(d) } : undefined,
  })

  const guardar = form.handleSubmit(async ({ persona }) => {
    if (!d) return
    // Actualización parcial: solo se envían los campos que cambiaron (el C.I. nunca)
    const original: Record<string, string | null> = personaParaApi(personaAFormulario(d))
    const cambios = Object.fromEntries(
      Object.entries(personaParaApi(persona)).filter(([campo, valor]) => campo !== 'ci' && valor !== original[campo]),
    )
    if (!Object.keys(cambios).length) {
      toast.info('No hay cambios para guardar.')
      return
    }
    try {
      await actualizar.mutateAsync({ ci, cuerpo: cambios })
      toast.success('Datos de la persona actualizados.')
    } catch (e) {
      toast.error(mensajeError(e))
    }
  })

  const elegida: Elegida | null = d ? { ...d, tiene_usuario: d.usuario !== null } : null

  return (
    <Dialog open onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{d ? nombreCompleto(d) : 'Persona'}</DialogTitle>
          <DialogDescription>{d && `C.I. ${documento(d.ci, d.expedido)}`}</DialogDescription>
        </DialogHeader>
        {ficha.isLoading ? (
          <p className="py-6 text-center text-slate-500">Cargando...</p>
        ) : ficha.isError || !d ? (
          <p className="py-6 text-center text-rose-600">{mensajeError(ficha.error)}</p>
        ) : (
          <div className="space-y-5">
            <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <Dato etiqueta="Estado" valor={<InsigniaEstado estado={d.estado_persona} />} />
              <div className="col-span-2"><Dato etiqueta="Roles" valor={<Roles roles={rolesPersona(d)} />} /></div>
              <Dato
                etiqueta="Cuenta de usuario"
                valor={
                  d.usuario ? (
                    <span className="flex flex-wrap items-center gap-1.5">
                      {d.usuario.nombre_usuario}
                      <InsigniaRol rol={d.usuario.rol} />
                      <InsigniaEstado estado={d.usuario.estado_usuario} />
                    </span>
                  ) : (
                    'Sin cuenta'
                  )
                }
              />
              <div className="col-span-2">
                <Dato
                  etiqueta="Inscripción (gestión abierta)"
                  valor={
                    d.inscripcion ? (
                      <span className="flex flex-wrap items-center gap-1.5">
                        {d.inscripcion.curso} · {d.inscripcion.gestion} · desde {fecha(d.inscripcion.fecha_inscripcion)}
                        <InsigniaEstado estado={d.inscripcion.estado_inscripcion} />
                      </span>
                    ) : null
                  }
                />
              </div>
            </dl>
            {d.es_usuario_actual && (
              <p className="flex items-center gap-2 rounded-lg bg-blue-50 px-3 py-2 text-xs text-blue-700">
                <InfoIcon className="size-4 shrink-0" /> Esta es su propia ficha: puede editar sus datos, pero no darse de baja.
              </p>
            )}
            <Separator />
            <FormProvider {...form}>
              <form id="form-persona" onSubmit={guardar} className="space-y-3">
                <h3 className="text-sm font-semibold text-slate-700">Datos personales</h3>
                <CamposPersona edicion />
              </form>
            </FormProvider>
          </div>
        )}
        <DialogFooter className="gap-2 sm:justify-between">
          <div className="flex flex-col gap-2 sm:flex-row">
            {elegida && d?.estado_persona === 'inactivo' && (
              <Button variant="outline" onClick={() => onReactivar(elegida)}>
                <UserCheckIcon /> Reactivar
              </Button>
            )}
            {elegida && d?.estado_persona === 'activo' && !d.es_usuario_actual && (
              <Button variant="outline" className="text-rose-700 hover:bg-rose-50" onClick={() => onBaja(elegida)}>
                <TrashIcon /> Dar de baja
              </Button>
            )}
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Button variant="outline" onClick={onCerrar}>Cerrar</Button>
            <Button type="submit" form="form-persona" disabled={!d || actualizar.isPending}>
              Guardar cambios
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function DialogoBaja({ persona, onCerrar }: { persona: Elegida; onCerrar: () => void }) {
  const baja = useBajaPersona()
  const form = useForm<z.infer<typeof esquemaBaja>>({ resolver: zodResolver(esquemaBaja), defaultValues: { motivo: '' } })
  const guardar = form.handleSubmit(async ({ motivo }) => {
    try {
      await baja.mutateAsync({ ci: persona.ci, motivo })
      toast.success(`${nombreCompleto(persona)} fue dado(a) de baja.`)
      onCerrar()
    } catch (e) {
      toast.error(mensajeError(e))
    }
  })
  return (
    <Dialog open onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>¿Dar de baja a {nombreCompleto(persona)}?</DialogTitle>
          <DialogDescription>
            Baja lógica: no se borra nada y se conserva su historial. La persona quedará inactiva
            {persona.tiene_usuario ? ', su cuenta de usuario se desactivará' : ''} y, si es estudiante, su inscripción
            activa pasará a “retirada” con la fecha de hoy y este motivo.
          </DialogDescription>
        </DialogHeader>
        <form id="form-baja-persona" onSubmit={guardar}>
          <Campo etiqueta="Motivo" error={form.formState.errors.motivo?.message} htmlFor="motivo-baja">
            <Textarea id="motivo-baja" rows={3} placeholder="Ej. cambio de colegio" {...form.register('motivo')} />
          </Campo>
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={onCerrar}>Cancelar</Button>
          <Button
            type="submit"
            form="form-baja-persona"
            className="bg-rose-600 text-white hover:bg-rose-700"
            disabled={baja.isPending}
          >
            Confirmar baja
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

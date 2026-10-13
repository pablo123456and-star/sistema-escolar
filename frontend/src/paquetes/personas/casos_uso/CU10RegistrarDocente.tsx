/**
 * CU10 - Registrar docente
 * Paquete: personas
 *
 * Actores ........: Administrador
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/personas/casos_uso/cu10_registrar_docente.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Listar con búsqueda (nombre/C.I.) y filtro de estado, registrar (reutilizando la persona si
 * ya existe), ver (con sus materias de la gestión abierta), editar, dar de baja (no si tiene
 * materias asignadas en la gestión abierta) y reactivar.
 *
 * Precondición:  Sesión iniciada como administrador. El CI no está registrado como docente.
 * Postcondición: El profesor queda registrado y puede recibir asignaciones y una cuenta de usuario.
 *
 * Estado: IMPLEMENTADO.
 */
import { useState, type ReactNode } from 'react'
import { FormProvider, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import type { z } from 'zod'
import { EyeIcon, PencilIcon, PlusIcon, RotateCcwIcon, SearchIcon, TrashIcon, UserCheckIcon } from 'lucide-react'
import Confirmar from '@/componentes/Confirmar'
import {
  AvatarIniciales,
  BotonAccion,
  Campo,
  EncabezadoPagina,
  FilaMensaje,
  InsigniaEstado,
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
import {
  useActualizarDocente,
  useBajaDocente,
  useDocente,
  useDocentes,
  useReactivarDocente,
  useRegistrarDocente,
} from '../api'
import CamposPersona from '../componentes/CamposPersona'
import {
  PERSONA_VACIA,
  esquemaBaja,
  esquemaDocente,
  personaAFormulario,
  personaParaApi,
  type Docente,
  type DocenteDetalle,
} from '../schemas'

const TAMANO = 10

const anios = (n: number | null) => (n === null ? '—' : `${n} ${n === 1 ? 'año' : 'años'}`)

export default function CU10RegistrarDocente() {
  const [busqueda, setBusqueda] = useState('')
  const [estado, setEstado] = useState(TODOS)
  const [pagina, setPagina] = useState(1)
  const q = useRetardo(busqueda)
  const lista = useDocentes({ q, estado: sinTodos(estado), pagina, tamano: TAMANO })

  const [formulario, setFormulario] = useState<{ ci: string | null } | null>(null)
  const [viendo, setViendo] = useState<string | null>(null)
  const [aBaja, setABaja] = useState<Docente | null>(null)
  const [aReactivar, setAReactivar] = useState<Docente | null>(null)
  const reactivar = useReactivarDocente()

  const confirmarReactivar = async () => {
    if (!aReactivar) return
    try {
      await reactivar.mutateAsync(aReactivar.ci)
      toast.success('Docente reactivado.')
      setAReactivar(null)
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  return (
    <div className="space-y-5">
      <EncabezadoPagina
        titulo="Gestión de docentes"
        descripcion="Registre a los docentes de la institución y sus datos profesionales."
        accion={
          <Button size="lg" onClick={() => setFormulario({ ci: null })}>
            <PlusIcon /> Nuevo docente
          </Button>
        }
      />

      <div className="rounded-xl border bg-white shadow-sm">
        <div className="grid gap-3 p-4 md:grid-cols-[1fr_180px_auto] md:items-end">
          <Campo etiqueta="Buscar docente">
            <div className="relative">
              <SearchIcon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" />
              <Input
                value={busqueda}
                onChange={(e) => { setBusqueda(e.target.value); setPagina(1) }}
                placeholder="Nombre o cédula..."
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
              <TableHead>Contacto</TableHead>
              <TableHead>Título académico</TableHead>
              <TableHead>Experiencia</TableHead>
              <TableHead className="text-center">Materias asignadas</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="pr-4 text-center">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {lista.isLoading ? (
              <FilaMensaje columnas={8} cargando />
            ) : lista.isError ? (
              <FilaMensaje columnas={8} mensaje={mensajeError(lista.error)} />
            ) : !lista.data?.items.length ? (
              <FilaMensaje columnas={8} mensaje="No se encontraron docentes." />
            ) : (
              lista.data.items.map((d, i) => (
                <TableRow key={d.ci}>
                  <TableCell className="pl-4 text-slate-500">{(pagina - 1) * TAMANO + i + 1}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <AvatarIniciales
                        nombre={nombreCompleto(d)}
                        className={d.sexo === 'F' ? 'bg-rose-100 text-rose-700' : d.sexo === 'M' ? 'bg-sky-100 text-sky-700' : undefined}
                      />
                      <div>
                        <p className="font-medium">{d.apellidos}, {d.nombre_persona}</p>
                        <p className="text-xs text-slate-500">C.I. {documento(d.ci, d.expedido)}</p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <p>{d.telefono ?? '—'}</p>
                    <p className="text-xs text-slate-500">{d.email ?? ''}</p>
                  </TableCell>
                  <TableCell>{d.titulo_academico ?? '—'}</TableCell>
                  <TableCell>{anios(d.anios_experiencia)}</TableCell>
                  <TableCell className="text-center">
                    <span className="inline-flex min-w-7 justify-center rounded-full bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-700">
                      {d.cantidad_asignaciones}
                    </span>
                  </TableCell>
                  <TableCell><InsigniaEstado estado={d.estado_persona} /></TableCell>
                  <TableCell className="pr-4">
                    <div className="flex justify-center gap-1.5">
                      <BotonAccion etiqueta="Ver" tono="azul" onClick={() => setViendo(d.ci)}>
                        <EyeIcon />
                      </BotonAccion>
                      <BotonAccion etiqueta="Editar" tono="ambar" onClick={() => setFormulario({ ci: d.ci })}>
                        <PencilIcon />
                      </BotonAccion>
                      {d.estado_persona === 'activo' ? (
                        <BotonAccion etiqueta="Dar de baja" tono="rojo" onClick={() => setABaja(d)}>
                          <TrashIcon />
                        </BotonAccion>
                      ) : (
                        <BotonAccion etiqueta="Reactivar" tono="verde" onClick={() => setAReactivar(d)}>
                          <UserCheckIcon />
                        </BotonAccion>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <Paginacion pagina={pagina} tamano={TAMANO} total={lista.data?.total ?? 0} etiqueta="docentes" onCambiar={setPagina} />
      </div>

      {formulario && <DialogoDocente ci={formulario.ci} onCerrar={() => setFormulario(null)} />}
      <DialogoDetalle ci={viendo} onCerrar={() => setViendo(null)} />
      {aBaja && <DialogoBaja docente={aBaja} onCerrar={() => setABaja(null)} />}
      <Confirmar
        abierto={!!aReactivar}
        onCambiar={(v) => !v && setAReactivar(null)}
        titulo="Reactivar docente"
        descripcion={`${aReactivar ? nombreCompleto(aReactivar) : ''} volverá a estar activo (y su cuenta de usuario, si tiene).`}
        textoConfirmar="Reactivar"
        icono={<UserCheckIcon />}
        ocupado={reactivar.isPending}
        onConfirmar={confirmarReactivar}
      />
    </div>
  )
}

type DatosDocente = z.infer<typeof esquemaDocente>

function DialogoDocente({ ci, onCerrar }: { ci: string | null; onCerrar: () => void }) {
  const edicion = ci !== null
  const existente = useDocente(ci)
  const registrar = useRegistrarDocente()
  const actualizar = useActualizarDocente()

  const form = useForm<DatosDocente>({
    resolver: zodResolver(esquemaDocente),
    defaultValues: { persona: PERSONA_VACIA, titulo_academico: '', fecha_contrato: '', anios_experiencia: '', antecedentes_laborales: '' },
    values: existente.data
      ? {
          persona: personaAFormulario(existente.data),
          titulo_academico: existente.data.titulo_academico ?? '',
          fecha_contrato: existente.data.fecha_contrato ?? '',
          anios_experiencia: existente.data.anios_experiencia?.toString() ?? '',
          antecedentes_laborales: existente.data.antecedentes_laborales ?? '',
        }
      : undefined,
  })

  const guardar = form.handleSubmit(async (d) => {
    const nulo = (v: string) => (v ? v : null)
    const profesionales = {
      titulo_academico: nulo(d.titulo_academico),
      fecha_contrato: nulo(d.fecha_contrato),
      anios_experiencia: d.anios_experiencia ? Number(d.anios_experiencia) : null,
      antecedentes_laborales: nulo(d.antecedentes_laborales),
    }
    try {
      if (edicion) {
        const { ci: _ci, ...persona } = personaParaApi(d.persona)
        await actualizar.mutateAsync({ ci, cuerpo: { persona, ...profesionales } })
        toast.success('Datos del docente actualizados.')
      } else {
        const r = await registrar.mutateAsync({ persona: personaParaApi(d.persona), ...profesionales })
        toast.success(`Docente ${nombreCompleto(r)} registrado. Ya se le pueden asignar materias.`)
      }
      onCerrar()
    } catch (e) {
      toast.error(mensajeError(e))
    }
  })

  const e = form.formState.errors
  const ocupado = registrar.isPending || actualizar.isPending
  return (
    <Dialog open onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{edicion ? 'Editar docente' : 'Nuevo docente'}</DialogTitle>
          <DialogDescription>
            {edicion
              ? 'Actualice los datos personales y profesionales.'
              : 'Si la persona ya está registrada (por ejemplo, como tutor), se reutilizan sus datos.'}
          </DialogDescription>
        </DialogHeader>
        {edicion && existente.isLoading ? (
          <p className="py-6 text-center text-slate-500">Cargando...</p>
        ) : (
          <FormProvider {...form}>
            <form id="form-docente" onSubmit={guardar} className="space-y-5">
              <section className="space-y-3">
                <h3 className="text-sm font-semibold text-slate-700">Datos personales</h3>
                <CamposPersona
                  edicion={edicion}
                  validarExistente={(p) => (p.es_profesor ? 'Esta persona ya está registrada como docente.' : null)}
                />
              </section>
              <Separator />
              <section className="grid gap-3 sm:grid-cols-3">
                <h3 className="text-sm font-semibold text-slate-700 sm:col-span-3">Datos profesionales</h3>
                <Campo etiqueta="Título académico" error={e.titulo_academico?.message} className="sm:col-span-3" htmlFor="titulo">
                  <Input id="titulo" placeholder="Ej. Lic. en Matemática" {...form.register('titulo_academico')} />
                </Campo>
                <Campo etiqueta="Fecha de contrato" error={e.fecha_contrato?.message} htmlFor="contrato">
                  <Input id="contrato" type="date" {...form.register('fecha_contrato')} />
                </Campo>
                <Campo etiqueta="Años de experiencia" error={e.anios_experiencia?.message} htmlFor="experiencia">
                  <Input id="experiencia" type="number" min={0} max={60} {...form.register('anios_experiencia')} />
                </Campo>
                <Campo etiqueta="Antecedentes laborales" error={e.antecedentes_laborales?.message} className="sm:col-span-3" htmlFor="antecedentes">
                  <Textarea id="antecedentes" rows={2} placeholder="Instituciones donde trabajó, cargos..." {...form.register('antecedentes_laborales')} />
                </Campo>
              </section>
            </form>
          </FormProvider>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={onCerrar}>Cancelar</Button>
          <Button type="submit" form="form-docente" disabled={ocupado}>
            {edicion ? 'Guardar cambios' : 'Registrar docente'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
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

function DialogoDetalle({ ci, onCerrar }: { ci: string | null; onCerrar: () => void }) {
  const detalle = useDocente(ci)
  const d: DocenteDetalle | undefined = detalle.data
  return (
    <Dialog open={!!ci} onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{d ? nombreCompleto(d) : 'Docente'}</DialogTitle>
          <DialogDescription>{d && `C.I. ${documento(d.ci, d.expedido)} · ${d.titulo_academico ?? 'Sin título registrado'}`}</DialogDescription>
        </DialogHeader>
        {!d ? (
          <p className="py-6 text-center text-slate-500">Cargando...</p>
        ) : (
          <div className="space-y-5">
            <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <Dato etiqueta="Estado" valor={<InsigniaEstado estado={d.estado_persona} />} />
              <Dato etiqueta="Fecha de contrato" valor={fecha(d.fecha_contrato)} />
              <Dato etiqueta="Experiencia" valor={anios(d.anios_experiencia)} />
              <Dato etiqueta="Teléfono" valor={d.telefono} />
              <Dato etiqueta="Correo" valor={d.email} />
              <Dato etiqueta="Cuenta de usuario" valor={d.tiene_usuario ? 'Sí' : 'No'} />
              <div className="col-span-2 sm:col-span-3"><Dato etiqueta="Dirección" valor={d.direccion} /></div>
              <div className="col-span-2 sm:col-span-3"><Dato etiqueta="Antecedentes laborales" valor={d.antecedentes_laborales} /></div>
            </dl>
            <Separator />
            <div>
              <h3 className="mb-2 text-sm font-semibold">
                Materias asignadas {d.gestion ? `en la gestión ${d.gestion}` : ''}
              </h3>
              {!d.gestion ? (
                <p className="text-sm text-slate-500">No hay una gestión abierta.</p>
              ) : d.asignaciones.length === 0 ? (
                <p className="text-sm text-slate-500">Sin materias asignadas. Se asignan en “Asignación de profesores”.</p>
              ) : (
                <ul className="divide-y rounded-lg border">
                  {d.asignaciones.map((a) => (
                    <li key={a.id_asignacion} className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 text-sm">
                      <span><b>{a.materia}</b> · {a.curso}</span>
                      <span className="rounded bg-slate-100 px-1.5 text-xs text-slate-600">Aula {a.aula}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

function DialogoBaja({ docente, onCerrar }: { docente: Docente; onCerrar: () => void }) {
  const baja = useBajaDocente()
  const form = useForm<z.infer<typeof esquemaBaja>>({ resolver: zodResolver(esquemaBaja), defaultValues: { motivo: '' } })
  const guardar = form.handleSubmit(async ({ motivo }) => {
    try {
      await baja.mutateAsync({ ci: docente.ci, motivo })
      toast.success('Docente dado de baja.')
      onCerrar()
    } catch (e) {
      toast.error(mensajeError(e))
    }
  })
  return (
    <Dialog open onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Dar de baja a {nombreCompleto(docente)}</DialogTitle>
          <DialogDescription>
            Baja lógica: se conserva todo su historial y su cuenta de usuario se desactiva. No es posible si tiene
            materias asignadas en la gestión abierta.
          </DialogDescription>
        </DialogHeader>
        <form id="form-baja" onSubmit={guardar}>
          <Campo etiqueta="Motivo" error={form.formState.errors.motivo?.message} htmlFor="motivo">
            <Textarea id="motivo" rows={3} placeholder="Ej. fin de contrato" {...form.register('motivo')} />
          </Campo>
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={onCerrar}>Cancelar</Button>
          <Button type="submit" form="form-baja" className="bg-rose-600 text-white hover:bg-rose-700" disabled={baja.isPending}>
            Dar de baja
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

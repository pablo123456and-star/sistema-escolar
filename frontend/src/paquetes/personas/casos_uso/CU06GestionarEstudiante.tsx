/**
 * CU06 - Registrar y gestionar estudiante
 * Paquete: personas
 *
 * Actores ........: Secretaría (rol administrador)
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/personas/casos_uso/cu06_gestionar_estudiante.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Listar con filtros (nombre/C.I./RUDE, grado, paralelo, estado), registrar (con tutor
 * principal e inscripción opcionales), ver, editar, dar de baja y reactivar.
 *
 * Precondición:  Sesión iniciada como administrador. El CI no está registrado como estudiante.
 * Postcondición: La persona y el estudiante quedan registrados (opcionalmente con su tutor principal y su inscripción).
 *
 * Estado: IMPLEMENTADO.
 */
import { useMemo, useState, type ReactNode } from 'react'
import { Controller, FormProvider, useForm } from 'react-hook-form'
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
  personasApi,
  useActualizarEstudiante,
  useBajaEstudiante,
  useEstudiante,
  useEstudiantes,
  useOpcionesEstudiantes,
  useReactivarEstudiante,
  useRegistrarEstudiante,
} from '../api'
import CamposPersona from '../componentes/CamposPersona'
import {
  PARENTESCOS,
  PERSONA_VACIA,
  esquemaBaja,
  esquemaEstudiante,
  personaAFormulario,
  personaParaApi,
  type Estudiante,
  type EstudianteDetalle,
} from '../schemas'

const TAMANO = 10
const SIN_CURSO = 'ninguno'

export default function CU06GestionarEstudiante() {
  const [busqueda, setBusqueda] = useState('')
  const [grado, setGrado] = useState(TODOS)
  const [paralelo, setParalelo] = useState(TODOS)
  const [estado, setEstado] = useState(TODOS)
  const [pagina, setPagina] = useState(1)
  const q = useRetardo(busqueda)

  const opciones = useOpcionesEstudiantes()
  const lista = useEstudiantes({
    q,
    id_grado: sinTodos(grado),
    paralelo: sinTodos(paralelo),
    estado: sinTodos(estado),
    pagina,
    tamano: TAMANO,
  })

  const grados = useMemo(() => {
    const vistos = new Map<number, string>()
    for (const c of opciones.data?.cursos ?? []) vistos.set(c.id_grado, `${c.nombre_grado} - ${c.nivel}`)
    return [...vistos.entries()]
  }, [opciones.data])

  const [formulario, setFormulario] = useState<{ ci: string | null } | null>(null)
  const [viendo, setViendo] = useState<string | null>(null)
  const [aBaja, setABaja] = useState<Estudiante | null>(null)
  const [aReactivar, setAReactivar] = useState<Estudiante | null>(null)
  const reactivar = useReactivarEstudiante()

  const conFiltro = (f: (v: string) => void) => (v: string) => {
    f(v)
    setPagina(1)
  }
  const limpiar = () => {
    setBusqueda('')
    setGrado(TODOS)
    setParalelo(TODOS)
    setEstado(TODOS)
    setPagina(1)
  }

  const confirmarReactivar = async () => {
    if (!aReactivar) return
    try {
      await reactivar.mutateAsync(aReactivar.ci)
      toast.success('Estudiante reactivado.')
      setAReactivar(null)
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  return (
    <div className="space-y-5">
      <EncabezadoPagina
        titulo="Gestión de estudiantes"
        descripcion="Administre la información de los estudiantes de la institución."
        accion={
          <Button size="lg" onClick={() => setFormulario({ ci: null })}>
            <PlusIcon /> Nuevo estudiante
          </Button>
        }
      />

      <div className="rounded-xl border bg-white shadow-sm">
        <div className="grid gap-3 p-4 md:grid-cols-[1fr_200px_140px_150px_auto] md:items-end">
          <Campo etiqueta="Buscar estudiante">
            <div className="relative">
              <SearchIcon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" />
              <Input
                value={busqueda}
                onChange={(e) => conFiltro(setBusqueda)(e.target.value)}
                placeholder="Nombre, cédula o código RUDE..."
                className="pl-9"
              />
            </div>
          </Campo>
          <Campo etiqueta="Grado">
            <Select value={grado} onValueChange={conFiltro(setGrado)}>
              <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value={TODOS}>Todos</SelectItem>
                {grados.map(([id, nombre]) => <SelectItem key={id} value={String(id)}>{nombre}</SelectItem>)}
              </SelectContent>
            </Select>
          </Campo>
          <Campo etiqueta="Paralelo">
            <Select value={paralelo} onValueChange={conFiltro(setParalelo)}>
              <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value={TODOS}>Todos</SelectItem>
                {opciones.data?.paralelos.map((p) => <SelectItem key={p} value={p}>{p}</SelectItem>)}
              </SelectContent>
            </Select>
          </Campo>
          <Campo etiqueta="Estado">
            <Select value={estado} onValueChange={conFiltro(setEstado)}>
              <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value={TODOS}>Todos</SelectItem>
                <SelectItem value="activo">Activo</SelectItem>
                <SelectItem value="inactivo">Inactivo</SelectItem>
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
              <TableHead>Foto</TableHead>
              <TableHead>Nombre completo</TableHead>
              <TableHead>Código RUDE</TableHead>
              <TableHead>Grado</TableHead>
              <TableHead className="text-center">Paralelo</TableHead>
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
              <FilaMensaje columnas={8} mensaje="No se encontraron estudiantes." />
            ) : (
              lista.data.items.map((est, i) => (
                <TableRow key={est.ci}>
                  <TableCell className="pl-4 text-slate-500">{(pagina - 1) * TAMANO + i + 1}</TableCell>
                  <TableCell>
                    <AvatarIniciales
                      nombre={nombreCompleto(est)}
                      className={est.sexo === 'F' ? 'bg-rose-100 text-rose-700' : est.sexo === 'M' ? 'bg-sky-100 text-sky-700' : undefined}
                    />
                  </TableCell>
                  <TableCell>
                    <p className="font-medium">{est.apellidos}, {est.nombre_persona}</p>
                    <p className="text-xs text-slate-500">C.I. {documento(est.ci, est.expedido)}</p>
                  </TableCell>
                  <TableCell>{est.rude ?? '—'}</TableCell>
                  <TableCell>
                    {est.grado ? `${est.grado} ${est.nivel}` : <span className="text-slate-400">Sin inscripción</span>}
                  </TableCell>
                  <TableCell className="text-center">{est.paralelo ?? '—'}</TableCell>
                  <TableCell><InsigniaEstado estado={est.estado_persona} /></TableCell>
                  <TableCell className="pr-4">
                    <div className="flex justify-center gap-1.5">
                      <BotonAccion etiqueta="Ver" tono="azul" onClick={() => setViendo(est.ci)}>
                        <EyeIcon />
                      </BotonAccion>
                      <BotonAccion etiqueta="Editar" tono="ambar" onClick={() => setFormulario({ ci: est.ci })}>
                        <PencilIcon />
                      </BotonAccion>
                      {est.estado_persona === 'activo' ? (
                        <BotonAccion etiqueta="Dar de baja" tono="rojo" onClick={() => setABaja(est)}>
                          <TrashIcon />
                        </BotonAccion>
                      ) : (
                        <BotonAccion etiqueta="Reactivar" tono="verde" onClick={() => setAReactivar(est)}>
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
        <Paginacion pagina={pagina} tamano={TAMANO} total={lista.data?.total ?? 0} etiqueta="estudiantes" onCambiar={setPagina} />
      </div>

      {formulario && <DialogoEstudiante ci={formulario.ci} onCerrar={() => setFormulario(null)} />}
      <DialogoDetalle ci={viendo} onCerrar={() => setViendo(null)} />
      {aBaja && <DialogoBaja estudiante={aBaja} onCerrar={() => setABaja(null)} />}
      <Confirmar
        abierto={!!aReactivar}
        onCambiar={(v) => !v && setAReactivar(null)}
        titulo="Reactivar estudiante"
        descripcion={`${aReactivar ? nombreCompleto(aReactivar) : ''} volverá a estar activo (y su cuenta de usuario, si tiene). Su inscripción retirada no se restaura.`}
        textoConfirmar="Reactivar"
        icono={<UserCheckIcon />}
        ocupado={reactivar.isPending}
        onConfirmar={confirmarReactivar}
      />
    </div>
  )
}

type DatosEstudiante = z.infer<typeof esquemaEstudiante>

function DialogoEstudiante({ ci, onCerrar }: { ci: string | null; onCerrar: () => void }) {
  const edicion = ci !== null
  const existente = useEstudiante(ci)
  const opciones = useOpcionesEstudiantes()
  const registrar = useRegistrarEstudiante()
  const actualizar = useActualizarEstudiante()
  const [tutorEncontrado, setTutorEncontrado] = useState<string | null>(null)

  const form = useForm<DatosEstudiante>({
    resolver: zodResolver(esquemaEstudiante),
    defaultValues: { persona: PERSONA_VACIA, rude: '', antecedentes_academicos: '', ci_tutor: '', parentesco: '', id_curso: '' },
    values: existente.data
      ? {
          persona: personaAFormulario(existente.data),
          rude: existente.data.rude ?? '',
          antecedentes_academicos: existente.data.antecedentes_academicos ?? '',
          ci_tutor: '',
          parentesco: '',
          id_curso: '',
        }
      : undefined,
  })

  const verificarTutor = async () => {
    const ciTutor = form.getValues('ci_tutor').trim()
    setTutorEncontrado(null)
    form.clearErrors('ci_tutor')
    if (!ciTutor) return
    try {
      const t = await personasApi.buscar(ciTutor)
      if (!t.es_tutor) {
        form.setError('ci_tutor', { message: 'Esa persona no está registrada como tutor. Regístrela en “Padres y tutores”.' })
        return
      }
      setTutorEncontrado(nombreCompleto(t))
    } catch (e) {
      form.setError('ci_tutor', { message: mensajeError(e) })
    }
  }

  const guardar = form.handleSubmit(async (d) => {
    const nulo = (v: string) => (v ? v : null)
    try {
      if (edicion) {
        const { ci: _ci, ...persona } = personaParaApi(d.persona)
        await actualizar.mutateAsync({
          ci,
          cuerpo: { persona, rude: nulo(d.rude), antecedentes_academicos: nulo(d.antecedentes_academicos) },
        })
        toast.success('Datos del estudiante actualizados.')
      } else {
        const e = await registrar.mutateAsync({
          persona: personaParaApi(d.persona),
          rude: nulo(d.rude),
          antecedentes_academicos: nulo(d.antecedentes_academicos),
          tutor: d.ci_tutor
            ? { ci_tutor: d.ci_tutor, parentesco: d.parentesco, es_principal: true, es_responsable_pago: true, autorizado_recoger: true }
            : null,
          id_curso: d.id_curso && d.id_curso !== SIN_CURSO ? Number(d.id_curso) : null,
        })
        toast.success(`Estudiante ${nombreCompleto(e)} registrado.`)
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
          <DialogTitle>{edicion ? 'Editar estudiante' : 'Nuevo estudiante'}</DialogTitle>
          <DialogDescription>
            {edicion
              ? 'Actualice los datos personales y académicos.'
              : 'Registre los datos del estudiante. El tutor principal y la inscripción son opcionales.'}
          </DialogDescription>
        </DialogHeader>
        {edicion && existente.isLoading ? (
          <p className="py-6 text-center text-slate-500">Cargando...</p>
        ) : (
          <FormProvider {...form}>
            <form id="form-estudiante" onSubmit={guardar} className="space-y-5">
              <section className="space-y-3">
                <h3 className="text-sm font-semibold text-slate-700">Datos personales</h3>
                <CamposPersona
                  edicion={edicion}
                  validarExistente={(p) => (p.es_estudiante ? 'Esta persona ya está registrada como estudiante.' : null)}
                />
              </section>
              <Separator />
              <section className="grid gap-3 sm:grid-cols-3">
                <h3 className="text-sm font-semibold text-slate-700 sm:col-span-3">Datos académicos</h3>
                <Campo etiqueta="Código RUDE" error={e.rude?.message} htmlFor="rude">
                  <Input id="rude" {...form.register('rude')} />
                </Campo>
                <Campo etiqueta="Antecedentes académicos" error={e.antecedentes_academicos?.message} className="sm:col-span-2" htmlFor="antecedentes">
                  <Textarea id="antecedentes" rows={2} placeholder="Unidad educativa anterior, observaciones..." {...form.register('antecedentes_academicos')} />
                </Campo>
              </section>
              {!edicion && (
                <>
                  <Separator />
                  <section className="grid gap-3 sm:grid-cols-3">
                    <h3 className="text-sm font-semibold text-slate-700 sm:col-span-3">Tutor principal (opcional)</h3>
                    <Campo etiqueta="C.I. del tutor" error={e.ci_tutor?.message} htmlFor="ci_tutor">
                      <Input id="ci_tutor" {...form.register('ci_tutor', { onBlur: verificarTutor })} />
                    </Campo>
                    <Campo etiqueta="Parentesco" error={e.parentesco?.message}>
                      <Controller
                        control={form.control}
                        name="parentesco"
                        render={({ field }) => (
                          <Select value={field.value} onValueChange={field.onChange}>
                            <SelectTrigger className="w-full"><SelectValue placeholder="Seleccione" /></SelectTrigger>
                            <SelectContent>
                              {PARENTESCOS.map((p) => <SelectItem key={p} value={p}>{p}</SelectItem>)}
                            </SelectContent>
                          </Select>
                        )}
                      />
                    </Campo>
                    <p className="self-end pb-2 text-sm text-emerald-700">{tutorEncontrado && `✓ ${tutorEncontrado}`}</p>
                  </section>
                  <Separator />
                  <section className="grid gap-3">
                    <h3 className="text-sm font-semibold text-slate-700">
                      Inscripción {opciones.data?.gestion ? `en la gestión ${opciones.data.gestion}` : ''} (opcional)
                    </h3>
                    {opciones.data?.gestion ? (
                      <Controller
                        control={form.control}
                        name="id_curso"
                        render={({ field }) => (
                          <Select value={field.value || SIN_CURSO} onValueChange={field.onChange}>
                            <SelectTrigger className="w-full sm:w-96"><SelectValue /></SelectTrigger>
                            <SelectContent>
                              <SelectItem value={SIN_CURSO}>No inscribir por ahora</SelectItem>
                              {opciones.data?.cursos.map((c) => (
                                <SelectItem key={c.id_curso} value={String(c.id_curso)} disabled={c.inscritos >= c.cupo_maximo}>
                                  {c.nombre_curso} ({c.inscritos}/{c.cupo_maximo})
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        )}
                      />
                    ) : (
                      <p className="text-sm text-slate-500">No hay una gestión abierta.</p>
                    )}
                  </section>
                </>
              )}
            </form>
          </FormProvider>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={onCerrar}>Cancelar</Button>
          <Button type="submit" form="form-estudiante" disabled={ocupado}>
            {edicion ? 'Guardar cambios' : 'Registrar estudiante'}
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
  const detalle = useEstudiante(ci)
  const d: EstudianteDetalle | undefined = detalle.data
  return (
    <Dialog open={!!ci} onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{d ? nombreCompleto(d) : 'Estudiante'}</DialogTitle>
          <DialogDescription>{d && `C.I. ${documento(d.ci, d.expedido)} · RUDE ${d.rude ?? '—'}`}</DialogDescription>
        </DialogHeader>
        {!d ? (
          <p className="py-6 text-center text-slate-500">Cargando...</p>
        ) : (
          <div className="space-y-5">
            <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              <Dato etiqueta="Estado" valor={<InsigniaEstado estado={d.estado_persona} />} />
              <Dato etiqueta="Fecha de nacimiento" valor={fecha(d.fecha_nacimiento)} />
              <Dato etiqueta="Sexo" valor={d.sexo === 'F' ? 'Femenino' : d.sexo === 'M' ? 'Masculino' : null} />
              <Dato etiqueta="Teléfono" valor={d.telefono} />
              <Dato etiqueta="Correo" valor={d.email} />
              <Dato etiqueta="Cuenta de usuario" valor={d.tiene_usuario ? 'Sí' : 'No'} />
              <div className="col-span-2 sm:col-span-3"><Dato etiqueta="Dirección" valor={d.direccion} /></div>
              <div className="col-span-2 sm:col-span-3"><Dato etiqueta="Antecedentes académicos" valor={d.antecedentes_academicos} /></div>
            </dl>
            <Separator />
            <div>
              <h3 className="mb-2 text-sm font-semibold">Inscripción actual</h3>
              {d.inscripcion ? (
                <p className="text-sm">
                  Gestión {d.inscripcion.gestion} · {d.inscripcion.curso} · <InsigniaEstado estado={d.inscripcion.estado_inscripcion} /> ·
                  desde {fecha(d.inscripcion.fecha_inscripcion)}
                </p>
              ) : (
                <p className="text-sm text-slate-500">No está inscrito en la gestión abierta.</p>
              )}
            </div>
            <Separator />
            <div>
              <h3 className="mb-2 text-sm font-semibold">Padres / tutores</h3>
              {d.tutores.length === 0 ? (
                <p className="text-sm text-slate-500">Sin tutores vinculados. Se vinculan en “Padres y tutores”.</p>
              ) : (
                <ul className="divide-y rounded-lg border">
                  {d.tutores.map((t) => (
                    <li key={t.ci_tutor} className="flex flex-wrap items-center justify-between gap-2 px-3 py-2 text-sm">
                      <span>
                        <b>{t.nombre_tutor}</b> · {t.parentesco} · C.I. {t.ci_tutor}
                        {t.telefono_tutor && ` · Tel. ${t.telefono_tutor}`}
                      </span>
                      <span className="flex gap-1">
                        {t.es_principal && <span className="rounded bg-blue-50 px-1.5 text-xs text-blue-700">Principal</span>}
                        {t.es_responsable_pago && <span className="rounded bg-amber-50 px-1.5 text-xs text-amber-700">Paga</span>}
                        {t.autorizado_recoger && <span className="rounded bg-emerald-50 px-1.5 text-xs text-emerald-700">Recoge</span>}
                      </span>
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

function DialogoBaja({ estudiante, onCerrar }: { estudiante: Estudiante; onCerrar: () => void }) {
  const baja = useBajaEstudiante()
  const form = useForm<z.infer<typeof esquemaBaja>>({ resolver: zodResolver(esquemaBaja), defaultValues: { motivo: '' } })
  const guardar = form.handleSubmit(async ({ motivo }) => {
    try {
      await baja.mutateAsync({ ci: estudiante.ci, motivo })
      toast.success('Estudiante dado de baja.')
      onCerrar()
    } catch (e) {
      toast.error(mensajeError(e))
    }
  })
  return (
    <Dialog open onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Dar de baja a {nombreCompleto(estudiante)}</DialogTitle>
          <DialogDescription>
            Baja lógica: se conserva todo su historial. Su cuenta de usuario se desactiva y su inscripción activa pasa a
            “retirada”.
          </DialogDescription>
        </DialogHeader>
        <form id="form-baja" onSubmit={guardar}>
          <Campo etiqueta="Motivo" error={form.formState.errors.motivo?.message} htmlFor="motivo">
            <Textarea id="motivo" rows={3} placeholder="Ej. cambio de ciudad" {...form.register('motivo')} />
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

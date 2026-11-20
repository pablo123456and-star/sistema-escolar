/**
 * CU08 - Registrar tutor y asociarlo a estudiante
 * Paquete: personas
 *
 * Actores ........: Secretaría (rol administrador)
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/personas/casos_uso/cu08_registrar_asociar_tutor.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Listar, registrar y editar padres/tutores; ver los estudiantes a su cargo; asociar
 * estudiantes (parentesco, principal, responsable de pago, autorizado a recoger),
 * modificar el vínculo y desvincular (no si ya hay pagos).
 *
 * Precondición:  Sesión iniciada como administrador. El estudiante existe.
 * Postcondición: El tutor queda registrado y vinculado con su parentesco; cada estudiante tiene a lo sumo un tutor principal.
 *
 * Estado: IMPLEMENTADO.
 */
import { useState } from 'react'
import { Controller, FormProvider, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import type { z } from 'zod'
import { EyeIcon, Link2Icon, PencilIcon, PlusIcon, RotateCcwIcon, SearchIcon, UnlinkIcon } from 'lucide-react'
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
import { Checkbox } from '@/componentes/ui/checkbox'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/componentes/ui/dialog'
import { Input } from '@/componentes/ui/input'
import { Label } from '@/componentes/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { Separator } from '@/componentes/ui/separator'
import { Switch } from '@/componentes/ui/switch'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { documento, nombreCompleto } from '@/lib/formato'
import { useRetardo } from '@/lib/useRetardo'
import { mensajeError } from '@/nucleo/api'
import {
  personasApi,
  useActualizarTutor,
  useActualizarVinculo,
  useDesvincular,
  useRegistrarTutor,
  useTutor,
  useTutores,
  useVincular,
} from '../api'
import CamposPersona from '../componentes/CamposPersona'
import {
  PARENTESCOS,
  PERSONA_VACIA,
  esquemaTutor,
  esquemaVinculo,
  personaAFormulario,
  personaParaApi,
  type Vinculo,
} from '../schemas'

const TAMANO = 10

export default function CU08RegistrarAsociarTutor() {
  const [busqueda, setBusqueda] = useState('')
  const [estado, setEstado] = useState(TODOS)
  const [pagina, setPagina] = useState(1)
  const q = useRetardo(busqueda)
  const lista = useTutores({ q, estado: sinTodos(estado), pagina, tamano: TAMANO })

  const [formulario, setFormulario] = useState<{ ci: string | null } | null>(null)
  const [viendo, setViendo] = useState<string | null>(null)

  return (
    <div className="space-y-5">
      <EncabezadoPagina
        titulo="Padres y tutores"
        descripcion="Registre a los padres o tutores y asócielos con los estudiantes a su cargo."
        accion={
          <Button size="lg" onClick={() => setFormulario({ ci: null })}>
            <PlusIcon /> Nuevo tutor
          </Button>
        }
      />

      <div className="rounded-xl border bg-white shadow-sm">
        <div className="grid gap-3 p-4 md:grid-cols-[1fr_180px_auto] md:items-end">
          <Campo etiqueta="Buscar tutor">
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
              <TableHead>Ocupación</TableHead>
              <TableHead className="text-center">Estudiantes a cargo</TableHead>
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
              <FilaMensaje columnas={7} mensaje="No se encontraron tutores." />
            ) : (
              lista.data.items.map((t, i) => (
                <TableRow key={t.ci}>
                  <TableCell className="pl-4 text-slate-500">{(pagina - 1) * TAMANO + i + 1}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <AvatarIniciales nombre={nombreCompleto(t)} />
                      <div>
                        <p className="font-medium">{t.apellidos}, {t.nombre_persona}</p>
                        <p className="text-xs text-slate-500">C.I. {documento(t.ci, t.expedido)}</p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <p>{t.telefono ?? '—'}</p>
                    <p className="text-xs text-slate-500">{t.email ?? ''}</p>
                  </TableCell>
                  <TableCell>{t.ocupacion ?? '—'}</TableCell>
                  <TableCell className="text-center">
                    <span className="inline-flex min-w-7 justify-center rounded-full bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-700">
                      {t.cantidad_estudiantes}
                    </span>
                  </TableCell>
                  <TableCell><InsigniaEstado estado={t.estado_persona} /></TableCell>
                  <TableCell className="pr-4">
                    <div className="flex justify-center gap-1.5">
                      <BotonAccion etiqueta="Ver y asociar estudiantes" tono="azul" onClick={() => setViendo(t.ci)}>
                        <EyeIcon />
                      </BotonAccion>
                      <BotonAccion etiqueta="Editar" tono="ambar" onClick={() => setFormulario({ ci: t.ci })}>
                        <PencilIcon />
                      </BotonAccion>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <Paginacion pagina={pagina} tamano={TAMANO} total={lista.data?.total ?? 0} etiqueta="tutores" onCambiar={setPagina} />
      </div>

      {formulario && (
        <DialogoTutor
          ci={formulario.ci}
          onCerrar={() => setFormulario(null)}
          onCreado={(ci) => { setFormulario(null); setViendo(ci) }}
        />
      )}
      <DialogoVinculos ci={viendo} onCerrar={() => setViendo(null)} />
    </div>
  )
}

type DatosTutor = z.infer<typeof esquemaTutor>

function DialogoTutor({ ci, onCerrar, onCreado }: { ci: string | null; onCerrar: () => void; onCreado: (ci: string) => void }) {
  const edicion = ci !== null
  const existente = useTutor(ci)
  const registrar = useRegistrarTutor()
  const actualizar = useActualizarTutor()
  const form = useForm<DatosTutor>({
    resolver: zodResolver(esquemaTutor),
    defaultValues: { persona: PERSONA_VACIA, ocupacion: '' },
    values: existente.data
      ? { persona: personaAFormulario(existente.data), ocupacion: existente.data.ocupacion ?? '' }
      : undefined,
  })

  const guardar = form.handleSubmit(async (d) => {
    try {
      if (edicion) {
        const { ci: _ci, ...persona } = personaParaApi(d.persona)
        await actualizar.mutateAsync({ ci, cuerpo: { persona, ocupacion: d.ocupacion || null } })
        toast.success('Datos del tutor actualizados.')
        onCerrar()
      } else {
        const t = await registrar.mutateAsync({ persona: personaParaApi(d.persona), ocupacion: d.ocupacion || null })
        toast.success(`Tutor ${nombreCompleto(t)} registrado. Ahora puede asociarle estudiantes.`)
        onCreado(t.ci)
      }
    } catch (e) {
      toast.error(mensajeError(e))
    }
  })

  return (
    <Dialog open onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{edicion ? 'Editar tutor' : 'Nuevo padre o tutor'}</DialogTitle>
          <DialogDescription>
            {edicion ? 'Actualice los datos de contacto y la ocupación.' : 'Si la persona ya está registrada (por ejemplo, como docente), se reutilizan sus datos.'}
          </DialogDescription>
        </DialogHeader>
        {edicion && existente.isLoading ? (
          <p className="py-6 text-center text-slate-500">Cargando...</p>
        ) : (
          <FormProvider {...form}>
            <form id="form-tutor" onSubmit={guardar} className="space-y-4">
              <CamposPersona
                edicion={edicion}
                validarExistente={(p) => (p.es_tutor ? 'Esta persona ya está registrada como tutor.' : null)}
              />
              <Campo etiqueta="Ocupación" error={form.formState.errors.ocupacion?.message} htmlFor="ocupacion" className="sm:w-1/2">
                <Input id="ocupacion" {...form.register('ocupacion')} />
              </Campo>
            </form>
          </FormProvider>
        )}
        <DialogFooter>
          <Button variant="outline" onClick={onCerrar}>Cancelar</Button>
          <Button type="submit" form="form-tutor" disabled={registrar.isPending || actualizar.isPending}>
            {edicion ? 'Guardar cambios' : 'Registrar tutor'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function DialogoVinculos({ ci, onCerrar }: { ci: string | null; onCerrar: () => void }) {
  const tutor = useTutor(ci)
  const actualizarVinculo = useActualizarVinculo()
  const desvincular = useDesvincular()
  const [aQuitar, setAQuitar] = useState<Vinculo | null>(null)
  const t = tutor.data

  const cambiar = async (v: Vinculo, campo: 'es_principal' | 'es_responsable_pago' | 'autorizado_recoger', valor: boolean) => {
    try {
      await actualizarVinculo.mutateAsync({ ci_tutor: v.ci_tutor, ci_estudiante: v.ci_estudiante, [campo]: valor })
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  const quitar = async () => {
    if (!aQuitar) return
    try {
      await desvincular.mutateAsync({ ci_tutor: aQuitar.ci_tutor, ci_estudiante: aQuitar.ci_estudiante })
      toast.success('Estudiante desvinculado.')
      setAQuitar(null)
    } catch (e) {
      toast.error(mensajeError(e))
      setAQuitar(null)
    }
  }

  return (
    <Dialog open={!!ci} onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>{t ? nombreCompleto(t) : 'Tutor'}</DialogTitle>
          <DialogDescription>
            {t && `C.I. ${documento(t.ci, t.expedido)} · ${t.ocupacion ?? 'Sin ocupación registrada'} · Tel. ${t.telefono ?? '—'}${t.tiene_usuario ? ' · Tiene cuenta de usuario' : ''}`}
          </DialogDescription>
        </DialogHeader>
        {!t ? (
          <p className="py-6 text-center text-slate-500">Cargando...</p>
        ) : (
          <div className="space-y-5">
            <div>
              <h3 className="mb-2 text-sm font-semibold">Estudiantes a su cargo</h3>
              <div className="overflow-x-auto rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-slate-50">
                      <TableHead className="pl-3">Estudiante</TableHead>
                      <TableHead>Parentesco</TableHead>
                      <TableHead className="text-center">Principal</TableHead>
                      <TableHead className="text-center">Paga</TableHead>
                      <TableHead className="text-center">Recoge</TableHead>
                      <TableHead className="pr-3 text-center">Quitar</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {t.estudiantes.length === 0 ? (
                      <FilaMensaje columnas={6} mensaje="Todavía no tiene estudiantes asociados." />
                    ) : (
                      t.estudiantes.map((v) => (
                        <TableRow key={v.ci_estudiante}>
                          <TableCell className="pl-3">
                            <p className="font-medium">{v.nombre_estudiante}</p>
                            <p className="text-xs text-slate-500">
                              C.I. {v.ci_estudiante} · {v.curso_estudiante ?? 'Sin inscripción'}
                              {v.estado_estudiante !== 'activo' && ' · dado de baja'}
                            </p>
                          </TableCell>
                          <TableCell>{v.parentesco}</TableCell>
                          {(
                            [
                              ['es_principal', 'Tutor principal'],
                              ['es_responsable_pago', 'Responsable de pago'],
                              ['autorizado_recoger', 'Autorizado a recoger'],
                            ] as const
                          ).map(([campo, texto]) => (
                            <TableCell key={campo} className="text-center">
                              <Switch
                                checked={v[campo]}
                                disabled={actualizarVinculo.isPending}
                                onCheckedChange={(valor) => cambiar(v, campo, valor)}
                                aria-label={`${texto}: ${v.nombre_estudiante}`}
                              />
                            </TableCell>
                          ))}
                          <TableCell className="pr-3">
                            <div className="flex justify-center">
                              <BotonAccion etiqueta="Desvincular" tono="rojo" onClick={() => setAQuitar(v)}>
                                <UnlinkIcon />
                              </BotonAccion>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
              <p className="mt-1 text-xs text-slate-500">
                Cada estudiante tiene un solo tutor principal: al marcar este, se desmarca el anterior.
              </p>
            </div>
            <Separator />
            {t.estado_persona === 'activo' ? (
              <FormularioAsociar ciTutor={t.ci} />
            ) : (
              <p className="text-sm text-slate-500">El tutor está dado de baja: no se le pueden asociar estudiantes.</p>
            )}
          </div>
        )}
        <Confirmar
          abierto={!!aQuitar}
          onCambiar={(v) => !v && setAQuitar(null)}
          titulo="Desvincular estudiante"
          descripcion={`${aQuitar?.nombre_estudiante} dejará de estar a cargo de este tutor. No es posible si el tutor ya registró pagos del estudiante.`}
          textoConfirmar="Desvincular"
          icono={<UnlinkIcon />}
          peligro
          ocupado={desvincular.isPending}
          onConfirmar={quitar}
        />
      </DialogContent>
    </Dialog>
  )
}

type DatosVinculo = z.infer<typeof esquemaVinculo>

function FormularioAsociar({ ciTutor }: { ciTutor: string }) {
  const vincular = useVincular()
  const [estudiante, setEstudiante] = useState<string | null>(null)
  const form = useForm<DatosVinculo>({
    resolver: zodResolver(esquemaVinculo),
    defaultValues: { ci_estudiante: '', parentesco: '', es_principal: false, es_responsable_pago: false, autorizado_recoger: true },
  })

  const verificar = async () => {
    const ciEst = form.getValues('ci_estudiante').trim()
    setEstudiante(null)
    form.clearErrors('ci_estudiante')
    if (!ciEst) return
    try {
      const p = await personasApi.buscar(ciEst)
      if (!p.es_estudiante) {
        form.setError('ci_estudiante', { message: 'Esa persona no está registrada como estudiante.' })
        return
      }
      setEstudiante(nombreCompleto(p))
    } catch (e) {
      form.setError('ci_estudiante', { message: mensajeError(e) })
    }
  }

  const guardar = form.handleSubmit(async (d) => {
    try {
      await vincular.mutateAsync({ ci_tutor: ciTutor, ...d })
      toast.success('Estudiante asociado.')
      form.reset()
      setEstudiante(null)
    } catch (e) {
      toast.error(mensajeError(e))
    }
  })

  const e = form.formState.errors
  return (
    <form onSubmit={guardar} className="space-y-3">
      <h3 className="text-sm font-semibold">Asociar estudiante</h3>
      <div className="grid gap-3 sm:grid-cols-3">
        <Campo etiqueta="C.I. del estudiante" error={e.ci_estudiante?.message} htmlFor="ci_estudiante">
          <Input id="ci_estudiante" {...form.register('ci_estudiante', { onBlur: verificar })} />
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
        <p className="self-end pb-2 text-sm text-emerald-700">{estudiante && `✓ ${estudiante}`}</p>
      </div>
      <div className="flex flex-wrap items-center gap-5">
        {(
          [
            ['es_principal', 'Tutor principal'],
            ['es_responsable_pago', 'Responsable de pago'],
            ['autorizado_recoger', 'Autorizado a recoger'],
          ] as const
        ).map(([campo, texto]) => (
          <Controller
            key={campo}
            control={form.control}
            name={campo}
            render={({ field }) => (
              <div className="flex items-center gap-2">
                <Checkbox id={campo} checked={field.value} onCheckedChange={(v) => field.onChange(v === true)} />
                <Label htmlFor={campo} className="font-normal">{texto}</Label>
              </div>
            )}
          />
        ))}
        <Button type="submit" className="ml-auto" disabled={vincular.isPending}>
          <Link2Icon /> Asociar
        </Button>
      </div>
    </form>
  )
}

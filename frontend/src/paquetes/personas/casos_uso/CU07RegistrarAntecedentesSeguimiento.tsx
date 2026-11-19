/**
 * CU07 - Registrar antecedentes médicos y seguimiento del estudiante
 * Paquete: personas
 *
 * Actores ........: Administrativo, Docente (registran); Padre/Tutor (consulta)
 * Rol del sistema : administrador, profesor; tutor (solo lectura)
 * Backend ........: backend/app/paquetes/personas/casos_uso/cu07_registrar_antecedentes_seguimiento.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * A la izquierda, los estudiantes que el usuario puede consultar (administrador: todos;
 * profesor: los de sus cursos en la gestión actual; tutor: sus hijos). A la derecha, la ficha:
 *   - Antecedentes: observación médica (la edita solo el administrador; el profesor y el tutor la ven)
 *     y antecedentes académicos (se editan en el CU06).
 *   - Seguimiento: historial de anotaciones (no se editan ni se borran) y "Nueva anotación"
 *     para el administrador y el profesor.
 * El estudiante elegido queda en la dirección (?ci=...), así se puede enlazar desde el inicio.
 *
 * Precondición:  El estudiante existe. Un docente solo registra seguimiento de sus propios estudiantes.
 * Postcondición: La observación médica o el seguimiento queda guardado y visible para sus tutores.
 *
 * Estado: IMPLEMENTADO.
 */
import { useState, type ReactNode } from 'react'
import { useSearchParams } from 'react-router'
import { Controller, useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import type { z } from 'zod'
import {
  AlertTriangleIcon,
  AwardIcon,
  BookOpenIcon,
  HeartPulseIcon,
  MessageSquareTextIcon,
  PencilIcon,
  PlusIcon,
  SearchIcon,
  ShieldAlertIcon,
  StethoscopeIcon,
  UserIcon,
  type LucideIcon,
} from 'lucide-react'
import { cn } from 'cn'
import { AvatarIniciales, Campo, EncabezadoPagina, InsigniaEstado, Paginacion } from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/componentes/ui/dialog'
import { Input } from '@/componentes/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { Textarea } from '@/componentes/ui/textarea'
import { documento, ETIQUETA_ROL, fecha, nombreCompleto } from '@/lib/formato'
import { useRetardo } from '@/lib/useRetardo'
import { mensajeError } from '@/nucleo/api'
import { useSesion } from '@/nucleo/auth/contexto'
import { useActualizarAntecedentes, useEstudiantesSeguimiento, useFichaSeguimiento, useRegistrarSeguimiento } from '../api'
import {
  esquemaAntecedentes,
  esquemaSeguimiento,
  ETIQUETA_GRAVEDAD,
  ETIQUETA_TIPO,
  GRAVEDADES,
  hoyBolivia,
  TIPOS_SEGUIMIENTO,
  type EstudianteSeguimiento,
  type FichaSeguimiento,
  type Seguimiento,
  type TipoSeguimiento,
} from '../schemas'

const TAMANO = 8

const ESTILO_TIPO: Record<TipoSeguimiento, { icono: LucideIcon; clase: string; borde: string }> = {
  conducta: { icono: ShieldAlertIcon, clase: 'bg-amber-50 text-amber-700 ring-amber-200', borde: 'border-l-amber-400' },
  academico: { icono: BookOpenIcon, clase: 'bg-blue-50 text-blue-700 ring-blue-200', borde: 'border-l-blue-400' },
  salud: { icono: StethoscopeIcon, clase: 'bg-rose-50 text-rose-700 ring-rose-200', borde: 'border-l-rose-400' },
  merito: { icono: AwardIcon, clase: 'bg-emerald-50 text-emerald-700 ring-emerald-200', borde: 'border-l-emerald-400' },
  otro: { icono: MessageSquareTextIcon, clase: 'bg-slate-100 text-slate-700 ring-slate-200', borde: 'border-l-slate-300' },
}

const COLOR_GRAVEDAD: Record<string, string> = {
  leve: 'bg-yellow-50 text-yellow-800 ring-yellow-200',
  grave: 'bg-orange-50 text-orange-700 ring-orange-200',
  muy_grave: 'bg-red-50 text-red-700 ring-red-200',
}

const DESCRIPCION_POR_ROL: Record<string, string> = {
  administrador: 'Registre la observación médica de cada estudiante y las anotaciones de su seguimiento.',
  profesor: 'Registre el seguimiento de los estudiantes de sus cursos y consulte sus antecedentes médicos.',
  tutor: 'Consulte los antecedentes médicos y el seguimiento registrado por el colegio de sus hijos.',
}

export default function CU07RegistrarAntecedentesSeguimiento() {
  const { usuario } = useSesion()
  const rol = usuario?.rol ?? ''
  const [busqueda, setBusqueda] = useState('')
  const [pagina, setPagina] = useState(1)
  const q = useRetardo(busqueda)
  const lista = useEstudiantesSeguimiento({ q, pagina, tamano: TAMANO })

  const [parametros, setParametros] = useSearchParams()
  const items = lista.data?.items ?? []
  // El tutor suele tener uno o dos hijos: se abre el primero sin tener que elegirlo
  const ci = parametros.get('ci') ?? (rol === 'tutor' && !q ? (items[0]?.ci ?? null) : null)
  const elegir = (nuevo: string) => setParametros({ ci: nuevo }, { replace: true })

  return (
    <div className="space-y-5">
      <EncabezadoPagina
        titulo="Antecedentes y seguimiento"
        descripcion={DESCRIPCION_POR_ROL[rol] ?? 'Antecedentes médicos y seguimiento del estudiante.'}
      />

      <div className="grid gap-5 lg:grid-cols-[340px_minmax(0,1fr)] lg:items-start">
        <ListaEstudiantes
          rol={rol}
          busqueda={busqueda}
          onBuscar={(v) => { setBusqueda(v); setPagina(1) }}
          lista={lista}
          pagina={pagina}
          onPagina={setPagina}
          seleccionado={ci}
          onElegir={elegir}
        />
        {ci ? (
          <Ficha key={ci} ci={ci} />
        ) : (
          <div className="flex min-h-64 flex-col items-center justify-center gap-2 rounded-xl border border-dashed bg-white p-8 text-center text-slate-500">
            <UserIcon className="size-8 text-slate-300" />
            <p className="font-medium text-slate-700">Elija un estudiante</p>
            <p className="text-sm">Verá su observación médica, sus antecedentes y el historial de seguimiento.</p>
          </div>
        )}
      </div>
    </div>
  )
}

// ---- Lista de estudiantes ------------------------------------------------------------
function ListaEstudiantes({
  rol,
  busqueda,
  onBuscar,
  lista,
  pagina,
  onPagina,
  seleccionado,
  onElegir,
}: {
  rol: string
  busqueda: string
  onBuscar: (v: string) => void
  lista: ReturnType<typeof useEstudiantesSeguimiento>
  pagina: number
  onPagina: (p: number) => void
  seleccionado: string | null
  onElegir: (ci: string) => void
}) {
  const vacio =
    rol === 'profesor'
      ? 'No tiene estudiantes en sus cursos de la gestión actual.'
      : rol === 'tutor'
        ? 'No tiene estudiantes a su cargo.'
        : 'No se encontraron estudiantes.'
  return (
    <div className="rounded-xl border bg-white shadow-sm">
      <div className="border-b p-3">
        <div className="relative">
          <SearchIcon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" />
          <Input
            value={busqueda}
            onChange={(e) => onBuscar(e.target.value)}
            placeholder="Buscar por nombre o C.I..."
            className="pl-9"
            aria-label="Buscar estudiante"
          />
        </div>
      </div>
      <ul className="divide-y">
        {lista.isLoading ? (
          <li className="p-6 text-center text-sm text-slate-500">Cargando...</li>
        ) : lista.isError ? (
          <li className="p-6 text-center text-sm text-rose-600">{mensajeError(lista.error)}</li>
        ) : !lista.data?.items.length ? (
          <li className="p-6 text-center text-sm text-slate-500">{vacio}</li>
        ) : (
          lista.data.items.map((e) => (
            <FilaEstudiante key={e.ci} e={e} activo={e.ci === seleccionado} onClick={() => onElegir(e.ci)} />
          ))
        )}
      </ul>
      {(lista.data?.total ?? 0) > TAMANO && (
        <Paginacion pagina={pagina} tamano={TAMANO} total={lista.data?.total ?? 0} etiqueta="estudiantes" onCambiar={onPagina} />
      )}
    </div>
  )
}

function FilaEstudiante({ e, activo, onClick }: { e: EstudianteSeguimiento; activo: boolean; onClick: () => void }) {
  return (
    <li>
      <button
        type="button"
        onClick={onClick}
        aria-current={activo}
        className={cn(
          'flex w-full items-center gap-3 px-3 py-2.5 text-left transition-colors hover:bg-slate-50',
          activo && 'bg-blue-50 hover:bg-blue-50',
        )}
      >
        <AvatarIniciales
          nombre={nombreCompleto(e)}
          className={e.sexo === 'F' ? 'bg-rose-100 text-rose-700' : e.sexo === 'M' ? 'bg-sky-100 text-sky-700' : undefined}
        />
        <div className="min-w-0 flex-1">
          <p className={cn('truncate text-sm font-medium', e.estado_persona !== 'activo' && 'text-slate-400 line-through')}>
            {e.apellidos}, {e.nombre_persona}
          </p>
          <p className="truncate text-xs text-slate-500">{e.curso ?? 'Sin inscripción en la gestión actual'}</p>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          {e.tiene_observacion_medica && (
            <HeartPulseIcon className="size-4 text-rose-500" aria-label="Tiene observación médica" />
          )}
          {e.cantidad_seguimientos > 0 && (
            <span
              className="inline-flex min-w-6 justify-center rounded-full bg-slate-100 px-1.5 text-xs font-semibold text-slate-600"
              title={`${e.cantidad_seguimientos} anotación(es) · última ${fecha(e.ultimo_seguimiento)}`}
            >
              {e.cantidad_seguimientos}
            </span>
          )}
        </div>
      </button>
    </li>
  )
}

// ---- Ficha del estudiante ------------------------------------------------------------
type Pestana = 'antecedentes' | 'seguimiento'

function Ficha({ ci }: { ci: string }) {
  const ficha = useFichaSeguimiento(ci)
  const [pestana, setPestana] = useState<Pestana>('seguimiento')
  const [nueva, setNueva] = useState(false)

  if (ficha.isLoading) {
    return <div className="rounded-xl border bg-white p-10 text-center text-slate-500 shadow-sm">Cargando...</div>
  }
  if (ficha.isError || !ficha.data) {
    return (
      <div className="rounded-xl border bg-white p-10 text-center text-rose-600 shadow-sm">
        {mensajeError(ficha.error)}
      </div>
    )
  }
  const f = ficha.data
  return (
    <div className="rounded-xl border bg-white shadow-sm">
      <div className="flex flex-col gap-3 border-b p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <AvatarIniciales nombre={nombreCompleto(f)} className="size-11 text-sm" />
          <div>
            <h2 className="text-lg font-semibold text-slate-900">{nombreCompleto(f)}</h2>
            <p className="text-sm text-slate-500">
              C.I. {documento(f.ci, f.expedido)}
              {f.rude && ` · RUDE ${f.rude}`}
              {f.curso && ` · ${f.curso}`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {f.estado_persona !== 'activo' && <InsigniaEstado estado={f.estado_persona} />}
          {f.puede_registrar_seguimiento && (
            <Button onClick={() => { setPestana('seguimiento'); setNueva(true) }}>
              <PlusIcon /> Nueva anotación
            </Button>
          )}
        </div>
      </div>

      {f.observacion_medica && pestana === 'seguimiento' && (
        <button
          type="button"
          onClick={() => setPestana('antecedentes')}
          className="flex w-full items-start gap-2 border-b bg-rose-50 px-4 py-2.5 text-left text-sm text-rose-800 hover:bg-rose-100"
        >
          <AlertTriangleIcon className="mt-0.5 size-4 shrink-0" />
          <span className="line-clamp-2"><b>Observación médica:</b> {f.observacion_medica}</span>
        </button>
      )}

      <div role="tablist" className="flex gap-1 border-b px-4">
        <BotonPestana activa={pestana === 'seguimiento'} onClick={() => setPestana('seguimiento')}>
          Seguimiento <span className="ml-1 text-xs text-slate-400">({f.seguimientos.length})</span>
        </BotonPestana>
        <BotonPestana activa={pestana === 'antecedentes'} onClick={() => setPestana('antecedentes')}>
          Antecedentes
        </BotonPestana>
      </div>

      <div className="p-4">
        {pestana === 'antecedentes' ? <Antecedentes ficha={f} /> : <Historial seguimientos={f.seguimientos} />}
      </div>

      {nueva && <DialogoSeguimiento ficha={f} onCerrar={() => setNueva(false)} />}
    </div>
  )
}

function BotonPestana({ activa, onClick, children }: { activa: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={activa}
      onClick={onClick}
      className={cn(
        '-mb-px border-b-2 px-3 py-2.5 text-sm font-medium transition-colors',
        activa ? 'border-blue-600 text-blue-700' : 'border-transparent text-slate-500 hover:text-slate-800',
      )}
    >
      {children}
    </button>
  )
}

// ---- Pestaña Seguimiento ------------------------------------------------------------
function Historial({ seguimientos }: { seguimientos: Seguimiento[] }) {
  const [filtro, setFiltro] = useState<TipoSeguimiento | null>(null)
  if (seguimientos.length === 0) {
    return <p className="py-8 text-center text-sm text-slate-500">Todavía no hay anotaciones de seguimiento.</p>
  }
  const presentes = TIPOS_SEGUIMIENTO.filter((t) => seguimientos.some((s) => s.tipo === t))
  const visibles = filtro ? seguimientos.filter((s) => s.tipo === filtro) : seguimientos
  return (
    <div className="space-y-3">
      {presentes.length > 1 && (
        <div className="flex flex-wrap gap-1.5">
          <Chip activo={filtro === null} onClick={() => setFiltro(null)}>Todas ({seguimientos.length})</Chip>
          {presentes.map((t) => (
            <Chip key={t} activo={filtro === t} onClick={() => setFiltro(t)}>
              {ETIQUETA_TIPO[t]} ({seguimientos.filter((s) => s.tipo === t).length})
            </Chip>
          ))}
        </div>
      )}
      <ul className="space-y-2.5">
        {visibles.map((s) => (
          <TarjetaSeguimiento key={s.id_seguimiento} s={s} />
        ))}
      </ul>
    </div>
  )
}

function Chip({ activo, onClick, children }: { activo: boolean; onClick: () => void; children: ReactNode }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={activo}
      className={cn(
        'rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors',
        activo ? 'border-blue-600 bg-blue-600 text-white' : 'bg-white text-slate-600 hover:bg-slate-50',
      )}
    >
      {children}
    </button>
  )
}

function TarjetaSeguimiento({ s }: { s: Seguimiento }) {
  const estilo = ESTILO_TIPO[s.tipo]
  const Icono = estilo.icono
  return (
    <li className={cn('rounded-lg border border-l-4 p-3', estilo.borde)}>
      <div className="flex flex-wrap items-center gap-2">
        <span className={cn('inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset', estilo.clase)}>
          <Icono className="size-3.5" /> {ETIQUETA_TIPO[s.tipo]}
        </span>
        {s.gravedad && (
          <span className={cn('rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset', COLOR_GRAVEDAD[s.gravedad])}>
            {ETIQUETA_GRAVEDAD[s.gravedad]}
          </span>
        )}
        <span className="ml-auto text-xs text-slate-500">{fecha(s.fecha)}</span>
      </div>
      <p className="mt-2 text-sm whitespace-pre-line text-slate-800">{s.descripcion}</p>
      {s.accion_tomada && (
        <p className="mt-1.5 text-sm whitespace-pre-line text-slate-600">
          <span className="font-medium text-slate-700">Acción tomada:</span> {s.accion_tomada}
        </p>
      )}
      <p className="mt-2 text-xs text-slate-400">
        Registrado por {s.es_mio ? 'usted' : s.registrado_por}
        {!s.es_mio && s.rol_registrado_por && ` (${ETIQUETA_ROL[s.rol_registrado_por] ?? s.rol_registrado_por})`}
      </p>
    </li>
  )
}

// ---- Pestaña Antecedentes ------------------------------------------------------------
function Antecedentes({ ficha }: { ficha: FichaSeguimiento }) {
  const [editando, setEditando] = useState(false)
  return (
    <div className="space-y-5">
      <section>
        <div className="mb-2 flex items-center justify-between gap-2">
          <h3 className="flex items-center gap-1.5 text-sm font-semibold text-slate-700">
            <HeartPulseIcon className="size-4 text-rose-500" /> Observación médica
          </h3>
          {ficha.puede_editar_antecedentes && !editando && (
            <Button variant="outline" size="sm" onClick={() => setEditando(true)}>
              <PencilIcon /> {ficha.observacion_medica ? 'Modificar' : 'Registrar'}
            </Button>
          )}
        </div>
        {editando ? (
          <FormularioObservacion ficha={ficha} onCerrar={() => setEditando(false)} />
        ) : ficha.observacion_medica ? (
          <p className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm whitespace-pre-line text-rose-900">
            {ficha.observacion_medica}
          </p>
        ) : (
          <p className="rounded-lg border border-dashed p-3 text-sm text-slate-500">Sin observaciones médicas registradas.</p>
        )}
        {!ficha.puede_editar_antecedentes && (
          <p className="mt-1.5 text-xs text-slate-400">Para actualizarla, comuníquese con la secretaría del colegio.</p>
        )}
      </section>

      <section>
        <h3 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-slate-700">
          <BookOpenIcon className="size-4 text-blue-500" /> Antecedentes académicos
        </h3>
        {ficha.antecedentes_academicos ? (
          <p className="rounded-lg border bg-slate-50 p-3 text-sm whitespace-pre-line text-slate-800">
            {ficha.antecedentes_academicos}
          </p>
        ) : (
          <p className="rounded-lg border border-dashed p-3 text-sm text-slate-500">Sin antecedentes académicos registrados.</p>
        )}
        {ficha.puede_editar_antecedentes && (
          <p className="mt-1.5 text-xs text-slate-400">Se editan en “Estudiantes” (datos del estudiante).</p>
        )}
      </section>

      <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
        <div>
          <dt className="text-xs text-slate-500">Fecha de nacimiento</dt>
          <dd>{fecha(ficha.fecha_nacimiento)}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Curso {ficha.gestion ? `(${ficha.gestion})` : ''}</dt>
          <dd>{ficha.curso ?? '—'}</dd>
        </div>
        <div>
          <dt className="text-xs text-slate-500">Estado</dt>
          <dd><InsigniaEstado estado={ficha.estado_persona} /></dd>
        </div>
      </dl>
    </div>
  )
}

function FormularioObservacion({ ficha, onCerrar }: { ficha: FichaSeguimiento; onCerrar: () => void }) {
  const guardarApi = useActualizarAntecedentes()
  const form = useForm<z.infer<typeof esquemaAntecedentes>>({
    resolver: zodResolver(esquemaAntecedentes),
    defaultValues: { observacion_medica: ficha.observacion_medica ?? '' },
  })
  const guardar = form.handleSubmit(async ({ observacion_medica }) => {
    try {
      await guardarApi.mutateAsync({ ci: ficha.ci, observacion_medica: observacion_medica.trim() || null })
      toast.success('Observación médica guardada.')
      onCerrar()
    } catch (e) {
      toast.error(mensajeError(e))
    }
  })
  return (
    <form onSubmit={guardar} className="space-y-2">
      <Campo etiqueta="Observación médica" error={form.formState.errors.observacion_medica?.message} htmlFor="observacion">
        <Textarea
          id="observacion"
          rows={4}
          autoFocus
          placeholder="Ej. Alergia a la penicilina. Asma leve: usa inhalador. Déjelo vacío si no tiene observaciones."
          {...form.register('observacion_medica')}
        />
      </Campo>
      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={onCerrar}>Cancelar</Button>
        <Button type="submit" disabled={guardarApi.isPending}>Guardar</Button>
      </div>
    </form>
  )
}

// ---- Nueva anotación -----------------------------------------------------------------
type DatosSeguimiento = z.infer<typeof esquemaSeguimiento>

function DialogoSeguimiento({ ficha, onCerrar }: { ficha: FichaSeguimiento; onCerrar: () => void }) {
  const registrar = useRegistrarSeguimiento()
  const hoy = hoyBolivia()
  const form = useForm<DatosSeguimiento>({
    resolver: zodResolver(esquemaSeguimiento),
    defaultValues: { tipo: undefined, gravedad: '', fecha: hoy, descripcion: '', accion_tomada: '' },
  })
  const tipo = useWatch({ control: form.control, name: 'tipo' })

  const guardar = form.handleSubmit(async (d) => {
    try {
      await registrar.mutateAsync({
        ci: ficha.ci,
        cuerpo: {
          tipo: d.tipo,
          gravedad: d.tipo === 'conducta' ? d.gravedad : null,
          fecha: d.fecha,
          descripcion: d.descripcion,
          accion_tomada: d.accion_tomada.trim() || null,
        },
      })
      toast.success('Anotación registrada. Sus tutores ya pueden verla.')
      onCerrar()
    } catch (e) {
      toast.error(mensajeError(e))
    }
  })

  const e = form.formState.errors
  return (
    <Dialog open onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Nueva anotación de seguimiento</DialogTitle>
          <DialogDescription>
            {nombreCompleto(ficha)}{ficha.curso ? ` · ${ficha.curso}` : ''}. Las anotaciones no se editan ni se
            borran: si hay un error, aclárelo con otra anotación.
          </DialogDescription>
        </DialogHeader>
        <form id="form-seguimiento" onSubmit={guardar} className="grid gap-3 sm:grid-cols-2">
          <Campo etiqueta="Tipo" error={e.tipo?.message}>
            <Controller
              control={form.control}
              name="tipo"
              render={({ field }) => (
                <Select value={field.value ?? ''} onValueChange={field.onChange}>
                  <SelectTrigger className="w-full" aria-label="Tipo"><SelectValue placeholder="Elija..." /></SelectTrigger>
                  <SelectContent>
                    {TIPOS_SEGUIMIENTO.map((t) => (
                      <SelectItem key={t} value={t}>{ETIQUETA_TIPO[t]}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </Campo>
          <Campo etiqueta="Fecha" error={e.fecha?.message} htmlFor="fecha-seguimiento">
            <Input id="fecha-seguimiento" type="date" max={hoy} {...form.register('fecha')} />
          </Campo>
          {tipo === 'conducta' && (
            <Campo etiqueta="Gravedad" error={e.gravedad?.message} className="sm:col-span-2">
              <Controller
                control={form.control}
                name="gravedad"
                render={({ field }) => (
                  <div className="grid grid-cols-3 gap-2" role="radiogroup" aria-label="Gravedad">
                    {GRAVEDADES.map((g) => (
                      <button
                        key={g}
                        type="button"
                        role="radio"
                        aria-checked={field.value === g}
                        onClick={() => field.onChange(g)}
                        className={cn(
                          'rounded-md border px-2 py-1.5 text-sm font-medium transition-colors',
                          field.value === g ? cn('ring-2 ring-inset', COLOR_GRAVEDAD[g]) : 'hover:bg-slate-50',
                        )}
                      >
                        {ETIQUETA_GRAVEDAD[g]}
                      </button>
                    ))}
                  </div>
                )}
              />
            </Campo>
          )}
          <Campo etiqueta="Descripción" error={e.descripcion?.message} className="sm:col-span-2" htmlFor="descripcion">
            <Textarea id="descripcion" rows={4} placeholder="¿Qué ocurrió o qué se observó?" {...form.register('descripcion')} />
          </Campo>
          <Campo etiqueta="Acción tomada (opcional)" error={e.accion_tomada?.message} className="sm:col-span-2" htmlFor="accion">
            <Textarea id="accion" rows={2} placeholder="Ej. Se citó al tutor, llamada de atención..." {...form.register('accion_tomada')} />
          </Campo>
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={onCerrar}>Cancelar</Button>
          <Button type="submit" form="form-seguimiento" disabled={registrar.isPending}>Registrar anotación</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

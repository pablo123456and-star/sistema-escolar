/**
 * CU21 - Registrar asistencia de estudiantes
 * Paquete: evaluacion
 *
 * Actores ........: Docente
 * Rol del sistema : profesor, administrador
 * Backend ........: backend/app/paquetes/evaluacion/casos_uso/cu21_registrar_asistencia.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * 1) Elegir la clase: primero las que tocan hoy según el horario (el profesor ve solo las
 *    suyas; el administrador, todas, con filtro por curso).
 * 2) Marcar a cada estudiante (presente, ausente, tardanza, justificado) con observación
 *    opcional y guardar toda la clase de una vez. Si la fecha ya tenía registro se carga y se
 *    corrige. Avisa si el día no figura en el horario y bloquea los periodos cerrados.
 *
 * Precondición:  El docente dicta esa clase. La fecha no es futura y está dentro de la gestión.
 * Postcondición: La asistencia de la clase queda registrada o corregida y auditada.
 *
 * Estado: IMPLEMENTADO.
 */
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { toast } from 'sonner'
import { cn } from 'cn'
import {
  ArrowLeftIcon,
  CalendarDaysIcon,
  CheckCheckIcon,
  ClipboardCheckIcon,
  LockIcon,
  MessageSquareTextIcon,
  SaveIcon,
  TriangleAlertIcon,
} from 'lucide-react'
import Confirmar from '@/componentes/Confirmar'
import { AvatarIniciales, Campo, EncabezadoPagina, FilaMensaje } from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Input } from '@/componentes/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { fecha as formatoFecha, nombreCompleto } from '@/lib/formato'
import { mensajeError } from '@/nucleo/api'
import { useSesion } from '@/nucleo/auth/contexto'
import { useClasesAsistencia, useGuardarAsistencia, useListaAsistencia } from '../api'
import { ESTADOS_ASISTENCIA, type ClaseAsistencia, type EstadoAsistencia, type ListaAsistencia } from '../schemas'

const DIAS = ['domingo', 'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']
const DIA_LEGIBLE: Record<string, string> = {
  lunes: 'Lunes', martes: 'Martes', miercoles: 'Miércoles', jueves: 'Jueves',
  viernes: 'Viernes', sabado: 'Sábado', domingo: 'Domingo',
}

const ESTILO_ESTADO: Record<EstadoAsistencia, { etiqueta: string; letra: string; activo: string; texto: string }> = {
  presente: { etiqueta: 'Presente', letra: 'P', activo: 'bg-emerald-600 text-white border-emerald-600', texto: 'text-emerald-700' },
  ausente: { etiqueta: 'Ausente', letra: 'A', activo: 'bg-rose-600 text-white border-rose-600', texto: 'text-rose-700' },
  tardanza: { etiqueta: 'Tardanza', letra: 'T', activo: 'bg-amber-500 text-white border-amber-500', texto: 'text-amber-700' },
  justificado: { etiqueta: 'Justificado', letra: 'J', activo: 'bg-sky-600 text-white border-sky-600', texto: 'text-sky-700' },
}

/** Día de la semana de una fecha "aaaa-mm-dd" (sin conversión de zona horaria). */
const diaDe = (iso: string) => DIAS[new Date(`${iso}T12:00:00`).getDay()]

export default function CU21RegistrarAsistencia() {
  const clases = useClasesAsistencia()
  const [clase, setClase] = useState<ClaseAsistencia | null>(null)
  const [fecha, setFecha] = useState('')

  if (clase && clases.data) {
    return (
      <PantallaLista
        clase={clase}
        fecha={fecha || clases.data.hoy}
        hoy={clases.data.hoy}
        fechaInicio={clases.data.fecha_inicio}
        onFecha={setFecha}
        onVolver={() => {
          setClase(null)
          setFecha('')
        }}
      />
    )
  }

  return (
    <div className="space-y-5">
      <EncabezadoPagina
        titulo="Registro de asistencia"
        descripcion="Elija la clase para tomar o corregir la asistencia de sus estudiantes."
      />
      {clases.isLoading ? (
        <p className="py-10 text-center text-slate-500">Cargando...</p>
      ) : clases.isError ? (
        <p className="py-10 text-center text-slate-500">{mensajeError(clases.error)}</p>
      ) : !clases.data?.gestion ? (
        <Vacio texto="No hay una gestión abierta: no se puede registrar asistencia." />
      ) : !clases.data.clases.length ? (
        <Vacio texto="No tiene clases asignadas en la gestión actual." />
      ) : (
        <SeleccionClase datos={clases.data.clases} hoy={clases.data.hoy} onElegir={setClase} />
      )}
    </div>
  )
}

function Vacio({ texto }: { texto: string }) {
  return <div className="rounded-xl border border-dashed bg-white py-12 text-center text-slate-500">{texto}</div>
}

// ------------------------------------------------------------
// Paso 1: elegir la clase
// ------------------------------------------------------------

function SeleccionClase({ datos, hoy, onElegir }: { datos: ClaseAsistencia[]; hoy: string; onElegir: (c: ClaseAsistencia) => void }) {
  const { usuario } = useSesion()
  const esAdministrador = usuario?.rol === 'administrador'
  const [idCurso, setIdCurso] = useState('todos')
  const diaHoy = diaDe(hoy)

  const cursos = useMemo(() => [...new Map(datos.map((c) => [c.id_curso, c.curso])).entries()], [datos])
  const visibles = datos.filter((c) => idCurso === 'todos' || String(c.id_curso) === idCurso)
  const deHoy = visibles.filter((c) => c.dias.includes(diaHoy))
  const otras = visibles.filter((c) => !c.dias.includes(diaHoy))

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 rounded-xl border bg-white p-4 shadow-sm sm:flex-row sm:items-end sm:justify-between">
        <div className="flex items-center gap-3">
          <span className="inline-flex size-10 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
            <CalendarDaysIcon className="size-5" />
          </span>
          <div>
            <p className="text-sm text-slate-500">Hoy</p>
            <p className="font-semibold text-slate-900">{DIA_LEGIBLE[diaHoy]} {formatoFecha(hoy)}</p>
          </div>
        </div>
        {esAdministrador && (
          <Campo etiqueta="Curso" className="sm:w-72">
            <Select value={idCurso} onValueChange={setIdCurso}>
              <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="todos">Todos los cursos</SelectItem>
                {cursos.map(([id, nombre]) => <SelectItem key={id} value={String(id)}>{nombre}</SelectItem>)}
              </SelectContent>
            </Select>
          </Campo>
        )}
      </div>

      <GrupoClases titulo={`Clases de hoy (${DIA_LEGIBLE[diaHoy]})`} vacio="No hay clases en el horario de hoy." clases={deHoy}
        deHoy mostrarProfesor={esAdministrador} onElegir={onElegir} />
      <GrupoClases titulo="Otras clases" vacio="" clases={otras} mostrarProfesor={esAdministrador} onElegir={onElegir} />
    </div>
  )
}

function GrupoClases({
  titulo, vacio, clases, deHoy, mostrarProfesor, onElegir,
}: {
  titulo: string
  vacio: string
  clases: ClaseAsistencia[]
  deHoy?: boolean
  mostrarProfesor: boolean
  onElegir: (c: ClaseAsistencia) => void
}) {
  if (!clases.length && !vacio) return null
  return (
    <section className="space-y-2">
      <h2 className="text-sm font-semibold tracking-wide text-slate-500 uppercase">{titulo}</h2>
      {!clases.length ? (
        <p className="rounded-lg border border-dashed bg-white p-4 text-sm text-slate-500">{vacio}</p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {clases.map((c) => (
            <button
              key={c.id_asignacion}
              onClick={() => onElegir(c)}
              className={cn(
                'flex flex-col gap-2 rounded-xl border bg-white p-4 text-left shadow-sm transition hover:border-primary hover:shadow-md',
                deHoy && 'border-l-4 border-l-primary',
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="truncate font-semibold text-slate-900">{c.materia}</p>
                  <p className="truncate text-sm text-slate-600">{c.curso}</p>
                </div>
                {deHoy && (
                  <span className={cn('shrink-0 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset',
                    c.registrada_hoy ? 'bg-emerald-50 text-emerald-700 ring-emerald-200' : 'bg-amber-50 text-amber-700 ring-amber-200')}
                  >
                    {c.registrada_hoy ? 'Registrada' : 'Pendiente'}
                  </span>
                )}
              </div>
              {mostrarProfesor && <p className="text-xs text-slate-500">Docente: {c.profesor}</p>}
              <div className="flex flex-wrap gap-1">
                {c.dias.length ? c.dias.map((d) => (
                  <span key={d} className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-600">{DIA_LEGIBLE[d]}</span>
                )) : <span className="text-[11px] text-slate-400">Sin horario asignado</span>}
              </div>
            </button>
          ))}
        </div>
      )}
    </section>
  )
}

// ------------------------------------------------------------
// Paso 2: lista de la clase en una fecha
// ------------------------------------------------------------

function PantallaLista({
  clase, fecha, hoy, fechaInicio, onFecha, onVolver,
}: {
  clase: ClaseAsistencia
  fecha: string
  hoy: string
  fechaInicio: string | null
  onFecha: (f: string) => void
  onVolver: () => void
}) {
  const lista = useListaAsistencia(clase.id_asignacion, fecha)
  const [conCambios, setConCambios] = useState(false)
  const [pendiente, setPendiente] = useState<(() => void) | null>(null)

  // Si hay cambios sin guardar, pregunta antes de cambiar de fecha, volver o cerrar la pestaña
  const siNoHayCambios = (accion: () => void) => (conCambios ? setPendiente(() => accion) : accion())
  useEffect(() => {
    if (!conCambios) return
    const avisar = (e: BeforeUnloadEvent) => e.preventDefault()
    window.addEventListener('beforeunload', avisar)
    return () => window.removeEventListener('beforeunload', avisar)
  }, [conCambios])

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-1">
          <Button variant="ghost" size="sm" className="-ml-2 text-slate-500" onClick={() => siNoHayCambios(onVolver)}>
            <ArrowLeftIcon /> Volver a las clases
          </Button>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">{clase.materia}</h1>
          <p className="text-sm text-slate-500">{clase.curso} · Docente: {clase.profesor}</p>
        </div>
        <Campo etiqueta="Fecha" htmlFor="fecha" className="sm:w-52">
          <Input
            id="fecha"
            type="date"
            value={fecha}
            min={fechaInicio ?? undefined}
            max={hoy}
            onChange={(e) => {
              const nueva = e.target.value
              if (nueva && nueva <= hoy) siNoHayCambios(() => onFecha(nueva))
            }}
          />
        </Campo>
      </div>

      {lista.isLoading ? (
        <p className="py-10 text-center text-slate-500">Cargando lista...</p>
      ) : lista.isError ? (
        <Vacio texto={mensajeError(lista.error)} />
      ) : lista.data ? (
        <Planilla
          key={`${lista.data.fecha}-${lista.dataUpdatedAt}`}
          lista={lista.data}
          onCambios={setConCambios}
        />
      ) : null}

      <Confirmar
        abierto={pendiente !== null}
        onCambiar={(v) => !v && setPendiente(null)}
        titulo="Cambios sin guardar"
        descripcion="La asistencia que marcó todavía no se guardó. ¿Desea descartarla?"
        textoConfirmar="Descartar cambios"
        icono={<TriangleAlertIcon />}
        peligro
        onConfirmar={() => {
          pendiente?.()
          setPendiente(null)
          setConCambios(false)
        }}
      />
    </div>
  )
}

type Marca = { estado: EstadoAsistencia | null; observacion: string }

function Planilla({ lista, onCambios }: { lista: ListaAsistencia; onCambios: (v: boolean) => void }) {
  const guardar = useGuardarAsistencia(lista.clase.id_asignacion)
  const original = useMemo(
    () => Object.fromEntries(lista.estudiantes.map((e) => [e.ci, { estado: e.estado, observacion: e.observacion ?? '' }])),
    [lista],
  )
  const [marcas, setMarcas] = useState<Record<string, Marca>>(original)
  const [conObservacion, setConObservacion] = useState(() => new Set(lista.estudiantes.filter((e) => e.observacion).map((e) => e.ci)))

  const cambiado = lista.estudiantes.some(
    (e) => marcas[e.ci].estado !== original[e.ci].estado || marcas[e.ci].observacion.trim() !== original[e.ci].observacion,
  )
  useEffect(() => onCambios(cambiado), [cambiado, onCambios])

  const marcar = (ci: string, cambio: Partial<Marca>) => setMarcas((m) => ({ ...m, [ci]: { ...m[ci], ...cambio } }))
  const sinMarcar = lista.estudiantes.filter((e) => !marcas[e.ci].estado).length
  const conteo = (estado: EstadoAsistencia) => lista.estudiantes.filter((e) => marcas[e.ci].estado === estado).length
  const bloqueada = !lista.editable

  const enviar = async () => {
    try {
      await guardar.mutateAsync({
        fecha: lista.fecha,
        registros: lista.estudiantes.map((e) => ({
          ci_estudiante: e.ci,
          estado: marcas[e.ci].estado as EstadoAsistencia,
          observacion: marcas[e.ci].observacion.trim() || null,
        })),
      })
      toast.success(`Asistencia del ${formatoFecha(lista.fecha)} ${lista.registrada ? 'corregida' : 'registrada'}.`)
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2 text-sm">
        <Aviso tono="gris" icono={<CalendarDaysIcon />}>
          {DIA_LEGIBLE[diaDe(lista.fecha)]} {formatoFecha(lista.fecha)}{lista.periodo ? ` · ${lista.periodo}` : ''}
        </Aviso>
        {lista.registrada && !bloqueada && (
          <Aviso tono="azul" icono={<ClipboardCheckIcon />}>Ya tiene registro: está corrigiendo la asistencia de este día.</Aviso>
        )}
        {!lista.dia_con_clase && (
          <Aviso tono="ambar" icono={<TriangleAlertIcon />}>
            Este día no figura en el horario de la clase. Puede registrarlo igual (ej. clase de recuperación).
          </Aviso>
        )}
        {bloqueada && <Aviso tono="rojo" icono={<LockIcon />}>{lista.motivo_no_editable}</Aviso>}
      </div>

      <div className="rounded-xl border bg-white shadow-sm">
        <div className="flex flex-col gap-2 border-b p-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-slate-600">{lista.estudiantes.length} estudiantes inscritos</p>
          <Button
            variant="outline"
            size="sm"
            disabled={bloqueada || !lista.estudiantes.length}
            onClick={() => setMarcas((m) => Object.fromEntries(Object.entries(m).map(([ci, x]) => [ci, { ...x, estado: 'presente' }])))}
          >
            <CheckCheckIcon /> Todos presentes
          </Button>
        </div>

        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50">
              <TableHead className="w-10 pl-4">#</TableHead>
              <TableHead>Estudiante</TableHead>
              <TableHead className="text-center">Asistencia</TableHead>
              <TableHead className="w-12 pr-4" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {!lista.estudiantes.length ? (
              <FilaMensaje columnas={4} mensaje="El curso no tiene estudiantes inscritos." />
            ) : (
              lista.estudiantes.map((e, i) => {
                const marca = marcas[e.ci]
                const abierta = conObservacion.has(e.ci)
                return (
                  <TableRow key={e.ci} className={cn(!marca.estado && 'bg-amber-50/40')}>
                    <TableCell className="pl-4 align-top text-slate-500">{i + 1}</TableCell>
                    <TableCell className="align-top">
                      <div className="flex items-center gap-2.5">
                        <AvatarIniciales nombre={nombreCompleto(e)} className="hidden sm:inline-flex" />
                        <div className="min-w-0">
                          <p className="font-medium whitespace-normal">{e.apellidos}, {e.nombre_persona}</p>
                          <p className="text-xs text-slate-500">C.I. {e.ci}</p>
                        </div>
                      </div>
                      {abierta && (
                        <Input
                          className="mt-2 h-8 text-sm"
                          placeholder="Observación (ej. presentó certificado médico)"
                          maxLength={300}
                          disabled={bloqueada}
                          value={marca.observacion}
                          onChange={(ev) => marcar(e.ci, { observacion: ev.target.value })}
                        />
                      )}
                    </TableCell>
                    <TableCell className="align-top">
                      <div className="flex justify-center gap-1" role="radiogroup" aria-label={`Asistencia de ${nombreCompleto(e)}`}>
                        {ESTADOS_ASISTENCIA.map((estado) => (
                          <button
                            key={estado}
                            role="radio"
                            aria-checked={marca.estado === estado}
                            title={ESTILO_ESTADO[estado].etiqueta}
                            disabled={bloqueada}
                            onClick={() => marcar(e.ci, { estado })}
                            className={cn(
                              'h-8 min-w-8 rounded-md border px-2 text-xs font-semibold transition-colors disabled:opacity-60',
                              marca.estado === estado ? ESTILO_ESTADO[estado].activo : 'bg-white text-slate-500 hover:bg-slate-50',
                            )}
                          >
                            <span className="lg:hidden">{ESTILO_ESTADO[estado].letra}</span>
                            <span className="hidden lg:inline">{ESTILO_ESTADO[estado].etiqueta}</span>
                          </button>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell className="pr-4 align-top">
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        aria-label="Observación"
                        title="Observación"
                        className={cn((abierta || marca.observacion) && 'text-primary')}
                        onClick={() =>
                          setConObservacion((s) => {
                            const n = new Set(s)
                            if (n.has(e.ci)) n.delete(e.ci)
                            else n.add(e.ci)
                            return n
                          })
                        }
                      >
                        <MessageSquareTextIcon />
                      </Button>
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>

        <div className="sticky bottom-0 flex flex-col gap-3 rounded-b-xl border-t bg-white/95 p-3 backdrop-blur sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
            {ESTADOS_ASISTENCIA.map((estado) => (
              <span key={estado} className={ESTILO_ESTADO[estado].texto}>
                {ESTILO_ESTADO[estado].etiqueta}: <b>{conteo(estado)}</b>
              </span>
            ))}
            {sinMarcar > 0 && <span className="text-slate-500">Sin marcar: <b>{sinMarcar}</b></span>}
          </div>
          <Button
            disabled={bloqueada || sinMarcar > 0 || !cambiado || guardar.isPending}
            title={sinMarcar > 0 ? 'Marque a todos los estudiantes para guardar' : undefined}
            onClick={enviar}
          >
            <SaveIcon /> {guardar.isPending ? 'Guardando...' : lista.registrada ? 'Guardar corrección' : 'Guardar asistencia'}
          </Button>
        </div>
      </div>
    </div>
  )
}

const TONO_AVISO = {
  gris: 'bg-slate-100 text-slate-700',
  azul: 'bg-blue-50 text-blue-700',
  ambar: 'bg-amber-50 text-amber-800',
  rojo: 'bg-rose-50 text-rose-700',
}

function Aviso({ tono, icono, children }: { tono: keyof typeof TONO_AVISO; icono: ReactNode; children: ReactNode }) {
  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 [&_svg]:size-4 [&_svg]:shrink-0', TONO_AVISO[tono])}>
      {icono}
      {children}
    </span>
  )
}

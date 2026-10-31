/**
 * CU22 - Consultar historial de asistencia
 * Paquete: evaluacion
 *
 * Actores ........: Tutor, Administrativo
 * Rol del sistema : tutor, administrador, estudiante, profesor
 * Backend ........: backend/app/paquetes/evaluacion/casos_uso/cu22_consultar_historial_asistencia.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * 1) Elegir al estudiante: el estudiante se ve a sí mismo; el tutor elige entre sus hijos; el
 *    profesor y el administrador filtran por curso (el backend solo devuelve los que puede ver).
 * 2) Resumen de la gestión: porcentaje general y una tarjeta por materia con su porcentaje
 *    ((presente + tardanza) / clases registradas) y los conteos por estado; al tocar una
 *    materia se filtra el detalle. Filtros de gestión y rango de fechas.
 * 3) Detalle por fecha: materia, estado y observación (solo lectura).
 *
 * Precondición:  Sesión iniciada. Un tutor solo consulta a sus estudiantes.
 * Postcondición: Se muestra el detalle de asistencia y el porcentaje por materia. No se modifica nada.
 *
 * Estado: IMPLEMENTADO.
 */
import { useMemo, useState } from 'react'
import { cn } from 'cn'
import { CalendarCheckIcon, FilterXIcon } from 'lucide-react'
import { Campo, EncabezadoPagina, FilaMensaje, Paginacion } from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Input } from '@/componentes/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { fecha as formatoFecha } from '@/lib/formato'
import { TODOS } from '@/lib/filtros'
import { mensajeError } from '@/nucleo/api'
import { useSesion } from '@/nucleo/auth/contexto'
import { useEstudiantesHistorial, useHistorialAsistencia } from '../api'
import {
  ESTADOS_ASISTENCIA,
  type ConteoAsistencia,
  type EstadoAsistencia,
  type EstudianteHistorial,
  type HistorialAsistencia,
  type MateriaHistorial,
} from '../schemas'

const TAMANO_PAGINA = 15

const ESTILO_ESTADO: Record<EstadoAsistencia, { etiqueta: string; insignia: string; texto: string }> = {
  presente: { etiqueta: 'Presente', insignia: 'bg-emerald-50 text-emerald-700 ring-emerald-200', texto: 'text-emerald-700' },
  ausente: { etiqueta: 'Ausente', insignia: 'bg-rose-50 text-rose-700 ring-rose-200', texto: 'text-rose-700' },
  tardanza: { etiqueta: 'Tardanza', insignia: 'bg-amber-50 text-amber-700 ring-amber-200', texto: 'text-amber-700' },
  justificado: { etiqueta: 'Justificado', insignia: 'bg-sky-50 text-sky-700 ring-sky-200', texto: 'text-sky-700' },
}

const DIAS = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
/** Día de la semana de una fecha "aaaa-mm-dd" (sin conversión de zona horaria). */
const diaDe = (iso: string) => DIAS[new Date(`${iso}T12:00:00`).getDay()]

/** Color según el porcentaje de asistencia. */
function tonoPorcentaje(p: number | null) {
  if (p === null) return { texto: 'text-slate-400', barra: 'bg-slate-200' }
  if (p >= 90) return { texto: 'text-emerald-700', barra: 'bg-emerald-500' }
  if (p >= 75) return { texto: 'text-amber-700', barra: 'bg-amber-500' }
  return { texto: 'text-rose-700', barra: 'bg-rose-500' }
}

export default function CU22ConsultarHistorialAsistencia() {
  const { usuario } = useSesion()
  const estudiantes = useEstudiantesHistorial()
  const [ci, setCi] = useState<string | null>(null)

  const lista = estudiantes.data?.estudiantes ?? []
  const esTutor = usuario?.rol === 'tutor'
  // El estudiante (uno solo) y el tutor (sus hijos) ven directamente al primero
  const elegido = ci ?? (lista.length === 1 || esTutor ? (lista[0]?.ci ?? null) : null)
  const propio = usuario?.rol === 'estudiante'

  return (
    <div className="space-y-5">
      <EncabezadoPagina
        titulo={propio ? 'Mi asistencia' : 'Historial de asistencia'}
        descripcion="Porcentaje de asistencia por materia y detalle de cada clase registrada."
      />
      {estudiantes.isLoading ? (
        <p className="py-10 text-center text-slate-500">Cargando...</p>
      ) : estudiantes.isError ? (
        <Vacio texto={mensajeError(estudiantes.error)} />
      ) : !lista.length ? (
        <Vacio texto={estudiantes.data?.gestion ? 'No tiene estudiantes para consultar en la gestión actual.' : 'Todavía no hay gestiones registradas.'} />
      ) : (
        <>
          {lista.length > 1 &&
            (esTutor ? (
              <PestanasHijos estudiantes={lista} ci={elegido} onElegir={setCi} />
            ) : (
              <SeleccionEstudiante estudiantes={lista} ci={elegido} onElegir={setCi} />
            ))}
          {elegido ? (
            <Historial key={elegido} ci={elegido} />
          ) : (
            <Vacio texto="Elija un estudiante para ver su historial de asistencia." />
          )}
        </>
      )}
    </div>
  )
}

function Vacio({ texto }: { texto: string }) {
  return <div className="rounded-xl border border-dashed bg-white py-12 text-center text-slate-500">{texto}</div>
}

// ------------------------------------------------------------
// Paso 1: elegir al estudiante
// ------------------------------------------------------------

/** Tutor: una pestaña por cada uno de sus estudiantes. */
function PestanasHijos({
  estudiantes, ci, onElegir,
}: {
  estudiantes: EstudianteHistorial[]
  ci: string | null
  onElegir: (ci: string) => void
}) {
  return (
    <div className="flex flex-wrap gap-2" role="tablist">
      {estudiantes.map((e) => (
        <button
          key={e.ci}
          role="tab"
          aria-selected={e.ci === ci}
          onClick={() => onElegir(e.ci)}
          className={cn(
            'rounded-lg border px-4 py-2 text-left text-sm transition-colors',
            e.ci === ci ? 'border-primary bg-primary text-primary-foreground shadow-sm' : 'bg-white text-slate-600 hover:bg-slate-50',
          )}
        >
          <span className="block font-medium">{e.nombre_persona} {e.apellidos}</span>
          <span className="block text-xs opacity-75">{e.curso}</span>
        </button>
      ))}
    </div>
  )
}

function SeleccionEstudiante({
  estudiantes, ci, onElegir,
}: {
  estudiantes: EstudianteHistorial[]
  ci: string | null
  onElegir: (ci: string) => void
}) {
  const cursos = useMemo(() => [...new Set(estudiantes.map((e) => e.curso))], [estudiantes])
  const [curso, setCurso] = useState(TODOS)
  const visibles = estudiantes.filter((e) => curso === TODOS || e.curso === curso)

  return (
    <div className="flex flex-col gap-3 rounded-xl border bg-white p-4 shadow-sm sm:flex-row sm:items-end">
      {cursos.length > 1 && (
        <Campo etiqueta="Curso" className="sm:w-72">
          <Select value={curso} onValueChange={setCurso}>
            <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value={TODOS}>Todos los cursos</SelectItem>
              {cursos.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
            </SelectContent>
          </Select>
        </Campo>
      )}
      <Campo etiqueta="Estudiante" className="sm:flex-1">
        <Select value={ci ?? ''} onValueChange={onElegir}>
          <SelectTrigger className="w-full"><SelectValue placeholder="Elija un estudiante" /></SelectTrigger>
          <SelectContent>
            {visibles.map((e) => (
              <SelectItem key={e.ci} value={e.ci}>
                {e.apellidos}, {e.nombre_persona} · {e.curso}{e.estado_inscripcion !== 'activa' ? ` (${e.estado_inscripcion})` : ''}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </Campo>
    </div>
  )
}

// ------------------------------------------------------------
// Paso 2 y 3: resumen por materia y detalle
// ------------------------------------------------------------

function Historial({ ci }: { ci: string }) {
  const [idGestion, setIdGestion] = useState<number | undefined>()
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const rangoInvalido = !!desde && !!hasta && desde > hasta
  const historial = useHistorialAsistencia(rangoInvalido ? null : ci, {
    id_gestion: idGestion,
    desde: desde || undefined,
    hasta: hasta || undefined,
  })
  const datos = historial.data

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 rounded-xl border bg-white p-4 shadow-sm lg:flex-row lg:items-end lg:justify-between">
        <div>
          {datos ? (
            <>
              <p className="font-semibold text-slate-900">{datos.estudiante.apellidos}, {datos.estudiante.nombre_persona}</p>
              <p className="text-sm text-slate-500">C.I. {datos.estudiante.ci} · {datos.estudiante.curso} · Gestión {datos.gestion}</p>
            </>
          ) : (
            <p className="text-sm text-slate-500">C.I. {ci}</p>
          )}
        </div>
        <div className="flex flex-wrap items-end gap-3">
          {datos && datos.gestiones.length > 1 && (
            <Campo etiqueta="Gestión" className="w-32">
              <Select value={String(datos.id_gestion)} onValueChange={(v) => setIdGestion(Number(v))}>
                <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {datos.gestiones.map((g) => <SelectItem key={g.id_gestion} value={String(g.id_gestion)}>{g.anio}</SelectItem>)}
                </SelectContent>
              </Select>
            </Campo>
          )}
          <Campo etiqueta="Desde" htmlFor="desde" className="w-40">
            <Input id="desde" type="date" value={desde} max={hasta || undefined} onChange={(e) => setDesde(e.target.value)} />
          </Campo>
          <Campo etiqueta="Hasta" htmlFor="hasta" className="w-40">
            <Input id="hasta" type="date" value={hasta} min={desde || undefined} onChange={(e) => setHasta(e.target.value)} />
          </Campo>
          {(desde || hasta) && (
            <Button variant="ghost" onClick={() => { setDesde(''); setHasta('') }}>
              <FilterXIcon /> Quitar fechas
            </Button>
          )}
        </div>
      </div>

      {rangoInvalido ? (
        <Vacio texto="La fecha 'desde' no puede ser posterior a la fecha 'hasta'." />
      ) : historial.isLoading ? (
        <p className="py-10 text-center text-slate-500">Cargando historial...</p>
      ) : historial.isError ? (
        <Vacio texto={mensajeError(historial.error)} />
      ) : datos ? (
        <Resumen key={`${datos.id_gestion}-${desde}-${hasta}`} datos={datos} />
      ) : null}
    </div>
  )
}

function Resumen({ datos }: { datos: HistorialAsistencia }) {
  const [idMateria, setIdMateria] = useState<number | null>(null)
  const [pagina, setPagina] = useState(1)
  const detalle = datos.detalle.filter((d) => idMateria === null || d.id_materia === idMateria)
  const materia = datos.materias.find((m) => m.id_materia === idMateria)

  const elegirMateria = (id: number | null) => {
    setIdMateria(id)
    setPagina(1)
  }

  return (
    <div className="space-y-4">
      <ResumenGeneral conteo={datos.general} />

      <section className="space-y-2">
        <h2 className="text-sm font-semibold tracking-wide text-slate-500 uppercase">Por materia</h2>
        {!datos.materias.length ? (
          <p className="rounded-lg border border-dashed bg-white p-4 text-sm text-slate-500">El curso no tiene materias asignadas.</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {datos.materias.map((m) => (
              <TarjetaMateria
                key={m.id_materia}
                materia={m}
                activa={m.id_materia === idMateria}
                onClick={() => elegirMateria(m.id_materia === idMateria ? null : m.id_materia)}
              />
            ))}
          </div>
        )}
      </section>

      <div className="rounded-xl border bg-white shadow-sm">
        <div className="flex flex-col gap-2 border-b p-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-slate-600">
            Detalle {materia ? <>de <b>{materia.materia}</b></> : 'de todas las materias'} · {detalle.length} registros
          </p>
          {materia && (
            <Button variant="outline" size="sm" onClick={() => elegirMateria(null)}>
              <FilterXIcon /> Ver todas
            </Button>
          )}
        </div>
        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50">
              <TableHead className="pl-4">Fecha</TableHead>
              <TableHead>Materia</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="pr-4">Observación</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!detalle.length ? (
              <FilaMensaje columnas={4} mensaje="No hay asistencia registrada con estos filtros." />
            ) : (
              detalle.slice((pagina - 1) * TAMANO_PAGINA, pagina * TAMANO_PAGINA).map((d) => (
                <TableRow key={`${d.fecha}-${d.id_materia}`}>
                  <TableCell className="pl-4">
                    <span className="font-medium">{formatoFecha(d.fecha)}</span>
                    <span className="ml-2 text-xs text-slate-500">{diaDe(d.fecha)}</span>
                  </TableCell>
                  <TableCell>{d.materia}</TableCell>
                  <TableCell>
                    <span className={cn('inline-flex rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset', ESTILO_ESTADO[d.estado].insignia)}>
                      {ESTILO_ESTADO[d.estado].etiqueta}
                    </span>
                  </TableCell>
                  <TableCell className="pr-4 whitespace-normal text-slate-600">{d.observacion ?? '—'}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        {detalle.length > TAMANO_PAGINA && (
          <Paginacion pagina={pagina} tamano={TAMANO_PAGINA} total={detalle.length} etiqueta="registros" onCambiar={setPagina} />
        )}
      </div>
    </div>
  )
}

function Conteos({ conteo }: { conteo: ConteoAsistencia }) {
  return (
    <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs">
      {ESTADOS_ASISTENCIA.map((estado) => (
        <span key={estado} className={ESTILO_ESTADO[estado].texto}>
          {ESTILO_ESTADO[estado].etiqueta}: <b>{conteo[estado]}</b>
        </span>
      ))}
    </div>
  )
}

function ResumenGeneral({ conteo }: { conteo: ConteoAsistencia }) {
  const tono = tonoPorcentaje(conteo.porcentaje)
  return (
    <div className="flex flex-col gap-3 rounded-xl border bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        <span className="inline-flex size-10 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
          <CalendarCheckIcon className="size-5" />
        </span>
        <div>
          <p className="text-sm text-slate-500">Asistencia general · {conteo.total} clases registradas</p>
          <p className={cn('text-2xl font-bold', tono.texto)}>
            {conteo.porcentaje === null ? 'Sin registros' : `${conteo.porcentaje.toFixed(1)} %`}
          </p>
        </div>
      </div>
      <Conteos conteo={conteo} />
    </div>
  )
}

function TarjetaMateria({ materia, activa, onClick }: { materia: MateriaHistorial; activa: boolean; onClick: () => void }) {
  const tono = tonoPorcentaje(materia.porcentaje)
  return (
    <button
      onClick={onClick}
      aria-pressed={activa}
      className={cn(
        'flex flex-col gap-2 rounded-xl border bg-white p-4 text-left shadow-sm transition hover:border-primary hover:shadow-md',
        activa && 'border-primary ring-2 ring-primary/20',
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="min-w-0 truncate font-semibold text-slate-900">{materia.materia}</p>
        <p className={cn('shrink-0 text-lg font-bold', tono.texto)}>
          {materia.porcentaje === null ? <span className="text-sm font-medium">Sin registros</span> : `${materia.porcentaje.toFixed(1)} %`}
        </p>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div className={cn('h-full rounded-full', tono.barra)} style={{ width: `${materia.porcentaje ?? 0}%` }} />
      </div>
      <p className="text-xs text-slate-500">{materia.total} clases registradas</p>
      <Conteos conteo={materia} />
    </button>
  )
}

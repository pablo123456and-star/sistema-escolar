/**
 * Piezas de los paneles de inicio (CU01): bienvenida, indicadores, avisos, tarjetas,
 * horario semanal, próximas clases, calificaciones, asistencia, cuotas y comunicados.
 */
import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { cn } from 'cn'
import {
  CalendarClockIcon,
  ChevronRightIcon,
  ClockIcon,
  MapPinIcon,
  MegaphoneIcon,
  SparklesIcon,
  type LucideIcon,
} from 'lucide-react'
import { InsigniaEstado } from '@/componentes/comunes'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { bolivianos, ETIQUETA_ROL, fecha, fechaHora } from '@/lib/formato'
import { useSesion } from '@/nucleo/auth/contexto'
import { useResumenInicio } from '@/paquetes/seguridad/api'
import { DIAS_CLASE, diaHoy, porcentajeAsistencia, promedioMateria, tonoNota, type ClaseProgramada } from './calculos'
import type { BloqueHorario, Comunicado, Cuota, NotaMateria, ResumenAsistencia } from './datosEjemplo'

export function Bienvenida({ extra }: { extra?: string }) {
  const { usuario } = useSesion()
  const { data } = useResumenInicio()
  return (
    <div>
      <h1 className="text-2xl font-bold text-slate-900">Bienvenido, {usuario?.nombres}</h1>
      <p className="text-slate-500">
        Sistema de Gestión Académica · {usuario && (usuario.cargo ?? ETIQUETA_ROL[usuario.rol])}
        {extra && ` · ${extra}`}
        {data?.gestion && ` · ${data.gestion}`}
      </p>
    </div>
  )
}

export function AvisoPrototipo({ casos, texto }: { casos: string; texto?: string }) {
  return (
    <div className="flex items-start gap-2 rounded-lg border border-dashed border-blue-200 bg-blue-50/60 px-3 py-2 text-xs text-blue-700">
      <SparklesIcon className="mt-px size-4 shrink-0" />
      <p>{texto ?? `Vista previa: la información de este panel es de ejemplo hasta implementar ${casos}.`}</p>
    </div>
  )
}

/** Lugar reservado para una sección cuyo caso de uso todavía no está implementado (sin datos de ejemplo). */
export function Pendiente({ texto }: { texto: string }) {
  return <p className="rounded-lg border border-dashed bg-slate-50 px-4 py-6 text-center text-sm text-slate-500">{texto}</p>
}

export function Indicador({
  titulo,
  valor,
  detalle,
  icono: Icono,
  tono,
}: {
  titulo: string
  valor?: number | string
  detalle?: string
  icono: LucideIcon
  tono: string
}) {
  return (
    <div className={cn('flex items-center gap-4 rounded-xl border p-5 shadow-sm', tono)}>
      <Icono className="size-10 shrink-0" strokeWidth={1.6} />
      <div className="min-w-0">
        <p className="text-sm font-medium text-slate-600">{titulo}</p>
        <p className="text-2xl font-bold text-slate-900">{valor ?? '—'}</p>
        {detalle && <p className="truncate text-xs text-slate-500">{detalle}</p>}
      </div>
    </div>
  )
}

export function Aviso({ icono: Icono, tono, titulo, children }: { icono: LucideIcon; tono: string; titulo: string; children: ReactNode }) {
  return (
    <div className={cn('flex gap-3 rounded-lg border p-3', tono)}>
      <Icono className="mt-0.5 size-5 shrink-0" />
      <div className="text-sm">
        <p className="font-semibold">{titulo}</p>
        <div className="text-slate-600">{children}</div>
      </div>
    </div>
  )
}

export function Tarjeta({
  titulo,
  icono: Icono,
  enlace,
  sinRelleno,
  className,
  children,
}: {
  titulo: string
  icono?: LucideIcon
  enlace?: { texto: string; ruta: string }
  sinRelleno?: boolean
  className?: string
  children: ReactNode
}) {
  return (
    <section className={cn('min-w-0 rounded-xl border bg-white shadow-sm', className)}>
      <div className="flex items-center justify-between gap-2 border-b px-4 py-3">
        <h2 className="flex items-center gap-2 font-semibold">
          {Icono && <Icono className="size-4 text-blue-600" />}
          {titulo}
        </h2>
        {enlace && (
          <Link to={enlace.ruta} className="shrink-0 text-sm text-blue-600 hover:underline">
            {enlace.texto}
          </Link>
        )}
      </div>
      <div className={cn(!sinRelleno && 'p-4')}>{children}</div>
    </section>
  )
}

export function AccesoRapido({ icono: Icono, titulo, descripcion, ruta }: { icono: LucideIcon; titulo: string; descripcion: string; ruta: string }) {
  return (
    <Link
      to={ruta}
      className="group flex items-center gap-3 rounded-xl border bg-white p-4 shadow-sm transition-colors hover:border-blue-200 hover:bg-blue-50/50"
    >
      <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
        <Icono className="size-5" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-semibold text-slate-900">{titulo}</span>
        <span className="block truncate text-xs text-slate-500">{descripcion}</span>
      </span>
      <ChevronRightIcon className="size-4 text-slate-400 group-hover:text-blue-600" />
    </Link>
  )
}

export function Nota({ valor }: { valor: number | null }) {
  if (valor === null) return <span className="text-slate-400">—</span>
  return <span className={cn('font-semibold', tonoNota(valor))}>{valor}</span>
}

export function Barra({ valor, className }: { valor: number; className?: string }) {
  const tono = valor >= 90 ? 'bg-emerald-500' : valor >= 75 ? 'bg-amber-500' : 'bg-rose-500'
  return (
    <div className={cn('h-2 w-full overflow-hidden rounded-full bg-slate-100', className)}>
      <div className={cn('h-full rounded-full', tono)} style={{ width: `${Math.min(100, valor)}%` }} />
    </div>
  )
}

/** Horario de lunes a viernes; resalta la columna de hoy. */
export function HorarioSemanal({ bloques, detalle }: { bloques: BloqueHorario[]; detalle: 'docente' | 'curso' }) {
  const hoy = diaHoy()
  const franjas = [...new Set(bloques.map((b) => `${b.inicio}-${b.fin}`))].sort()
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] border-collapse text-sm">
        <thead>
          <tr className="bg-slate-50 text-left text-slate-600">
            <th className="w-28 px-3 py-2 font-medium">Hora</th>
            {DIAS_CLASE.map((d) => (
              <th key={d.dia} className={cn('px-3 py-2 font-medium', d.dia === hoy && 'bg-blue-50 text-blue-700')}>
                {d.etiqueta}
                {d.dia === hoy && <span className="ml-1 text-xs font-normal">(hoy)</span>}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {franjas.map((franja) => {
            const [inicio, fin] = franja.split('-')
            return (
              <tr key={franja} className="border-t">
                <td className="px-3 py-2 whitespace-nowrap text-slate-500">
                  {inicio} – {fin}
                </td>
                {DIAS_CLASE.map((d) => {
                  const b = bloques.find((x) => x.dia === d.dia && x.inicio === inicio)
                  return (
                    <td key={d.dia} className={cn('px-2 py-2 align-top', d.dia === hoy && 'bg-blue-50/60')}>
                      {b && (
                        <div className="rounded-md border-l-4 border-blue-500 bg-white px-2 py-1.5 shadow-xs">
                          <p className="font-medium text-slate-900">{b.materia}</p>
                          <p className="text-xs text-slate-500">
                            {b.aula} · {detalle === 'docente' ? b.docente : b.curso}
                          </p>
                        </div>
                      )}
                    </td>
                  )
                })}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

/** Lista de próximas clases; `acciones` agrega botones por clase (ej. tomar asistencia). */
export function ListaClases({
  clases,
  detalle,
  acciones,
}: {
  clases: ClaseProgramada[]
  detalle: 'docente' | 'curso'
  acciones?: (c: ClaseProgramada) => ReactNode
}) {
  if (!clases.length) return <p className="text-sm text-slate-500">No hay clases programadas.</p>
  return (
    <ul className="divide-y">
      {clases.map((c) => (
        <li key={`${c.fecha}-${c.bloque.inicio}`} className="flex flex-col gap-2 py-3 first:pt-0 last:pb-0 sm:flex-row sm:items-center">
          <div className="flex min-w-0 flex-1 items-center gap-3">
            <span
              className={cn(
                'flex w-16 shrink-0 flex-col items-center rounded-lg px-2 py-1.5 text-xs font-semibold',
                c.esHoy ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600',
              )}
            >
              {c.etiqueta}
            </span>
            <div className="min-w-0">
              <p className="truncate font-medium text-slate-900">{c.bloque.materia}</p>
              <p className="flex flex-wrap items-center gap-x-3 text-xs text-slate-500">
                <span className="inline-flex items-center gap-1">
                  <ClockIcon className="size-3" /> {c.bloque.inicio} – {c.bloque.fin}
                </span>
                <span className="inline-flex items-center gap-1">
                  <MapPinIcon className="size-3" /> {c.bloque.aula}
                </span>
                <span>{detalle === 'docente' ? c.bloque.docente : c.bloque.curso}</span>
              </p>
            </div>
          </div>
          {acciones && <div className="flex gap-2 sm:shrink-0">{acciones(c)}</div>}
        </li>
      ))}
    </ul>
  )
}

export function TablaNotas({ notas }: { notas: NotaMateria[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow className="bg-slate-50">
          <TableHead className="pl-4">Materia</TableHead>
          <TableHead className="text-center">1er T.</TableHead>
          <TableHead className="text-center">2do T.</TableHead>
          <TableHead className="text-center">3er T.</TableHead>
          <TableHead className="pr-4 text-center">Promedio</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {notas.map((n) => (
          <TableRow key={n.materia}>
            <TableCell className="pl-4">
              <p className="font-medium text-slate-900">{n.materia}</p>
              <p className="text-xs text-slate-500">{n.docente}</p>
            </TableCell>
            <TableCell className="text-center"><Nota valor={n.t1} /></TableCell>
            <TableCell className="text-center"><Nota valor={n.t2} /></TableCell>
            <TableCell className="text-center">
              {n.t3 === null ? <span className="text-xs text-slate-400">En curso</span> : <Nota valor={n.t3} />}
            </TableCell>
            <TableCell className="pr-4 text-center"><Nota valor={promedioMateria(n)} /></TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

const ETIQUETA_FALTA = { falta: 'Falta', atraso: 'Atraso', licencia: 'Licencia' }
const TONO_FALTA = { falta: 'bg-rose-50 text-rose-700', atraso: 'bg-amber-50 text-amber-700', licencia: 'bg-sky-50 text-sky-700' }

export function DetalleAsistencia({ asistencia, periodo = 'Septiembre' }: { asistencia: ResumenAsistencia; periodo?: string }) {
  const porcentaje = porcentajeAsistencia(asistencia)
  const conteos = [
    { texto: 'Presente', valor: asistencia.presentes, tono: 'text-emerald-600' },
    { texto: 'Atraso', valor: asistencia.atrasos, tono: 'text-amber-600' },
    { texto: 'Falta', valor: asistencia.faltas, tono: 'text-rose-600' },
    { texto: 'Licencia', valor: asistencia.licencias, tono: 'text-sky-600' },
  ]
  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-baseline justify-between">
          <span className="text-3xl font-bold text-slate-900">{porcentaje}%</span>
          <span className="text-xs text-slate-500">{periodo}</span>
        </div>
        <Barra valor={porcentaje} className="mt-2" />
      </div>
      <div className="grid grid-cols-4 gap-2 text-center">
        {conteos.map((c) => (
          <div key={c.texto} className="rounded-lg bg-slate-50 py-2">
            <p className={cn('text-lg font-bold', c.tono)}>{c.valor}</p>
            <p className="text-[11px] text-slate-500">{c.texto}</p>
          </div>
        ))}
      </div>
      {asistencia.recientes.length > 0 ? (
        <ul className="space-y-2">
          {asistencia.recientes.map((r) => (
            <li key={`${r.fecha}-${r.materia}`} className="flex items-center justify-between gap-2 text-sm">
              <span className="min-w-0 truncate">
                <span className="text-slate-500">{fecha(r.fecha)}</span> · {r.materia}
              </span>
              <span className={cn('shrink-0 rounded-md px-2 py-0.5 text-xs font-medium', TONO_FALTA[r.tipo])}>
                {ETIQUETA_FALTA[r.tipo]}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-emerald-600">Sin faltas ni atrasos registrados.</p>
      )}
    </div>
  )
}

export function ListaCuotas({ cuotas, cantidad = 4 }: { cuotas: Cuota[]; cantidad?: number }) {
  const pagadas = cuotas.filter((c) => c.estado === 'pagada').length
  const deuda = cuotas.filter((c) => c.estado === 'vencida').reduce((a, c) => a + c.monto, 0)
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2 text-center">
        <div className="rounded-lg bg-emerald-50 py-2">
          <p className="text-lg font-bold text-emerald-600">{pagadas}</p>
          <p className="text-[11px] text-slate-500">Cuotas pagadas</p>
        </div>
        <div className={cn('rounded-lg py-2', deuda ? 'bg-rose-50' : 'bg-slate-50')}>
          <p className={cn('text-lg font-bold', deuda ? 'text-rose-600' : 'text-slate-700')}>{bolivianos(deuda)}</p>
          <p className="text-[11px] text-slate-500">Deuda vencida</p>
        </div>
      </div>
      <ul className="divide-y">
        {cuotas.slice(-cantidad).reverse().map((c) => (
          <li key={c.mes} className="flex items-center justify-between gap-2 py-2 text-sm">
            <div className="min-w-0">
              <p className="font-medium text-slate-900">{c.mes}</p>
              <p className="text-xs text-slate-500">
                {c.estado === 'pagada' ? `Pagado el ${fecha(c.pagado_en)}` : `Vence el ${fecha(c.vence)}`}
              </p>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <span className="text-slate-700">{bolivianos(c.monto)}</span>
              <InsigniaEstado estado={c.estado} />
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

export function ListaComunicados({ comunicados }: { comunicados: Comunicado[] }) {
  if (!comunicados.length) return <p className="text-sm text-slate-500">No hay comunicados.</p>
  return (
    <ul className="space-y-3">
      {comunicados.map((c) => {
        const citacion = c.tipo === 'citacion'
        const Icono = citacion ? CalendarClockIcon : MegaphoneIcon
        return (
          <li key={c.titulo} className={cn('flex gap-3 rounded-lg border p-3', citacion ? 'border-amber-100 bg-amber-50' : 'border-slate-100')}>
            <Icono className={cn('mt-0.5 size-5 shrink-0', citacion ? 'text-amber-600' : 'text-blue-600')} />
            <div className="min-w-0 text-sm">
              <p className="font-semibold text-slate-900">{c.titulo}</p>
              <p className="line-clamp-2 text-slate-600">{c.contenido}</p>
              {c.fecha_citacion && <p className="mt-1 font-medium text-amber-700">Citación: {fechaHora(c.fecha_citacion)}</p>}
              <p className="mt-1 text-xs text-slate-400">
                {c.autor} · {fecha(c.fecha)}
              </p>
            </div>
          </li>
        )
      })}
    </ul>
  )
}

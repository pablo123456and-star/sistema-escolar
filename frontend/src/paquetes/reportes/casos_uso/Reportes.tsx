/**
 * Reportes (consigna del ciclo 3: «Reportes: estático y dinámico. Generar a 2 formatos»)
 * Paquete: reportes
 *
 * Actores ........: Director, Secretaría
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/reportes/casos_uso/reportes_estaticos.py y reporte_dinamico.py
 *
 * Pantalla:
 * - Reportes fijos: se elige el reporte (morosos, inscritos, asistencia o rendimiento por curso) y sus
 *   parámetros; se ve en pantalla y se descarga en PDF o Excel.
 * - Reporte personalizado: se elige la fuente, los filtros, las columnas y el orden; vista previa y
 *   descarga en PDF o Excel.
 *
 * Estado: IMPLEMENTADO.
 */
import { useState } from 'react'
import { DownloadIcon, FileSpreadsheetIcon, FileTextIcon, Loader2Icon, PlayIcon } from 'lucide-react'
import { toast } from 'sonner'
import { Campo } from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/componentes/ui/card'
import { Checkbox } from '@/componentes/ui/checkbox'
import { Input } from '@/componentes/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { TODOS } from '@/lib/filtros'
import { fecha, fechaHora } from '@/lib/formato'
import { descargar, mensajeError } from '@/nucleo/api'
import { useCatalogoReportes, useFuentesReporte, useOpcionesReportes, useReporteEstatico, useVistaPreviaDinamica } from '../api'
import type { DatosReporteDinamico, Formato, FuenteReporte, OpcionesReportes, ParametrosEstatico, Reporte, TipoColumna } from '../schemas'

// ------------------------------------------------------------------ utilidades

function celda(valor: string | number | null, tipo: TipoColumna): string {
  if (valor === null || valor === '') return '—'
  if (tipo === 'fecha') return fecha(String(valor))
  if (tipo === 'decimal') return Number(valor).toLocaleString('es-BO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  if (tipo === 'porcentaje') return `${Number(valor).toLocaleString('es-BO', { maximumFractionDigits: 1 })} %`
  return String(valor)
}

function Aviso({ texto }: { texto: string }) {
  return <p className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600">{texto}</p>
}

function SelectorSimple({
  valor,
  onCambiar,
  opciones,
  marcador,
  conTodos,
}: {
  valor: string
  onCambiar: (v: string) => void
  opciones: { valor: string; etiqueta: string }[]
  marcador: string
  conTodos?: boolean
}) {
  return (
    <Select value={valor || (conTodos ? TODOS : '')} onValueChange={(v) => onCambiar(v === TODOS ? '' : v)}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder={marcador} />
      </SelectTrigger>
      <SelectContent>
        {conTodos && <SelectItem value={TODOS}>Todos</SelectItem>}
        {opciones.map((o) => (
          <SelectItem key={o.valor} value={o.valor}>
            {o.etiqueta}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

const opcionesDe = {
  gestion: (o: OpcionesReportes) =>
    o.gestiones.map((g) => ({ valor: String(g.id_gestion), etiqueta: `${g.anio}${g.estado_gestion === 'abierta' ? ' (abierta)' : ''}` })),
  nivel: (o: OpcionesReportes) => o.niveles.map((n) => ({ valor: String(n.id_nivel), etiqueta: n.nombre_nivel })),
  curso: (o: OpcionesReportes, nivel?: string) =>
    o.cursos.filter((c) => !nivel || String(c.id_nivel) === nivel).map((c) => ({ valor: String(c.id_curso), etiqueta: c.nombre_curso })),
  periodo: (o: OpcionesReportes, gestion?: string) =>
    o.periodos
      .filter((p) => !gestion || String(p.id_gestion) === gestion)
      .map((p) => ({ valor: String(p.id_periodo), etiqueta: `${p.anio} · ${p.nombre_periodo}` })),
  materia: (o: OpcionesReportes) => o.materias.map((m) => ({ valor: String(m.id_materia), etiqueta: m.nombre_materia })),
}

// ------------------------------------------------------------------ página

export default function Reportes() {
  const [tab, setTab] = useState<'fijos' | 'dinamico'>('fijos')
  const opciones = useOpcionesReportes()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Reportes</h1>
        <p className="text-sm text-slate-500">Reportes fijos y personalizados para ver en pantalla y descargar en PDF o Excel.</p>
      </div>
      <div className="flex gap-2 border-b" role="tablist">
        {(
          [
            ['fijos', 'Reportes fijos'],
            ['dinamico', 'Reporte personalizado'],
          ] as const
        ).map(([t, texto]) => (
          <button
            key={t}
            role="tab"
            aria-selected={tab === t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 font-medium ${tab === t ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-600'}`}
          >
            {texto}
          </button>
        ))}
      </div>
      {opciones.isLoading && <p className="text-slate-500">Cargando...</p>}
      {opciones.isError && <Aviso texto={mensajeError(opciones.error)} />}
      {opciones.data && (tab === 'fijos' ? <ReportesFijos opciones={opciones.data} /> : <ReporteDinamico opciones={opciones.data} />)}
    </div>
  )
}

// ------------------------------------------------------------------ vista del reporte y descargas

function VistaReporte({ reporte, onDescargar }: { reporte: Reporte; onDescargar: (formato: Formato) => Promise<void> }) {
  const [bajando, setBajando] = useState<Formato | null>(null)
  const bajar = async (formato: Formato) => {
    setBajando(formato)
    try {
      await onDescargar(formato)
      toast.success(`Reporte descargado en ${formato === 'pdf' ? 'PDF' : 'Excel'}.`)
    } catch (e) {
      toast.error(mensajeError(e))
    } finally {
      setBajando(null)
    }
  }
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold">{reporte.titulo}</h3>
          <p className="text-xs text-slate-500">
            {reporte.filtros.join(' · ')} · Generado el {fechaHora(reporte.generado_en)}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => bajar('pdf')} disabled={bajando !== null}>
            {bajando === 'pdf' ? <Loader2Icon className="mr-2 size-4 animate-spin" /> : <FileTextIcon className="mr-2 size-4 text-red-600" />}
            Descargar PDF
          </Button>
          <Button variant="outline" onClick={() => bajar('xlsx')} disabled={bajando !== null}>
            {bajando === 'xlsx' ? (
              <Loader2Icon className="mr-2 size-4 animate-spin" />
            ) : (
              <FileSpreadsheetIcon className="mr-2 size-4 text-emerald-600" />
            )}
            Descargar Excel
          </Button>
        </div>
      </div>
      <div className="max-h-[60vh] overflow-auto rounded border">
        <table className="w-full border-separate border-spacing-0 text-sm">
          <thead>
            <tr>
              {reporte.columnas.map((c) => (
                <th
                  key={c.clave}
                  className={`sticky top-0 z-10 border-b bg-[#0B2352] px-3 py-2 text-xs font-semibold whitespace-nowrap text-white ${
                    c.tipo === 'texto' || c.tipo === 'fecha' ? 'text-left' : 'text-right'
                  }`}
                >
                  {c.titulo}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {reporte.filas.map((f, i) => (
              <tr key={i} className={i % 2 ? 'bg-slate-50' : 'bg-white'}>
                {reporte.columnas.map((c) => (
                  <td
                    key={c.clave}
                    className={`border-b px-3 py-1.5 ${c.tipo === 'texto' || c.tipo === 'fecha' ? 'text-left' : 'text-right tabular-nums'}`}
                  >
                    {celda(f[c.clave], c.tipo)}
                  </td>
                ))}
              </tr>
            ))}
            {!reporte.filas.length && (
              <tr>
                <td colSpan={reporte.columnas.length} className="p-6 text-center text-slate-500">
                  No hay datos para los filtros elegidos.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="space-y-1 text-sm">
        {reporte.mostradas < reporte.total && (
          <p className="text-amber-700">
            Vista previa: {reporte.mostradas} de {reporte.total} registros. El PDF y el Excel incluyen hasta 5000.
          </p>
        )}
        {reporte.resumen.map((r) => (
          <p key={r} className="font-medium">
            {r}
          </p>
        ))}
      </div>
    </div>
  )
}

// ------------------------------------------------------------------ reportes fijos

function ReportesFijos({ opciones }: { opciones: OpcionesReportes }) {
  const catalogo = useCatalogoReportes()
  const [clave, setClave] = useState<string | null>(null)
  const abierta = opciones.gestiones.find((g) => g.estado_gestion === 'abierta') ?? opciones.gestiones[0]
  const [gestion, setGestion] = useState(abierta ? String(abierta.id_gestion) : '')
  const [curso, setCurso] = useState('')
  const [periodo, setPeriodo] = useState('')

  const elegido = catalogo.data?.find((r) => r.clave === clave)
  const pide = (p: 'gestion' | 'curso' | 'periodo') => elegido?.parametros.includes(p) ?? false
  const params: ParametrosEstatico = {
    id_gestion: pide('gestion') && gestion ? Number(gestion) : undefined,
    id_curso: pide('curso') && curso ? Number(curso) : undefined,
    id_periodo: pide('periodo') && periodo ? Number(periodo) : undefined,
  }
  const listo = !!elegido && (!pide('gestion') || !!gestion) && (!pide('curso') || !!curso) && (!pide('periodo') || !!periodo)
  const reporte = useReporteEstatico(clave, params, listo)

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {catalogo.data?.map((r) => (
          <button
            key={r.clave}
            onClick={() => setClave(r.clave)}
            className={`rounded-lg border p-4 text-left transition-colors ${
              r.clave === clave ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-500' : 'bg-white hover:bg-slate-50'
            }`}
          >
            <p className="font-semibold">{r.nombre}</p>
            <p className="mt-1 text-xs text-slate-500">{r.descripcion}</p>
          </button>
        ))}
      </div>

      {elegido && (
        <Card>
          <CardHeader>
            <CardTitle>{elegido.nombre}</CardTitle>
            <CardDescription>{elegido.descripcion}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {pide('gestion') && (
                <Campo etiqueta="Gestión">
                  <SelectorSimple valor={gestion} onCambiar={setGestion} opciones={opcionesDe.gestion(opciones)} marcador="Seleccione" />
                </Campo>
              )}
              {pide('curso') && (
                <Campo etiqueta="Curso">
                  <SelectorSimple valor={curso} onCambiar={setCurso} opciones={opcionesDe.curso(opciones)} marcador="Seleccione el curso" />
                </Campo>
              )}
              {pide('periodo') && (
                <Campo etiqueta="Periodo">
                  <SelectorSimple
                    valor={periodo}
                    onCambiar={setPeriodo}
                    opciones={opcionesDe.periodo(opciones)}
                    marcador="Seleccione el periodo"
                  />
                </Campo>
              )}
            </div>
            {!listo && <Aviso texto="Complete los datos para ver el reporte." />}
            {reporte.isLoading && <p className="text-slate-500">Generando reporte...</p>}
            {reporte.isError && <Aviso texto={mensajeError(reporte.error)} />}
            {reporte.data && listo && (
              <VistaReporte
                reporte={reporte.data}
                onDescargar={(formato) =>
                  descargar(`/reportes/estaticos/${clave}`, `reporte_${clave}.${formato}`, { params: { ...params, formato } })
                }
              />
            )}
          </CardContent>
        </Card>
      )}
      {!elegido && <Aviso texto="Elija un reporte." />}
    </div>
  )
}

// ------------------------------------------------------------------ reporte dinámico

function ReporteDinamico({ opciones }: { opciones: OpcionesReportes }) {
  const fuentes = useFuentesReporte()
  const vista = useVistaPreviaDinamica()
  const [clave, setClave] = useState<string | null>(null)
  const [filtros, setFiltros] = useState<Record<string, string>>({})
  const [columnas, setColumnas] = useState<string[]>([])
  const [orden, setOrden] = useState('')
  const [descendente, setDescendente] = useState(false)

  const fuente = fuentes.data?.find((f) => f.clave === clave)

  const elegirFuente = (f: FuenteReporte) => {
    setClave(f.clave)
    setFiltros({})
    setColumnas(f.columnas.filter((c) => c.por_defecto).map((c) => c.clave))
    setOrden('')
    setDescendente(false)
    vista.reset()
  }
  const alternar = (c: string) =>
    setColumnas((actual) => {
      if (actual.includes(c)) return actual.filter((x) => x !== c)
      // se respeta el orden de la fuente
      return fuente ? fuente.columnas.map((x) => x.clave).filter((x) => x === c || actual.includes(x)) : [...actual, c]
    })

  const datos: DatosReporteDinamico | null = fuente
    ? { fuente: fuente.clave, columnas, filtros, orden: orden || null, descendente }
    : null

  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {fuentes.data?.map((f) => (
          <button
            key={f.clave}
            onClick={() => elegirFuente(f)}
            className={`rounded-lg border p-4 text-left transition-colors ${
              f.clave === clave ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-500' : 'bg-white hover:bg-slate-50'
            }`}
          >
            <p className="font-semibold">{f.nombre}</p>
            <p className="mt-1 text-xs text-slate-500">{f.descripcion}</p>
          </button>
        ))}
      </div>
      {!fuente && <Aviso texto="Elija la fuente de datos del reporte." />}

      {fuente && datos && (
        <Card>
          <CardHeader>
            <CardTitle>Reporte personalizado: {fuente.nombre}</CardTitle>
            <CardDescription>Elija los filtros, las columnas y el orden; luego genere la vista previa.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div>
              <p className="mb-2 text-sm font-semibold">1. Filtros</p>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {fuente.filtros.map((f) => {
                  const valor = filtros[f.clave] ?? ''
                  const cambiar = (v: string) => {
                    setFiltros((x) => {
                      const nuevo = { ...x, [f.clave]: v }
                      if (f.clave === 'nivel') delete nuevo.curso
                      if (f.clave === 'gestion') delete nuevo.periodo
                      return nuevo
                    })
                  }
                  let control
                  if (f.tipo === 'fecha') {
                    control = <Input type="date" value={valor} onChange={(e) => cambiar(e.target.value)} />
                  } else if (f.tipo === 'numero') {
                    control = <Input type="number" min={0} max={100} value={valor} onChange={(e) => cambiar(e.target.value)} />
                  } else {
                    const lista =
                      f.tipo === 'opcion'
                        ? f.opciones
                        : f.tipo === 'curso'
                          ? opcionesDe.curso(opciones, filtros.nivel)
                          : f.tipo === 'periodo'
                            ? opcionesDe.periodo(opciones, filtros.gestion)
                            : opcionesDe[f.tipo](opciones)
                    control = <SelectorSimple valor={valor} onCambiar={cambiar} opciones={lista} marcador="Todos" conTodos />
                  }
                  return (
                    <Campo key={f.clave} etiqueta={f.titulo}>
                      {control}
                    </Campo>
                  )
                })}
              </div>
            </div>

            <div>
              <div className="mb-2 flex items-center gap-3">
                <p className="text-sm font-semibold">2. Columnas ({columnas.length})</p>
                <button className="text-xs text-blue-600 hover:underline" onClick={() => setColumnas(fuente.columnas.map((c) => c.clave))}>
                  Todas
                </button>
                <button className="text-xs text-blue-600 hover:underline" onClick={() => setColumnas([])}>
                  Ninguna
                </button>
              </div>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5">
                {fuente.columnas.map((c) => (
                  <label key={c.clave} className="flex cursor-pointer items-center gap-2 text-sm">
                    <Checkbox checked={columnas.includes(c.clave)} onCheckedChange={() => alternar(c.clave)} />
                    {c.titulo}
                  </label>
                ))}
              </div>
            </div>

            <div>
              <p className="mb-2 text-sm font-semibold">3. Orden</p>
              <div className="flex flex-wrap items-center gap-4">
                <div className="w-64">
                  <SelectorSimple
                    valor={orden}
                    onCambiar={setOrden}
                    opciones={fuente.columnas.filter((c) => columnas.includes(c.clave)).map((c) => ({ valor: c.clave, etiqueta: c.titulo }))}
                    marcador="Orden por defecto"
                    conTodos
                  />
                </div>
                <label className="flex cursor-pointer items-center gap-2 text-sm">
                  <Checkbox checked={descendente} onCheckedChange={(v) => setDescendente(v === true)} disabled={!orden} />
                  Descendente (de mayor a menor)
                </label>
              </div>
            </div>

            <Button onClick={() => vista.mutate(datos)} disabled={!columnas.length || vista.isPending}>
              {vista.isPending ? <Loader2Icon className="mr-2 size-4 animate-spin" /> : <PlayIcon className="mr-2 size-4" />}
              Generar vista previa
            </Button>
            {!columnas.length && <span className="ml-3 text-sm text-red-600">Elija al menos una columna.</span>}

            {vista.isError && <Aviso texto={mensajeError(vista.error)} />}
            {vista.data && (
              <VistaReporte
                reporte={vista.data}
                onDescargar={(formato) =>
                  descargar('/reportes/dinamico', `reporte_${fuente.clave}.${formato}`, {
                    metodo: 'POST',
                    cuerpo: datos,
                    params: { formato },
                  })
                }
              />
            )}
            {vista.data && JSON.stringify(datos) !== JSON.stringify(vista.variables) && (
              <p className="flex items-center gap-2 text-sm text-amber-700">
                <DownloadIcon className="size-4" /> Cambió los filtros o columnas: genere otra vez la vista previa (la descarga usa la
                configuración actual).
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

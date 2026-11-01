/**
 * CU24 - Generar y consultar boletín/libreta (incluye centralizador)
 * Paquete: evaluacion
 *
 * Actores ........: Tutor, Estudiante (genera: Administrativo)
 * Rol del sistema : tutor, estudiante, administrador
 * Backend ........: backend/app/paquetes/evaluacion/casos_uso/cu24_generar_consultar_boletin.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Pantalla:
 * - Administrador: emitir boletines (periodo completo o un curso), consultar el boletín de un estudiante
 *   (periodo → curso → estudiante) y ver el centralizador de un curso.
 * - Tutor: elige el periodo y a uno de sus estudiantes. Estudiante: elige el periodo.
 * - Los periodos incluyen gestiones anteriores; el boletín y el centralizador se imprimen desde el navegador.
 *
 * Precondición:  El estudiante tiene calificaciones en el periodo. Tutor y estudiante solo consultan lo suyo.
 * Postcondición: El boletín queda emitido con su promedio y disponible para consulta e impresión.
 *
 * Estado: IMPLEMENTADO.
 */
import { useState } from 'react'
import { Loader2, PrinterIcon } from 'lucide-react'
import { toast } from 'sonner'
import { Campo } from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/componentes/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/componentes/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { TODOS } from '@/lib/filtros'
import { fecha } from '@/lib/formato'
import { mensajeError } from '@/nucleo/api'
import { useSesion } from '@/nucleo/auth/contexto'
import {
  useBoletin,
  useCentralizador,
  useEmitirBoletines,
  useEstudiantesBoletin,
  useOpcionesCursos,
  useOpcionesPeriodos,
} from '../api'
import type { Boletin, Centralizador, CursoOpcionCU24, PeriodoOpcionCU24 } from '../schemas'

type Rol = 'administrador' | 'tutor' | 'estudiante'

/** Periodo sugerido: el último trimestre cerrado de la gestión más reciente (o el primero si ninguno cerró). */
function periodoSugerido(periodos: PeriodoOpcionCU24[]): number | null {
  if (!periodos.length) return null
  const ultimaGestion = periodos.filter((p) => p.anio === periodos[0].anio)
  const cerrados = ultimaGestion.filter((p) => p.estado_periodo === 'cerrado')
  return (cerrados.at(-1) ?? ultimaGestion[0]).id_periodo
}

const etiquetaPeriodo = (p: PeriodoOpcionCU24) =>
  `${p.anio} · ${p.nombre_periodo}${p.estado_periodo === 'abierto' ? ' (en curso)' : ''}`

const promedio = (valores: number[]) => (valores.length ? valores.reduce((a, b) => a + b, 0) / valores.length : null)

export default function CU24GenerarConsultarBoletin() {
  const sesion = useSesion()
  const rol = sesion.usuario?.rol as Rol | undefined
  const [tab, setTab] = useState<'boletin' | 'centralizador'>('boletin')
  const periodos = useOpcionesPeriodos().data ?? []
  const cursos = useOpcionesCursos().data ?? []

  if (rol !== 'administrador' && rol !== 'tutor' && rol !== 'estudiante') return null

  const titulo = rol === 'administrador' ? 'Boletines y centralizador' : rol === 'tutor' ? 'Boletín de mis estudiantes' : 'Mi boletín'
  const descripcion =
    rol === 'administrador'
      ? 'Emitir boletines, consultarlos y ver el centralizador académico de un curso.'
      : 'Notas por materia y promedio del trimestre, también de gestiones anteriores.'

  return (
    <div className="space-y-6">
      <div className="print:hidden">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">{titulo}</h1>
        <p className="text-sm text-slate-500">{descripcion}</p>
      </div>

      {rol === 'administrador' && (
        <div className="flex gap-2 border-b print:hidden" role="tablist">
          {(['boletin', 'centralizador'] as const).map((t) => (
            <button
              key={t}
              role="tab"
              aria-selected={tab === t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 font-medium ${tab === t ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-600'}`}
            >
              {t === 'boletin' ? 'Boletines' : 'Centralizador'}
            </button>
          ))}
        </div>
      )}

      {rol === 'administrador' && tab === 'boletin' && <EmitirBoletines periodos={periodos} cursos={cursos} />}
      {(rol !== 'administrador' || tab === 'boletin') && <ConsultarBoletin rol={rol} periodos={periodos} cursos={cursos} />}
      {rol === 'administrador' && tab === 'centralizador' && <VerCentralizador periodos={periodos} cursos={cursos} />}
    </div>
  )
}

// ------------------------------------------------------------
// Listas desplegables
// ------------------------------------------------------------

function SelectorPeriodo({
  periodos,
  valor,
  onCambiar,
}: {
  periodos: PeriodoOpcionCU24[]
  valor: number | null
  onCambiar: (id: number) => void
}) {
  return (
    <Select value={valor?.toString() ?? ''} onValueChange={(v) => onCambiar(Number(v))}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder="Seleccione el periodo" />
      </SelectTrigger>
      <SelectContent>
        {periodos.map((p) => (
          <SelectItem key={p.id_periodo} value={p.id_periodo.toString()}>
            {etiquetaPeriodo(p)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

function SelectorCurso({
  cursos,
  valor,
  onCambiar,
  conTodos,
}: {
  cursos: CursoOpcionCU24[]
  valor: number | null
  onCambiar: (id: number | null) => void
  conTodos?: boolean
}) {
  return (
    <Select
      value={valor?.toString() ?? (conTodos ? TODOS : '')}
      onValueChange={(v) => onCambiar(v === TODOS ? null : Number(v))}
    >
      <SelectTrigger className="w-full">
        <SelectValue placeholder="Seleccione el curso" />
      </SelectTrigger>
      <SelectContent>
        {conTodos && <SelectItem value={TODOS}>Todos los cursos</SelectItem>}
        {cursos.map((c) => (
          <SelectItem key={c.id_curso} value={c.id_curso.toString()}>
            {c.nombre_curso}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

// ------------------------------------------------------------
// Emitir boletines (administrador)
// ------------------------------------------------------------

function EmitirBoletines({ periodos, cursos }: { periodos: PeriodoOpcionCU24[]; cursos: CursoOpcionCU24[] }) {
  const [abierto, setAbierto] = useState(false)
  const [idPeriodo, setIdPeriodo] = useState<number | null>(null)
  const [idCurso, setIdCurso] = useState<number | null>(null)
  const emitir = useEmitirBoletines()

  const confirmar = () => {
    if (!idPeriodo) {
      toast.error('Seleccione un periodo.')
      return
    }
    emitir.mutate(
      { id_periodo: idPeriodo, id_curso: idCurso ?? undefined },
      {
        onSuccess: (r) => {
          toast.success(
            r.cantidad
              ? `Se emitieron ${r.cantidad} boletines del ${r.periodo}.`
              : `Ningún estudiante tiene notas en el ${r.periodo}${idCurso ? ' para ese curso' : ''}.`,
          )
          setAbierto(false)
        },
        onError: (e) => toast.error(mensajeError(e)),
      },
    )
  }

  return (
    <Card className="print:hidden">
      <CardHeader>
        <CardTitle>Emitir boletines</CardTitle>
        <CardDescription>
          Calcula el promedio de cada estudiante con notas en el periodo. Volver a emitir actualiza el promedio y la fecha.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button onClick={() => setAbierto(true)}>Emitir boletines</Button>
      </CardContent>

      <Dialog open={abierto} onOpenChange={setAbierto}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Emitir boletines</DialogTitle>
            <DialogDescription>Puede emitir los de todo el periodo o solo los de un curso.</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Campo etiqueta="Periodo *">
              <SelectorPeriodo periodos={periodos} valor={idPeriodo} onCambiar={setIdPeriodo} />
            </Campo>
            <Campo etiqueta="Curso (opcional)">
              <SelectorCurso cursos={cursos} valor={idCurso} onCambiar={setIdCurso} conTodos />
            </Campo>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAbierto(false)}>
              Cancelar
            </Button>
            <Button onClick={confirmar} disabled={emitir.isPending}>
              {emitir.isPending && <Loader2 className="mr-2 size-4 animate-spin" />}
              Emitir
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}

// ------------------------------------------------------------
// Consultar boletín (los tres roles)
// ------------------------------------------------------------

function ConsultarBoletin({ rol, periodos, cursos }: { rol: Rol; periodos: PeriodoOpcionCU24[]; cursos: CursoOpcionCU24[] }) {
  const ciSesion = useSesion().usuario?.ci ?? null
  const [periodoElegido, setPeriodoElegido] = useState<number | null>(null)
  const [idCurso, setIdCurso] = useState<number | null>(null)
  const [ciElegido, setCiElegido] = useState<string | null>(null)

  const idPeriodo = periodoElegido ?? periodoSugerido(periodos)
  const esAdmin = rol === 'administrador'
  // El administrador primero elige el curso (para no listar a todo el colegio)
  const estudiantes = useEstudiantesBoletin(rol === 'estudiante' || (esAdmin && !idCurso) ? null : idPeriodo, idCurso)
  const lista = estudiantes.data ?? []

  // El estudiante elegido debe estar en la lista del periodo/curso actual; si hay uno solo, se elige solo
  const ci =
    rol === 'estudiante'
      ? ciSesion
      : lista.some((e) => e.ci === ciElegido)
        ? ciElegido
        : lista.length === 1
          ? lista[0].ci
          : null

  const boletin = useBoletin(ci, idPeriodo)

  return (
    <Card>
      <CardHeader className="print:hidden">
        <CardTitle>Consultar boletín</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3 print:hidden">
          <Campo etiqueta="Periodo">
            <SelectorPeriodo periodos={periodos} valor={idPeriodo} onCambiar={setPeriodoElegido} />
          </Campo>
          {esAdmin && (
            <Campo etiqueta="Curso">
              <SelectorCurso
                cursos={cursos}
                valor={idCurso}
                onCambiar={(id) => {
                  setIdCurso(id)
                  setCiElegido(null)
                }}
              />
            </Campo>
          )}
          {rol !== 'estudiante' && (
            <Campo etiqueta="Estudiante">
              <Select value={ci ?? ''} onValueChange={setCiElegido} disabled={!lista.length}>
                <SelectTrigger className="w-full">
                  <SelectValue
                    placeholder={
                      esAdmin && !idCurso
                        ? 'Primero elija el curso'
                        : estudiantes.isLoading
                          ? 'Cargando...'
                          : lista.length
                            ? 'Seleccione el estudiante'
                            : 'Sin estudiantes inscritos en esa gestión'
                    }
                  />
                </SelectTrigger>
                <SelectContent>
                  {lista.map((e) => (
                    <SelectItem key={e.ci} value={e.ci}>
                      {e.apellidos} {e.nombre_persona} — {e.nombre_curso}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Campo>
          )}
        </div>

        {boletin.isLoading && <p className="text-slate-500">Cargando boletín...</p>}
        {boletin.isError && <p className="text-amber-700">{mensajeError(boletin.error)}</p>}
        {boletin.data && <VistaBoletin boletin={boletin.data} />}
      </CardContent>
    </Card>
  )
}

function VistaBoletin({ boletin }: { boletin: Boletin }) {
  return (
    <div className="space-y-4">
      <div className="space-y-4 rounded border border-gray-200 bg-white p-6">
        <div className="flex flex-wrap justify-between gap-2">
          <div>
            <p className="font-bold">
              {boletin.nombre_persona} {boletin.apellidos}
            </p>
            <p className="text-sm text-gray-600">CI: {boletin.ci}</p>
            <p className="text-sm text-gray-600">Gestión: {boletin.anio}</p>
          </div>
          <div className="text-right">
            <p className="font-bold">{boletin.nombre_periodo}</p>
            <p className="text-sm text-gray-600">Emitido: {fecha(boletin.fecha_emision_b)}</p>
          </div>
        </div>

        {boletin.nombre_curso && <p className="border-t pt-2 font-medium">Curso: {boletin.nombre_curso}</p>}

        <div className="border-t pt-4">
          <h3 className="mb-3 font-bold">Notas por materia</h3>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Materia</TableHead>
                <TableHead className="text-right">Nota final</TableHead>
                <TableHead className="text-center">Dimensiones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {boletin.notas_por_materia.map((nota) => (
                <TableRow key={nota.id_materia}>
                  <TableCell>{nota.materia}</TableCell>
                  <TableCell className="text-right font-semibold">{nota.nota_final.toFixed(2)}</TableCell>
                  <TableCell className="text-center">
                    {nota.dimensiones_registradas} / {nota.dimensiones_totales}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        <div className="border-t bg-blue-50 p-4">
          <p className="text-sm text-gray-600">Promedio general</p>
          <p className="text-2xl font-bold text-blue-600">{boletin.promedio_general_b.toFixed(2)}</p>
        </div>

        <div className="border-t pt-4">
          <p className="text-sm font-medium">Observaciones</p>
          <p className="mt-1 text-gray-700">{boletin.observaciones_generales_boletin || 'Sin observaciones'}</p>
        </div>
      </div>
      <Button onClick={() => window.print()} variant="outline" className="print:hidden">
        <PrinterIcon className="mr-2 size-4" /> Imprimir
      </Button>
    </div>
  )
}

// ------------------------------------------------------------
// Centralizador (administrador)
// ------------------------------------------------------------

function VerCentralizador({ periodos, cursos }: { periodos: PeriodoOpcionCU24[]; cursos: CursoOpcionCU24[] }) {
  const [idCurso, setIdCurso] = useState<number | null>(null)
  const [periodoElegido, setPeriodoElegido] = useState<number | null>(null)
  const idPeriodo = periodoElegido ?? periodoSugerido(periodos)
  const centralizador = useCentralizador(idCurso, idPeriodo)

  return (
    <Card>
      <CardHeader className="print:hidden">
        <CardTitle>Centralizador académico</CardTitle>
        <CardDescription>Notas finales de un curso en un periodo, por materia.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 print:hidden">
          <Campo etiqueta="Curso">
            <SelectorCurso cursos={cursos} valor={idCurso} onCambiar={setIdCurso} />
          </Campo>
          <Campo etiqueta="Periodo">
            <SelectorPeriodo periodos={periodos} valor={idPeriodo} onCambiar={setPeriodoElegido} />
          </Campo>
        </div>

        {centralizador.isLoading && <p className="text-slate-500">Cargando centralizador...</p>}
        {centralizador.isError && <p className="text-amber-700">{mensajeError(centralizador.error)}</p>}
        {centralizador.data && <TablaCentralizador datos={centralizador.data} />}
      </CardContent>
    </Card>
  )
}

function TablaCentralizador({ datos }: { datos: Centralizador }) {
  // Cada fila trae solo las notas que existen: se ubican por id_materia en las columnas del backend
  const notaDe = (fila: Centralizador['filas'][number], idMateria: number) =>
    fila.notas.find((n) => n.id_materia === idMateria)?.nota_final ?? null
  const promedioMateria = (idMateria: number) =>
    promedio(datos.filas.map((f) => notaDe(f, idMateria)).filter((v): v is number => v !== null))
  const promedioCurso = promedio(datos.filas.map((f) => f.promedio_estudiante).filter((v): v is number => v !== null))
  const formato = (v: number | null) => (v === null ? '—' : v.toFixed(2))

  return (
    <div className="space-y-4">
      <p className="hidden font-semibold print:block">
        Centralizador · {datos.curso} · {datos.periodo}
      </p>
      <div className="overflow-x-auto rounded border">
        <table className="w-full text-sm">
          <thead className="bg-gray-100">
            <tr>
              <th className="border-r border-b p-2 text-left font-semibold">Estudiante</th>
              {datos.materias.map((m) => (
                <th key={m.id_materia} className="max-w-xs border-r border-b p-2 text-center text-xs font-semibold whitespace-normal">
                  {m.materia}
                </th>
              ))}
              <th className="border-b bg-blue-50 p-2 text-center font-semibold">Promedio</th>
            </tr>
          </thead>
          <tbody>
            {datos.filas.map((fila, i) => (
              <tr key={fila.ci} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                <td className="border-r border-b p-2">
                  {fila.apellidos} {fila.nombre_persona}
                </td>
                {datos.materias.map((m) => (
                  <td key={m.id_materia} className="border-r border-b p-2 text-center font-semibold">
                    {formato(notaDe(fila, m.id_materia))}
                  </td>
                ))}
                <td className="border-b bg-blue-50 p-2 text-center font-bold">{formato(fila.promedio_estudiante)}</td>
              </tr>
            ))}
            <tr className="bg-blue-100 font-bold">
              <td className="border-r border-b p-2">Promedio por materia</td>
              {datos.materias.map((m) => (
                <td key={m.id_materia} className="border-r border-b p-2 text-center">
                  {formato(promedioMateria(m.id_materia))}
                </td>
              ))}
              <td className="border-b p-2 text-center">{formato(promedioCurso)}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <Button onClick={() => window.print()} variant="outline" className="print:hidden">
        <PrinterIcon className="mr-2 size-4" /> Imprimir centralizador
      </Button>
    </div>
  )
}

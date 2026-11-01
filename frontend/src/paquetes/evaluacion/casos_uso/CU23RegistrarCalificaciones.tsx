/**
 * CU23 - Registrar calificaciones y evaluaciones (incluye autoevaluación y cierre de periodo)
 * Paquete: evaluacion
 *
 * Actores ........: Docente (Estudiante para su autoevaluación, Administrador para cerrar periodo)
 * Rol del sistema : profesor, estudiante, administrador
 * Backend ........: backend/app/paquetes/evaluacion/casos_uso/cu23_registrar_calificaciones.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Pantalla:
 * - Docente: elige una de sus clases y el trimestre y llena la planilla (Ser, Saber, Hacer, Decidir).
 *   La nota final se suma en vivo; Enter baja a la fila siguiente; se guarda todo el curso de una vez.
 * - Administrador: lo mismo con cualquier clase (también corrige trimestres cerrados) y además
 *   cierra el trimestre (emite los boletines) o lo reabre para corregir.
 * - Estudiante: ve sus notas por materia y registra su autoevaluación mientras el trimestre está abierto.
 *
 * Precondición:  El docente dicta la materia al estudiante. El periodo está abierto. Cada puntaje no supera el máximo de su dimensión.
 * Postcondición: Las notas quedan guardadas por dimensión y la nota final se calcula sola. Al cerrar el periodo se emiten los boletines.
 *
 * Estado: IMPLEMENTADO.
 */
import { useState, type KeyboardEvent } from 'react'
import { LockIcon, LockOpenIcon, SaveIcon, Undo2Icon } from 'lucide-react'
import { toast } from 'sonner'
import Confirmar from '@/componentes/Confirmar'
import { Campo } from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/componentes/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { fecha } from '@/lib/formato'
import { mensajeError } from '@/nucleo/api'
import { useSesion } from '@/nucleo/auth/contexto'
import {
  useCambiarPeriodo,
  useClasesCalificacion,
  useGuardarAutoevaluacion,
  useGuardarPlanilla,
  useMisCalificaciones,
  usePlanilla,
} from '../api'
import type { DimensionCU23, NotaEstudianteCU23, PeriodoCU23, PlanillaCU23, Puntajes } from '../schemas'

// ------------------------------------------------------------
// Utilidades
// ------------------------------------------------------------

/** Último trimestre que ya empezó (o el primero si ninguno empezó). */
function periodoSugerido(periodos: PeriodoCU23[]): number | null {
  const iniciados = periodos.filter((p) => p.iniciado)
  return (iniciados.at(-1) ?? periodos[0])?.id_periodo ?? null
}

function etiquetaPeriodo(p: PeriodoCU23) {
  if (!p.iniciado) return `${p.nombre_periodo} (desde ${fecha(p.fecha_inicio_p)})`
  return `${p.nombre_periodo}${p.estado_periodo === 'cerrado' ? ' (cerrado)' : ''}`
}

/** Texto de una casilla a número: vacío = null; acepta coma decimal. NaN si no es un número. */
function aNumero(texto: string): number | null {
  const limpio = texto.trim().replace(',', '.')
  if (limpio === '') return null
  return /^\d+(\.\d{1,2})?$/.test(limpio) ? Number(limpio) : Number.NaN
}

/** Color de la nota final: roja solo si está completa y no llega a la mínima; gris si está incompleta. */
function colorNota(nota: number | null, completa: boolean, minima: number | null) {
  if (nota === null) return 'font-bold'
  if (!completa) return 'text-slate-400'
  return minima !== null && nota < minima ? 'font-bold text-red-600' : 'font-bold'
}

const mostrar = (v: number | null | undefined) => (v === null || v === undefined ? '' : String(v))
const formatoNota = (v: number | null) => (v === null ? '—' : v.toFixed(2).replace(/\.00$/, ''))

function errorCasilla(texto: string, dimension: DimensionCU23): string | null {
  const v = aNumero(texto)
  if (v === null) return null
  if (Number.isNaN(v)) return 'Número con hasta 2 decimales'
  if (v > dimension.puntaje_maximo) return `Máximo ${dimension.puntaje_maximo}`
  return null
}

/** Enter baja a la misma columna de la fila siguiente (como en una hoja de cálculo). */
function bajarConEnter(e: KeyboardEvent<HTMLInputElement>) {
  if (e.key !== 'Enter') return
  e.preventDefault()
  const { fila, col } = e.currentTarget.dataset
  const siguiente = document.querySelector<HTMLInputElement>(`input[data-fila="${Number(fila) + 1}"][data-col="${col}"]`)
  siguiente?.focus()
  siguiente?.select()
}

function Aviso({ texto, tono = 'ambar' }: { texto: string; tono?: 'ambar' | 'gris' }) {
  return (
    <p
      className={`rounded-md border px-3 py-2 text-sm ${
        tono === 'ambar' ? 'border-amber-200 bg-amber-50 text-amber-800' : 'border-slate-200 bg-slate-50 text-slate-600'
      }`}
    >
      {texto}
    </p>
  )
}

function SelectorPeriodo({
  periodos,
  valor,
  onCambiar,
  soloIniciados,
}: {
  periodos: PeriodoCU23[]
  valor: number | null
  onCambiar: (id: number) => void
  soloIniciados?: boolean
}) {
  return (
    <Select value={valor?.toString() ?? ''} onValueChange={(v) => onCambiar(Number(v))}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder="Seleccione el trimestre" />
      </SelectTrigger>
      <SelectContent>
        {periodos.map((p) => (
          <SelectItem key={p.id_periodo} value={p.id_periodo.toString()} disabled={soloIniciados && !p.iniciado}>
            {etiquetaPeriodo(p)}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

// ------------------------------------------------------------
// Página
// ------------------------------------------------------------

export default function CU23RegistrarCalificaciones() {
  const rol = useSesion().usuario?.rol
  if (rol === 'estudiante') return <MisCalificaciones />
  if (rol === 'profesor' || rol === 'administrador') return <RegistrarNotas esAdmin={rol === 'administrador'} />
  return null
}

// ------------------------------------------------------------
// Docente / administrador
// ------------------------------------------------------------

function RegistrarNotas({ esAdmin }: { esAdmin: boolean }) {
  const datos = useClasesCalificacion()
  const [idClase, setIdClase] = useState<number | null>(null)
  const [periodoElegido, setPeriodoElegido] = useState<number | null>(null)

  const clases = datos.data?.clases ?? []
  const periodos = datos.data?.periodos ?? []
  const idPeriodo = periodoElegido ?? periodoSugerido(periodos)
  const clase = idClase ?? (clases.length === 1 ? clases[0].id_asignacion : null)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">{esAdmin ? 'Calificaciones' : 'Registrar calificaciones'}</h1>
        <p className="text-sm text-slate-500">
          Puntaje por dimensión de cada estudiante; la nota final es la suma.
          {datos.data?.gestion ? ` Gestión ${datos.data.gestion}.` : ''}
        </p>
      </div>

      {datos.isLoading && <p className="text-slate-500">Cargando...</p>}
      {datos.isError && <Aviso texto={mensajeError(datos.error)} />}
      {datos.data && !datos.data.gestion && <Aviso texto="No hay una gestión abierta." />}
      {datos.data?.gestion && !clases.length && (
        <Aviso texto={esAdmin ? 'Aún no hay materias asignadas a profesores.' : 'No tiene materias asignadas en esta gestión.'} />
      )}

      {esAdmin && periodos.length > 0 && <Trimestres periodos={periodos} />}

      {clases.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Planilla de notas</CardTitle>
            <CardDescription>
              Elija la clase y el trimestre. Enter baja a la fila siguiente; Tab pasa a la siguiente dimensión.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <Campo etiqueta="Clase">
                <Select value={clase?.toString() ?? ''} onValueChange={(v) => setIdClase(Number(v))}>
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Seleccione curso y materia" />
                  </SelectTrigger>
                  <SelectContent>
                    {clases.map((c) => (
                      <SelectItem key={c.id_asignacion} value={c.id_asignacion.toString()}>
                        {c.curso} — {c.materia}
                        {esAdmin ? ` (${c.profesor})` : ''}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Campo>
              <Campo etiqueta="Trimestre">
                <SelectorPeriodo periodos={periodos} valor={idPeriodo} onCambiar={setPeriodoElegido} soloIniciados />
              </Campo>
            </div>
            {clase && idPeriodo ? (
              <Planilla key={`${clase}-${idPeriodo}`} idClase={clase} idPeriodo={idPeriodo} />
            ) : (
              <Aviso tono="gris" texto="Elija la clase para ver la planilla." />
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

type Edicion = { puntajes: Record<string, string>; observacion?: string }

function Planilla({ idClase, idPeriodo }: { idClase: number; idPeriodo: number }) {
  const planilla = usePlanilla(idClase, idPeriodo)
  const guardar = useGuardarPlanilla(idClase)
  // Solo se guardan las casillas cambiadas (por estudiante); lo demás se muestra desde el servidor
  const [ediciones, setEdiciones] = useState<Record<string, Edicion>>({})

  if (planilla.isLoading) return <p className="text-slate-500">Cargando planilla...</p>
  if (planilla.isError) return <Aviso texto={mensajeError(planilla.error)} />
  if (!planilla.data) return null
  const datos: PlanillaCU23 = planilla.data

  const docentes = datos.dimensiones.filter((d) => !d.es_autoevaluacion)
  const autoevaluacion = datos.dimensiones.find((d) => d.es_autoevaluacion)

  const texto = (e: NotaEstudianteCU23, d: DimensionCU23) =>
    ediciones[e.ci]?.puntajes[d.id_dimension] ?? mostrar(e.puntajes[d.id_dimension])
  const observacion = (e: NotaEstudianteCU23) => ediciones[e.ci]?.observacion ?? e.observacion ?? ''

  const cambiar = (ci: string, cambio: (actual: Edicion) => Edicion) =>
    setEdiciones((todas) => ({ ...todas, [ci]: cambio(todas[ci] ?? { puntajes: {} }) }))

  // Cambios reales (comparados con lo guardado) y errores de validación
  const cambios = datos.estudiantes.flatMap((e) => {
    const ed = ediciones[e.ci]
    if (!ed) return []
    const puntajes: Record<string, number | null> = {}
    for (const [id, t] of Object.entries(ed.puntajes)) {
      const v = aNumero(t)
      if (Number.isNaN(v as number)) continue
      if (v !== (e.puntajes[id] ?? null)) puntajes[id] = v
    }
    const obsCambio = ed.observacion !== undefined && (ed.observacion.trim() || null) !== (e.observacion ?? null)
    if (!Object.keys(puntajes).length && !obsCambio) return []
    return [{ ci_estudiante: e.ci, puntajes, ...(obsCambio ? { observacion: ed.observacion?.trim() || null } : {}) }]
  })
  const conError = datos.estudiantes.some((e) => docentes.some((d) => errorCasilla(texto(e, d), d)))

  const notaEnVivo = (e: NotaEstudianteCU23) => {
    const valores = [
      ...docentes.map((d) => aNumero(texto(e, d))),
      autoevaluacion ? (e.puntajes[autoevaluacion.id_dimension] ?? null) : null,
    ].filter((v): v is number => v !== null && !Number.isNaN(v))
    return valores.length ? valores.reduce((a, b) => a + b, 0) : null
  }
  const completa = (e: NotaEstudianteCU23) =>
    datos.dimensiones.every((d) => (d.es_autoevaluacion ? e.puntajes[d.id_dimension] !== undefined : aNumero(texto(e, d)) !== null))
  const completas = datos.estudiantes.filter(completa).length

  const enviar = () =>
    guardar.mutate(
      { id_periodo: idPeriodo, notas: cambios },
      {
        onSuccess: () => {
          setEdiciones({})
          toast.success(`Notas guardadas (${cambios.length} estudiante${cambios.length === 1 ? '' : 's'}).`)
        },
        onError: (e) => toast.error(mensajeError(e)),
      },
    )

  if (!datos.estudiantes.length) return <Aviso tono="gris" texto="El curso no tiene estudiantes inscritos." />

  return (
    <div className="space-y-3">
      {!datos.editable && datos.motivo_no_editable && <Aviso texto={datos.motivo_no_editable} />}
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
        <span>
          {datos.estudiantes.length} estudiantes · {completas} con todas las dimensiones · En{' '}
          <span className="font-semibold text-red-600">rojo</span>: nota menor a {datos.nota_minima} · En{' '}
          <span className="text-slate-400">gris</span>: nota incompleta.
        </span>
        {autoevaluacion && <span>La autoevaluación la registra cada estudiante.</span>}
      </div>

      <div className="max-h-[65vh] overflow-auto rounded border">
        <table className="w-full border-separate border-spacing-0 text-sm">
          <thead>
            <tr>
              <th className="sticky top-0 left-0 z-30 min-w-36 border-r border-b bg-gray-100 px-2 py-2 text-left font-semibold sm:px-3">
                Estudiante
              </th>
              {datos.dimensiones.map((d) => (
                <th key={d.id_dimension} className="sticky top-0 z-20 border-r border-b bg-gray-100 px-2 py-2 text-center text-xs font-semibold">
                  {d.nombre_dimension}
                  <span className="block font-normal text-slate-500">/{d.puntaje_maximo}</span>
                </th>
              ))}
              <th className="sticky top-0 z-20 border-r border-b bg-blue-100 px-2 py-2 text-center font-semibold">Nota final</th>
              <th className="sticky top-0 z-20 min-w-48 border-b bg-gray-100 px-2 py-2 text-left text-xs font-semibold">Observación</th>
            </tr>
          </thead>
          <tbody>
            {datos.estudiantes.map((e, fila) => {
              const nota = notaEnVivo(e)
              const editado = cambios.some((c) => c.ci_estudiante === e.ci)
              return (
                <tr key={e.ci}>
                  <td
                    className={`sticky left-0 z-10 border-r border-b px-2 py-1.5 sm:px-3 sm:whitespace-nowrap ${editado ? 'bg-amber-50' : 'bg-white'}`}
                  >
                    {e.apellidos} {e.nombre_persona}
                  </td>
                  {datos.dimensiones.map((d, col) => {
                    if (d.es_autoevaluacion) {
                      return (
                        <td key={d.id_dimension} className="border-r border-b bg-slate-50 px-2 text-center text-slate-500 tabular-nums">
                          {formatoNota(e.puntajes[d.id_dimension] ?? null)}
                        </td>
                      )
                    }
                    const valor = texto(e, d)
                    const error = errorCasilla(valor, d)
                    return (
                      <td key={d.id_dimension} className="border-r border-b px-1 py-1 text-center">
                        <input
                          value={valor}
                          inputMode="decimal"
                          disabled={!datos.editable}
                          data-fila={fila}
                          data-col={col}
                          onKeyDown={bajarConEnter}
                          onFocus={(ev) => ev.currentTarget.select()}
                          onChange={(ev) =>
                            cambiar(e.ci, (ed) => ({ ...ed, puntajes: { ...ed.puntajes, [d.id_dimension]: ev.target.value } }))
                          }
                          title={error ?? undefined}
                          aria-label={`${d.nombre_dimension} de ${e.apellidos} ${e.nombre_persona}`}
                          aria-invalid={!!error}
                          className={`w-14 rounded border px-1.5 py-1 text-center tabular-nums outline-none focus:ring-2 focus:ring-blue-400 disabled:bg-transparent disabled:text-slate-700 ${
                            error ? 'border-red-500 bg-red-50 text-red-700' : 'border-slate-300'
                          }`}
                        />
                      </td>
                    )
                  })}
                  <td
                    className={`border-r border-b bg-blue-50 px-2 text-center tabular-nums ${colorNota(
                      nota,
                      completa(e),
                      datos.nota_minima,
                    )}`}
                    title={nota !== null && !completa(e) ? 'Nota incompleta: faltan dimensiones' : undefined}
                  >
                    {formatoNota(nota)}
                  </td>
                  <td className="border-b px-1 py-1">
                    <input
                      value={observacion(e)}
                      maxLength={300}
                      disabled={!datos.editable}
                      placeholder={datos.editable ? 'Opcional' : ''}
                      onChange={(ev) => cambiar(e.ci, (ed) => ({ ...ed, observacion: ev.target.value }))}
                      aria-label={`Observación de ${e.apellidos} ${e.nombre_persona}`}
                      className="w-full rounded border border-slate-300 px-2 py-1 text-xs outline-none focus:ring-2 focus:ring-blue-400 disabled:border-transparent disabled:bg-transparent"
                    />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {datos.editable && (
        <div className="flex flex-wrap items-center gap-2">
          <Button onClick={enviar} disabled={!cambios.length || conError || guardar.isPending}>
            <SaveIcon className="mr-2 size-4" />
            {guardar.isPending ? 'Guardando...' : `Guardar cambios${cambios.length ? ` (${cambios.length})` : ''}`}
          </Button>
          {Object.keys(ediciones).length > 0 && (
            <Button variant="outline" onClick={() => setEdiciones({})} disabled={guardar.isPending}>
              <Undo2Icon className="mr-2 size-4" /> Descartar
            </Button>
          )}
          {conError && <span className="text-sm text-red-600">Corrija las casillas en rojo antes de guardar.</span>}
          {!conError && cambios.length > 0 && <span className="text-sm text-amber-700">Tiene cambios sin guardar.</span>}
        </div>
      )}
    </div>
  )
}

// ------------------------------------------------------------
// Administrador: cerrar y reabrir trimestres
// ------------------------------------------------------------

function Trimestres({ periodos }: { periodos: PeriodoCU23[] }) {
  const cambiar = useCambiarPeriodo()
  const [pedido, setPedido] = useState<{ periodo: PeriodoCU23; accion: 'cerrar' | 'reabrir' } | null>(null)

  const confirmar = () => {
    if (!pedido) return
    cambiar.mutate(
      { id_periodo: pedido.periodo.id_periodo, accion: pedido.accion },
      {
        onSuccess: (r) => {
          toast.success(
            r.estado_periodo === 'cerrado'
              ? `${r.periodo} cerrado. Se emitieron ${r.boletines} boletines.`
              : `${r.periodo} reabierto: los docentes ya pueden corregir notas.`,
          )
          setPedido(null)
        },
        onError: (e) => toast.error(mensajeError(e)),
      },
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Trimestres</CardTitle>
        <CardDescription>
          Al cerrar un trimestre sus notas quedan fijas y se emiten los boletines. Si hay que corregir algo, se puede reabrir.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 md:grid-cols-3">
          {periodos.map((p) => (
            <div key={p.id_periodo} className="flex flex-col gap-2 rounded-lg border p-3">
              <div className="flex items-center justify-between gap-2">
                <p className="font-semibold">{p.nombre_periodo}</p>
                <span
                  className={`rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${
                    !p.iniciado
                      ? 'bg-slate-100 text-slate-600 ring-slate-200'
                      : p.estado_periodo === 'cerrado'
                        ? 'bg-slate-800 text-white ring-slate-800'
                        : 'bg-emerald-50 text-emerald-700 ring-emerald-200'
                  }`}
                >
                  {!p.iniciado ? 'Aún no empieza' : p.estado_periodo === 'cerrado' ? 'Cerrado' : 'Abierto'}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                {fecha(p.fecha_inicio_p)} al {fecha(p.fecha_final_p)}
              </p>
              {p.iniciado && (
                <p className={`text-xs ${p.notas_pendientes ? 'text-amber-700' : 'text-emerald-700'}`}>
                  {p.notas_pendientes ? `${p.notas_pendientes} notas sin registrar o incompletas` : 'Todas las notas completas'}
                </p>
              )}
              {p.iniciado &&
                (p.estado_periodo === 'abierto' ? (
                  <Button size="sm" onClick={() => setPedido({ periodo: p, accion: 'cerrar' })}>
                    <LockIcon className="mr-2 size-4" /> Cerrar trimestre
                  </Button>
                ) : (
                  <Button size="sm" variant="outline" onClick={() => setPedido({ periodo: p, accion: 'reabrir' })}>
                    <LockOpenIcon className="mr-2 size-4" /> Reabrir
                  </Button>
                ))}
            </div>
          ))}
        </div>
      </CardContent>

      <Confirmar
        abierto={pedido !== null}
        onCambiar={(abierto) => !abierto && setPedido(null)}
        titulo={pedido?.accion === 'cerrar' ? `¿Cerrar el ${pedido.periodo.nombre_periodo}?` : `¿Reabrir el ${pedido?.periodo.nombre_periodo}?`}
        descripcion={
          pedido?.accion === 'cerrar' ? (
            <>
              Las notas quedarán fijas (solo usted podrá corregirlas) y se emitirán los boletines del trimestre.
              {pedido.periodo.notas_pendientes > 0 && (
                <span className="mt-2 block font-medium text-amber-700">
                  Atención: hay {pedido.periodo.notas_pendientes} notas sin registrar o incompletas.
                </span>
              )}
            </>
          ) : (
            'Los docentes podrán volver a corregir notas y los estudiantes su autoevaluación. Al cerrarlo otra vez se reemitirán los boletines.'
          )
        }
        textoConfirmar={pedido?.accion === 'cerrar' ? 'Cerrar trimestre' : 'Reabrir'}
        ocupado={cambiar.isPending}
        onConfirmar={confirmar}
      />
    </Card>
  )
}

// ------------------------------------------------------------
// Estudiante: mis calificaciones y autoevaluación
// ------------------------------------------------------------

function MisCalificaciones() {
  const [periodoElegido, setPeriodoElegido] = useState<number | null>(null)
  const datos = useMisCalificaciones(periodoElegido)
  const guardar = useGuardarAutoevaluacion()
  const [autos, setAutos] = useState<Record<number, string>>({})

  const d = datos.data
  const auto = d?.dimensiones.find((x) => x.es_autoevaluacion)
  const docentes = d?.dimensiones.filter((x) => !x.es_autoevaluacion) ?? []

  const valorAuto = (idMateria: number, puntajes: Puntajes) =>
    autos[idMateria] ?? (auto ? mostrar(puntajes[auto.id_dimension]) : '')
  const cambios =
    d && auto
      ? d.materias.flatMap((m) => {
          if (autos[m.id_materia] === undefined) return []
          const v = aNumero(autos[m.id_materia])
          if (Number.isNaN(v as number) || v === (m.puntajes[auto.id_dimension] ?? null)) return []
          return [{ id_materia: m.id_materia, puntaje: v }]
        })
      : []
  const conError = !!(d && auto && d.materias.some((m) => errorCasilla(valorAuto(m.id_materia, m.puntajes), auto)))

  const enviar = () => {
    if (!d?.periodo) return
    guardar.mutate(
      { id_periodo: d.periodo.id_periodo, autoevaluaciones: cambios },
      {
        onSuccess: () => {
          setAutos({})
          toast.success('Autoevaluación guardada.')
        },
        onError: (e) => toast.error(mensajeError(e)),
      },
    )
  }

  const notaEnVivo = (m: { id_materia: number; puntajes: Puntajes }) => {
    const valores = [
      ...docentes.map((x) => m.puntajes[x.id_dimension] ?? null),
      auto ? aNumero(valorAuto(m.id_materia, m.puntajes)) : null,
    ].filter((v): v is number => v !== null && !Number.isNaN(v))
    return valores.length ? valores.reduce((a, b) => a + b, 0) : null
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Mis calificaciones</h1>
        <p className="text-sm text-slate-500">
          Revise sus notas por materia y registre su autoevaluación mientras el trimestre está abierto.
          {d?.curso ? ` ${d.curso} · Gestión ${d.gestion}.` : ''}
        </p>
      </div>

      {datos.isLoading && <p className="text-slate-500">Cargando...</p>}
      {datos.isError && <Aviso texto={mensajeError(datos.error)} />}

      {d && (
        <Card>
          <CardContent className="space-y-4">
            <div className="max-w-sm">
              <Campo etiqueta="Trimestre">
                <SelectorPeriodo
                  periodos={d.periodos}
                  valor={d.periodo?.id_periodo ?? null}
                  onCambiar={(id) => {
                    setAutos({})
                    setPeriodoElegido(id)
                  }}
                />
              </Campo>
            </div>
            {!d.autoevaluacion_editable && d.motivo_no_editable && <Aviso tono="gris" texto={d.motivo_no_editable} />}

            {d.materias.length > 0 && (
              <div className="overflow-x-auto rounded border">
                <table className="w-full border-separate border-spacing-0 text-sm">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="sticky left-0 z-10 min-w-36 border-r border-b bg-gray-100 px-2 py-2 text-left font-semibold sm:px-3">
                        Materia
                      </th>
                      {d.dimensiones.map((x) => (
                        <th key={x.id_dimension} className="border-r border-b px-2 py-2 text-center text-xs font-semibold">
                          {x.nombre_dimension}
                          <span className="block font-normal text-slate-500">/{x.puntaje_maximo}</span>
                        </th>
                      ))}
                      <th className="border-b bg-blue-100 px-2 py-2 text-center font-semibold">Nota final</th>
                    </tr>
                  </thead>
                  <tbody>
                    {d.materias.map((m) => {
                      const nota = notaEnVivo(m)
                      const completa = d.dimensiones.every((x) =>
                        x.es_autoevaluacion ? aNumero(valorAuto(m.id_materia, m.puntajes)) !== null : m.puntajes[x.id_dimension] !== undefined,
                      )
                      return (
                        <tr key={m.id_materia}>
                          <td className="sticky left-0 z-10 border-r border-b bg-white px-2 py-1.5 sm:px-3">
                            <span className="font-medium">{m.materia}</span>
                            <span className="block text-xs text-slate-500">{m.profesor}</span>
                            {m.observacion && <span className="block text-xs text-slate-600 italic">“{m.observacion}”</span>}
                          </td>
                          {d.dimensiones.map((x) => {
                            if (!x.es_autoevaluacion || !d.autoevaluacion_editable) {
                              return (
                                <td key={x.id_dimension} className="border-r border-b px-2 text-center tabular-nums">
                                  {formatoNota(m.puntajes[x.id_dimension] ?? null)}
                                </td>
                              )
                            }
                            const valor = valorAuto(m.id_materia, m.puntajes)
                            const error = errorCasilla(valor, x)
                            return (
                              <td key={x.id_dimension} className="border-r border-b px-1 py-1 text-center">
                                <input
                                  value={valor}
                                  inputMode="decimal"
                                  onFocus={(ev) => ev.currentTarget.select()}
                                  onChange={(ev) => setAutos((a) => ({ ...a, [m.id_materia]: ev.target.value }))}
                                  title={error ?? undefined}
                                  aria-label={`Autoevaluación de ${m.materia}`}
                                  aria-invalid={!!error}
                                  className={`w-14 rounded border px-1.5 py-1 text-center tabular-nums outline-none focus:ring-2 focus:ring-blue-400 ${
                                    error ? 'border-red-500 bg-red-50 text-red-700' : 'border-slate-300'
                                  }`}
                                />
                              </td>
                            )
                          })}
                          <td
                            className={`border-b bg-blue-50 px-2 text-center tabular-nums ${colorNota(nota, completa, d.nota_minima)}`}
                            title={nota !== null && !completa ? 'Nota incompleta: faltan dimensiones' : undefined}
                          >
                            {formatoNota(nota)}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {d.autoevaluacion_editable && d.materias.length > 0 && (
              <div className="flex flex-wrap items-center gap-2">
                <Button onClick={enviar} disabled={!cambios.length || conError || guardar.isPending}>
                  <SaveIcon className="mr-2 size-4" />
                  {guardar.isPending ? 'Guardando...' : 'Guardar autoevaluación'}
                </Button>
                {conError && auto && (
                  <span className="text-sm text-red-600">La autoevaluación va de 0 a {auto.puntaje_maximo}.</span>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}

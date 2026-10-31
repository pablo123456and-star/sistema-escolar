/**
 * CU15 - Gestionar gestión académica (año lectivo)
 * Paquete: academico
 *
 * Actores ........: Administrador
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/academico/casos_uso/cu15_gestionar_gestion_academica.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Una pestaña por gestión (año). De la gestión elegida se ve el resumen (inscritos, retirados,
 * promedio, cobrado, vencido), sus periodos y las dimensiones de evaluación (deben sumar 100).
 * Mientras la gestión está abierta se configura todo; al cerrarla (acción irreversible) cada
 * estudiante queda promovido o reprobado y ya no admite cambios.
 *
 * Precondición:  Sesión iniciada como administrador. Para cerrar: la gestión está abierta.
 * Postcondición: La gestión, sus periodos y dimensiones quedan configurados. Al cerrarla, cada estudiante queda promovido o reprobado.
 *
 * Estado: IMPLEMENTADO.
 */
import { useState, type ReactNode } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import { cn } from 'cn'
import { LockIcon, PencilIcon, PlusIcon, SaveIcon, Trash2Icon } from 'lucide-react'
import Confirmar from '@/componentes/Confirmar'
import { BotonAccion, Campo, EncabezadoPagina, InsigniaEstado } from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/componentes/ui/dialog'
import { Input } from '@/componentes/ui/input'
import { fecha } from '@/lib/formato'
import { mensajeError } from '@/nucleo/api'
import {
  useCerrarGestion,
  useDimensiones,
  useEliminarPeriodo,
  useGestiones,
  useGuardarDimensiones,
  useGuardarGestion,
  useGuardarPeriodo,
  usePeriodos,
  useResumenGestion,
} from '../api'
import {
  type DatosDimension,
  type DatosGestion,
  type DatosPeriodo,
  type Dimensiones,
  esquemaGestion,
  esquemaPeriodo,
  type Gestion,
  type Periodo,
} from '../schemas'

type Edicion = { tipo: 'gestion'; gestion?: Gestion } | { tipo: 'periodo'; gestion: Gestion; periodo?: Periodo }

const SELECT_CLASE =
  'h-8 w-full rounded-lg border border-input bg-transparent px-2.5 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50'

/** Guarda, avisa y cierra; si el backend rechaza, muestra su mensaje y deja el diálogo abierto. */
async function guardarYCerrar(guardar: () => Promise<unknown>, exito: string, onCerrar?: () => void) {
  try {
    await guardar()
    toast.success(exito)
    onCerrar?.()
  } catch (e) {
    toast.error(mensajeError(e))
  }
}

const numero = (texto: string | null | undefined) => (texto === null || texto === undefined ? 0 : Number(texto))
const bolivianos = (texto: string) => `Bs ${numero(texto).toLocaleString('es-BO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

export default function CU15GestionarGestionAcademica() {
  const gestiones = useGestiones()
  const [idElegido, setIdElegido] = useState<number | null>(null)
  const [edicion, setEdicion] = useState<Edicion | null>(null)
  const [cerrando, setCerrando] = useState(false)
  const cerrar = useCerrarGestion()

  const lista = gestiones.data ?? []
  const gestion = lista.find((g) => g.id_gestion === idElegido) ?? lista.find((g) => g.estado_gestion === 'abierta') ?? lista[0]
  const hayAbierta = lista.some((g) => g.estado_gestion === 'abierta')

  const confirmarCierre = async () => {
    if (!gestion) return
    try {
      const r = await cerrar.mutateAsync(gestion.id_gestion)
      toast.success(`Gestión ${gestion.anio} cerrada: ${r.promovidos} promovidos y ${r.reprobados} reprobados.`)
    } catch (e) {
      toast.error(mensajeError(e))
    }
    setCerrando(false)
  }

  return (
    <div className="space-y-5">
      <EncabezadoPagina
        titulo="Gestión académica"
        descripcion="Configure el año lectivo: sus periodos y las dimensiones de evaluación. Al terminar el año, ciérrelo."
        accion={
          <Button onClick={() => setEdicion({ tipo: 'gestion' })} disabled={hayAbierta} title={hayAbierta ? 'Ya hay una gestión abierta' : undefined}>
            <PlusIcon /> Nueva gestión
          </Button>
        }
      />

      {gestiones.isLoading ? (
        <p className="py-10 text-center text-slate-500">Cargando...</p>
      ) : gestiones.isError ? (
        <p className="py-10 text-center text-slate-500">{mensajeError(gestiones.error)}</p>
      ) : !gestion ? (
        <div className="rounded-xl border border-dashed bg-white py-12 text-center text-slate-500">
          Todavía no hay gestiones. Registre la primera con <b>Nueva gestión</b>.
        </div>
      ) : (
        <>
          <div className="flex flex-wrap gap-2" role="tablist">
            {lista.map((g) => (
              <button
                key={g.id_gestion}
                role="tab"
                aria-selected={g.id_gestion === gestion.id_gestion}
                onClick={() => setIdElegido(g.id_gestion)}
                className={cn(
                  'rounded-lg border px-4 py-2 text-sm font-medium transition-colors',
                  g.id_gestion === gestion.id_gestion
                    ? 'border-primary bg-primary text-primary-foreground shadow-sm'
                    : 'bg-white text-slate-600 hover:bg-slate-50',
                )}
              >
                {g.anio}
                <span className="ml-2 text-xs opacity-75">{g.estado_gestion}</span>
              </button>
            ))}
          </div>

          <PanelGestion
            gestion={gestion}
            onEditar={setEdicion}
            onCerrar={() => setCerrando(true)}
          />
        </>
      )}

      {edicion?.tipo === 'gestion' && <DialogoGestion edicion={edicion} onCerrar={() => setEdicion(null)} />}
      {edicion?.tipo === 'periodo' && <DialogoPeriodo edicion={edicion} onCerrar={() => setEdicion(null)} />}

      <Confirmar
        abierto={cerrando}
        onCambiar={(v) => !v && setCerrando(false)}
        titulo={`Cerrar la gestión ${gestion?.anio ?? ''}`}
        descripcion="Cada estudiante inscrito quedará promovido o reprobado según su promedio, se cerrarán todos los periodos y ya no se podrá modificar nada de esta gestión. Esta acción no se puede deshacer."
        textoConfirmar="Cerrar gestión"
        icono={<LockIcon />}
        peligro
        ocupado={cerrar.isPending}
        onConfirmar={confirmarCierre}
      />
    </div>
  )
}

function PanelGestion({
  gestion,
  onEditar,
  onCerrar,
}: {
  gestion: Gestion
  onEditar: (e: Edicion) => void
  onCerrar: () => void
}) {
  const abierta = gestion.estado_gestion === 'abierta'
  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 rounded-xl border bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold text-slate-900">Gestión {gestion.anio}</h2>
            <InsigniaEstado estado={gestion.estado_gestion} />
          </div>
          <p className="text-sm text-slate-500">
            Del {fecha(gestion.fecha_inicio_g)} al {fecha(gestion.fecha_final_g)} · nota mínima de aprobación{' '}
            {numero(gestion.nota_minima_aprobacion)}
          </p>
        </div>
        {abierta && (
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => onEditar({ tipo: 'gestion', gestion })}>
              <PencilIcon /> Modificar
            </Button>
            <Button variant="destructive" onClick={onCerrar}>
              <LockIcon /> Cerrar gestión
            </Button>
          </div>
        )}
      </div>

      <Resumen idGestion={gestion.id_gestion} />
      <SeccionPeriodos gestion={gestion} onEditar={onEditar} />
      <SeccionDimensiones gestion={gestion} />
    </div>
  )
}

// ------------------------------------------------------------
// Resumen
// ------------------------------------------------------------

function Resumen({ idGestion }: { idGestion: number }) {
  const resumen = useResumenGestion(idGestion)
  const r = resumen.data
  const datos: [string, string][] = [
    ['Inscritos activos', r ? String(r.inscritos_activos) : '—'],
    ['Retirados', r ? String(r.retirados) : '—'],
    ['Finalizados', r ? String(r.finalizados) : '—'],
    ['Promedio general', r?.promedio_general ? numero(r.promedio_general).toFixed(2) : '—'],
    ['Cobrado', r ? bolivianos(r.total_cobrado) : '—'],
    ['Vencido sin pagar', r ? bolivianos(r.total_vencido) : '—'],
  ]
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
      {datos.map(([etiqueta, valor]) => (
        <div key={etiqueta} className="rounded-xl border bg-white p-4 shadow-sm">
          <p className="text-xs text-slate-500">{etiqueta}</p>
          <p className="mt-1 text-xl font-bold text-slate-900">{valor}</p>
        </div>
      ))}
    </div>
  )
}

// ------------------------------------------------------------
// Periodos
// ------------------------------------------------------------

function SeccionPeriodos({ gestion, onEditar }: { gestion: Gestion; onEditar: (e: Edicion) => void }) {
  const periodos = usePeriodos(gestion.id_gestion)
  const eliminar = useEliminarPeriodo()
  const [aEliminar, setAEliminar] = useState<Periodo | null>(null)
  const abierta = gestion.estado_gestion === 'abierta'

  const confirmarEliminar = async () => {
    if (!aEliminar) return
    await guardarYCerrar(() => eliminar.mutateAsync(aEliminar.id_periodo), `Se eliminó ${aEliminar.nombre_periodo}.`)
    setAEliminar(null)
  }

  return (
    <Seccion
      titulo="Periodos"
      descripcion="Trimestres, bimestres o semestres dentro de las fechas de la gestión, sin solaparse."
      accion={
        abierta && (
          <Button variant="outline" onClick={() => onEditar({ tipo: 'periodo', gestion })}>
            <PlusIcon /> Nuevo periodo
          </Button>
        )
      }
    >
      {periodos.isLoading ? (
        <p className="py-6 text-center text-sm text-slate-500">Cargando...</p>
      ) : !periodos.data?.length ? (
        <p className="py-6 text-center text-sm text-slate-500">Esta gestión aún no tiene periodos.</p>
      ) : (
        <ul className="divide-y">
          {periodos.data.map((p) => (
            <li key={p.id_periodo} className="flex items-center justify-between gap-3 py-3">
              <div className="min-w-0">
                <p className="truncate font-medium text-slate-900">
                  {p.nombre_periodo} <span className="text-xs font-normal text-slate-500 capitalize">{p.tipo}</span>
                </p>
                <p className="text-sm text-slate-500">
                  {fecha(p.fecha_inicio_p)} al {fecha(p.fecha_final_p)}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <InsigniaEstado estado={p.estado_periodo} />
                {abierta && (
                  <>
                    <BotonAccion etiqueta="Modificar periodo" tono="ambar" onClick={() => onEditar({ tipo: 'periodo', gestion, periodo: p })}>
                      <PencilIcon />
                    </BotonAccion>
                    <BotonAccion etiqueta="Eliminar periodo" tono="rojo" onClick={() => setAEliminar(p)}>
                      <Trash2Icon />
                    </BotonAccion>
                  </>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      <Confirmar
        abierto={aEliminar !== null}
        onCambiar={(v) => !v && setAEliminar(null)}
        titulo="Confirmar eliminación"
        descripcion={`¿Eliminar ${aEliminar?.nombre_periodo ?? ''}? Esta acción no se puede deshacer.`}
        textoConfirmar="Eliminar"
        icono={<Trash2Icon />}
        peligro
        ocupado={eliminar.isPending}
        onConfirmar={confirmarEliminar}
      />
    </Seccion>
  )
}

// ------------------------------------------------------------
// Dimensiones de evaluación
// ------------------------------------------------------------

function SeccionDimensiones({ gestion }: { gestion: Gestion }) {
  const dimensiones = useDimensiones(gestion.id_gestion)
  return (
    <Seccion
      titulo="Dimensiones de evaluación"
      descripcion="Las partes de la nota (ser, saber, hacer, decidir, autoevaluación). Deben sumar exactamente 100 para guardarse."
    >
      {dimensiones.isLoading || !dimensiones.data ? (
        <p className="py-6 text-center text-sm text-slate-500">Cargando...</p>
      ) : (
        <EditorDimensiones
          // al cambiar lo guardado se reinicia el borrador
          key={`${gestion.id_gestion}-${JSON.stringify(dimensiones.data.dimensiones)}`}
          idGestion={gestion.id_gestion}
          editable={gestion.estado_gestion === 'abierta'}
          guardadas={dimensiones.data}
        />
      )}
    </Seccion>
  )
}

function EditorDimensiones({ idGestion, editable, guardadas }: { idGestion: number; editable: boolean; guardadas: Dimensiones }) {
  const guardar = useGuardarDimensiones()
  const [filas, setFilas] = useState<DatosDimension[]>(
    guardadas.dimensiones.map((d) => ({
      nombre_dimension: d.nombre_dimension,
      puntaje_maximo: numero(d.puntaje_maximo),
      es_autoevaluacion: d.es_autoevaluacion,
    })),
  )
  // redondeo a 2 decimales (como NUMERIC(5,2) en la BD) para evitar errores de coma flotante
  const suma = Math.round(filas.reduce((a, f) => a + (Number.isFinite(f.puntaje_maximo) ? f.puntaje_maximo : 0), 0) * 100) / 100
  const valido = filas.length > 0 && filas.every((f) => f.nombre_dimension.trim() && f.puntaje_maximo > 0) && suma === 100

  const cambiar = (i: number, cambios: Partial<DatosDimension>) =>
    setFilas((actual) =>
      actual.map((f, j) => {
        if (j === i) return { ...f, ...cambios }
        // solo una dimensión puede ser la autoevaluación
        return cambios.es_autoevaluacion ? { ...f, es_autoevaluacion: false } : f
      }),
    )

  return (
    <div className="space-y-3">
      {filas.map((f, i) => (
        <div key={i} className="grid grid-cols-[1fr_6rem_auto_auto] items-center gap-2">
          <Input
            aria-label="Nombre de la dimensión"
            value={f.nombre_dimension}
            maxLength={30}
            disabled={!editable}
            onChange={(e) => cambiar(i, { nombre_dimension: e.target.value })}
          />
          <Input
            aria-label="Puntaje máximo"
            type="number"
            min={1}
            max={100}
            value={Number.isFinite(f.puntaje_maximo) ? f.puntaje_maximo : ''}
            disabled={!editable}
            onChange={(e) => cambiar(i, { puntaje_maximo: e.target.valueAsNumber })}
          />
          <label className="flex items-center gap-1.5 text-xs text-slate-600">
            <input
              type="checkbox"
              checked={f.es_autoevaluacion}
              disabled={!editable}
              onChange={(e) => cambiar(i, { es_autoevaluacion: e.target.checked })}
            />
            Autoevaluación
          </label>
          {editable && (
            <BotonAccion etiqueta="Quitar dimensión" tono="rojo" onClick={() => setFilas((a) => a.filter((_, j) => j !== i))}>
              <Trash2Icon />
            </BotonAccion>
          )}
        </div>
      ))}

      <div className="flex flex-wrap items-center justify-between gap-3 border-t pt-3">
        <p className={cn('text-sm font-medium', suma === 100 ? 'text-emerald-600' : 'text-amber-600')}>
          Suma: {suma} / 100 {suma === 100 ? '✓' : suma > 100 ? '(excede 100: no se puede guardar)' : '(incompleta: no se puede guardar)'}
        </p>
        {editable && (
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => setFilas((a) => [...a, { nombre_dimension: '', puntaje_maximo: Math.max(0, 100 - suma) || 1, es_autoevaluacion: false }])}
              disabled={filas.length >= 10}
            >
              <PlusIcon /> Agregar
            </Button>
            <Button
              disabled={!valido || guardar.isPending}
              onClick={() =>
                guardarYCerrar(
                  () => guardar.mutateAsync({ id_gestion: idGestion, dimensiones: filas.map((f) => ({ ...f, nombre_dimension: f.nombre_dimension.trim() })) }),
                  'Dimensiones guardadas.',
                )
              }
            >
              <SaveIcon /> Guardar
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}

function Seccion({ titulo, descripcion, accion, children }: { titulo: string; descripcion: string; accion?: ReactNode; children: ReactNode }) {
  return (
    <div className="rounded-xl border bg-white shadow-sm">
      <div className="flex flex-col gap-2 border-b p-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="font-semibold text-slate-900">{titulo}</h3>
          <p className="text-sm text-slate-500">{descripcion}</p>
        </div>
        {accion}
      </div>
      <div className="p-4">{children}</div>
    </div>
  )
}

// ------------------------------------------------------------
// Diálogos de registro y modificación
// ------------------------------------------------------------

function DialogoFormulario({
  titulo,
  descripcion,
  ocupado,
  onCerrar,
  onGuardar,
  children,
}: {
  titulo: string
  descripcion: string
  ocupado: boolean
  onCerrar: () => void
  onGuardar: () => void
  children: ReactNode
}) {
  return (
    <Dialog open onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{titulo}</DialogTitle>
          <DialogDescription>{descripcion}</DialogDescription>
        </DialogHeader>
        <form
          id="form-cu15"
          className="grid gap-3"
          noValidate
          onSubmit={(e) => {
            e.preventDefault()
            onGuardar()
          }}
        >
          {children}
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={onCerrar}>Cancelar</Button>
          <Button type="submit" form="form-cu15" disabled={ocupado}>Guardar</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function DialogoGestion({ edicion, onCerrar }: { edicion: Extract<Edicion, { tipo: 'gestion' }>; onCerrar: () => void }) {
  const guardar = useGuardarGestion()
  const g = edicion.gestion
  const anioSugerido = new Date().getFullYear()
  const form = useForm<DatosGestion>({
    resolver: zodResolver(esquemaGestion),
    defaultValues: {
      anio: g?.anio ?? anioSugerido,
      fecha_inicio_g: g?.fecha_inicio_g ?? `${anioSugerido}-02-01`,
      fecha_final_g: g?.fecha_final_g ?? `${anioSugerido}-11-30`,
      nota_minima_aprobacion: g ? numero(g.nota_minima_aprobacion) : 51,
    },
  })
  const e = form.formState.errors
  const enviar = form.handleSubmit((datos) =>
    guardarYCerrar(
      () => guardar.mutateAsync({ id: g?.id_gestion, datos }),
      g ? 'Gestión actualizada.' : `Gestión ${datos.anio} registrada.`,
      onCerrar,
    ),
  )
  return (
    <DialogoFormulario
      titulo={g ? `Modificar gestión ${g.anio}` : 'Nueva gestión académica'}
      descripcion="El año debe coincidir con el de la fecha de inicio."
      ocupado={guardar.isPending}
      onCerrar={onCerrar}
      onGuardar={enviar}
    >
      <div className="grid grid-cols-2 gap-3">
        <Campo etiqueta="Año" htmlFor="anio" error={e.anio?.message}>
          <Input id="anio" type="number" {...form.register('anio', { valueAsNumber: true })} />
        </Campo>
        <Campo etiqueta="Nota mínima de aprobación" htmlFor="nota_minima_aprobacion" error={e.nota_minima_aprobacion?.message}>
          <Input id="nota_minima_aprobacion" type="number" min={0} max={100} {...form.register('nota_minima_aprobacion', { valueAsNumber: true })} />
        </Campo>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Campo etiqueta="Fecha de inicio" htmlFor="fecha_inicio_g" error={e.fecha_inicio_g?.message}>
          <Input id="fecha_inicio_g" type="date" {...form.register('fecha_inicio_g')} />
        </Campo>
        <Campo etiqueta="Fecha final" htmlFor="fecha_final_g" error={e.fecha_final_g?.message}>
          <Input id="fecha_final_g" type="date" {...form.register('fecha_final_g')} />
        </Campo>
      </div>
    </DialogoFormulario>
  )
}

function DialogoPeriodo({ edicion, onCerrar }: { edicion: Extract<Edicion, { tipo: 'periodo' }>; onCerrar: () => void }) {
  const guardar = useGuardarPeriodo()
  const p = edicion.periodo
  const form = useForm<DatosPeriodo>({
    resolver: zodResolver(esquemaPeriodo),
    defaultValues: {
      nombre_periodo: p?.nombre_periodo ?? '',
      tipo: p?.tipo ?? 'trimestre',
      fecha_inicio_p: p?.fecha_inicio_p ?? edicion.gestion.fecha_inicio_g,
      fecha_final_p: p?.fecha_final_p ?? edicion.gestion.fecha_final_g,
    },
  })
  const e = form.formState.errors
  const enviar = form.handleSubmit((datos) =>
    guardarYCerrar(
      () => guardar.mutateAsync({ id: p?.id_periodo, id_gestion: edicion.gestion.id_gestion, datos }),
      p ? 'Periodo actualizado.' : `${datos.nombre_periodo} registrado.`,
      onCerrar,
    ),
  )
  return (
    <DialogoFormulario
      titulo={p ? 'Modificar periodo' : 'Nuevo periodo'}
      descripcion={`Gestión ${edicion.gestion.anio}: del ${fecha(edicion.gestion.fecha_inicio_g)} al ${fecha(edicion.gestion.fecha_final_g)}.`}
      ocupado={guardar.isPending}
      onCerrar={onCerrar}
      onGuardar={enviar}
    >
      <div className="grid grid-cols-[1fr_9rem] gap-3">
        <Campo etiqueta="Nombre" htmlFor="nombre_periodo" error={e.nombre_periodo?.message}>
          <Input id="nombre_periodo" autoFocus maxLength={50} placeholder="1er Trimestre" {...form.register('nombre_periodo')} />
        </Campo>
        <Campo etiqueta="Tipo" htmlFor="tipo" error={e.tipo?.message}>
          <select id="tipo" className={SELECT_CLASE} {...form.register('tipo')}>
            <option value="trimestre">Trimestre</option>
            <option value="bimestre">Bimestre</option>
            <option value="semestre">Semestre</option>
          </select>
        </Campo>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Campo etiqueta="Fecha de inicio" htmlFor="fecha_inicio_p" error={e.fecha_inicio_p?.message}>
          <Input id="fecha_inicio_p" type="date" {...form.register('fecha_inicio_p')} />
        </Campo>
        <Campo etiqueta="Fecha final" htmlFor="fecha_final_p" error={e.fecha_final_p?.message}>
          <Input id="fecha_final_p" type="date" {...form.register('fecha_final_p')} />
        </Campo>
      </div>
    </DialogoFormulario>
  )
}

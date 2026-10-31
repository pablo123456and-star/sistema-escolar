/**
 * CU25 - Registrar pago de mensualidad (incluye aranceles, becas, cuotas y morosos)
 * Paquete: administracion
 *
 * Actores ........: Administrativo
 * Rol del sistema : administrador (tutor y estudiante consultan)
 * Backend ........: backend/app/paquetes/administracion/casos_uso/cu25_registrar_pago_mensualidad.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Administrador, por pestañas:
 *   - Cobrar: buscar al estudiante, ver sus cuotas y cobrar una pendiente (método y tutor que paga);
 *     al cobrar se muestra el recibo de pago para imprimir. Un cobro mal hecho se revierte y una
 *     cuota que ya no corresponde se anula (ambos con motivo).
 *   - Aranceles por nivel, Becas por estudiante, Generar cuotas de un mes y Morosos (cuotas
 *     atrasadas con el teléfono del tutor).
 * Tutor y estudiante: sus cuotas y los recibos de las pagadas. Si el pago en línea está habilitado,
 * pagan una cuota pendiente con tarjeta en Stripe (MODO DE PRUEBA, tarjeta 4242 4242 4242 4242);
 * al volver, el backend confirma el pago con Stripe y se muestra el recibo.
 *
 * Precondición:  La cuota está pendiente y quien cobra es un administrativo.
 * Postcondición: La cuota queda pagada con número de recibo único y fecha; queda registrado en la bitácora.
 *
 * Estado: IMPLEMENTADO.
 */
import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { useSearchParams } from 'react-router'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import { cn } from 'cn'
import {
  BanIcon,
  CalendarPlusIcon,
  CoinsIcon,
  CreditCardIcon,
  PencilIcon,
  PhoneIcon,
  PlusIcon,
  PrinterIcon,
  ReceiptTextIcon,
  SearchIcon,
  TriangleAlertIcon,
  Undo2Icon,
  WalletIcon,
} from 'lucide-react'
import Confirmar from '@/componentes/Confirmar'
import Escudo from '@/componentes/Escudo'
import { BotonAccion, Campo, EncabezadoPagina, FilaMensaje } from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/componentes/ui/dialog'
import { Input } from '@/componentes/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { Textarea } from '@/componentes/ui/textarea'
import { fecha as formatoFecha } from '@/lib/formato'
import { useRetardo } from '@/lib/useRetardo'
import { mensajeError } from '@/nucleo/api'
import { useSesion } from '@/nucleo/auth/contexto'
import {
  useAranceles,
  useBecas,
  useCobrar,
  useConfirmarPagoEnLinea,
  useCorregirCuota,
  useEstadoCuenta,
  useEstadoPagoEnLinea,
  useEstudiantesPago,
  useGenerarCuotas,
  useGuardarArancel,
  useGuardarBeca,
  useIniciarPagoEnLinea,
  useMisCuotas,
  useMorosos,
  useRecibo,
} from '../api'
import {
  type ArancelNivel,
  type Beca,
  type Cuota,
  type DatosArancel,
  type DatosBeca,
  type DatosMotivo,
  type EstadoCuenta,
  type EstadoCuota,
  esquemaArancel,
  esquemaBeca,
  esquemaMotivo,
  MESES,
  METODOS_PAGO,
  type MetodoPago,
  type Recibo,
} from '../schemas'

/** "Bs 1.550,00" */
const bs = (monto: number) => `Bs ${monto.toLocaleString('es-BO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
const nroRecibo = (n: number) => String(n).padStart(6, '0')

const ETIQUETA_METODO: Record<MetodoPago, string> = {
  efectivo: 'Efectivo', transferencia: 'Transferencia', qr: 'QR', tarjeta: 'Tarjeta',
}

const ESTILO_CUOTA: Record<EstadoCuota, { etiqueta: string; clase: string }> = {
  pendiente: { etiqueta: 'Pendiente', clase: 'bg-amber-50 text-amber-700 ring-amber-200' },
  atrasado: { etiqueta: 'Atrasada', clase: 'bg-rose-50 text-rose-700 ring-rose-200' },
  pagado: { etiqueta: 'Pagada', clase: 'bg-emerald-50 text-emerald-700 ring-emerald-200' },
  anulado: { etiqueta: 'Anulada', clase: 'bg-slate-100 text-slate-500 ring-slate-200' },
}

type Pestana = 'cobrar' | 'aranceles' | 'becas' | 'cuotas' | 'morosos'
const PESTANAS: { id: Pestana; texto: string }[] = [
  { id: 'cobrar', texto: 'Cobrar' },
  { id: 'aranceles', texto: 'Aranceles' },
  { id: 'becas', texto: 'Becas' },
  { id: 'cuotas', texto: 'Generar cuotas' },
  { id: 'morosos', texto: 'Morosos' },
]

export default function CU25RegistrarPagoMensualidad() {
  const { usuario } = useSesion()
  return usuario?.rol === 'administrador' ? <PantallaAdministrador /> : <PantallaMisCuotas />
}

function Vacio({ texto }: { texto: ReactNode }) {
  return <div className="rounded-xl border border-dashed bg-white py-12 text-center text-slate-500">{texto}</div>
}

function Cargando({ consulta }: { consulta: { isLoading: boolean; isError: boolean; error: unknown } }) {
  if (consulta.isLoading) return <p className="py-10 text-center text-slate-500">Cargando...</p>
  if (consulta.isError) return <Vacio texto={mensajeError(consulta.error)} />
  return null
}

// ------------------------------------------------------------
// Administrador
// ------------------------------------------------------------

function PantallaAdministrador() {
  const [pestana, setPestana] = useState<Pestana>('cobrar')
  const [ci, setCi] = useState<string | null>(null)

  return (
    <div className="space-y-5">
      <EncabezadoPagina
        titulo="Pagos de mensualidad"
        descripcion="Cobre las cuotas, emita el recibo de pago y configure aranceles, becas y cuotas del mes."
      />
      <div className="flex flex-wrap gap-2" role="tablist">
        {PESTANAS.map((p) => (
          <button
            key={p.id}
            role="tab"
            aria-selected={p.id === pestana}
            onClick={() => setPestana(p.id)}
            className={cn(
              'rounded-lg border px-4 py-2 text-sm font-medium transition-colors',
              p.id === pestana ? 'border-primary bg-primary text-primary-foreground shadow-sm' : 'bg-white text-slate-600 hover:bg-slate-50',
            )}
          >
            {p.texto}
          </button>
        ))}
      </div>

      {pestana === 'cobrar' && <PestanaCobrar ci={ci} onElegir={setCi} />}
      {pestana === 'aranceles' && <PestanaAranceles />}
      {pestana === 'becas' && <PestanaBecas />}
      {pestana === 'cuotas' && <PestanaGenerarCuotas />}
      {pestana === 'morosos' && (
        <PestanaMorosos
          onCobrar={(ciMoroso) => {
            setCi(ciMoroso)
            setPestana('cobrar')
          }}
        />
      )}
    </div>
  )
}

// ---------- Cobrar ----------

function PestanaCobrar({ ci, onElegir }: { ci: string | null; onElegir: (ci: string) => void }) {
  const [texto, setTexto] = useState('')
  const buscar = useRetardo(texto.trim())
  const estudiantes = useEstudiantesPago(buscar)

  return (
    <div className="grid gap-4 lg:grid-cols-[360px_1fr]">
      <div className="space-y-3 rounded-xl border bg-white p-3 shadow-sm lg:self-start">
        <div className="relative">
          <SearchIcon className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" />
          <Input className="pl-9" placeholder="Buscar por nombre o C.I." value={texto} onChange={(e) => setTexto(e.target.value)} />
        </div>
        {estudiantes.isLoading || estudiantes.isError ? (
          <Cargando consulta={estudiantes} />
        ) : !estudiantes.data?.estudiantes.length ? (
          <p className="py-6 text-center text-sm text-slate-500">
            {estudiantes.data?.gestion ? 'No se encontraron estudiantes.' : 'No hay una gestión abierta.'}
          </p>
        ) : (
          <ul className="max-h-[560px] space-y-1 overflow-y-auto">
            {estudiantes.data.estudiantes.map((e) => (
              <li key={e.ci}>
                <button
                  onClick={() => onElegir(e.ci)}
                  className={cn(
                    'flex w-full items-center justify-between gap-2 rounded-lg px-3 py-2 text-left transition-colors hover:bg-slate-50',
                    e.ci === ci && 'bg-blue-50 ring-1 ring-blue-200 hover:bg-blue-50',
                  )}
                >
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-medium text-slate-900">{e.apellidos}, {e.nombre_persona}</span>
                    <span className="block truncate text-xs text-slate-500">C.I. {e.ci} · {e.curso}</span>
                  </span>
                  {e.atrasadas > 0 ? (
                    <Chip clase="bg-rose-50 text-rose-700 ring-rose-200">{e.atrasadas} atrasada{e.atrasadas > 1 ? 's' : ''}</Chip>
                  ) : e.pendientes > 0 ? (
                    <Chip clase="bg-amber-50 text-amber-700 ring-amber-200">{e.pendientes} pendiente{e.pendientes > 1 ? 's' : ''}</Chip>
                  ) : (
                    <Chip clase="bg-emerald-50 text-emerald-700 ring-emerald-200">Al día</Chip>
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      {ci ? <CuentaAdministrador key={ci} ci={ci} /> : <Vacio texto="Busque y elija un estudiante para ver sus cuotas." />}
    </div>
  )
}

function Chip({ clase, children }: { clase: string; children: ReactNode }) {
  return <span className={cn('shrink-0 rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset', clase)}>{children}</span>
}

type Correccion = { cuota: Cuota; accion: 'revertir' | 'anular' }

function CuentaAdministrador({ ci }: { ci: string }) {
  const cuenta = useEstadoCuenta(ci)
  const [cobro, setCobro] = useState<Cuota | null>(null)
  const [correccion, setCorreccion] = useState<Correccion | null>(null)
  const [recibo, setRecibo] = useState<{ id_pago: number; datos?: Recibo } | null>(null)

  if (!cuenta.data) return <Cargando consulta={cuenta} />
  return (
    <div className="space-y-4">
      <ResumenCuenta cuenta={cuenta.data} />
      <TablaCuotas
        cuotas={cuenta.data.cuotas}
        acciones={(c) =>
          c.estado_pago === 'pendiente' ? (
            <>
              <Button size="sm" onClick={() => setCobro(c)}><CoinsIcon /> Cobrar</Button>
              <BotonAccion etiqueta="Anular cuota" tono="rojo" onClick={() => setCorreccion({ cuota: c, accion: 'anular' })}>
                <BanIcon />
              </BotonAccion>
            </>
          ) : c.estado_pago === 'pagado' ? (
            <>
              <BotonAccion etiqueta="Ver recibo" tono="azul" onClick={() => setRecibo({ id_pago: c.id_pago })}>
                <ReceiptTextIcon />
              </BotonAccion>
              <BotonAccion etiqueta="Revertir cobro" tono="ambar" onClick={() => setCorreccion({ cuota: c, accion: 'revertir' })}>
                <Undo2Icon />
              </BotonAccion>
            </>
          ) : null
        }
      />
      {cobro && (
        <DialogoCobro
          cuota={cobro}
          cuenta={cuenta.data}
          onCerrar={() => setCobro(null)}
          onCobrado={(datos) => {
            setCobro(null)
            setRecibo({ id_pago: datos.id_pago, datos })
          }}
        />
      )}
      {correccion && <DialogoCorreccion correccion={correccion} onCerrar={() => setCorreccion(null)} />}
      {recibo && <DialogoRecibo id_pago={recibo.id_pago} inicial={recibo.datos} onCerrar={() => setRecibo(null)} />}
    </div>
  )
}

function ResumenCuenta({ cuenta }: { cuenta: EstadoCuenta }) {
  const e = cuenta.estudiante
  return (
    <div className="flex flex-col gap-3 rounded-xl border bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="font-semibold text-slate-900">{e.apellidos}, {e.nombre_persona}</p>
        <p className="text-sm text-slate-500">C.I. {e.ci}{e.curso ? ` · ${e.curso}` : ''}</p>
      </div>
      <div className="flex gap-6 text-sm">
        <div>
          <p className="text-slate-500">Atrasado</p>
          <p className={cn('text-lg font-bold', cuenta.total_atrasado ? 'text-rose-700' : 'text-slate-400')}>{bs(cuenta.total_atrasado)}</p>
        </div>
        <div>
          <p className="text-slate-500">Total pendiente</p>
          <p className="text-lg font-bold text-slate-900">{bs(cuenta.total_pendiente)}</p>
        </div>
      </div>
    </div>
  )
}

/** Cuotas agrupadas por gestión. "acciones" pone los botones de cada fila (solo lectura si no se indica). */
function TablaCuotas({ cuotas, acciones }: { cuotas: Cuota[]; acciones: (c: Cuota) => ReactNode }) {
  const porGestion = useMemo(() => [...new Set(cuotas.map((c) => c.anio))].map((anio) => ({
    anio,
    cuotas: cuotas.filter((c) => c.anio === anio),
  })), [cuotas])

  if (!cuotas.length) return <Vacio texto="Todavía no tiene cuotas generadas." />
  return (
    <>
      {porGestion.map((g) => (
        <div key={g.anio} className="rounded-xl border bg-white shadow-sm">
          <p className="border-b px-4 py-2.5 text-sm font-semibold text-slate-700">Gestión {g.anio}</p>
          <Table>
            <TableHeader>
              <TableRow className="bg-slate-50">
                <TableHead className="pl-4">Mes</TableHead>
                <TableHead>Vence</TableHead>
                <TableHead className="text-right">Monto</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Recibo</TableHead>
                <TableHead className="pr-4 text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {g.cuotas.map((c) => (
                <TableRow key={c.id_pago} className={cn(c.estado_actual === 'anulado' && 'text-slate-400')}>
                  <TableCell className="pl-4 align-top">
                    <p className="font-medium">{MESES[c.mes - 1]}</p>
                    {c.observacion_pago && (
                      <p className="max-w-64 text-xs whitespace-pre-line text-slate-500">{c.observacion_pago}</p>
                    )}
                  </TableCell>
                  <TableCell className="align-top">{formatoFecha(c.fecha_vencimiento)}</TableCell>
                  <TableCell className="text-right align-top">
                    <p className="font-medium">{bs(c.monto)}</p>
                    {c.descuento_aplicado > 0 && <p className="text-xs text-emerald-700">Beca: −{bs(c.descuento_aplicado)}</p>}
                  </TableCell>
                  <TableCell className="align-top">
                    <Chip clase={ESTILO_CUOTA[c.estado_actual].clase}>{ESTILO_CUOTA[c.estado_actual].etiqueta}</Chip>
                    {c.dias_atraso > 0 && <p className="mt-1 text-xs text-rose-600">{c.dias_atraso} días de atraso</p>}
                  </TableCell>
                  <TableCell className="align-top">
                    {c.numero_recibo ? (
                      <>
                        <p className="font-mono text-xs">N° {nroRecibo(c.numero_recibo)}</p>
                        <p className="text-xs text-slate-500">
                          {formatoFecha(c.fecha_pago)} · {c.metodo_pago ? ETIQUETA_METODO[c.metodo_pago] : ''}
                        </p>
                      </>
                    ) : '—'}
                  </TableCell>
                  <TableCell className="pr-4 align-top">
                    <div className="flex justify-end gap-1.5">{acciones(c)}</div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ))}
    </>
  )
}

const SIN_TUTOR = 'ninguno'

function DialogoCobro({
  cuota, cuenta, onCerrar, onCobrado,
}: {
  cuota: Cuota
  cuenta: EstadoCuenta
  onCerrar: () => void
  onCobrado: (recibo: Recibo) => void
}) {
  const cobrar = useCobrar()
  const [metodo, setMetodo] = useState<MetodoPago>('efectivo')
  const [tutor, setTutor] = useState(cuenta.tutores[0]?.ci ?? SIN_TUTOR)

  const enviar = async () => {
    try {
      const recibo = await cobrar.mutateAsync({
        id_pago: cuota.id_pago,
        datos: { metodo_pago: metodo, ci_tutor: tutor === SIN_TUTOR ? null : tutor },
      })
      toast.success(`Cuota de ${MESES[cuota.mes - 1]} cobrada. Recibo N° ${nroRecibo(recibo.numero_recibo)}.`)
      onCobrado(recibo)
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  return (
    <Dialog open onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Cobrar mensualidad</DialogTitle>
          <DialogDescription>
            {cuenta.estudiante.apellidos}, {cuenta.estudiante.nombre_persona} · {MESES[cuota.mes - 1]} {cuota.anio}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-1.5 rounded-lg bg-slate-50 p-3 text-sm">
          <Linea texto="Monto mensual" valor={bs(cuota.monto + cuota.descuento_aplicado)} />
          {cuota.descuento_aplicado > 0 && <Linea texto="Descuento por beca" valor={`−${bs(cuota.descuento_aplicado)}`} />}
          <Linea texto="Total a cobrar" valor={bs(cuota.monto)} fuerte />
          {cuota.estado_actual === 'atrasado' && (
            <p className="flex items-center gap-1.5 pt-1 text-xs text-rose-600">
              <TriangleAlertIcon className="size-3.5" /> Venció el {formatoFecha(cuota.fecha_vencimiento)} ({cuota.dias_atraso} días de atraso).
            </p>
          )}
        </div>
        <Campo etiqueta="Pagado por">
          <Select value={tutor} onValueChange={setTutor}>
            <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
            <SelectContent>
              {cuenta.tutores.map((t) => (
                <SelectItem key={t.ci} value={t.ci}>
                  {t.nombre_persona} {t.apellidos} ({t.parentesco}){t.es_responsable_pago ? ' · responsable de pago' : ''}
                </SelectItem>
              ))}
              {!cuenta.tutores.length && <SelectItem value={SIN_TUTOR}>Sin tutor registrado</SelectItem>}
            </SelectContent>
          </Select>
        </Campo>
        <Campo etiqueta="Método de pago">
          <Select value={metodo} onValueChange={(v) => setMetodo(v as MetodoPago)}>
            <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
            <SelectContent>
              {METODOS_PAGO.map((m) => <SelectItem key={m} value={m}>{ETIQUETA_METODO[m]}</SelectItem>)}
            </SelectContent>
          </Select>
        </Campo>
        <DialogFooter>
          <Button variant="outline" onClick={onCerrar}>Cancelar</Button>
          <Button onClick={enviar} disabled={cobrar.isPending}>
            <CoinsIcon /> {cobrar.isPending ? 'Cobrando...' : `Cobrar ${bs(cuota.monto)}`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function Linea({ texto, valor, fuerte }: { texto: string; valor: string; fuerte?: boolean }) {
  return (
    <div className={cn('flex justify-between gap-4', fuerte && 'border-t pt-1.5 font-semibold text-slate-900')}>
      <span className={cn(!fuerte && 'text-slate-600')}>{texto}</span>
      <span>{valor}</span>
    </div>
  )
}

function DialogoCorreccion({ correccion, onCerrar }: { correccion: Correccion; onCerrar: () => void }) {
  const corregir = useCorregirCuota()
  const { cuota, accion } = correccion
  const revertir = accion === 'revertir'
  const form = useForm<DatosMotivo>({ resolver: zodResolver(esquemaMotivo), defaultValues: { motivo: '' } })
  const enviar = form.handleSubmit(async ({ motivo }) => {
    try {
      await corregir.mutateAsync({ id_pago: cuota.id_pago, accion, motivo })
      toast.success(revertir ? `Cobro de ${MESES[cuota.mes - 1]} revertido: la cuota vuelve a pendiente.` : `Cuota de ${MESES[cuota.mes - 1]} anulada.`)
      onCerrar()
    } catch (e) {
      toast.error(mensajeError(e))
    }
  })

  return (
    <Dialog open onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{revertir ? 'Revertir cobro' : 'Anular cuota'} · {MESES[cuota.mes - 1]} {cuota.anio}</DialogTitle>
          <DialogDescription>
            {revertir
              ? `Para corregir un cobro mal hecho. La cuota vuelve a pendiente y el recibo N° ${nroRecibo(cuota.numero_recibo ?? 0)} queda anulado (su número no se reutiliza).`
              : 'Para dar de baja una cuota que ya no corresponde (ej. retiro del estudiante). No se puede deshacer.'}
          </DialogDescription>
        </DialogHeader>
        <form id="form-correccion" noValidate onSubmit={enviar}>
          <Campo etiqueta="Motivo" htmlFor="motivo" error={form.formState.errors.motivo?.message}>
            <Textarea id="motivo" rows={3} maxLength={300} autoFocus
              placeholder={revertir ? 'Ej.: se registró con el método de pago equivocado' : 'Ej.: el estudiante se retiró en agosto'}
              {...form.register('motivo')} />
          </Campo>
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={onCerrar}>Cancelar</Button>
          <Button type="submit" form="form-correccion" variant={revertir ? 'default' : 'destructive'} disabled={corregir.isPending}>
            {revertir ? <><Undo2Icon /> Revertir cobro</> : <><BanIcon /> Anular cuota</>}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ---------- Recibo de pago ----------

/** Al imprimir solo se muestra el recibo (el resto de la página queda oculto). */
const ESTILO_IMPRESION = `@media print {
  body * { visibility: hidden !important; }
  #recibo-pago, #recibo-pago * { visibility: visible !important; }
  #recibo-pago { position: fixed; top: 0; left: 0; width: 100%; border: none; }
}`

function DialogoRecibo({ id_pago, inicial, onCerrar }: { id_pago: number; inicial?: Recibo; onCerrar: () => void }) {
  const consulta = useRecibo(inicial ? null : id_pago)
  const recibo = inicial ?? consulta.data
  return (
    <Dialog open onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Recibo de pago</DialogTitle>
          <DialogDescription>Comprobante interno del pago de la mensualidad.</DialogDescription>
        </DialogHeader>
        {recibo ? <ReciboImprimible recibo={recibo} /> : <Cargando consulta={consulta} />}
        <DialogFooter>
          <Button variant="outline" onClick={onCerrar}>Cerrar</Button>
          <Button onClick={() => window.print()} disabled={!recibo}><PrinterIcon /> Imprimir</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function ReciboImprimible({ recibo: r }: { recibo: Recibo }) {
  return (
    <div id="recibo-pago" className="space-y-3 rounded-lg border bg-white p-5 text-sm text-slate-800">
      <style>{ESTILO_IMPRESION}</style>
      <div className="flex items-center justify-between gap-3 border-b pb-3">
        <div className="flex items-center gap-3">
          <Escudo className="size-12" />
          <div className="leading-tight">
            <p className="text-xs text-slate-500">Unidad Educativa</p>
            <p className="font-semibold text-[#12306B]">“Mariscal Sucre G”</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs font-semibold tracking-wide text-slate-500 uppercase">Recibo de pago</p>
          <p className="font-mono text-lg font-bold">N° {nroRecibo(r.numero_recibo)}</p>
          <p className="text-xs text-slate-500">Fecha: {formatoFecha(r.fecha_pago)}</p>
        </div>
      </div>
      <div className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
        <span className="text-slate-500">Estudiante:</span><span>{r.estudiante} · C.I. {r.ci_estudiante}</span>
        <span className="text-slate-500">Curso:</span><span>{r.curso ?? '—'} · Gestión {r.gestion}</span>
        <span className="text-slate-500">Concepto:</span><span>Mensualidad de {MESES[r.mes - 1].toLowerCase()} {r.gestion}</span>
      </div>
      <div className="space-y-1 rounded-md bg-slate-50 p-3">
        <Linea texto="Monto mensual" valor={bs(r.monto_mensual)} />
        {r.descuento > 0 && <Linea texto={`Descuento (beca ${r.porcentaje_beca} %)`} valor={`−${bs(r.descuento)}`} />}
        <Linea texto="TOTAL PAGADO" valor={bs(r.total)} fuerte />
      </div>
      <div className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
        <span className="text-slate-500">Método:</span><span>{ETIQUETA_METODO[r.metodo_pago]}</span>
        <span className="text-slate-500">Pagado por:</span><span>{r.tutor ? `${r.tutor}${r.parentesco ? ` (${r.parentesco})` : ''}` : '—'}</span>
        <span className="text-slate-500">Cobrado por:</span><span>{r.cajero}{r.cargo ? ` (${r.cargo})` : ''}</span>
      </div>
      <p className="border-t pt-2 text-center text-xs text-slate-500">Comprobante interno – no válido como factura</p>
    </div>
  )
}

// ---------- Aranceles ----------

function PestanaAranceles() {
  const aranceles = useAranceles()
  const [edicion, setEdicion] = useState<ArancelNivel | null>(null)
  if (!aranceles.data) return <Cargando consulta={aranceles} />
  if (!aranceles.data.gestion) return <Vacio texto="No hay una gestión abierta." />
  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-500">
        Monto mensual por nivel en la gestión {aranceles.data.gestion}. Un cambio rige para las cuotas que se generen después.
      </p>
      <div className="rounded-xl border bg-white shadow-sm">
        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50">
              <TableHead className="pl-4">Nivel</TableHead>
              <TableHead className="text-right">Monto mensual</TableHead>
              <TableHead className="text-center">Vence el día</TableHead>
              <TableHead className="pr-4 text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!aranceles.data.niveles.length ? (
              <FilaMensaje columnas={4} mensaje="No hay niveles educativos registrados." />
            ) : (
              aranceles.data.niveles.map((n) => (
                <TableRow key={n.id_nivel}>
                  <TableCell className="pl-4 font-medium">{n.nivel}</TableCell>
                  <TableCell className="text-right">
                    {n.monto_mensual === null ? <Chip clase="bg-amber-50 text-amber-700 ring-amber-200">Sin arancel</Chip> : bs(n.monto_mensual)}
                  </TableCell>
                  <TableCell className="text-center">{n.dia_vencimiento ?? '—'}</TableCell>
                  <TableCell className="pr-4 text-right">
                    <Button size="sm" variant="outline" onClick={() => setEdicion(n)}>
                      {n.id_arancel ? <><PencilIcon /> Modificar</> : <><PlusIcon /> Registrar</>}
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      {edicion && <DialogoArancel nivel={edicion} onCerrar={() => setEdicion(null)} />}
    </div>
  )
}

function DialogoFormulario({
  titulo, descripcion, ocupado, onCerrar, onGuardar, children,
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
          id="form-cu25"
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
          <Button type="submit" form="form-cu25" disabled={ocupado}>Guardar</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/** Guarda, avisa y cierra; si el backend rechaza, muestra su mensaje y deja el diálogo abierto. */
async function guardarYCerrar(guardar: () => Promise<unknown>, exito: string, onCerrar: () => void) {
  try {
    await guardar()
    toast.success(exito)
    onCerrar()
  } catch (e) {
    toast.error(mensajeError(e))
  }
}

function DialogoArancel({ nivel, onCerrar }: { nivel: ArancelNivel; onCerrar: () => void }) {
  const guardar = useGuardarArancel()
  const form = useForm<DatosArancel>({
    resolver: zodResolver(esquemaArancel),
    defaultValues: { monto_mensual: nivel.monto_mensual ?? undefined, dia_vencimiento: nivel.dia_vencimiento ?? 10 },
  })
  const e = form.formState.errors
  const enviar = form.handleSubmit((datos) =>
    guardarYCerrar(
      () => guardar.mutateAsync({ id_arancel: nivel.id_arancel, id_nivel: nivel.id_nivel, datos }),
      `Arancel de ${nivel.nivel} ${nivel.id_arancel ? 'actualizado' : 'registrado'}.`,
      onCerrar,
    ),
  )
  return (
    <DialogoFormulario
      titulo={`Arancel de ${nivel.nivel}`}
      descripcion="Rige para las cuotas que se generen después; las ya generadas no cambian."
      ocupado={guardar.isPending}
      onCerrar={onCerrar}
      onGuardar={enviar}
    >
      <Campo etiqueta="Monto mensual (Bs)" htmlFor="monto_mensual" error={e.monto_mensual?.message}>
        <Input id="monto_mensual" type="number" min={1} step="0.01" autoFocus {...form.register('monto_mensual', { valueAsNumber: true })} />
      </Campo>
      <Campo etiqueta="Día de vencimiento (1 a 28)" htmlFor="dia_vencimiento" error={e.dia_vencimiento?.message}>
        <Input id="dia_vencimiento" type="number" min={1} max={28} {...form.register('dia_vencimiento', { valueAsNumber: true })} />
      </Campo>
    </DialogoFormulario>
  )
}

// ---------- Becas ----------

function PestanaBecas() {
  const becas = useBecas()
  const [edicion, setEdicion] = useState<{ beca?: Beca } | null>(null)
  if (!becas.data) return <Cargando consulta={becas} />
  if (!becas.data.gestion) return <Vacio texto="No hay una gestión abierta." />
  return (
    <div className="space-y-3">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-slate-500">
          Descuento por estudiante en la gestión {becas.data.gestion}. Con beca del 100 % no se generan cuotas.
        </p>
        <Button onClick={() => setEdicion({})}><PlusIcon /> Nueva beca</Button>
      </div>
      <div className="rounded-xl border bg-white shadow-sm">
        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50">
              <TableHead className="pl-4">Estudiante</TableHead>
              <TableHead>Curso</TableHead>
              <TableHead className="text-right">Descuento</TableHead>
              <TableHead>Motivo</TableHead>
              <TableHead className="pr-4 text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!becas.data.becas.length ? (
              <FilaMensaje columnas={5} mensaje="No hay becas registradas en esta gestión." />
            ) : (
              becas.data.becas.map((b) => (
                <TableRow key={b.id_beca}>
                  <TableCell className="pl-4">
                    <p className="font-medium">{b.apellidos}, {b.nombre_persona}</p>
                    <p className="text-xs text-slate-500">C.I. {b.ci_estudiante}</p>
                  </TableCell>
                  <TableCell>{b.curso ?? '—'}</TableCell>
                  <TableCell className="text-right font-semibold text-emerald-700">{b.porcentaje_descuento} %</TableCell>
                  <TableCell className="whitespace-normal text-slate-600">{b.motivo_beca ?? '—'}</TableCell>
                  <TableCell className="pr-4">
                    <div className="flex justify-end">
                      <BotonAccion etiqueta="Modificar beca" tono="azul" onClick={() => setEdicion({ beca: b })}><PencilIcon /></BotonAccion>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      {edicion && <DialogoBeca beca={edicion.beca} onCerrar={() => setEdicion(null)} />}
    </div>
  )
}

function DialogoBeca({ beca, onCerrar }: { beca?: Beca; onCerrar: () => void }) {
  const guardar = useGuardarBeca()
  const estudiantes = useEstudiantesPago('')
  const form = useForm<DatosBeca>({
    resolver: zodResolver(esquemaBeca),
    defaultValues: {
      ci_estudiante: beca?.ci_estudiante ?? '',
      porcentaje_descuento: beca?.porcentaje_descuento,
      motivo_beca: beca?.motivo_beca ?? '',
    },
  })
  const e = form.formState.errors
  const enviar = form.handleSubmit(({ ci_estudiante, porcentaje_descuento, motivo_beca }) =>
    guardarYCerrar(
      () => guardar.mutateAsync({
        id_beca: beca?.id_beca,
        datos: { ...(beca ? {} : { ci_estudiante }), porcentaje_descuento, motivo_beca: motivo_beca || null },
      }),
      beca ? 'Beca actualizada.' : 'Beca registrada.',
      onCerrar,
    ),
  )
  return (
    <DialogoFormulario
      titulo={beca ? 'Modificar beca' : 'Nueva beca'}
      descripcion="Rige para las cuotas que se generen después; las ya generadas no cambian."
      ocupado={guardar.isPending}
      onCerrar={onCerrar}
      onGuardar={enviar}
    >
      <Campo etiqueta="Estudiante" error={e.ci_estudiante?.message}>
        {beca ? (
          <Input disabled value={`${beca.apellidos}, ${beca.nombre_persona}`} />
        ) : (
          <Select value={form.watch('ci_estudiante')} onValueChange={(v) => form.setValue('ci_estudiante', v, { shouldValidate: true })}>
            <SelectTrigger className="w-full"><SelectValue placeholder="Elija un estudiante inscrito" /></SelectTrigger>
            <SelectContent>
              {estudiantes.data?.estudiantes.map((x) => (
                <SelectItem key={x.ci} value={x.ci}>{x.apellidos}, {x.nombre_persona} · {x.curso}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </Campo>
      <Campo etiqueta="Porcentaje de descuento" htmlFor="porcentaje_descuento" error={e.porcentaje_descuento?.message}>
        <Input id="porcentaje_descuento" type="number" min={1} max={100} step="0.01"
          {...form.register('porcentaje_descuento', { valueAsNumber: true })} />
      </Campo>
      <Campo etiqueta="Motivo (opcional)" htmlFor="motivo_beca" error={e.motivo_beca?.message}>
        <Input id="motivo_beca" maxLength={150} placeholder="Ej.: rendimiento académico" {...form.register('motivo_beca')} />
      </Campo>
    </DialogoFormulario>
  )
}

// ---------- Generar cuotas ----------

function PestanaGenerarCuotas() {
  const generar = useGenerarCuotas()
  const [mes, setMes] = useState(String(new Date().getMonth() + 1))
  const [confirmar, setConfirmar] = useState(false)
  const [resultado, setResultado] = useState<string | null>(null)
  const nombreMes = MESES[Number(mes) - 1]

  const enviar = async () => {
    setConfirmar(false)
    try {
      const r = await generar.mutateAsync(Number(mes))
      const texto = r.cuotas_creadas
        ? `Se generaron ${r.cuotas_creadas} cuotas de ${nombreMes} ${r.gestion}.`
        : `Las cuotas de ${nombreMes} ${r.gestion} ya estaban generadas: no se creó ninguna nueva.`
      setResultado(texto)
      toast.success(texto)
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  return (
    <div className="max-w-xl space-y-4 rounded-xl border bg-white p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
          <CalendarPlusIcon className="size-5" />
        </span>
        <p className="text-sm text-slate-600">
          Crea la cuota del mes para cada estudiante con inscripción activa, según el arancel de su nivel y su beca.
          Las cuotas ya generadas no se duplican y con beca del 100 % no se genera cuota.
        </p>
      </div>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <Campo etiqueta="Mes" className="sm:w-56">
          <Select value={mes} onValueChange={(v) => { setMes(v); setResultado(null) }}>
            <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
            <SelectContent>
              {MESES.map((m, i) => <SelectItem key={m} value={String(i + 1)}>{m}</SelectItem>)}
            </SelectContent>
          </Select>
        </Campo>
        <Button onClick={() => setConfirmar(true)} disabled={generar.isPending}>
          <CalendarPlusIcon /> {generar.isPending ? 'Generando...' : `Generar cuotas de ${nombreMes}`}
        </Button>
      </div>
      {resultado && <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{resultado}</p>}
      <Confirmar
        abierto={confirmar}
        onCambiar={setConfirmar}
        titulo={`Generar cuotas de ${nombreMes}`}
        descripcion="Se creará la cuota del mes para todos los estudiantes inscritos que todavía no la tengan."
        textoConfirmar="Generar"
        icono={<CalendarPlusIcon />}
        onConfirmar={enviar}
      />
    </div>
  )
}

// ---------- Morosos ----------

function PestanaMorosos({ onCobrar }: { onCobrar: (ci: string) => void }) {
  const morosos = useMorosos()
  if (!morosos.data) return <Cargando consulta={morosos} />
  const lista = morosos.data.morosos
  return (
    <div className="space-y-3">
      <div className="flex flex-col gap-3 rounded-xl border bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <span className="inline-flex size-10 items-center justify-center rounded-lg bg-rose-50 text-rose-600">
            <WalletIcon className="size-5" />
          </span>
          <div>
            <p className="text-sm text-slate-500">{lista.length} estudiantes con cuotas atrasadas</p>
            <p className="text-2xl font-bold text-rose-700">{bs(morosos.data.total_deuda)}</p>
          </div>
        </div>
      </div>
      <div className="rounded-xl border bg-white shadow-sm">
        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50">
              <TableHead className="pl-4">Estudiante</TableHead>
              <TableHead>Cuotas atrasadas</TableHead>
              <TableHead className="text-right">Deuda</TableHead>
              <TableHead className="text-center">Atraso</TableHead>
              <TableHead>Tutor responsable</TableHead>
              <TableHead className="pr-4 text-right">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!lista.length ? (
              <FilaMensaje columnas={6} mensaje="No hay cuotas atrasadas." />
            ) : (
              lista.map((m) => (
                <TableRow key={m.ci_estudiante}>
                  <TableCell className="pl-4">
                    <p className="font-medium">{m.estudiante}</p>
                    <p className="text-xs text-slate-500">C.I. {m.ci_estudiante}{m.curso ? ` · ${m.curso}` : ''}</p>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {m.cuotas.map((c) => (
                        <span key={c.id_pago} className="rounded bg-rose-50 px-1.5 py-0.5 text-[11px] text-rose-700">
                          {MESES[c.mes - 1].slice(0, 3)} {c.anio}
                        </span>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-semibold text-rose-700">{bs(m.deuda)}</TableCell>
                  <TableCell className="text-center text-sm">{m.dias_atraso} días</TableCell>
                  <TableCell>
                    <p className="text-sm">{m.tutor ?? '—'}</p>
                    {m.telefono && (
                      <p className="flex items-center gap-1 text-xs text-slate-500"><PhoneIcon className="size-3" /> {m.telefono}</p>
                    )}
                  </TableCell>
                  <TableCell className="pr-4 text-right">
                    <Button size="sm" variant="outline" onClick={() => onCobrar(m.ci_estudiante)}><CoinsIcon /> Cobrar</Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}

// ------------------------------------------------------------
// Tutor y estudiante: sus cuotas (solo lectura)
// ------------------------------------------------------------

function PantallaMisCuotas() {
  const { usuario } = useSesion()
  const cuentas = useMisCuotas()
  const enLinea = useEstadoPagoEnLinea().data?.habilitado ?? false
  const [ci, setCi] = useState<string | null>(null)
  const [recibo, setRecibo] = useState<{ id_pago: number; datos?: Recibo } | null>(null)
  const [aPagar, setAPagar] = useState<Cuota | null>(null)
  useRetornoDePago((datos) => setRecibo({ id_pago: datos.id_pago, datos }))

  const lista = cuentas.data ?? []
  const cuenta = lista.find((c) => c.estudiante.ci === ci) ?? lista[0]

  return (
    <div className="space-y-5">
      <EncabezadoPagina
        titulo={usuario?.rol === 'estudiante' ? 'Mis pagos' : 'Pagos de mensualidad'}
        descripcion={enLinea ? 'Cuotas de la mensualidad: pague en línea las pendientes o vea los recibos de las pagadas.'
          : 'Cuotas de la mensualidad y recibos de las que ya se pagaron.'}
      />
      {!cuentas.data ? (
        <Cargando consulta={cuentas} />
      ) : !cuenta ? (
        <Vacio texto="No hay estudiantes con cuotas para mostrar." />
      ) : (
        <>
          {lista.length > 1 && (
            <div className="flex flex-wrap gap-2" role="tablist">
              {lista.map((c) => (
                <button
                  key={c.estudiante.ci}
                  role="tab"
                  aria-selected={c === cuenta}
                  onClick={() => setCi(c.estudiante.ci)}
                  className={cn(
                    'rounded-lg border px-4 py-2 text-left text-sm transition-colors',
                    c === cuenta ? 'border-primary bg-primary text-primary-foreground shadow-sm' : 'bg-white text-slate-600 hover:bg-slate-50',
                  )}
                >
                  <span className="block font-medium">{c.estudiante.nombre_persona} {c.estudiante.apellidos}</span>
                  <span className="block text-xs opacity-75">{c.estudiante.curso}</span>
                </button>
              ))}
            </div>
          )}
          <ResumenCuenta cuenta={cuenta} />
          <TablaCuotas
            cuotas={cuenta.cuotas}
            acciones={(c) =>
              c.estado_pago === 'pagado' ? (
                <Button size="sm" variant="outline" onClick={() => setRecibo({ id_pago: c.id_pago })}><ReceiptTextIcon /> Recibo</Button>
              ) : c.estado_pago === 'pendiente' && enLinea ? (
                <Button size="sm" onClick={() => setAPagar(c)}><CreditCardIcon /> Pagar en línea</Button>
              ) : null
            }
          />
        </>
      )}
      {aPagar && cuenta && <DialogoPagoEnLinea cuota={aPagar} cuenta={cuenta} onCerrar={() => setAPagar(null)} />}
      {recibo && <DialogoRecibo id_pago={recibo.id_pago} inicial={recibo.datos} onCerrar={() => setRecibo(null)} />}
    </div>
  )
}

/** Al volver de Stripe (?pago=exito&id_sesion=...): se confirma el pago una sola vez y se limpia la dirección. */
function useRetornoDePago(onPagado: (recibo: Recibo) => void) {
  const [parametros, setParametros] = useSearchParams()
  const confirmar = useConfirmarPagoEnLinea()
  const atendido = useRef(false)
  const pago = parametros.get('pago')
  const idSesion = parametros.get('id_sesion')

  useEffect(() => {
    if (!pago || atendido.current) return
    atendido.current = true
    setParametros({}, { replace: true })
    if (pago === 'cancelado') {
      toast.info('Pago cancelado: no se cobró nada.')
      return
    }
    if (pago === 'exito' && idSesion) {
      confirmar
        .mutateAsync(idSesion)
        .then((r) => {
          toast.success(`Pago registrado. Recibo N° ${nroRecibo(r.numero_recibo)}.`)
          onPagado(r)
        })
        .catch((e) => toast.error(mensajeError(e)))
    }
  }, [pago, idSesion, confirmar, onPagado, setParametros])
}

function DialogoPagoEnLinea({ cuota, cuenta, onCerrar }: { cuota: Cuota; cuenta: EstadoCuenta; onCerrar: () => void }) {
  const iniciar = useIniciarPagoEnLinea()
  const irAPagar = async () => {
    try {
      const { url } = await iniciar.mutateAsync(cuota.id_pago)
      window.location.assign(url)
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }
  return (
    <Dialog open onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Pagar en línea</DialogTitle>
          <DialogDescription>
            {cuenta.estudiante.apellidos}, {cuenta.estudiante.nombre_persona} · {MESES[cuota.mes - 1]} {cuota.anio}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-1.5 rounded-lg bg-slate-50 p-3 text-sm">
          <Linea texto="Monto mensual" valor={bs(cuota.monto + cuota.descuento_aplicado)} />
          {cuota.descuento_aplicado > 0 && <Linea texto="Descuento por beca" valor={`−${bs(cuota.descuento_aplicado)}`} />}
          <Linea texto="Total a pagar" valor={bs(cuota.monto)} fuerte />
        </div>
        <div className="flex gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
          <TriangleAlertIcon className="size-4 shrink-0" />
          <p>
            <b>Modo de prueba:</b> no se cobra dinero real. En la página de Stripe use la tarjeta{' '}
            <b>4242 4242 4242 4242</b>, cualquier fecha futura y cualquier código de seguridad.
          </p>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onCerrar}>Cancelar</Button>
          <Button onClick={irAPagar} disabled={iniciar.isPending}>
            <CreditCardIcon /> {iniciar.isPending ? 'Abriendo Stripe...' : `Pagar ${bs(cuota.monto)}`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

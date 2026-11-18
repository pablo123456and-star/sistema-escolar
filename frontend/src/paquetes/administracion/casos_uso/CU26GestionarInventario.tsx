/**
 * CU26 - Gestionar inventario (registrar, actualizar, consultar bienes)
 * Paquete: administracion
 *
 * Actores ........: Administrativo
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/administracion/casos_uso/cu26_gestionar_inventario.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  Sesión iniciada como administrador. Para una salida: hay stock suficiente.
 * Postcondición: El bien queda registrado y su stock se actualiza con cada movimiento.
 *
 * Pantalla: ruta /administracion/inventario
 * - Resumen (bienes, stock bajo, sin stock) que también filtra la tabla, y buscador.
 * - Tabla de bienes con su stock y estado; acciones: Entrada, Salida, Historial, Editar y Eliminar
 *   (eliminar solo si el bien no tiene movimientos).
 * - La cantidad nunca se edita: cambia solo con entradas y salidas (el backend calcula el estado
 *   "stock bajo" con el stock mínimo de cada bien).
 *
 * Estado: IMPLEMENTADO.
 */
import { useEffect, useState, type ReactNode } from 'react'
import { Controller, useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import {
  AlertTriangleIcon,
  ArrowDownToLineIcon,
  ArrowUpFromLineIcon,
  HistoryIcon,
  Loader2Icon,
  PackageIcon,
  PackageXIcon,
  PencilIcon,
  PlusIcon,
  SearchIcon,
  Trash2Icon,
} from 'lucide-react'
import { cn } from 'cn'
import Confirmar from '@/componentes/Confirmar'
import { BotonAccion, Campo, EncabezadoPagina, FilaMensaje } from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Card, CardContent } from '@/componentes/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/componentes/ui/dialog'
import { Input } from '@/componentes/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { Textarea } from '@/componentes/ui/textarea'
import { fechaHora } from '@/lib/formato'
import { useRetardo } from '@/lib/useRetardo'
import { mensajeError } from '@/nucleo/api'
import {
  useActualizarBien,
  useEliminarBien,
  useInventario,
  useMovimientos,
  useRegistrarBien,
  useRegistrarMovimiento,
} from '../api'
import {
  esquemaBien,
  esquemaMovimiento,
  type Bien,
  type DatosBien,
  type DatosMovimiento,
  type EstadoStock,
  type TipoMovimiento,
} from '../schemas'

const TODOS = 'todos'

export default function CU26GestionarInventario() {
  const [texto, setTexto] = useState('')
  const [estado, setEstado] = useState<EstadoStock | ''>('')
  const buscar = useRetardo(texto.trim())
  const { data, isLoading, isError, error } = useInventario(buscar, estado)
  // Totales sin filtro de estado para el resumen (misma búsqueda)
  const { data: resumen } = useInventario(buscar, '')
  const eliminar = useEliminarBien()

  const [editar, setEditar] = useState<Bien | null>(null)
  const [nuevoAbierto, setNuevoAbierto] = useState(false)
  const [movimiento, setMovimiento] = useState<{ bien: Bien; tipo: TipoMovimiento } | null>(null)
  const [historial, setHistorial] = useState<Bien | null>(null)
  const [aEliminar, setAEliminar] = useState<Bien | null>(null)

  const confirmarEliminar = async () => {
    if (!aEliminar) return
    try {
      const r = await eliminar.mutateAsync(aEliminar.id_inventario)
      toast.success(r.mensaje)
      setAEliminar(null)
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  const alternar = (valor: EstadoStock | '') => setEstado(estado === valor ? '' : valor)

  return (
    <div className="space-y-6">
      <EncabezadoPagina
        titulo="Inventario"
        descripcion="Bienes del colegio y su stock. La cantidad cambia solo con entradas y salidas, que quedan en el historial."
        accion={
          <Button onClick={() => setNuevoAbierto(true)} className="gap-2">
            <PlusIcon className="size-4" /> Nuevo bien
          </Button>
        }
      />

      <div className="grid gap-3 sm:grid-cols-3">
        <TarjetaResumen
          titulo="Bienes registrados"
          valor={resumen?.total}
          icono={<PackageIcon className="size-5" />}
          tono="bg-blue-50 text-blue-600"
          activo={estado === ''}
          onClick={() => setEstado('')}
        />
        <TarjetaResumen
          titulo="Stock bajo"
          valor={resumen?.stock_bajo}
          icono={<AlertTriangleIcon className="size-5" />}
          tono="bg-amber-50 text-amber-600"
          activo={estado === 'bajo'}
          onClick={() => alternar('bajo')}
        />
        <TarjetaResumen
          titulo="Sin stock"
          valor={resumen?.sin_stock}
          icono={<PackageXIcon className="size-5" />}
          tono="bg-rose-50 text-rose-600"
          activo={estado === 'sin_stock'}
          onClick={() => alternar('sin_stock')}
        />
      </div>

      <Card>
        <CardContent className="space-y-4 py-4">
          <div className="flex flex-col gap-3 md:flex-row md:items-center">
            <div className="relative md:w-80">
              <SearchIcon className="absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-slate-400" />
              <Input
                value={texto}
                onChange={(e) => setTexto(e.target.value)}
                placeholder="Buscar por nombre u observación..."
                className="pl-8"
              />
            </div>
            <Select value={estado || TODOS} onValueChange={(v) => setEstado(v === TODOS ? '' : (v as EstadoStock))}>
              <SelectTrigger className="md:w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={TODOS}>Todos los estados</SelectItem>
                <SelectItem value="normal">Stock normal</SelectItem>
                <SelectItem value="bajo">Stock bajo</SelectItem>
                <SelectItem value="sin_stock">Sin stock</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Bien</TableHead>
                  <TableHead className="text-right">Cantidad</TableHead>
                  <TableHead className="text-right">Mínimo</TableHead>
                  <TableHead>Estado</TableHead>
                  <TableHead>Último movimiento</TableHead>
                  <TableHead className="text-right">Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  <FilaMensaje columnas={6} cargando />
                ) : isError ? (
                  <FilaMensaje columnas={6} mensaje={mensajeError(error)} />
                ) : !data?.bienes.length ? (
                  <FilaMensaje columnas={6} mensaje={buscar || estado ? 'Ningún bien coincide con el filtro.' : 'Todavía no hay bienes registrados.'} />
                ) : (
                  data.bienes.map((b) => (
                    <TableRow key={b.id_inventario}>
                      <TableCell className="whitespace-normal">
                        <p className="font-medium text-slate-900">{b.nombre}</p>
                        {b.observacion && <p className="text-xs text-slate-500">{b.observacion}</p>}
                      </TableCell>
                      <TableCell className="text-right text-base font-semibold text-slate-900 tabular-nums">{b.cantidad}</TableCell>
                      <TableCell className="text-right text-slate-500 tabular-nums">{b.stock_minimo || '—'}</TableCell>
                      <TableCell>
                        <InsigniaStock estado={b.estado} />
                      </TableCell>
                      <TableCell className="text-sm text-slate-500">
                        {b.ultimo_movimiento ? fechaHora(b.ultimo_movimiento) : 'Sin movimientos'}
                      </TableCell>
                      <TableCell>
                        <div className="flex justify-end gap-1.5">
                          <BotonAccion etiqueta="Registrar entrada" tono="verde" onClick={() => setMovimiento({ bien: b, tipo: 'entrada' })}>
                            <ArrowDownToLineIcon className="size-4" />
                          </BotonAccion>
                          <BotonAccion
                            etiqueta={b.cantidad ? 'Registrar salida' : 'Sin stock para sacar'}
                            tono="ambar"
                            disabled={!b.cantidad}
                            onClick={() => setMovimiento({ bien: b, tipo: 'salida' })}
                          >
                            <ArrowUpFromLineIcon className="size-4" />
                          </BotonAccion>
                          <BotonAccion etiqueta="Historial de movimientos" tono="azul" onClick={() => setHistorial(b)}>
                            <HistoryIcon className="size-4" />
                          </BotonAccion>
                          <BotonAccion etiqueta="Editar datos" tono="gris" onClick={() => setEditar(b)}>
                            <PencilIcon className="size-4" />
                          </BotonAccion>
                          {b.movimientos === 0 && (
                            <BotonAccion etiqueta="Eliminar (no tiene movimientos)" tono="rojo" onClick={() => setAEliminar(b)}>
                              <Trash2Icon className="size-4" />
                            </BotonAccion>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      <DialogoBien
        abierto={nuevoAbierto || editar !== null}
        bien={editar}
        onCerrar={() => {
          setNuevoAbierto(false)
          setEditar(null)
        }}
      />
      <DialogoMovimiento datos={movimiento} onCerrar={() => setMovimiento(null)} />
      <DialogoHistorial bien={historial} onCerrar={() => setHistorial(null)} />
      <Confirmar
        abierto={aEliminar !== null}
        onCambiar={(abierto) => !abierto && setAEliminar(null)}
        titulo="Eliminar bien"
        descripcion={
          <>
            Se eliminará <b>«{aEliminar?.nombre}»</b> del inventario. Solo se permite porque todavía no tiene movimientos.
          </>
        }
        textoConfirmar="Eliminar"
        icono={<Trash2Icon />}
        peligro
        ocupado={eliminar.isPending}
        onConfirmar={confirmarEliminar}
      />
    </div>
  )
}

// ------------------------------------------------------------
// Piezas de la pantalla
// ------------------------------------------------------------

function TarjetaResumen({
  titulo,
  valor,
  icono,
  tono,
  activo,
  onClick,
}: {
  titulo: string
  valor?: number
  icono: ReactNode
  tono: string
  activo: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'flex items-center gap-3 rounded-xl border bg-white p-4 text-left transition hover:border-blue-300',
        activo && 'border-blue-500 ring-1 ring-blue-500',
      )}
    >
      <span className={cn('flex size-10 items-center justify-center rounded-full', tono)}>{icono}</span>
      <span>
        <span className="block text-2xl font-bold text-slate-900">{valor ?? '—'}</span>
        <span className="text-sm text-slate-500">{titulo}</span>
      </span>
    </button>
  )
}

const ESTILO_STOCK: Record<EstadoStock, { texto: string; clase: string }> = {
  normal: { texto: 'Normal', clase: 'bg-emerald-50 text-emerald-700 ring-emerald-200' },
  bajo: { texto: 'Stock bajo', clase: 'bg-amber-50 text-amber-700 ring-amber-200' },
  sin_stock: { texto: 'Sin stock', clase: 'bg-rose-50 text-rose-700 ring-rose-200' },
}

function InsigniaStock({ estado }: { estado: EstadoStock }) {
  const { texto, clase } = ESTILO_STOCK[estado]
  return <span className={cn('rounded-md px-2 py-0.5 text-xs font-medium whitespace-nowrap ring-1 ring-inset', clase)}>{texto}</span>
}

// ------------------------------------------------------------
// Registrar o corregir un bien
// ------------------------------------------------------------

function DialogoBien({ abierto, bien, onCerrar }: { abierto: boolean; bien: Bien | null; onCerrar: () => void }) {
  const registrar = useRegistrarBien()
  const actualizar = useActualizarBien()
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<DatosBien>({ resolver: zodResolver(esquemaBien), defaultValues: { nombre: '', stock_minimo: '0', observacion: '' } })

  useEffect(() => {
    if (abierto)
      reset({ nombre: bien?.nombre ?? '', stock_minimo: String(bien?.stock_minimo ?? 0), observacion: bien?.observacion ?? '' })
  }, [abierto, bien, reset])

  const enviar = async (d: DatosBien) => {
    const cuerpo = { nombre: d.nombre, stock_minimo: Number(d.stock_minimo), observacion: d.observacion || null }
    try {
      if (bien) {
        await actualizar.mutateAsync({ id_inventario: bien.id_inventario, ...cuerpo })
        toast.success('Datos del bien actualizados.')
      } else {
        await registrar.mutateAsync(cuerpo)
        toast.success('Bien registrado con cantidad 0. Registre una entrada para cargar su stock.')
      }
      onCerrar()
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  return (
    <Dialog open={abierto} onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <PackageIcon className="size-5 text-primary" /> {bien ? 'Editar bien' : 'Nuevo bien'}
          </DialogTitle>
          <DialogDescription>
            {bien
              ? `La cantidad (${bien.cantidad}) no se edita aquí: se corrige con una entrada o una salida.`
              : 'El bien empieza con cantidad 0; su stock llega con la primera entrada.'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(enviar)} className="space-y-4">
          <Campo etiqueta="Nombre" error={errors.nombre?.message} htmlFor="nombre">
            <Input id="nombre" {...register('nombre')} placeholder="Ej. Pupitres" />
          </Campo>
          <Campo etiqueta="Stock mínimo (0 = sin alerta)" error={errors.stock_minimo?.message} htmlFor="stock_minimo">
            <Input id="stock_minimo" inputMode="numeric" {...register('stock_minimo')} />
          </Campo>
          <Campo etiqueta="Observación (opcional)" error={errors.observacion?.message} htmlFor="observacion">
            <Textarea id="observacion" rows={3} {...register('observacion')} placeholder="Ej. Dos en reparación" />
          </Campo>
          <DialogFooter className="gap-2 border-t pt-4 sm:gap-0">
            <Button type="button" variant="outline" onClick={onCerrar} disabled={isSubmitting}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting} className="gap-2">
              {isSubmitting && <Loader2Icon className="size-4 animate-spin" />}
              {bien ? 'Guardar cambios' : 'Registrar bien'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ------------------------------------------------------------
// Registrar una entrada o una salida
// ------------------------------------------------------------

function DialogoMovimiento({ datos, onCerrar }: { datos: { bien: Bien; tipo: TipoMovimiento } | null; onCerrar: () => void }) {
  const mover = useRegistrarMovimiento()
  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors, isSubmitting },
  } = useForm<DatosMovimiento>({
    resolver: zodResolver(esquemaMovimiento),
    defaultValues: { tipo: 'entrada', cantidad: '', motivo: '', destino: '' },
  })
  const tipo = useWatch({ control, name: 'tipo' })
  const cantidad = Number(useWatch({ control, name: 'cantidad' })) || 0
  const bien = datos?.bien

  useEffect(() => {
    if (datos) reset({ tipo: datos.tipo, cantidad: '', motivo: '', destino: '' })
  }, [datos, reset])

  const quedara = bien ? bien.cantidad + (tipo === 'entrada' ? cantidad : -cantidad) : 0

  const enviar = async (d: DatosMovimiento) => {
    if (!bien) return
    try {
      const r = await mover.mutateAsync({
        id_inventario: bien.id_inventario,
        tipo: d.tipo,
        cantidad: Number(d.cantidad),
        motivo: d.motivo,
        destino: d.tipo === 'salida' ? d.destino : null,
      })
      toast.success(
        `${d.tipo === 'entrada' ? 'Entrada' : 'Salida'} registrada: «${r.bien.nombre}» queda con ${r.bien.cantidad}.`,
      )
      if (r.aviso) toast.warning(r.aviso)
      onCerrar()
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  return (
    <Dialog open={datos !== null} onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {tipo === 'entrada' ? (
              <ArrowDownToLineIcon className="size-5 text-emerald-600" />
            ) : (
              <ArrowUpFromLineIcon className="size-5 text-amber-600" />
            )}
            {tipo === 'entrada' ? 'Registrar entrada' : 'Registrar salida'}
          </DialogTitle>
          <DialogDescription>
            {bien?.nombre} · disponible: <b>{bien?.cantidad}</b>
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(enviar)} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <Campo etiqueta="Tipo" error={errors.tipo?.message}>
              <Controller
                control={control}
                name="tipo"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="entrada">Entrada</SelectItem>
                      <SelectItem value="salida" disabled={!bien?.cantidad}>
                        Salida
                      </SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </Campo>
            <Campo etiqueta="Cantidad" error={errors.cantidad?.message} htmlFor="cantidad">
              <Input id="cantidad" inputMode="numeric" autoFocus {...register('cantidad')} placeholder="0" />
            </Campo>
          </div>
          <Campo etiqueta="Motivo" error={errors.motivo?.message} htmlFor="motivo">
            <Input
              id="motivo"
              {...register('motivo')}
              placeholder={tipo === 'entrada' ? 'Ej. Compra, donación, devolución' : 'Ej. Entrega a Educación Física'}
            />
          </Campo>
          {tipo === 'salida' && (
            <Campo etiqueta="Destino" error={errors.destino?.message} htmlFor="destino">
              <Input id="destino" {...register('destino')} placeholder="Ej. Aula 12, cancha, sala de profesores" />
            </Campo>
          )}
          {cantidad > 0 && (
            <p
              className={cn(
                'rounded-md px-3 py-2 text-sm',
                quedara < 0 ? 'bg-rose-50 text-rose-700' : 'bg-slate-50 text-slate-600',
              )}
            >
              {quedara < 0 ? `No alcanza: solo hay ${bien?.cantidad}.` : `Después del movimiento quedarán ${quedara}.`}
            </p>
          )}
          <DialogFooter className="gap-2 border-t pt-4 sm:gap-0">
            <Button type="button" variant="outline" onClick={onCerrar} disabled={isSubmitting}>
              Cancelar
            </Button>
            <Button type="submit" disabled={isSubmitting} className="gap-2">
              {isSubmitting && <Loader2Icon className="size-4 animate-spin" />}
              Registrar {tipo}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ------------------------------------------------------------
// Historial de movimientos de un bien
// ------------------------------------------------------------

function DialogoHistorial({ bien, onCerrar }: { bien: Bien | null; onCerrar: () => void }) {
  const { data, isLoading, isError, error } = useMovimientos(bien?.id_inventario ?? null)

  return (
    <Dialog open={bien !== null} onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <HistoryIcon className="size-5 text-primary" /> Historial de movimientos
          </DialogTitle>
          <DialogDescription>
            {bien?.nombre} · stock actual: <b>{data?.bien.cantidad ?? bien?.cantidad}</b>. Los movimientos no se editan:
            un error se corrige con un movimiento contrario.
          </DialogDescription>
        </DialogHeader>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Fecha</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead className="text-right">Cantidad</TableHead>
                <TableHead className="text-right">Saldo</TableHead>
                <TableHead>Motivo / destino</TableHead>
                <TableHead>Responsable</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <FilaMensaje columnas={6} cargando />
              ) : isError ? (
                <FilaMensaje columnas={6} mensaje={mensajeError(error)} />
              ) : !data?.movimientos.length ? (
                <FilaMensaje columnas={6} mensaje="El bien todavía no tiene movimientos." />
              ) : (
                data.movimientos.map((m) => (
                  <TableRow key={m.id_movimiento}>
                    <TableCell className="text-sm whitespace-nowrap text-slate-600">{fechaHora(m.fecha)}</TableCell>
                    <TableCell>
                      <span
                        className={cn(
                          'rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset',
                          m.tipo === 'entrada'
                            ? 'bg-emerald-50 text-emerald-700 ring-emerald-200'
                            : 'bg-amber-50 text-amber-700 ring-amber-200',
                        )}
                      >
                        {m.tipo === 'entrada' ? 'Entrada' : 'Salida'}
                      </span>
                    </TableCell>
                    <TableCell
                      className={cn('text-right font-semibold tabular-nums', m.tipo === 'entrada' ? 'text-emerald-700' : 'text-amber-700')}
                    >
                      {m.tipo === 'entrada' ? '+' : '−'}
                      {m.cantidad}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">{m.saldo}</TableCell>
                    <TableCell className="text-sm whitespace-normal text-slate-600">
                      {m.motivo ?? '—'}
                      {m.destino && <span className="block text-xs text-slate-400">Destino: {m.destino}</span>}
                    </TableCell>
                    <TableCell className="text-sm whitespace-normal text-slate-600">{m.responsable}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </DialogContent>
    </Dialog>
  )
}

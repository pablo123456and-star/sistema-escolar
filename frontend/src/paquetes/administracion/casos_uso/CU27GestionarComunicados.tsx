/**
 * CU27 - Gestionar comunicados y citaciones
 * Paquete: administracion
 *
 * Actores ........: Administrativo, Docente (publican); Tutor, Estudiante (leen)
 * Rol del sistema : administrador, profesor, tutor, estudiante
 * Backend ........: backend/app/paquetes/administracion/casos_uso/cu27_gestionar_comunicados.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  Un docente solo publica a sus cursos o a sus estudiantes.
 * Postcondición: El comunicado queda visible para sus destinatarios y se registra quién lo leyó.
 *
 * Pantalla: ruta /administracion/cu27
 * - Todos: bandeja con los comunicados dirigidos a él, filtros (no leídos, citaciones) y "Marcar como leído".
 * - Administrador y docente: botón "Nuevo comunicado" (el administrador puede publicar a todos; el docente
 *   solo a sus cursos o estudiantes), pestaña "Enviados por mí", registro de lectura y eliminar.
 *
 * Estado: IMPLEMENTADO.
 */
import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { Controller, useForm, useWatch } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import {
  CalendarClockIcon,
  CheckCheckIcon,
  CheckIcon,
  EyeIcon,
  Loader2Icon,
  MegaphoneIcon,
  PlusIcon,
  SearchIcon,
  SendIcon,
  Trash2Icon,
  UsersIcon,
} from 'lucide-react'
import { cn } from 'cn'
import Confirmar from '@/componentes/Confirmar'
import { Campo, EncabezadoPagina } from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Card, CardContent } from '@/componentes/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/componentes/ui/dialog'
import { Input } from '@/componentes/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { Textarea } from '@/componentes/ui/textarea'
import { ETIQUETA_ROL, fechaHora } from '@/lib/formato'
import { mensajeError } from '@/nucleo/api'
import { useSesion } from '@/nucleo/auth/contexto'
import {
  useBandeja,
  useDestinosComunicado,
  useEliminarComunicado,
  useLecturas,
  useMarcarLeido,
  usePublicarComunicado,
} from '../api'
import { esquemaComunicado, type Comunicado, type DatosComunicado } from '../schemas'

type Filtro = 'todos' | 'no_leidos' | 'citaciones' | 'enviados'

const VACIO: DatosComunicado = {
  titulo: '',
  contenido: '',
  tipo_comunicado: 'general',
  alcance: 'curso',
  id_curso: '',
  ci_estudiante: '',
  fecha_citacion: '',
}

export default function CU27GestionarComunicados() {
  const { usuario } = useSesion()
  const rol = usuario?.rol
  const publica = rol === 'administrador' || rol === 'profesor'

  const { data, isLoading, isError, error } = useBandeja()
  const marcarLeido = useMarcarLeido()
  const eliminar = useEliminarComunicado()

  const [filtro, setFiltro] = useState<Filtro>('todos')
  const [buscar, setBuscar] = useState('')
  const [nuevoAbierto, setNuevoAbierto] = useState(false)
  const [verLecturas, setVerLecturas] = useState<Comunicado | null>(null)
  const [aEliminar, setAEliminar] = useState<Comunicado | null>(null)

  const comunicados = useMemo(() => {
    const texto = buscar.trim().toLowerCase()
    return (data?.comunicados ?? []).filter((c) => {
      if (filtro === 'no_leidos' && !(c.es_destinatario && !c.leido_en)) return false
      if (filtro === 'citaciones' && c.tipo_comunicado !== 'citacion') return false
      if (filtro === 'enviados' && !c.es_mio) return false
      if (!texto) return true
      return [c.titulo, c.contenido, c.autor, c.destinatario].some((x) => x.toLowerCase().includes(texto))
    })
  }, [data, filtro, buscar])

  const pestanas: { valor: Filtro; texto: string; cantidad?: number }[] = [
    { valor: 'todos', texto: 'Todos' },
    { valor: 'no_leidos', texto: 'No leídos', cantidad: data?.no_leidos },
    { valor: 'citaciones', texto: 'Citaciones' },
    ...(publica ? [{ valor: 'enviados' as Filtro, texto: 'Enviados por mí' }] : []),
  ]

  const leer = async (c: Comunicado) => {
    try {
      await marcarLeido.mutateAsync(c.id_comunicado)
      toast.success('Comunicado marcado como leído.')
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  const confirmarEliminar = async () => {
    if (!aEliminar) return
    try {
      const r = await eliminar.mutateAsync(aEliminar.id_comunicado)
      toast.success(r.mensaje)
      setAEliminar(null)
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  return (
    <div className="space-y-6">
      <EncabezadoPagina
        titulo="Comunicados y citaciones"
        descripcion={
          rol === 'administrador'
            ? 'Publique avisos a toda la comunidad, a un curso o a un estudiante, y revise quién los leyó.'
            : rol === 'profesor'
              ? 'Envíe comunicados y citaciones a sus cursos o estudiantes, y revise quién los leyó.'
              : rol === 'tutor'
                ? 'Avisos del colegio y citaciones sobre sus estudiantes.'
                : 'Avisos del colegio para usted y su curso.'
        }
        accion={
          publica && (
            <Button onClick={() => setNuevoAbierto(true)} className="gap-2">
              <PlusIcon className="size-4" /> Nuevo comunicado
            </Button>
          )
        }
      />

      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-wrap gap-2">
          {pestanas.map((p) => (
            <Button
              key={p.valor}
              size="sm"
              variant={filtro === p.valor ? 'default' : 'outline'}
              onClick={() => setFiltro(p.valor)}
              className="gap-2"
            >
              {p.texto}
              {!!p.cantidad && (
                <span className="rounded-full bg-rose-500 px-1.5 text-[11px] font-semibold text-white">{p.cantidad}</span>
              )}
            </Button>
          ))}
        </div>
        <div className="relative md:w-72">
          <SearchIcon className="absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-slate-400" />
          <Input value={buscar} onChange={(e) => setBuscar(e.target.value)} placeholder="Buscar comunicado..." className="pl-8" />
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center gap-2 py-16 text-sm text-slate-500">
          <Loader2Icon className="size-4 animate-spin" /> Cargando comunicados...
        </div>
      ) : isError ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-rose-600">{mensajeError(error)}</CardContent>
        </Card>
      ) : comunicados.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-14 text-center text-sm text-slate-500">
            <MegaphoneIcon className="size-8 text-slate-300" />
            {filtro === 'no_leidos' ? 'No tiene comunicados sin leer.' : 'No hay comunicados para mostrar.'}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {comunicados.map((c) => (
            <TarjetaComunicado
              key={c.id_comunicado}
              c={c}
              puedeGestionar={rol === 'administrador' || c.es_mio}
              leyendo={marcarLeido.isPending && marcarLeido.variables === c.id_comunicado}
              onLeer={() => leer(c)}
              onLecturas={() => setVerLecturas(c)}
              onEliminar={() => setAEliminar(c)}
            />
          ))}
        </div>
      )}

      {publica && <DialogoNuevo abierto={nuevoAbierto} onCambiar={setNuevoAbierto} />}
      <DialogoLecturas comunicado={verLecturas} onCerrar={() => setVerLecturas(null)} />
      <Confirmar
        abierto={aEliminar !== null}
        onCambiar={(abierto) => !abierto && setAEliminar(null)}
        titulo="Eliminar comunicado"
        descripcion={
          <>
            Se eliminará <b>«{aEliminar?.titulo}»</b> y su registro de lectura. Sus destinatarios ya no lo verán.
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
// Tarjeta de un comunicado
// ------------------------------------------------------------

function TarjetaComunicado({
  c,
  puedeGestionar,
  leyendo,
  onLeer,
  onLecturas,
  onEliminar,
}: {
  c: Comunicado
  puedeGestionar: boolean
  leyendo: boolean
  onLeer: () => void
  onLecturas: () => void
  onEliminar: () => void
}) {
  const [expandido, setExpandido] = useState(false)
  const nuevo = c.es_destinatario && !c.leido_en
  const citacion = c.tipo_comunicado === 'citacion'
  const largo = c.contenido.length > 220

  return (
    <Card className={cn('border-l-4', nuevo ? 'border-l-blue-500' : citacion ? 'border-l-amber-400' : 'border-l-slate-200')}>
      <CardContent className="space-y-3 py-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-3">
            <span
              className={cn(
                'mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-full',
                citacion ? 'bg-amber-50 text-amber-600' : 'bg-blue-50 text-blue-600',
              )}
            >
              {citacion ? <CalendarClockIcon className="size-4" /> : <MegaphoneIcon className="size-4" />}
            </span>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="font-semibold text-slate-900">{c.titulo}</h3>
                {citacion && <Etiqueta clase="bg-amber-50 text-amber-700 ring-amber-200">Citación</Etiqueta>}
                {nuevo && <Etiqueta clase="bg-blue-50 text-blue-700 ring-blue-200">Nuevo</Etiqueta>}
              </div>
              <p className="text-xs text-slate-500">
                {c.autor}
                {c.rol_autor && ` · ${ETIQUETA_ROL[c.rol_autor] ?? c.rol_autor}`} · {fechaHora(c.fecha_publicacion)}
              </p>
              <p className="mt-0.5 flex items-center gap-1 text-xs text-slate-500">
                <UsersIcon className="size-3" />
                Para: {c.alcance === 'estudiante' && citacion ? `tutores de ${c.destinatario}` : c.destinatario}
              </p>
            </div>
          </div>
          <div className="flex shrink-0 flex-wrap items-center gap-2 sm:justify-end">
            {c.es_destinatario &&
              (c.leido_en ? (
                <span className="flex items-center gap-1 text-xs text-emerald-600">
                  <CheckCheckIcon className="size-4" /> Leído el {fechaHora(c.leido_en)}
                </span>
              ) : (
                <Button size="sm" variant="outline" onClick={onLeer} disabled={leyendo} className="gap-1.5">
                  {leyendo ? <Loader2Icon className="size-3.5 animate-spin" /> : <CheckIcon className="size-3.5" />}
                  Marcar como leído
                </Button>
              ))}
            {puedeGestionar && (
              <>
                <Button size="sm" variant="outline" onClick={onLecturas} className="gap-1.5">
                  <EyeIcon className="size-3.5" /> Lecturas ({c.lecturas ?? 0})
                </Button>
                <Button size="icon-sm" variant="ghost" onClick={onEliminar} aria-label="Eliminar" className="text-rose-600">
                  <Trash2Icon className="size-4" />
                </Button>
              </>
            )}
          </div>
        </div>

        {citacion && c.fecha_citacion && (
          <div className="flex items-center gap-2 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">
            <CalendarClockIcon className="size-4" />
            Se le cita el <b>{fechaHora(c.fecha_citacion)}</b>
          </div>
        )}

        <p className={cn('text-sm whitespace-pre-line text-slate-700', !expandido && largo && 'line-clamp-3')}>{c.contenido}</p>
        {largo && (
          <button type="button" className="text-xs font-medium text-blue-600 hover:underline" onClick={() => setExpandido(!expandido)}>
            {expandido ? 'Ver menos' : 'Ver completo'}
          </button>
        )}
      </CardContent>
    </Card>
  )
}

function Etiqueta({ clase, children }: { clase: string; children: ReactNode }) {
  return <span className={cn('rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset', clase)}>{children}</span>
}

// ------------------------------------------------------------
// Publicar un comunicado o una citación
// ------------------------------------------------------------

function DialogoNuevo({ abierto, onCambiar }: { abierto: boolean; onCambiar: (abierto: boolean) => void }) {
  const { data: destinos, isLoading } = useDestinosComunicado(abierto)
  const publicar = usePublicarComunicado()
  const [filtroEst, setFiltroEst] = useState('')

  const {
    register,
    handleSubmit,
    control,
    reset,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<DatosComunicado>({ resolver: zodResolver(esquemaComunicado), defaultValues: VACIO })

  const tipo = useWatch({ control, name: 'tipo_comunicado' })
  const alcance = useWatch({ control, name: 'alcance' })

  // Formulario limpio cada vez que se abre (el administrador empieza con "Toda la comunidad")
  useEffect(() => {
    if (abierto) reset({ ...VACIO, alcance: destinos?.puede_todos ? 'todos' : 'curso' })
  }, [abierto, destinos?.puede_todos, reset])

  const cambiar = (valor: boolean) => {
    if (!valor) setFiltroEst('')
    onCambiar(valor)
  }

  // Una citación siempre va a un estudiante (a sus tutores)
  useEffect(() => {
    if (tipo === 'citacion') setValue('alcance', 'estudiante')
  }, [tipo, setValue])

  const estudiantes = useMemo(() => {
    const texto = filtroEst.trim().toLowerCase()
    const lista = destinos?.estudiantes ?? []
    return (texto ? lista.filter((e) => `${e.nombre} ${e.ci} ${e.curso}`.toLowerCase().includes(texto)) : lista).slice(0, 100)
  }, [destinos, filtroEst])

  const enviar = async (d: DatosComunicado) => {
    try {
      await publicar.mutateAsync({
        titulo: d.titulo,
        contenido: d.contenido,
        tipo_comunicado: d.tipo_comunicado,
        alcance: d.alcance,
        id_curso: d.alcance === 'curso' ? Number(d.id_curso) : null,
        ci_estudiante: d.alcance === 'estudiante' ? d.ci_estudiante : null,
        // Bolivia es UTC-4 todo el año
        fecha_citacion: d.tipo_comunicado === 'citacion' ? `${d.fecha_citacion}:00-04:00` : null,
      })
      toast.success(d.tipo_comunicado === 'citacion' ? 'Citación enviada.' : 'Comunicado publicado.')
      cambiar(false)
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  return (
    <Dialog open={abierto} onOpenChange={cambiar}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <SendIcon className="size-5 text-primary" /> Nuevo comunicado
          </DialogTitle>
          <DialogDescription>
            {destinos?.gestion ? `Se publica en la gestión ${destinos.gestion}.` : 'Elija a quién va dirigido y escriba el mensaje.'}
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center gap-2 py-8 text-sm text-slate-500">
            <Loader2Icon className="size-4 animate-spin" /> Cargando destinatarios...
          </div>
        ) : destinos && destinos.gestion === null ? (
          <p className="py-6 text-sm text-rose-600">No hay una gestión abierta: no se pueden publicar comunicados.</p>
        ) : (
          <form onSubmit={handleSubmit(enviar)} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <Campo etiqueta="Tipo" error={errors.tipo_comunicado?.message}>
                <Controller
                  control={control}
                  name="tipo_comunicado"
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="general">Comunicado</SelectItem>
                        <SelectItem value="citacion">Citación a tutores</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                />
              </Campo>
              <Campo etiqueta="Dirigido a" error={errors.alcance?.message}>
                <Controller
                  control={control}
                  name="alcance"
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange} disabled={tipo === 'citacion'}>
                      <SelectTrigger className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {destinos?.puede_todos && <SelectItem value="todos">Toda la comunidad</SelectItem>}
                        <SelectItem value="curso">Un curso</SelectItem>
                        <SelectItem value="estudiante">Un estudiante</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                />
              </Campo>
            </div>

            {alcance === 'curso' && (
              <Campo etiqueta="Curso" error={errors.id_curso?.message}>
                <Controller
                  control={control}
                  name="id_curso"
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder={destinos?.cursos.length ? 'Seleccione el curso' : 'No tiene cursos asignados'} />
                      </SelectTrigger>
                      <SelectContent>
                        {destinos?.cursos.map((c) => (
                          <SelectItem key={c.id_curso} value={String(c.id_curso)}>
                            {c.nombre_curso}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                />
              </Campo>
            )}

            {alcance === 'estudiante' && (
              <Campo etiqueta={tipo === 'citacion' ? 'Estudiante (se cita a sus tutores)' : 'Estudiante'} error={errors.ci_estudiante?.message}>
                <div className="space-y-2">
                  <Input value={filtroEst} onChange={(e) => setFiltroEst(e.target.value)} placeholder="Filtrar por nombre, CI o curso..." />
                  <Controller
                    control={control}
                    name="ci_estudiante"
                    render={({ field }) => (
                      <Select value={field.value} onValueChange={field.onChange}>
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder={estudiantes.length ? 'Seleccione el estudiante' : 'Sin estudiantes'} />
                        </SelectTrigger>
                        <SelectContent>
                          {estudiantes.map((e) => (
                            <SelectItem key={e.ci} value={e.ci}>
                              {e.nombre} · {e.curso}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    )}
                  />
                </div>
              </Campo>
            )}

            {tipo === 'citacion' && (
              <Campo etiqueta="Fecha y hora de la citación" error={errors.fecha_citacion?.message} htmlFor="fecha_citacion">
                <Input id="fecha_citacion" type="datetime-local" {...register('fecha_citacion')} />
              </Campo>
            )}

            <Campo etiqueta="Título" error={errors.titulo?.message} htmlFor="titulo">
              <Input id="titulo" {...register('titulo')} placeholder="Ej. Reunión de padres de familia" />
            </Campo>
            <Campo etiqueta="Mensaje" error={errors.contenido?.message} htmlFor="contenido">
              <Textarea id="contenido" rows={5} {...register('contenido')} placeholder="Escriba el comunicado..." />
            </Campo>

            <DialogFooter className="gap-2 border-t pt-4 sm:gap-0">
              <Button type="button" variant="outline" onClick={() => cambiar(false)} disabled={isSubmitting}>
                Cancelar
              </Button>
              <Button type="submit" disabled={isSubmitting} className="gap-2">
                {isSubmitting ? <Loader2Icon className="size-4 animate-spin" /> : <SendIcon className="size-4" />}
                {tipo === 'citacion' ? 'Enviar citación' : 'Publicar'}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  )
}

// ------------------------------------------------------------
// Registro de lectura (autor o administrador)
// ------------------------------------------------------------

function DialogoLecturas({ comunicado, onCerrar }: { comunicado: Comunicado | null; onCerrar: () => void }) {
  const { data, isLoading, isError, error } = useLecturas(comunicado?.id_comunicado ?? null)
  const porcentaje = data && data.total_destinatarios ? Math.round((data.total_leidos / data.total_destinatarios) * 100) : 0

  return (
    <Dialog open={comunicado !== null} onOpenChange={(abierto) => !abierto && onCerrar()}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <EyeIcon className="size-5 text-primary" /> Registro de lectura
          </DialogTitle>
          <DialogDescription>{comunicado?.titulo}</DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center gap-2 py-8 text-sm text-slate-500">
            <Loader2Icon className="size-4 animate-spin" /> Cargando...
          </div>
        ) : isError ? (
          <p className="py-6 text-sm text-rose-600">{mensajeError(error)}</p>
        ) : (
          data && (
            <div className="space-y-4">
              <div>
                <div className="mb-1 flex justify-between text-sm">
                  <span className="text-slate-600">
                    <b>{data.total_leidos}</b> de <b>{data.total_destinatarios}</b> destinatarios lo leyeron
                  </span>
                  <span className="font-medium text-slate-900">{porcentaje} %</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-emerald-500" style={{ width: `${porcentaje}%` }} />
                </div>
              </div>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Nombre</TableHead>
                      <TableHead>Relación</TableHead>
                      <TableHead>Lectura</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.destinatarios.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={3} className="py-6 text-center text-sm text-slate-500">
                          El comunicado no tiene destinatarios.
                        </TableCell>
                      </TableRow>
                    ) : (
                      data.destinatarios.map((d) => (
                        <TableRow key={d.ci}>
                          <TableCell>
                            <p className="font-medium text-slate-900">{d.nombre}</p>
                            <p className="text-xs text-slate-500">CI {d.ci}</p>
                          </TableCell>
                          <TableCell className="text-sm whitespace-normal text-slate-600">{d.relacion}</TableCell>
                          <TableCell>
                            {d.leido_en ? (
                              <span className="flex items-center gap-1 text-xs text-emerald-600">
                                <CheckCheckIcon className="size-4" /> {fechaHora(d.leido_en)}
                              </span>
                            ) : d.tiene_cuenta ? (
                              <span className="text-xs text-amber-600">Pendiente</span>
                            ) : (
                              <span className="text-xs text-slate-400">Sin cuenta en el sistema</span>
                            )}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </div>
          )
        )}
      </DialogContent>
    </Dialog>
  )
}

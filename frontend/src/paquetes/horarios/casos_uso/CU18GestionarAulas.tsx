/**
 * CU18 - Gestionar aulas
 * Paquete: horarios
 *
 * Actores ........: Administrador
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/horarios/casos_uso/cu18_gestionar_aulas.py
 *
 * Precondición:  Sesión iniciada como administrador.
 * Postcondición: El aula queda registrada o actualizada. Un aula en mantenimiento o inactiva no se puede asignar.
 *
 * Estado: IMPLEMENTADO.
 */
import { useMemo, useState } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import {
  DoorOpen,
  Edit2,
  Loader2,
  Plus,
  Power,
  Search,
  Trash2,
  Users,
  Wrench,
} from 'lucide-react'
import Confirmar from '@/componentes/Confirmar'
import { Campo, EncabezadoPagina } from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/componentes/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/componentes/ui/dialog'
import { Input } from '@/componentes/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/componentes/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/componentes/ui/table'
import { mensajeError } from '@/nucleo/api'
import {
  useAulas,
  useCrearAula,
  useEditarAula,
  useEliminarAula,
} from '../api'
import {
  esquemaAula,
  type AulaItem,
  type DatosAula,
  type EstadoAula,
} from '../schemas'

function BadgeEstadoAula({ estado }: { estado: EstadoAula }) {
  if (estado === 'disponible') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
        <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
        Disponible
      </span>
    )
  }
  if (estado === 'mantenimiento') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700 dark:bg-amber-950/40 dark:text-amber-300">
        <Wrench className="size-3" />
        Mantenimiento
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-400">
      <Power className="size-3" />
      Inactiva
    </span>
  )
}

export default function CU18GestionarAulas() {
  const { data: aulas, isLoading, isError, error } = useAulas()
  const crearAula = useCrearAula()
  const editarAula = useEditarAula()
  const eliminarAula = useEliminarAula()

  const [busqueda, setBusqueda] = useState('')
  const [filtroEstado, setFiltroEstado] = useState<string>('todos')
  const [aulaEnEdicion, setAulaEnEdicion] = useState<AulaItem | null>(null)
  const [dialogoAbierto, setDialogoAbierto] = useState(false)
  const [aulaAEliminar, setAulaAEliminar] = useState<AulaItem | null>(null)

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<DatosAula>({
    resolver: zodResolver(esquemaAula),
    defaultValues: {
      numero: '',
      capacidad: '30',
      tipo_aula: '',
      estado_aula: 'disponible',
    },
  })

  const abrirModalCrear = () => {
    setAulaEnEdicion(null)
    reset({
      numero: '',
      capacidad: '30',
      tipo_aula: '',
      estado_aula: 'disponible',
    })
    setDialogoAbierto(true)
  }

  const abrirModalEditar = (aula: AulaItem) => {
    setAulaEnEdicion(aula)
    reset({
      numero: aula.numero,
      capacidad: String(aula.capacidad ?? 30),
      tipo_aula: aula.tipo_aula ?? '',
      estado_aula: aula.estado_aula,
    })
    setDialogoAbierto(true)
  }

  const onSubmit = async (valores: DatosAula) => {
    const capNum = Number(valores.capacidad)
    if (isNaN(capNum) || capNum <= 0) {
      toast.error('La capacidad debe ser un número entero mayor a 0')
      return
    }

    try {
      if (aulaEnEdicion) {
        await editarAula.mutateAsync({
          id_aula: aulaEnEdicion.id_aula,
          cuerpo: {
            numero: valores.numero,
            capacidad: capNum,
            tipo_aula: valores.tipo_aula?.trim() || null,
            estado_aula: valores.estado_aula,
          },
        })
        toast.success(`Aula "${valores.numero}" actualizada correctamente.`)
      } else {
        await crearAula.mutateAsync({
          numero: valores.numero,
          capacidad: capNum,
          tipo_aula: valores.tipo_aula?.trim() || null,
          estado_aula: valores.estado_aula,
        })
        toast.success(`Aula "${valores.numero}" registrada con éxito.`)
      }
      setDialogoAbierto(false)
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  const cambiarEstadoRapido = async (aula: AulaItem, nuevoEstado: EstadoAula) => {
    try {
      await editarAula.mutateAsync({
        id_aula: aula.id_aula,
        cuerpo: { estado_aula: nuevoEstado },
      })
      toast.success(`Estado del aula "${aula.numero}" cambiado a ${nuevoEstado}.`)
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  const confirmarEliminar = async () => {
    if (!aulaAEliminar) return
    try {
      await eliminarAula.mutateAsync(aulaAEliminar.id_aula)
      toast.success(`Aula "${aulaAEliminar.numero}" eliminada correctamente.`)
      setAulaAEliminar(null)
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  const aulasFiltradas = useMemo(() => {
    if (!aulas) return []
    return aulas.filter((a) => {
      const coincideTexto =
        a.numero.toLowerCase().includes(busqueda.toLowerCase()) ||
        (a.tipo_aula ?? '').toLowerCase().includes(busqueda.toLowerCase())
      const coincideEstado =
        filtroEstado === 'todos' || a.estado_aula === filtroEstado
      return coincideTexto && coincideEstado
    })
  }, [aulas, busqueda, filtroEstado])

  const stats = useMemo(() => {
    if (!aulas) return { total: 0, disponibles: 0, mantenimiento: 0, inactivas: 0 }
    return {
      total: aulas.length,
      disponibles: aulas.filter((a) => a.estado_aula === 'disponible').length,
      mantenimiento: aulas.filter((a) => a.estado_aula === 'mantenimiento').length,
      inactivas: aulas.filter((a) => a.estado_aula === 'inactiva').length,
    }
  }, [aulas])

  return (
    <div className="space-y-6">
      <EncabezadoPagina
        titulo="Gestionar Aulas"
        descripcion="Administre las aulas de la institución escolar, su capacidad física, estado de disponibilidad y clases asignadas."
        accion={
          <Button onClick={abrirModalCrear} className="gap-2 shadow-sm font-medium">
            <Plus className="size-4" />
            Registrar Aula
          </Button>
        }
      />

      {/* Tarjetas resumen */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="border shadow-xs bg-card/60 backdrop-blur-xs">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Total Aulas
              </p>
              <p className="text-2xl font-bold tracking-tight text-foreground">{stats.total}</p>
            </div>
            <div className="size-10 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
              <DoorOpen className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border shadow-xs bg-card/60 backdrop-blur-xs">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Disponibles
              </p>
              <p className="text-2xl font-bold tracking-tight text-emerald-600 dark:text-emerald-400">
                {stats.disponibles}
              </p>
            </div>
            <div className="size-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
              <DoorOpen className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border shadow-xs bg-card/60 backdrop-blur-xs">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Mantenimiento
              </p>
              <p className="text-2xl font-bold tracking-tight text-amber-600 dark:text-amber-400">
                {stats.mantenimiento}
              </p>
            </div>
            <div className="size-10 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-600 dark:text-amber-400">
              <Wrench className="size-5" />
            </div>
          </CardContent>
        </Card>

        <Card className="border shadow-xs bg-card/60 backdrop-blur-xs">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Inactivas
              </p>
              <p className="text-2xl font-bold tracking-tight text-slate-500">
                {stats.inactivas}
              </p>
            </div>
            <div className="size-10 rounded-xl bg-slate-500/10 flex items-center justify-center text-slate-500">
              <Power className="size-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filtros y Búsqueda */}
      <Card className="border shadow-xs">
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por número o tipo de aula..."
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                className="pl-9 h-9"
              />
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-muted-foreground whitespace-nowrap">
                Estado:
              </span>
              <Select value={filtroEstado} onValueChange={setFiltroEstado}>
                <SelectTrigger className="w-[170px] h-9 text-xs">
                  <SelectValue placeholder="Todos los estados" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos los estados</SelectItem>
                  <SelectItem value="disponible">Disponibles</SelectItem>
                  <SelectItem value="mantenimiento">En mantenimiento</SelectItem>
                  <SelectItem value="inactiva">Inactivas</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabla de Aulas */}
      <Card className="border shadow-xs overflow-hidden">
        <CardHeader className="border-b bg-muted/20 px-6 py-4">
          <CardTitle className="text-base flex items-center justify-between">
            <span className="flex items-center gap-2 font-semibold">
              <DoorOpen className="size-4.5 text-primary" />
              Listado General de Aulas
            </span>
            <span className="text-xs font-normal text-muted-foreground">
              Mostrando {aulasFiltradas.length} de {aulas?.length ?? 0} registradas
            </span>
          </CardTitle>
          <CardDescription>
            Consulte la capacidad física y el número de materias/clases vinculadas a cada aula.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3 text-muted-foreground text-sm">
              <Loader2 className="size-7 animate-spin text-primary" />
              <span>Cargando listado de aulas...</span>
            </div>
          ) : isError ? (
            <div className="py-12 text-center text-sm text-destructive px-4">
              {mensajeError(error)}
            </div>
          ) : aulasFiltradas.length === 0 ? (
            <div className="py-16 text-center text-sm text-muted-foreground italic">
              {busqueda || filtroEstado !== 'todos'
                ? 'No se encontraron aulas con los criterios de búsqueda seleccionados.'
                : 'No existen aulas registradas en el sistema aún.'}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/40 hover:bg-muted/40">
                    <TableHead className="w-32 font-semibold">Número</TableHead>
                    <TableHead className="font-semibold">Tipo</TableHead>
                    <TableHead className="w-32 font-semibold">Capacidad</TableHead>
                    <TableHead className="w-36 font-semibold">Estado</TableHead>
                    <TableHead className="w-36 text-center font-semibold">Clases asignadas</TableHead>
                    <TableHead className="w-44 text-right font-semibold">Acciones</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {aulasFiltradas.map((item) => (
                    <TableRow key={item.id_aula} className="hover:bg-muted/20">
                      <TableCell className="font-bold text-foreground">
                        <span className="font-mono text-sm bg-muted/60 px-2 py-0.5 rounded border">
                          {item.numero}
                        </span>
                      </TableCell>
                      <TableCell className="font-medium text-foreground">
                        {item.tipo_aula ? (
                          <span>{item.tipo_aula}</span>
                        ) : (
                          <span className="text-muted-foreground italic text-xs">Sin especificar</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1.5 text-sm">
                          <Users className="size-3.5 text-muted-foreground" />
                          <span className="font-medium text-foreground">
                            {item.capacidad ?? '—'}
                          </span>
                          <span className="text-xs text-muted-foreground">est.</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <BadgeEstadoAula estado={item.estado_aula} />
                      </TableCell>
                      <TableCell className="text-center">
                        <span
                          className={`inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                            item.total_clases_asignadas > 0
                              ? 'bg-primary/10 text-primary'
                              : 'bg-muted text-muted-foreground'
                          }`}
                        >
                          {item.total_clases_asignadas}{' '}
                          {item.total_clases_asignadas === 1 ? 'clase' : 'clases'}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          {/* Cambiar estado */}
                          <Select
                            value={item.estado_aula}
                            onValueChange={(val) => {
                              if (val !== item.estado_aula) {
                                cambiarEstadoRapido(item, val as EstadoAula)
                              }
                            }}
                          >
                            <SelectTrigger className="h-8 w-28 text-xs font-medium">
                              <SelectValue placeholder="Estado" />
                            </SelectTrigger>
                            <SelectContent align="end">
                              <SelectItem value="disponible">Disponible</SelectItem>
                              <SelectItem value="mantenimiento">Mantenimiento</SelectItem>
                              <SelectItem value="inactiva">Inactiva</SelectItem>
                            </SelectContent>
                          </Select>

                          {/* Editar */}
                          <Button
                            variant="outline"
                            size="icon-sm"
                            className="h-8 w-8 text-muted-foreground hover:text-foreground"
                            onClick={() => abrirModalEditar(item)}
                            title="Editar aula"
                          >
                            <Edit2 className="size-3.5" />
                          </Button>

                          {/* Eliminar */}
                          <Button
                            variant="outline"
                            size="icon-sm"
                            className="h-8 w-8 text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950/30"
                            onClick={() => setAulaAEliminar(item)}
                            title="Eliminar aula"
                          >
                            <Trash2 className="size-3.5" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Modal / Ventana de Registro o Edición */}
      <Dialog open={dialogoAbierto} onOpenChange={setDialogoAbierto}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <DoorOpen className="size-5 text-primary" />
              {aulaEnEdicion ? `Editar Aula ${aulaEnEdicion.numero}` : 'Registrar Nueva Aula'}
            </DialogTitle>
            <DialogDescription>
              {aulaEnEdicion
                ? 'Actualice la información física o el estado del aula.'
                : 'Ingrese los datos del ambiente para su uso en horarios y asignaciones.'}
            </DialogDescription>
          </DialogHeader>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 py-2">
            <Campo
              etiqueta="Número o Identificador del Aula"
              error={errors.numero?.message}
            >
              <Input
                {...register('numero')}
                placeholder="Ej. A-101, LAB-FIS, B-204"
                disabled={isSubmitting}
                className="font-mono uppercase"
              />
            </Campo>

            <Campo
              etiqueta="Capacidad de Estudiantes"
              error={errors.capacidad?.message}
            >
              <Input
                type="number"
                min={1}
                {...register('capacidad')}
                placeholder="Ej. 35"
                disabled={isSubmitting}
              />
            </Campo>

            <Campo
              etiqueta="Tipo de Aula (opcional)"
              error={errors.tipo_aula?.message}
            >
              <Input
                {...register('tipo_aula')}
                placeholder="Ej. Teoría, Laboratorio, Taller"
                disabled={isSubmitting}
              />
            </Campo>

            <Campo
              etiqueta="Estado del Aula"
              error={errors.estado_aula?.message}
            >
              <Controller
                control={control}
                name="estado_aula"
                render={({ field }) => (
                  <Select
                    value={field.value}
                    onValueChange={field.onChange}
                    disabled={isSubmitting}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Seleccione el estado" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="disponible">Disponible (habilitada para clases)</SelectItem>
                      <SelectItem value="mantenimiento">Mantenimiento (reparaciones/obras)</SelectItem>
                      <SelectItem value="inactiva">Inactiva (fuera de servicio)</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
            </Campo>

            <DialogFooter className="pt-4 border-t gap-2 sm:gap-0">
              <Button
                type="button"
                variant="outline"
                onClick={() => setDialogoAbierto(false)}
                disabled={isSubmitting}
              >
                Cancelar
              </Button>
              <Button type="submit" disabled={isSubmitting} className="gap-2">
                {isSubmitting && <Loader2 className="size-4 animate-spin" />}
                {aulaEnEdicion ? 'Guardar Cambios' : 'Registrar Aula'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Confirmar Eliminación */}
      <Confirmar
        abierto={aulaAEliminar !== null}
        onCambiar={(abierto) => !abierto && setAulaAEliminar(null)}
        onConfirmar={confirmarEliminar}
        titulo={`¿Eliminar el aula "${aulaAEliminar?.numero}"?`}
        descripcion={
          aulaAEliminar?.total_clases_asignadas && aulaAEliminar.total_clases_asignadas > 0
            ? `Esta aula tiene ${aulaAEliminar.total_clases_asignadas} clases asignadas actualmente. La base de datos no permitirá eliminarla; se recomienda cambiar su estado a inactiva.`
            : 'Esta acción eliminará permanentemente el registro del aula si no cuenta con clases asignadas.'
        }
        textoConfirmar="Eliminar Aula"
        peligro
        ocupado={eliminarAula.isPending}
      />
    </div>
  )
}

/**
 * CU17 - Consultar historial de inscripciones
 * Paquete: academico
 *
 * Actores ........: Tutor, Estudiante, Administrador
 * Rol del sistema : tutor, estudiante, administrador
 * Backend ........: backend/app/paquetes/academico/casos_uso/cu17_consultar_historial_inscripciones.py
 *
 * Pantalla: ruta /academico/cu17
 * - Tutor: elige a su hijo en un selector.
 * - Estudiante: ve el suyo directo (automático).
 * - Administrador: buscador predictivo por CI o nombre de estudiante.
 * - Tabla: Gestión | Curso | Estado | Inscrito el | Retiro (fecha y motivo) | Resultado final | Promedio anual.
 *
 * Estado: IMPLEMENTADO.
 */
import { useEffect, useMemo, useState } from 'react'
import {
  CalendarIcon,
  CheckCircle2,
  GraduationCap,
  History,
  Loader2,
  Search,
  UserCheck,
  XCircle,
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/componentes/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { Input } from '@/componentes/ui/input'
import { fecha } from '@/lib/formato'
import { useSesion } from '@/nucleo/auth/contexto'
import { useEstudiantesHistorial, useHistorialInscripciones } from '../api'
import type { HistorialInscripcionItem } from '../schemas'

function BadgeEstado({ estado }: { estado: HistorialInscripcionItem['estado_inscripcion'] }) {
  if (estado === 'activa') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400">
        <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" />
        Activa
      </span>
    )
  }
  if (estado === 'retirada') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-medium text-rose-700 dark:bg-rose-950/40 dark:text-rose-400">
        <span className="size-1.5 rounded-full bg-rose-500" />
        Retirada
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-950/40 dark:text-blue-400">
      <span className="size-1.5 rounded-full bg-blue-500" />
      Finalizada
    </span>
  )
}

function BadgeResultado({ resultado }: { resultado?: HistorialInscripcionItem['resultado_final'] }) {
  if (!resultado) {
    return <span className="text-muted-foreground text-xs italic">En curso / Sin cierre</span>
  }
  if (resultado === 'promovido') {
    return (
      <span className="inline-flex items-center gap-1 rounded-md bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-300">
        <CheckCircle2 className="size-3.5 text-emerald-600 dark:text-emerald-400" />
        Promovido
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800 dark:bg-amber-900/50 dark:text-amber-300">
      <XCircle className="size-3.5 text-amber-600 dark:text-amber-400" />
      Reprobado
    </span>
  )
}

export default function CU17ConsultarHistorialInscripciones() {
  const { usuario } = useSesion()
  const rol = usuario?.rol

  const [busquedaAdmin, setBusquedaAdmin] = useState('')
  const [ciSeleccionado, setCiSeleccionado] = useState<string | null>(null)

  // Lista de estudiantes visibles para el rol actual
  const { data: listaEstudiantes = [], isLoading: cargandoLista } = useEstudiantesHistorial(
    rol === 'administrador' ? busquedaAdmin : undefined
  )

  // Si es estudiante, fijar su propio CI
  useEffect(() => {
    if (rol === 'estudiante' && usuario?.ci) {
      setCiSeleccionado(usuario.ci)
    } else if (rol === 'tutor' && listaEstudiantes.length > 0 && !ciSeleccionado) {
      // Auto-seleccionar primer hijo si es tutor
      setCiSeleccionado(listaEstudiantes[0].ci)
    }
  }, [rol, usuario?.ci, listaEstudiantes, ciSeleccionado])

  // Consulta de historial del CI seleccionado
  const {
    data: historialData,
    isLoading: cargandoHistorial,
    isError,
    error,
  } = useHistorialInscripciones(ciSeleccionado)

  const estudianteActivo = useMemo(() => {
    if (historialData) {
      return {
        ci: historialData.ci,
        nombre: historialData.nombre_completo,
        rude: historialData.codigo_rude,
      }
    }
    const encontrado = listaEstudiantes.find((e) => e.ci === ciSeleccionado)
    if (encontrado) {
      return {
        ci: encontrado.ci,
        nombre: encontrado.nombre_completo,
        rude: encontrado.codigo_rude,
      }
    }
    return null
  }, [historialData, listaEstudiantes, ciSeleccionado])

  return (
    <div className="space-y-6">
      {/* Encabezado */}
      <div>
        <div className="flex items-center gap-2">
          <History className="size-6 text-primary" />
          <h1 className="text-2xl font-bold tracking-tight">Historial de Inscripciones</h1>
        </div>
        <p className="text-muted-foreground text-sm mt-1">
          {rol === 'estudiante' && 'Consulta el registro histórico de tus gestiones cursadas, cursos y calificaciones anuales.'}
          {rol === 'tutor' && 'Visualiza el historial académico de los estudiantes que tienes a tu cargo.'}
          {rol === 'administrador' && 'Búsqueda y consulta del historial académico de cualquier estudiante registrado.'}
        </p>
      </div>

      {/* Selector según el rol */}
      {rol === 'tutor' && (
        <Card className="border-border/60 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <UserCheck className="size-4 text-primary" />
              Seleccionar estudiante a su cargo
            </CardTitle>
            <CardDescription>
              Seleccione al estudiante para ver sus gestiones académicas cursadas.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {cargandoLista ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
                <Loader2 className="size-4 animate-spin" /> Cargando tutelados...
              </div>
            ) : listaEstudiantes.length === 0 ? (
              <p className="text-sm text-muted-foreground italic">No tiene estudiantes asociados a su cuenta de tutor.</p>
            ) : (
              <div className="max-w-md">
                <Select
                  value={ciSeleccionado ?? ''}
                  onValueChange={(val) => setCiSeleccionado(val)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Seleccione un estudiante" />
                  </SelectTrigger>
                  <SelectContent>
                    {listaEstudiantes.map((est) => (
                      <SelectItem key={est.ci} value={est.ci}>
                        {est.nombre_completo} (CI: {est.ci})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {rol === 'administrador' && (
        <Card className="border-border/60 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Search className="size-4 text-primary" />
              Buscar estudiante
            </CardTitle>
            <CardDescription>
              Busque por carnet de identidad (CI), nombres, apellidos o código RUDE.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2 max-w-md">
              <div className="relative flex-1">
                <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
                <Input
                  placeholder="Ej: 4500001 o Quispe..."
                  className="pl-8"
                  value={busquedaAdmin}
                  onChange={(e) => setBusquedaAdmin(e.target.value)}
                />
              </div>
            </div>

            {cargandoLista ? (
              <div className="flex items-center gap-2 text-sm text-muted-foreground py-2">
                <Loader2 className="size-4 animate-spin" /> Buscando estudiantes...
              </div>
            ) : listaEstudiantes.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 pt-1 max-h-48 overflow-y-auto pr-1">
                {listaEstudiantes.map((est) => {
                  const seleccionado = est.ci === ciSeleccionado
                  return (
                    <button
                      key={est.ci}
                      type="button"
                      onClick={() => setCiSeleccionado(est.ci)}
                      className={`text-left p-3 rounded-lg border text-sm transition-all ${
                        seleccionado
                          ? 'border-primary bg-primary/5 ring-1 ring-primary'
                          : 'border-border/70 bg-card hover:bg-muted/50'
                      }`}
                    >
                      <div className="font-semibold text-foreground truncate">{est.nombre_completo}</div>
                      <div className="text-xs text-muted-foreground flex justify-between mt-1">
                        <span>CI: {est.ci}</span>
                        {est.codigo_rude && <span>RUDE: {est.codigo_rude}</span>}
                      </div>
                      {est.curso_actual && (
                        <div className="text-xs text-primary/80 truncate mt-1">
                          Último: {est.curso_actual}
                        </div>
                      )}
                    </button>
                  )
                })}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground italic">
                {busquedaAdmin ? 'No se encontraron estudiantes con ese criterio.' : 'Mostrando primeros estudiantes activos.'}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Ficha Resumen del Estudiante Seleccionado */}
      {estudianteActivo && (
        <div className="bg-gradient-to-r from-muted/50 via-muted/30 to-background border rounded-xl p-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-full bg-primary/10 text-primary">
              <GraduationCap className="size-6" />
            </div>
            <div>
              <div className="text-xs uppercase font-semibold tracking-wider text-muted-foreground">
                Historial del Estudiante
              </div>
              <div className="text-lg font-bold text-foreground">
                {estudianteActivo.nombre}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="rounded-md border bg-card px-3 py-1.5 text-center">
              <span className="text-xs text-muted-foreground block">Carnet de Identidad</span>
              <span className="font-medium text-foreground">{estudianteActivo.ci}</span>
            </div>
            {estudianteActivo.rude && (
              <div className="rounded-md border bg-card px-3 py-1.5 text-center">
                <span className="text-xs text-muted-foreground block">Código RUDE</span>
                <span className="font-medium text-foreground">{estudianteActivo.rude}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tabla del Historial */}
      <Card className="border-border/60 shadow-sm overflow-hidden">
        <CardHeader className="border-b bg-muted/20 pb-4">
          <CardTitle className="text-base flex items-center justify-between">
            <span className="flex items-center gap-2">
              <CalendarIcon className="size-4 text-primary" />
              Gestiones Académicas Cursadas
            </span>
            {historialData && (
              <span className="text-xs font-normal text-muted-foreground">
                Total gestiones: <span className="font-semibold text-foreground">{historialData.inscripciones.length}</span>
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {cargandoHistorial ? (
            <div className="flex flex-col items-center justify-center py-12 gap-2 text-muted-foreground text-sm">
              <Loader2 className="size-6 animate-spin text-primary" />
              <span>Cargando historial de inscripciones...</span>
            </div>
          ) : isError ? (
            <div className="py-10 text-center text-sm text-destructive px-4">
              {error instanceof Error ? error.message : 'Error al consultar el historial de inscripciones.'}
            </div>
          ) : !ciSeleccionado ? (
            <div className="py-12 text-center text-sm text-muted-foreground">
              Seleccione un estudiante para consultar su historial de inscripciones.
            </div>
          ) : historialData?.inscripciones.length === 0 ? (
            <div className="py-12 text-center text-sm text-muted-foreground italic">
              Este estudiante no cuenta con gestiones o inscripciones registradas en el sistema.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/40 hover:bg-muted/40">
                    <TableHead className="w-24 font-semibold">Gestión</TableHead>
                    <TableHead className="font-semibold">Curso</TableHead>
                    <TableHead className="w-28 font-semibold">Estado</TableHead>
                    <TableHead className="w-32 font-semibold">Inscrito el</TableHead>
                    <TableHead className="font-semibold">Retiro (Fecha / Motivo)</TableHead>
                    <TableHead className="w-36 font-semibold">Resultado Final</TableHead>
                    <TableHead className="w-32 text-right font-semibold">Promedio Anual</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {historialData?.inscripciones.map((item) => (
                    <TableRow key={item.id_inscripcion} className="hover:bg-muted/20">
                      <TableCell className="font-bold text-foreground">
                        <div className="flex items-center gap-1.5">
                          <span className="text-primary font-mono text-sm">{item.anio}</span>
                        </div>
                      </TableCell>
                      <TableCell className="font-medium text-foreground">
                        {item.curso}
                      </TableCell>
                      <TableCell>
                        <BadgeEstado estado={item.estado_inscripcion} />
                      </TableCell>
                      <TableCell className="text-muted-foreground text-sm">
                        {fecha(item.fecha_inscripcion)}
                      </TableCell>
                      <TableCell>
                        {item.fecha_retiro ? (
                          <div className="text-xs space-y-0.5">
                            <span className="font-semibold text-rose-600 dark:text-rose-400">
                              {fecha(item.fecha_retiro)}
                            </span>
                            {item.motivo_retiro && (
                              <p className="text-muted-foreground line-clamp-2 italic">
                                &ldquo;{item.motivo_retiro}&rdquo;
                              </p>
                            )}
                          </div>
                        ) : (
                          <span className="text-muted-foreground text-xs italic">—</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <BadgeResultado resultado={item.resultado_final} />
                      </TableCell>
                      <TableCell className="text-right">
                        {item.promedio_anual !== null && item.promedio_anual !== undefined ? (
                          <span
                            className={`font-mono font-bold px-2 py-0.5 rounded text-sm ${
                              Number(item.promedio_anual) >= 51
                                ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300'
                                : 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300'
                            }`}
                          >
                            {Number(item.promedio_anual).toFixed(2)}
                          </span>
                        ) : (
                          <span className="text-muted-foreground text-xs italic">Sin notas</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

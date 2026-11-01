/**
 * CU24 - Generar y consultar boletín/libreta (incluye centralizador)
 * Paquete: evaluacion
 *
 * Actores ........: Tutor, Estudiante (genera: Administrativo)
 * Rol del sistema : tutor, estudiante, administrador
 * Backend ........: backend/app/paquetes/evaluacion/casos_uso/cu24_generar_consultar_boletin.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  El estudiante tiene calificaciones en el periodo. Tutor y estudiante solo consultan lo suyo.
 * Postcondición: El boletín queda emitido con su promedio; la libreta queda disponible para consulta.
 *
 * Estado: IMPLEMENTADO.
 */
import { useState } from 'react'
import { mensajeError } from '@/nucleo/api'
import { useSesion } from '@/nucleo/auth/contexto'
import { useBoletin, useCentralizador, useEmitirBoletines, useOpcionesPeriodos, useOpcionesCursos } from '../api'
import { useEstudiantesHistorial } from '../api'
import { Button } from '@/componentes/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/componentes/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/componentes/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { Loader2 } from 'lucide-react'
import { toast } from 'sonner'

// Formatea fecha YYYY-MM-DD a DD/MM/YYYY sin conversión de zona horaria
const formatFecha = (fechaStr: string) => {
  const [year, month, day] = fechaStr.split('-')
  return `${day}/${month}/${year}`
}

export default function CU24GenerarConsultarBoletin() {
  const sesion = useSesion()
  const [tab, setTab] = useState<'boletin' | 'centralizador'>('boletin')

  // Cargar períodos y cursos desde el backend
  const { data: periodosData } = useOpcionesPeriodos()
  const { data: cursosData } = useOpcionesCursos()
  const periodos = periodosData?.map(p => ({ id: p.id_periodo, nombre: p.nombre_periodo })) ?? []
  const cursos = cursosData?.map(c => ({ id: c.id_curso, nombre: c.nombre_curso })) ?? []

  // Estados para "Consultar Boletín"
  const [ciEstudiante, setCiEstudiante] = useState<string | null>(null)
  const [idPeriodoB, setIdPeriodoB] = useState<number | null>(null)

  // Calcular CI a consultar según el rol
  const ciAConsultar = sesion.usuario?.rol === 'estudiante' ? sesion.usuario?.ci || null : ciEstudiante

  // Hook useBoletin siempre se llama (arriba del componente, sin condiciones)
  const { data: boletin, isLoading: cargandoBoletin, error: errorBoletin } = useBoletin(ciAConsultar, idPeriodoB)

  // Estados para "Centralizador"
  const [idCurso, setIdCurso] = useState<number | null>(null)
  const [idPeriodoC, setIdPeriodoC] = useState<number | null>(null)
  const { data: centralizador, isLoading: cargandoCentralizador } = useCentralizador(idCurso, idPeriodoC)

  // Estados para "Emitir Boletines"
  const [showEmitir, setShowEmitir] = useState(false)
  const [idPeriodoEmitir, setIdPeriodoEmitir] = useState<number | null>(null)
  const [idCursoEmitir, setIdCursoEmitir] = useState<number | null>(null)
  const { mutate: emitir, isPending: emitiendoBoletines } = useEmitirBoletines()

  // Cargar estudiantes (para tutor)
  const { data: estudiantesData } = useEstudiantesHistorial()
  const estudiantes = estudiantesData?.estudiantes ?? []

  const handleEmitir = () => {
    if (!idPeriodoEmitir) {
      toast.error('Selecciona un período')
      return
    }
    emitir({ id_periodo: idPeriodoEmitir, id_curso: idCursoEmitir ?? undefined }, {
      onSuccess: (data) => {
        toast.success(`${data.cantidad} boletines emitidos`)
        setShowEmitir(false)
      },
      onError: (err: any) => {
        toast.error(err.message || 'Error al emitir boletines')
      },
    })
  }

  const handleImprimir = () => {
    window.print()
  }

  // ADMINISTRADOR: acceso completo
  if (sesion.usuario?.rol === 'administrador') {
    return (
      <div className="space-y-6 p-4">
        <div className="print:hidden">
          <h1 className="text-3xl font-bold">Boletines y Libretas</h1>
          <p className="text-gray-600">Emitir boletines, consultar y ver centralizador académico</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b print:hidden">
          <button
            onClick={() => setTab('boletin')}
            className={`px-4 py-2 font-medium ${tab === 'boletin' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-600'}`}
          >
            Consultar Boletín
          </button>
          <button
            onClick={() => setTab('centralizador')}
            className={`px-4 py-2 font-medium ${tab === 'centralizador' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-600'}`}
          >
            Centralizador
          </button>
        </div>

        {tab === 'boletin' && (
          <div className="space-y-4">
            <Card className="print:hidden">
              <CardHeader>
                <CardTitle>Emitir Boletines</CardTitle>
                <CardDescription>Genera los boletines para un período o curso específico</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Button onClick={() => setShowEmitir(true)} variant="default">
                    Emitir Boletines
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Consultar Boletín</CardTitle>
                <CardDescription>Busca el boletín de un estudiante</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 md:grid-cols-1 print:hidden">
                  <div>
                    <label className="text-sm font-medium">CI Estudiante</label>
                    <input
                      type="text"
                      value={ciEstudiante ?? ''}
                      onChange={(e) => setCiEstudiante(e.target.value || null)}
                      placeholder="4500001"
                      className="mt-1 w-full rounded border p-2"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium">Período</label>
                    <Select value={idPeriodoB?.toString()} onValueChange={(v) => setIdPeriodoB(Number(v))}>
                      <SelectTrigger>
                        <SelectValue placeholder="Selecciona período" />
                      </SelectTrigger>
                      <SelectContent>
                        {periodos.map((p) => (
                          <SelectItem key={p.id} value={p.id.toString()}>
                            {p.nombre}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {cargandoBoletin && <p className="text-gray-500">Cargando boletín...</p>}
                {errorBoletin && <p className="text-red-500">{mensajeError(errorBoletin)}</p>}

                {boletin && (
                  <div className="print-boletin space-y-4 rounded border border-gray-200 bg-white p-6">
                    <div className="flex justify-between">
                      <div>
                        <p className="font-bold">{boletin.nombre_persona} {boletin.apellidos}</p>
                        <p className="text-sm text-gray-600">CI: {boletin.ci}</p>
                        <p className="text-sm text-gray-600">Gestión: {boletin.anio}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold">{boletin.nombre_periodo}</p>
                        <p className="text-sm text-gray-600">Emitido: {formatFecha(boletin.fecha_emision_b)}</p>
                      </div>
                    </div>

                    {boletin.nombre_curso && (
                      <p className="border-t pt-2 font-medium">Curso: {boletin.nombre_curso}</p>
                    )}

                    {/* Notas por materia */}
                    <div className="border-t pt-4">
                      <h3 className="mb-3 font-bold">Notas por Materia</h3>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Materia</TableHead>
                            <TableHead className="text-right">Nota Final</TableHead>
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

                    {/* Promedio General */}
                    <div className="border-t bg-blue-50 p-4">
                      <p className="text-sm text-gray-600">Promedio General</p>
                      <p className="text-2xl font-bold text-blue-600">{boletin.promedio_general_b.toFixed(2)}</p>
                    </div>

                    <div className="border-t pt-4">
                      <p className="text-sm font-medium">Observaciones</p>
                      <p className="mt-1 text-gray-700">
                        {boletin.observaciones_generales_boletin || 'Sin observaciones'}
                      </p>
                    </div>
                  </div>
                )}

                {boletin && (
                  <Button onClick={handleImprimir} variant="outline" className="print:hidden">
                    Imprimir
                  </Button>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {tab === 'centralizador' && (
          <Card>
            <CardHeader>
              <CardTitle>Centralizador Académico</CardTitle>
              <CardDescription>Notas de un curso por período</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 md:grid-cols-1 print:hidden">
                <div>
                  <label className="text-sm font-medium">Curso</label>
                  <Select value={idCurso?.toString()} onValueChange={(v) => setIdCurso(Number(v))}>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecciona curso" />
                    </SelectTrigger>
                    <SelectContent>
                      {cursos.map((c) => (
                        <SelectItem key={c.id} value={c.id.toString()}>
                          {c.nombre}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="text-sm font-medium">Período</label>
                  <Select value={idPeriodoC?.toString()} onValueChange={(v) => setIdPeriodoC(Number(v))}>
                    <SelectTrigger>
                      <SelectValue placeholder="Selecciona período" />
                    </SelectTrigger>
                    <SelectContent>
                      {periodos.map((p) => (
                        <SelectItem key={p.id} value={p.id.toString()}>
                          {p.nombre}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {cargandoCentralizador && <p className="text-gray-500">Cargando centralizador...</p>}

              {centralizador && (
                <div className="overflow-x-auto rounded border">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="border-r border-b p-2 text-left font-semibold">Estudiante</th>
                        {/* Dinamicamente agregar columnas de materias */}
                        {centralizador.filas.length > 0 &&
                          centralizador.filas[0].notas.map((nota) => (
                            <th key={nota.id_materia} className="border-r border-b p-2 text-center text-xs font-semibold whitespace-normal max-w-xs">
                              {nota.materia}
                            </th>
                          ))}
                        <th className="border-b p-2 text-center font-semibold bg-blue-50">Promedio</th>
                      </tr>
                    </thead>
                    <tbody>
                      {centralizador.filas.map((fila, idx) => (
                        <tr key={fila.ci} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                          <td className="border-r border-b p-2 text-sm">
                            {fila.nombre_persona} {fila.apellidos}
                          </td>
                          {fila.notas.map((nota) => (
                            <td key={nota.id_materia} className="border-r border-b p-2 text-center text-sm font-semibold">
                              {nota.nota_final.toFixed(2)}
                            </td>
                          ))}
                          <td className="border-b p-2 text-center font-bold bg-blue-50">
                            {fila.promedio_estudiante?.toFixed(2) ?? '—'}
                          </td>
                        </tr>
                      ))}
                      {centralizador.filas.length > 0 && (
                        <tr className="bg-blue-100 font-bold">
                          <td className="border-r border-b p-2 text-sm">Promedio por Materia</td>
                          {centralizador.filas[0].notas.map((nota) => {
                            const promedio = centralizador.filas.reduce((sum, fila) => {
                              const notaFila = fila.notas.find(n => n.id_materia === nota.id_materia)
                              return sum + (notaFila?.nota_final ?? 0)
                            }, 0) / centralizador.filas.length
                            return (
                              <td key={nota.id_materia} className="border-r border-b p-2 text-center">
                                {promedio.toFixed(2)}
                              </td>
                            )
                          })}
                          <td className="border-b p-2 text-center">
                            {(centralizador.filas.reduce((sum, fila) => sum + (fila.promedio_estudiante ?? 0), 0) / centralizador.filas.length).toFixed(2)}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}

              {centralizador && (
                <Button onClick={handleImprimir} variant="outline" className="print:hidden">
                  Imprimir Centralizador
                </Button>
              )}
            </CardContent>
          </Card>
        )}

        {/* Modal Emitir */}
        <Dialog open={showEmitir} onOpenChange={setShowEmitir}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Emitir Boletines</DialogTitle>
              <DialogDescription>
                Confirma la emisión de boletines. Puedes emitir para un período completo o solo para un curso.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Período *</label>
                <Select value={idPeriodoEmitir?.toString()} onValueChange={(v) => setIdPeriodoEmitir(Number(v))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecciona período" />
                  </SelectTrigger>
                  <SelectContent>
                    {periodos.map((p) => (
                      <SelectItem key={p.id} value={p.id.toString()}>
                        {p.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Curso (opcional)</label>
                <Select value={idCursoEmitir?.toString() ?? ''} onValueChange={(v) => setIdCursoEmitir(v ? Number(v) : null)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Todos los cursos" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">Todos los cursos</SelectItem>
                    {cursos.map((c) => (
                      <SelectItem key={c.id} value={c.id.toString()}>
                        {c.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowEmitir(false)}>
                Cancelar
              </Button>
              <Button onClick={handleEmitir} disabled={emitiendoBoletines} variant="default">
                {emitiendoBoletines ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                Emitir
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    )
  }

  // TUTOR: consulta estudiantes a su cargo
  if (sesion.usuario?.rol === 'tutor') {
    return (
      <div className="space-y-6 p-4">
        <div>
          <h1 className="text-3xl font-bold">Boletín de mis Estudiantes</h1>
          <p className="text-gray-600">Consulta los boletines de tus estudiantes</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Consultar Boletín</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4 md:grid-cols-1">
              <div>
                <label className="text-sm font-medium">Estudiante</label>
                <Select value={ciEstudiante ?? ''} onValueChange={(v) => setCiEstudiante(v || null)}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecciona estudiante" />
                  </SelectTrigger>
                  <SelectContent>
                    {estudiantes.map((est) => (
                      <SelectItem key={est.ci} value={est.ci}>
                        {est.nombre_persona} {est.apellidos} ({est.ci})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Período</label>
                <Select value={idPeriodoB?.toString()} onValueChange={(v) => setIdPeriodoB(Number(v))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Selecciona período" />
                  </SelectTrigger>
                  <SelectContent>
                    {periodos.map((p) => (
                      <SelectItem key={p.id} value={p.id.toString()}>
                        {p.nombre}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {cargandoBoletin && <p className="text-gray-500">Cargando boletín...</p>}
            {errorBoletin && <p className="text-red-500">{mensajeError(errorBoletin)}</p>}

            {boletin && (
              <div className="print-boletin space-y-4 rounded border border-gray-200 bg-white p-6">
                <div className="flex justify-between">
                  <div>
                    <p className="font-bold">{boletin.nombre_persona} {boletin.apellidos}</p>
                    <p className="text-sm text-gray-600">CI: {boletin.ci}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold">{boletin.nombre_periodo}</p>
                    <p className="text-sm text-gray-600">Emitido: {new Date(boletin.fecha_emision_b).toLocaleDateString()}</p>
                  </div>
                </div>

                {boletin.nombre_curso && (
                  <p className="border-t pt-2 font-medium">Curso: {boletin.nombre_curso}</p>
                )}

                <div className="border-t pt-4">
                  <h3 className="mb-3 font-bold">Notas por Materia</h3>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Materia</TableHead>
                        <TableHead className="text-right">Nota Final</TableHead>
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
                  <p className="text-sm text-gray-600">Promedio General</p>
                  <p className="text-2xl font-bold text-blue-600">{boletin.promedio_general_b.toFixed(2)}</p>
                </div>

                <div className="border-t pt-4">
                  <p className="text-sm font-medium">Observaciones</p>
                  <p className="mt-1 text-gray-700">
                    {boletin.observaciones_generales_boletin || 'Sin observaciones'}
                  </p>
                </div>
              </div>
            )}

            {boletin && (
              <Button onClick={handleImprimir} variant="outline">
                Imprimir
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  // Auto-seleccionar primer período cuando lleguen los datos (para estudiante)
  if (sesion.usuario?.rol === 'estudiante' && periodos.length > 0 && idPeriodoB === null) {
    setIdPeriodoB(periodos[0].id)
  }

  // ESTUDIANTE: consulta su boletín
  if (sesion.usuario?.rol === 'estudiante') {
    return (
      <div className="space-y-6 p-4">
        <div className="print:hidden">
          <h1 className="text-3xl font-bold">Mi Boletín</h1>
          <p className="text-gray-600">Consulta tu boletín académico</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Selecciona Período</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="print:hidden">
              <label className="text-sm font-medium">Período</label>
              <Select value={idPeriodoB?.toString() ?? ''} onValueChange={(v) => setIdPeriodoB(Number(v))}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecciona período" />
                </SelectTrigger>
                <SelectContent>
                  {periodos.map((p) => (
                    <SelectItem key={p.id} value={p.id.toString()}>
                      {p.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {cargandoBoletin && <p className="text-gray-500">Cargando boletín...</p>}
            {errorBoletin && <p className="text-red-500">{mensajeError(errorBoletin)}</p>}
            {!boletin && !cargandoBoletin && idPeriodoB && <p className="text-yellow-600">No hay boletín emitido para este período.</p>}

            {boletin && (
              <div className="print-boletin space-y-4 rounded border border-gray-200 bg-white p-6">
                <div className="flex justify-between">
                  <div>
                    <p className="font-bold">{boletin.nombre_persona} {boletin.apellidos}</p>
                    <p className="text-sm text-gray-600">CI: {boletin.ci}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold">{boletin.nombre_periodo}</p>
                    <p className="text-sm text-gray-600">Emitido: {formatFecha(boletin.fecha_emision_b)}</p>
                  </div>
                </div>

                {boletin.nombre_curso && (
                  <p className="border-t pt-2 font-medium">Curso: {boletin.nombre_curso}</p>
                )}

                <div className="border-t pt-4">
                  <h3 className="mb-3 font-bold">Notas por Materia</h3>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Materia</TableHead>
                        <TableHead className="text-right">Nota Final</TableHead>
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
                  <p className="text-sm text-gray-600">Promedio General</p>
                  <p className="text-2xl font-bold text-blue-600">{boletin.promedio_general_b.toFixed(2)}</p>
                </div>

                <div className="border-t pt-4">
                  <p className="text-sm font-medium">Observaciones</p>
                  <p className="mt-1 text-gray-700">
                    {boletin.observaciones_generales_boletin || 'Sin observaciones'}
                  </p>
                </div>
              </div>
            )}

            {boletin && (
              <Button onClick={handleImprimir} variant="outline" className="print:hidden">
                Imprimir
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }
}

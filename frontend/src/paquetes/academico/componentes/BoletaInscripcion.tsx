/**
 * Boleta de inscripción (CU16): datos del estudiante, gestión y curso, materias con su docente y aula,
 * y horario semanal del curso. Se imprime con window.print(): el resto de la página lleva print:hidden.
 *
 * El horario se muestra como tabla ordenada por día y hora. Cuando exista
 * paquetes/horarios/componentes/GrillaHorario.tsx (CU19/CU20) se puede usar en modo solo lectura.
 */
import type { ReactNode } from 'react'
import { ArrowLeftIcon, PrinterIcon } from 'lucide-react'
import { InsigniaEstado } from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { documento, fecha } from '@/lib/formato'
import type { Boleta } from '../schemas'

const DIAS: Record<string, string> = {
  lunes: 'Lunes',
  martes: 'Martes',
  miercoles: 'Miércoles',
  jueves: 'Jueves',
  viernes: 'Viernes',
  sabado: 'Sábado',
  domingo: 'Domingo',
}

function Dato({ etiqueta, children }: { etiqueta: string; children: ReactNode }) {
  return (
    <div>
      <p className="text-xs text-slate-500">{etiqueta}</p>
      <p className="font-medium text-slate-900">{children}</p>
    </div>
  )
}

export default function BoletaInscripcion({ boleta, onVolver }: { boleta: Boleta; onVolver: () => void }) {
  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:justify-between print:hidden">
        <Button variant="outline" onClick={onVolver}>
          <ArrowLeftIcon /> Volver a la búsqueda
        </Button>
        <Button onClick={() => window.print()}>
          <PrinterIcon /> Imprimir boleta
        </Button>
      </div>

      <article className="space-y-5 rounded-xl border bg-white p-4 shadow-sm sm:p-6 print:border-0 print:p-0 print:shadow-none">
        <header className="flex flex-col gap-1 border-b pb-4 text-center">
          <p className="text-sm text-slate-500">Unidad Educativa “Mariscal Sucre G”</p>
          <h2 className="text-xl font-bold tracking-tight text-[#12306B]">Boleta de inscripción — Gestión {boleta.gestion}</h2>
          <p className="text-sm text-slate-500">
            N.º {String(boleta.id_inscripcion).padStart(6, '0')} · Fecha de inscripción: {fecha(boleta.fecha_inscripcion)}
          </p>
        </header>

        <section className="grid gap-3 sm:grid-cols-3">
          <h3 className="text-sm font-semibold text-slate-700 sm:col-span-3">Datos del estudiante</h3>
          <Dato etiqueta="Nombre completo">{boleta.apellidos}, {boleta.nombre_persona}</Dato>
          <Dato etiqueta="C.I.">{documento(boleta.ci, boleta.expedido)}</Dato>
          <Dato etiqueta="Código RUDE">{boleta.rude ?? '—'}</Dato>
          <Dato etiqueta="Fecha de nacimiento">{fecha(boleta.fecha_nacimiento)}</Dato>
          <Dato etiqueta="Curso">{boleta.grado} “{boleta.paralelo}” — {boleta.nivel}</Dato>
          <Dato etiqueta="Estado de la inscripción"><InsigniaEstado estado={boleta.estado_inscripcion} /></Dato>
        </section>

        <section className="space-y-2">
          <h3 className="text-sm font-semibold text-slate-700">Materias del curso</h3>
          <div className="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead className="pl-4">Materia</TableHead>
                  <TableHead>Docente</TableHead>
                  <TableHead className="pr-4 text-center">Aula</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {boleta.materias.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={3} className="h-16 text-center text-slate-500">El grado no tiene materias en su plan de estudios.</TableCell>
                  </TableRow>
                ) : (
                  boleta.materias.map((m) => (
                    <TableRow key={m.materia}>
                      <TableCell className="pl-4 font-medium">{m.materia}</TableCell>
                      <TableCell>{m.docente ?? <span className="text-slate-400">Sin asignar</span>}</TableCell>
                      <TableCell className="pr-4 text-center">{m.aula ?? '—'}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </section>

        <section className="space-y-2 print:break-inside-avoid">
          <h3 className="text-sm font-semibold text-slate-700">Horario semanal</h3>
          <div className="rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead className="pl-4">Día</TableHead>
                  <TableHead>Hora</TableHead>
                  <TableHead>Materia</TableHead>
                  <TableHead>Docente</TableHead>
                  <TableHead className="pr-4 text-center">Aula</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {boleta.horario.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="h-16 text-center text-slate-500">El curso todavía no tiene horario registrado.</TableCell>
                  </TableRow>
                ) : (
                  boleta.horario.map((b, i) => (
                    <TableRow key={i}>
                      <TableCell className="pl-4 font-medium">{DIAS[b.dia] ?? b.dia}</TableCell>
                      <TableCell className="whitespace-nowrap">{b.hora_inicio.slice(0, 5)} – {b.hora_final.slice(0, 5)}</TableCell>
                      <TableCell>{b.materia}</TableCell>
                      <TableCell>{b.docente}</TableCell>
                      <TableCell className="pr-4 text-center">{b.aula}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </section>

        <footer className="hidden grid-cols-2 gap-10 pt-16 text-center text-sm text-slate-600 print:grid">
          <p className="border-t pt-2">Firma del padre, madre o tutor</p>
          <p className="border-t pt-2">Secretaría</p>
        </footer>
      </article>
    </div>
  )
}

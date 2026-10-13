/**
 * CU20 - Consultar horarios
 * Paquete: horarios
 *
 * Actores ........: Docente, Estudiante, Tutor, Administrativo
 * Rol del sistema : profesor, estudiante, tutor, administrador
 * Backend ........: backend/app/paquetes/horarios/casos_uso/cu20_consultar_horarios.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Horario semanal en solo lectura (con botón Imprimir). Lo que se puede elegir depende del rol
 * (el backend lo valida): administrador cualquier curso o docente; profesor su horario y sus
 * cursos; estudiante su curso; tutor el curso de cada uno de sus estudiantes.
 *
 * Precondición:  Sesión iniciada.
 * Postcondición: Se muestra el horario semanal del curso o del profesor. No se modifica nada.
 *
 * Estado: IMPLEMENTADO.
 */
import { useMemo, useState } from 'react'
import { Loader2Icon, PrinterIcon } from 'lucide-react'
import { Campo, EncabezadoPagina } from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { mensajeError } from '@/nucleo/api'
import { useHorarioConsulta, useOpcionesConsulta } from '../api'
import GrillaHorario from '../componentes/GrillaHorario'
import type { FiltroConsulta, OpcionesConsulta } from '../schemas'

type Opcion = { valor: string; etiqueta: string; filtro: FiltroConsulta | null }
type Grupo = { titulo: string; opciones: Opcion[] }

/** Opciones del selector según el rol (el backend ya filtró lo que el usuario puede ver). */
function gruposPorRol(o: OpcionesConsulta): Grupo[] {
  const cursos = o.cursos.map((c) => ({ valor: `curso:${c.id_curso}`, etiqueta: c.nombre_curso, filtro: { id_curso: c.id_curso } }))
  const docentes = o.docentes.map((d) => ({ valor: `docente:${d.ci}`, etiqueta: d.nombre, filtro: { ci_profesor: d.ci } }))
  switch (o.rol) {
    case 'administrador':
      return [{ titulo: 'Cursos', opciones: cursos }, { titulo: 'Docentes', opciones: docentes }]
    case 'profesor':
      return [
        { titulo: 'Mi horario', opciones: docentes.map((d) => ({ ...d, etiqueta: `Mi horario (${d.etiqueta})` })) },
        { titulo: 'Cursos donde dicto', opciones: cursos },
      ]
    case 'tutor':
      return [{
        titulo: 'Mis estudiantes',
        opciones: o.estudiantes.map((e) => ({
          valor: `estudiante:${e.ci}`,
          etiqueta: e.nombre_curso ? `${e.nombre} — ${e.nombre_curso}` : `${e.nombre} (sin inscripción activa)`,
          filtro: e.id_curso ? { id_curso: e.id_curso } : null,
        })),
      }]
    default:
      return [{ titulo: 'Mi curso', opciones: cursos }]
  }
}

export default function CU20ConsultarHorarios() {
  const opciones = useOpcionesConsulta()
  const grupos = useMemo(() => (opciones.data ? gruposPorRol(opciones.data) : []), [opciones.data])
  const todas = grupos.flatMap((g) => g.opciones)
  const [elegido, setElegido] = useState<string | null>(null)
  // Por defecto: la primera opción con horario (salvo el administrador, que elige)
  const valor = elegido ?? (opciones.data?.rol === 'administrador' ? null : todas.find((o) => o.filtro)?.valor ?? null)
  const filtro = todas.find((o) => o.valor === valor)?.filtro ?? null
  const horario = useHorarioConsulta(filtro)
  const datos = horario.data

  return (
    <div className="space-y-5">
      <div className="print:hidden">
        <EncabezadoPagina
          titulo="Consultar horarios"
          descripcion="Horario semanal de clases de la gestión abierta."
          accion={
            <Button size="lg" variant="outline" disabled={!datos?.bloques.length} onClick={() => window.print()}>
              <PrinterIcon /> Imprimir
            </Button>
          }
        />
      </div>

      <div className="rounded-xl border bg-white shadow-sm print:border-0 print:shadow-none">
        <div className="grid gap-3 p-4 md:grid-cols-[minmax(0,420px)_1fr] md:items-end print:hidden">
          {opciones.isLoading ? (
            <p className="text-sm text-slate-500">Cargando...</p>
          ) : opciones.isError ? (
            <p className="text-sm text-destructive">{mensajeError(opciones.error)}</p>
          ) : !opciones.data?.gestion ? (
            <p className="text-sm text-slate-500">No hay una gestión abierta.</p>
          ) : !todas.length ? (
            <p className="text-sm text-slate-500">
              {opciones.data.rol === 'estudiante'
                ? 'No tiene una inscripción activa en la gestión abierta.'
                : 'No hay horarios que pueda consultar.'}
            </p>
          ) : (
            <Campo etiqueta="Horario de">
              <Select value={valor ?? ''} onValueChange={setElegido}>
                <SelectTrigger className="w-full"><SelectValue placeholder="Seleccione un curso o docente" /></SelectTrigger>
                <SelectContent>
                  {grupos.filter((g) => g.opciones.length).map((g) => (
                    <SelectGroup key={g.titulo}>
                      <SelectLabel>{g.titulo}</SelectLabel>
                      {g.opciones.map((o) => (
                        <SelectItem key={o.valor} value={o.valor} disabled={!o.filtro}>{o.etiqueta}</SelectItem>
                      ))}
                    </SelectGroup>
                  ))}
                </SelectContent>
              </Select>
            </Campo>
          )}
        </div>

        {filtro === null ? (
          todas.length > 0 && (
            <p className="border-t px-4 py-10 text-center text-slate-500 print:hidden">Seleccione un curso o un docente.</p>
          )
        ) : horario.isLoading ? (
          <p className="flex items-center justify-center gap-2 border-t px-4 py-10 text-slate-500">
            <Loader2Icon className="size-4 animate-spin" /> Cargando...
          </p>
        ) : horario.isError ? (
          <p className="border-t px-4 py-10 text-center text-slate-500">{mensajeError(horario.error)}</p>
        ) : (
          datos && (
            <div className="border-t print:border-0">
              <div className="px-4 pt-4 print:px-0 print:pt-0">
                <p className="hidden text-sm text-slate-500 print:block">Unidad Educativa “Mariscal Sucre G”</p>
                <h2 className="text-lg font-semibold text-slate-900">
                  Horario {datos.tipo === 'curso' ? 'del curso' : 'del docente'} {datos.titulo}
                </h2>
                <p className="text-sm text-slate-500">Gestión {datos.gestion}</p>
              </div>
              {datos.bloques.length ? (
                <div className="md:p-2 print:p-0 print:pt-3">
                  <GrillaHorario bloques={datos.bloques} detalle={datos.tipo === 'curso' ? 'docente' : 'curso'} />
                </div>
              ) : (
                <p className="px-4 py-10 text-center text-slate-500">
                  Todavía no hay horario registrado para {datos.tipo === 'curso' ? 'este curso' : 'este docente'}.
                </p>
              )}
            </div>
          )
        )}
      </div>
    </div>
  )
}

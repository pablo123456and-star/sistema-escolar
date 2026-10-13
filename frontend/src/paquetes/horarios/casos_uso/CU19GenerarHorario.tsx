/**
 * CU19 - Generar horario de clases (aula, profesor, materia)
 * Paquete: horarios
 *
 * Actores ........: Admin. académico
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/horarios/casos_uso/cu19_generar_horario.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Elegir un curso de la gestión abierta, ver su horario semanal en la grilla y agregar,
 * modificar o eliminar bloques (asignación + día + horas). Los choques de docente, aula o
 * curso los detecta la BD y se muestran en pantalla.
 *
 * Precondición:  La asignación existe y la gestión está abierta.
 * Postcondición: El bloque de horario queda registrado sin choques de profesor, aula ni curso en la misma gestión.
 *
 * Estado: IMPLEMENTADO.
 */
import { useState } from 'react'
import { Link } from 'react-router'
import { Controller, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import { CalendarPlusIcon, Loader2Icon, TrashIcon } from 'lucide-react'
import Confirmar from '@/componentes/Confirmar'
import { Campo, EncabezadoPagina } from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/componentes/ui/dialog'
import { Input } from '@/componentes/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { mensajeError } from '@/nucleo/api'
import { useAgregarBloque, useCursosHorario, useEliminarBloque, useHorarioCurso, useModificarBloque } from '../api'
import GrillaHorario from '../componentes/GrillaHorario'
import { DIAS, esquemaBloque, type AsignacionBloque, type Bloque, type DatosBloque } from '../schemas'

export default function CU19GenerarHorario() {
  const cursos = useCursosHorario()
  const [idCurso, setIdCurso] = useState<number | null>(null)
  const horario = useHorarioCurso(idCurso)
  const [formulario, setFormulario] = useState<{ bloque: Bloque | null } | null>(null)
  const [aEliminar, setAEliminar] = useState<Bloque | null>(null)
  const eliminar = useEliminarBloque()

  const confirmarEliminar = async () => {
    if (!aEliminar) return
    try {
      await eliminar.mutateAsync(aEliminar.id_horario)
      toast.success('Bloque eliminado.')
      setAEliminar(null)
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  const datos = horario.data
  const sinAsignaciones = datos && datos.asignaciones.length === 0

  return (
    <div className="space-y-5">
      <EncabezadoPagina
        titulo="Generar horario de clases"
        descripcion="Arme el horario semanal de cada curso a partir de sus asignaciones (materia, docente y aula)."
        accion={
          <Button size="lg" disabled={!datos || sinAsignaciones} onClick={() => setFormulario({ bloque: null })}>
            <CalendarPlusIcon /> Agregar bloque
          </Button>
        }
      />

      <div className="rounded-xl border bg-white shadow-sm">
        <div className="grid gap-3 p-4 md:grid-cols-[minmax(0,420px)_1fr] md:items-end">
          <Campo etiqueta="Curso">
            <Select value={idCurso ? String(idCurso) : ''} onValueChange={(v) => setIdCurso(Number(v))}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder={cursos.isLoading ? 'Cargando...' : 'Seleccione un curso'} />
              </SelectTrigger>
              <SelectContent>
                {cursos.data?.map((c) => (
                  <SelectItem key={c.id_curso} value={String(c.id_curso)}>
                    {c.nombre_curso} ({c.bloques} {c.bloques === 1 ? 'bloque' : 'bloques'})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Campo>
          {cursos.isError && <p className="text-sm text-destructive">{mensajeError(cursos.error)}</p>}
        </div>

        {idCurso === null ? (
          <p className="border-t px-4 py-10 text-center text-slate-500">Seleccione un curso para ver y armar su horario.</p>
        ) : horario.isLoading ? (
          <p className="flex items-center justify-center gap-2 border-t px-4 py-10 text-slate-500">
            <Loader2Icon className="size-4 animate-spin" /> Cargando...
          </p>
        ) : horario.isError ? (
          <p className="border-t px-4 py-10 text-center text-slate-500">{mensajeError(horario.error)}</p>
        ) : sinAsignaciones ? (
          <div className="space-y-2 border-t px-4 py-10 text-center">
            <p className="font-medium text-slate-700">Curso sin asignaciones</p>
            <p className="text-sm text-slate-500">
              Primero asigne docente y aula a sus materias en{' '}
              <Link to="/academico/asignaciones" className="text-blue-600 underline">Asignación de profesores</Link>.
            </p>
          </div>
        ) : (
          datos && (
            <>
              <ResumenAsignaciones asignaciones={datos.asignaciones} />
              {datos.bloques.length ? (
                <div className="border-t md:p-2">
                  <GrillaHorario
                    bloques={datos.bloques}
                    detalle="docente"
                    onEditar={(b) => setFormulario({ bloque: b })}
                    onEliminar={setAEliminar}
                  />
                </div>
              ) : (
                <p className="border-t px-4 py-10 text-center text-slate-500">
                  {datos.nombre_curso} todavía no tiene bloques. Use “Agregar bloque”.
                </p>
              )}
            </>
          )
        )}
      </div>

      {formulario && datos && (
        <DialogoBloque
          idCurso={datos.id_curso}
          asignaciones={datos.asignaciones}
          bloque={formulario.bloque}
          onCerrar={() => setFormulario(null)}
        />
      )}
      <Confirmar
        abierto={!!aEliminar}
        onCambiar={(v) => !v && setAEliminar(null)}
        titulo="Eliminar bloque"
        descripcion={aEliminar ? `Se quitará ${aEliminar.nombre_materia} del ${DIAS.find((d) => d.dia === aEliminar.dia)?.etiqueta.toLowerCase()} de ${aEliminar.hora_inicio.slice(0, 5)} a ${aEliminar.hora_final.slice(0, 5)}.` : ''}
        textoConfirmar="Eliminar"
        icono={<TrashIcon />}
        peligro
        ocupado={eliminar.isPending}
        onConfirmar={confirmarEliminar}
      />
    </div>
  )
}

/** Materias del curso con su docente, aula y cuántos bloques tienen frente a su carga horaria. */
function ResumenAsignaciones({ asignaciones }: { asignaciones: AsignacionBloque[] }) {
  return (
    <div className="flex flex-wrap gap-2 border-t px-4 py-3">
      {asignaciones.map((a) => (
        <span key={a.id_asignacion} className="rounded-md border bg-slate-50 px-2 py-1 text-xs text-slate-600">
          <span className="font-medium text-slate-800">{a.nombre_materia}</span> · {a.profesor} · {a.aula} ·{' '}
          <span className={a.bloques === 0 ? 'text-amber-600' : 'text-emerald-700'}>
            {a.bloques} {a.bloques === 1 ? 'bloque' : 'bloques'}
          </span>
        </span>
      ))}
    </div>
  )
}

function DialogoBloque({
  idCurso,
  asignaciones,
  bloque,
  onCerrar,
}: {
  idCurso: number
  asignaciones: AsignacionBloque[]
  bloque: Bloque | null
  onCerrar: () => void
}) {
  const agregar = useAgregarBloque()
  const modificar = useModificarBloque()
  const form = useForm<DatosBloque>({
    resolver: zodResolver(esquemaBloque),
    defaultValues: bloque
      ? {
          id_asignacion: String(bloque.id_asignacion),
          dia: bloque.dia,
          hora_inicio: bloque.hora_inicio.slice(0, 5),
          hora_final: bloque.hora_final.slice(0, 5),
        }
      : { id_asignacion: '', dia: '', hora_inicio: '', hora_final: '' },
  })

  const guardar = form.handleSubmit(async (d) => {
    const cuerpo = { ...d, id_asignacion: Number(d.id_asignacion) }
    try {
      if (bloque) {
        await modificar.mutateAsync({ id_horario: bloque.id_horario, cuerpo })
        toast.success('Bloque actualizado.')
      } else {
        await agregar.mutateAsync({ id_curso: idCurso, cuerpo })
        toast.success('Bloque agregado al horario.')
      }
      onCerrar()
    } catch (e) {
      toast.error(mensajeError(e))
    }
  })

  const e = form.formState.errors
  const ocupado = agregar.isPending || modificar.isPending
  return (
    <Dialog open onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{bloque ? 'Editar bloque' : 'Agregar bloque'}</DialogTitle>
          <DialogDescription>Elija la materia (con su docente y aula), el día y el horario de la clase.</DialogDescription>
        </DialogHeader>
        <form id="form-bloque" onSubmit={guardar} className="grid gap-3 sm:grid-cols-2">
          <Campo etiqueta="Materia · docente · aula" error={e.id_asignacion?.message} className="sm:col-span-2">
            <Controller
              control={form.control}
              name="id_asignacion"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger className="w-full"><SelectValue placeholder="Seleccione" /></SelectTrigger>
                  <SelectContent>
                    {asignaciones.map((a) => (
                      <SelectItem key={a.id_asignacion} value={String(a.id_asignacion)}>
                        {a.nombre_materia} · {a.profesor} · {a.aula}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </Campo>
          <Campo etiqueta="Día" error={e.dia?.message} className="sm:col-span-2">
            <Controller
              control={form.control}
              name="dia"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger className="w-full"><SelectValue placeholder="Seleccione" /></SelectTrigger>
                  <SelectContent>
                    {DIAS.map((d) => <SelectItem key={d.dia} value={d.dia}>{d.etiqueta}</SelectItem>)}
                  </SelectContent>
                </Select>
              )}
            />
          </Campo>
          <Campo etiqueta="Hora de inicio" error={e.hora_inicio?.message} htmlFor="hora_inicio">
            <Input id="hora_inicio" type="time" {...form.register('hora_inicio')} />
          </Campo>
          <Campo etiqueta="Hora de fin" error={e.hora_final?.message} htmlFor="hora_final">
            <Input id="hora_final" type="time" {...form.register('hora_final')} />
          </Campo>
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={onCerrar} disabled={ocupado}>Cancelar</Button>
          <Button type="submit" form="form-bloque" disabled={ocupado}>
            {ocupado && <Loader2Icon className="animate-spin" />} {bloque ? 'Guardar cambios' : 'Agregar'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

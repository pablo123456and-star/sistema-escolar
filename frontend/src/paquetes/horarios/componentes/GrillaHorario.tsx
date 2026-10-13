/**
 * Grilla semanal de horario (CU19 y CU20; también la puede usar la boleta del CU16).
 * Días en columnas, franjas horarias en filas; cada bloque muestra materia, docente y/o curso y aula.
 *
 *  - Solo lectura: <GrillaHorario bloques={...} detalle="curso" />
 *  - Editable (CU19): pasar onEditar y onEliminar para mostrar los botones en cada bloque.
 *
 * En celular se muestra como lista por día (sin scroll horizontal); al imprimir siempre sale la grilla.
 */
import { cn } from 'cn'
import { PencilIcon, TrashIcon } from 'lucide-react'
import { BotonAccion } from '@/componentes/comunes'
import { DIAS, type Bloque } from '../schemas'

type Props = {
  bloques: Bloque[]
  /** Qué mostrar debajo de la materia: el docente (horario de un curso) o el curso (horario de un docente). */
  detalle: 'docente' | 'curso'
  onEditar?: (bloque: Bloque) => void
  onEliminar?: (bloque: Bloque) => void
}

// Un color por materia para distinguir los bloques a simple vista
const COLORES = [
  'border-blue-500 bg-blue-50/70',
  'border-emerald-500 bg-emerald-50/70',
  'border-violet-500 bg-violet-50/70',
  'border-amber-500 bg-amber-50/70',
  'border-rose-500 bg-rose-50/70',
  'border-cyan-500 bg-cyan-50/70',
  'border-orange-500 bg-orange-50/70',
  'border-slate-500 bg-slate-50',
]

const hhmm = (hora: string) => hora.slice(0, 5)

export default function GrillaHorario({ bloques, detalle, onEditar, onEliminar }: Props) {
  // Lunes a viernes siempre; sábado y domingo solo si tienen clases
  const dias = DIAS.filter((d) => (d.dia !== 'sabado' && d.dia !== 'domingo') || bloques.some((b) => b.dia === d.dia))
  const franjas = [...new Set(bloques.map((b) => `${hhmm(b.hora_inicio)}-${hhmm(b.hora_final)}`))].sort()
  const materias = [...new Set(bloques.map((b) => b.id_materia))]
  const color = (b: Bloque) => COLORES[materias.indexOf(b.id_materia) % COLORES.length]
  const editable = !!(onEditar || onEliminar)

  const tarjeta = (b: Bloque) => (
    <div key={b.id_horario} className={cn('rounded-md border-l-4 px-2 py-1.5 shadow-xs print:shadow-none', color(b))}>
      <p className="font-medium text-slate-900">{b.nombre_materia}</p>
      <p className="text-xs text-slate-600">{detalle === 'docente' ? b.profesor : b.nombre_curso}</p>
      <p className="text-xs text-slate-500">Aula {b.aula}</p>
      {editable && (
        <div className="mt-1.5 flex justify-end gap-1 print:hidden">
          {onEditar && (
            <BotonAccion etiqueta="Editar bloque" tono="ambar" onClick={() => onEditar(b)}>
              <PencilIcon />
            </BotonAccion>
          )}
          {onEliminar && (
            <BotonAccion etiqueta="Eliminar bloque" tono="rojo" onClick={() => onEliminar(b)}>
              <TrashIcon />
            </BotonAccion>
          )}
        </div>
      )}
    </div>
  )

  if (!bloques.length) return null

  return (
    <>
      {/* Escritorio e impresión: grilla */}
      <div className="hidden md:block print:block">
        <table className="w-full table-fixed border-collapse text-sm">
          <thead>
            <tr className="bg-slate-50 text-left text-slate-600">
              <th className="w-28 px-3 py-2 font-medium">Hora</th>
              {dias.map((d) => (
                <th key={d.dia} className="px-3 py-2 font-medium">{d.etiqueta}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {franjas.map((franja) => {
              const [inicio, fin] = franja.split('-')
              return (
                <tr key={franja} className="border-t">
                  <td className="px-3 py-2 align-top whitespace-nowrap text-slate-500">
                    {inicio} – {fin}
                  </td>
                  {dias.map((d) => (
                    <td key={d.dia} className="space-y-1 px-1.5 py-1.5 align-top">
                      {bloques
                        .filter((b) => b.dia === d.dia && hhmm(b.hora_inicio) === inicio && hhmm(b.hora_final) === fin)
                        .map(tarjeta)}
                    </td>
                  ))}
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Celular: lista por día */}
      <div className="space-y-4 p-4 md:hidden print:hidden">
        {dias.map((d) => {
          const delDia = bloques.filter((b) => b.dia === d.dia)
          if (!delDia.length) return null
          return (
            <section key={d.dia} className="space-y-2">
              <h3 className="text-sm font-semibold text-slate-700">{d.etiqueta}</h3>
              {delDia.map((b) => (
                <div key={b.id_horario} className="flex gap-3">
                  <p className="w-24 shrink-0 pt-1.5 text-xs text-slate-500">
                    {hhmm(b.hora_inicio)} – {hhmm(b.hora_final)}
                  </p>
                  <div className="min-w-0 flex-1">{tarjeta(b)}</div>
                </div>
              ))}
            </section>
          )
        })}
      </div>
    </>
  )
}

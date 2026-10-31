/**
 * Panel de inicio del padre/tutor: elige a uno de sus estudiantes vinculados (CU09) y ve
 * su promedio y calificaciones (CU23/CU24), asistencia (CU22), mensualidades (CU25),
 * próximas clases (CU20) y comunicados/citaciones (CU27).
 *
 * PROTOTIPO: el horario ya es real (CU20); el resto usa datosEjemplo.ts hasta implementar esos casos de uso.
 */
import { useState } from 'react'
import { cn } from 'cn'
import {
  CalendarCheckIcon,
  CalendarClockIcon,
  MegaphoneIcon,
  NotebookPenIcon,
  TrendingUpIcon,
  WalletIcon,
} from 'lucide-react'
import { AvatarIniciales } from '@/componentes/comunes'
import { bolivianos, fecha } from '@/lib/formato'
import { useHorarioInicio, useOpcionesConsulta } from '@/paquetes/horarios/api'
import { porcentajeAsistencia, promedioGeneral, proximaCuota, proximasClases } from './calculos'
import {
  AvisoPrototipo,
  Bienvenida,
  DetalleAsistencia,
  Indicador,
  ListaClases,
  ListaComunicados,
  ListaCuotas,
  TablaNotas,
  Tarjeta,
} from './componentes'
import { HIJOS_TUTOR } from './datosEjemplo'

export default function PanelTutor() {
  const [indice, setIndice] = useState(0)
  const e = HIJOS_TUTOR[indice]
  const cursoHijo = useOpcionesConsulta().data?.estudiantes.find((h) => h.ci === e.ci)?.id_curso
  const horario = useHorarioInicio(cursoHijo ? { id_curso: cursoHijo } : null)
  const cuota = proximaCuota(e.cuotas)
  const citaciones = e.comunicados.filter((c) => c.tipo === 'citacion').length

  return (
    <div className="space-y-6">
      <Bienvenida />
      <AvisoPrototipo casos="CU09, CU22, CU24, CU25 y CU27" />

      <div>
        <h2 className="mb-2 text-sm font-medium text-slate-600">Mis estudiantes</h2>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {HIJOS_TUTOR.map((h, i) => (
            <button
              key={h.ci}
              type="button"
              onClick={() => setIndice(i)}
              aria-pressed={i === indice}
              className={cn(
                'flex items-center gap-3 rounded-xl border bg-white p-4 text-left shadow-sm transition-colors',
                i === indice ? 'border-blue-500 ring-2 ring-blue-500/20' : 'hover:border-blue-200 hover:bg-blue-50/50',
              )}
            >
              <AvatarIniciales nombre={h.nombre} className="size-11 text-sm" />
              <span className="min-w-0">
                <span className="block truncate font-semibold text-slate-900">{h.nombre}</span>
                <span className="block text-xs text-slate-500">
                  {h.curso} · {h.parentesco}
                </span>
              </span>
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Indicador titulo="Promedio general" valor={promedioGeneral(e.notas) ?? '—'} detalle="Sobre 100 puntos" icono={TrendingUpIcon} tono="border-blue-100 bg-blue-50 text-blue-600" />
        <Indicador titulo="Asistencia" valor={`${porcentajeAsistencia(e.asistencia)}%`} detalle="Mes de septiembre" icono={CalendarCheckIcon} tono="border-emerald-100 bg-emerald-50 text-emerald-600" />
        <Indicador
          titulo="Próxima cuota"
          valor={cuota ? bolivianos(cuota.monto) : 'Al día'}
          detalle={cuota && `${cuota.mes} · vence ${fecha(cuota.vence)}`}
          icono={WalletIcon}
          tono={cuota?.estado === 'vencida' ? 'border-rose-100 bg-rose-50 text-rose-600' : 'border-orange-100 bg-orange-50 text-orange-600'}
        />
        <Indicador
          titulo="Comunicados"
          valor={e.comunicados.length}
          detalle={citaciones ? `${citaciones} citación(es)` : 'Sin citaciones'}
          icono={MegaphoneIcon}
          tono="border-violet-100 bg-violet-50 text-violet-600"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Tarjeta titulo={`Calificaciones de ${e.nombre.split(' ')[0]}`} icono={NotebookPenIcon} enlace={{ texto: 'Ver boletín', ruta: '/evaluacion/cu24' }} sinRelleno>
          <TablaNotas notas={e.notas} />
        </Tarjeta>
        <Tarjeta titulo="Mensualidades" icono={WalletIcon} enlace={{ texto: 'Ver pagos', ruta: '/administracion/cu25' }}>
          <ListaCuotas cuotas={e.cuotas} />
        </Tarjeta>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Tarjeta titulo="Asistencia" icono={CalendarCheckIcon} enlace={{ texto: 'Historial', ruta: '/evaluacion/historial-asistencia' }}>
          <DetalleAsistencia asistencia={e.asistencia} />
        </Tarjeta>
        <Tarjeta titulo="Próximas clases" icono={CalendarClockIcon} enlace={{ texto: 'Horario', ruta: '/horarios/consulta' }}>
          <ListaClases clases={proximasClases(horario)} detalle="docente" />
        </Tarjeta>
        <Tarjeta titulo="Comunicados" icono={MegaphoneIcon} enlace={{ texto: 'Ver todos', ruta: '/administracion/cu27' }}>
          <ListaComunicados comunicados={e.comunicados} />
        </Tarjeta>
      </div>
    </div>
  )
}

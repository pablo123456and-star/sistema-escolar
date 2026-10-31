/**
 * Panel de inicio del padre/tutor: elige a uno de sus estudiantes vinculados (CU09) y ve
 * su promedio y calificaciones (CU23/CU24), asistencia (CU22), mensualidades (CU25),
 * próximas clases (CU20) y comunicados/citaciones (CU27).
 *
 * Datos reales: sus estudiantes y mensualidades (CU25), asistencia (CU22) y horario (CU20).
 * Las calificaciones (CU23/CU24) y los comunicados (CU27) se muestran cuando se implementen.
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
import { useSesion } from '@/nucleo/auth/contexto'
import { useMisCuotas } from '@/paquetes/administracion/api'
import { useHistorialAsistencia } from '@/paquetes/evaluacion/api'
import { useHorarioInicio, useOpcionesConsulta } from '@/paquetes/horarios/api'
import { cuotasDelPanel, porcentajeAsistencia, proximaCuota, proximasClases, resumenAsistencia } from './calculos'
import {
  AvisoPrototipo,
  Bienvenida,
  DetalleAsistencia,
  Indicador,
  ListaClases,
  ListaCuotas,
  Pendiente,
  Tarjeta,
} from './componentes'

export default function PanelTutor() {
  const { usuario } = useSesion()
  const cuentas = useMisCuotas()
  const [indice, setIndice] = useState(0)
  const hijos = cuentas.data ?? []
  const cuenta = hijos[indice] ?? hijos[0]
  const e = cuenta?.estudiante
  const cursoHijo = useOpcionesConsulta().data?.estudiantes.find((h) => h.ci === e?.ci)?.id_curso
  const horario = useHorarioInicio(cursoHijo ? { id_curso: cursoHijo } : null)
  const historial = useHistorialAsistencia(e?.ci ?? null, {})

  const asistencia = resumenAsistencia(historial.data)
  const conAsistencia = (historial.data?.general.total ?? 0) > 0
  const cuotas = cuotasDelPanel(cuenta)
  const cuota = proximaCuota(cuotas)
  const gestion = historial.data ? `Gestión ${historial.data.gestion}` : 'Gestión actual'
  const parentesco = (c: NonNullable<typeof cuenta>) => c.tutores.find((t) => t.ci === usuario?.ci)?.parentesco

  return (
    <div className="space-y-6">
      <Bienvenida />
      <AvisoPrototipo
        casos="CU23, CU24 y CU27"
        texto="Sus estudiantes, la asistencia, las mensualidades y el horario son datos reales. Las calificaciones y los comunicados aparecerán cuando se implementen CU23, CU24 y CU27."
      />

      {cuentas.isLoading ? (
        <p className="py-10 text-center text-slate-500">Cargando...</p>
      ) : !cuenta || !e ? (
        <Pendiente texto="No tiene estudiantes vinculados. Comuníquese con la secretaría." />
      ) : (
        <>
          <div>
            <h2 className="mb-2 text-sm font-medium text-slate-600">Mis estudiantes</h2>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {hijos.map((h, i) => (
                <button
                  key={h.estudiante.ci}
                  type="button"
                  onClick={() => setIndice(i)}
                  aria-pressed={h === cuenta}
                  className={cn(
                    'flex items-center gap-3 rounded-xl border bg-white p-4 text-left shadow-sm transition-colors',
                    h === cuenta ? 'border-blue-500 ring-2 ring-blue-500/20' : 'hover:border-blue-200 hover:bg-blue-50/50',
                  )}
                >
                  <AvatarIniciales nombre={`${h.estudiante.nombre_persona} ${h.estudiante.apellidos}`} className="size-11 text-sm" />
                  <span className="min-w-0">
                    <span className="block truncate font-semibold text-slate-900">
                      {h.estudiante.nombre_persona} {h.estudiante.apellidos}
                    </span>
                    <span className="block text-xs text-slate-500">
                      {h.estudiante.curso ?? 'Sin curso'}{parentesco(h) ? ` · ${parentesco(h)}` : ''}
                    </span>
                  </span>
                </button>
              ))}
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Indicador titulo="Promedio general" valor="—" detalle="Disponible con CU23" icono={TrendingUpIcon} tono="border-blue-100 bg-blue-50 text-blue-600" />
            <Indicador
              titulo="Asistencia"
              valor={conAsistencia ? `${porcentajeAsistencia(asistencia)}%` : '—'}
              detalle={conAsistencia ? gestion : 'Sin registros'}
              icono={CalendarCheckIcon}
              tono="border-emerald-100 bg-emerald-50 text-emerald-600"
            />
            <Indicador
              titulo="Próxima cuota"
              valor={cuota ? bolivianos(cuota.monto) : cuotas.length ? 'Al día' : '—'}
              detalle={cuota ? `${cuota.mes} · vence ${fecha(cuota.vence)}` : cuotas.length ? 'Sin cuotas pendientes' : 'Sin cuotas generadas'}
              icono={WalletIcon}
              tono={cuota?.estado === 'vencida' ? 'border-rose-100 bg-rose-50 text-rose-600' : 'border-orange-100 bg-orange-50 text-orange-600'}
            />
            <Indicador titulo="Comunicados" valor="—" detalle="Disponible con CU27" icono={MegaphoneIcon} tono="border-violet-100 bg-violet-50 text-violet-600" />
          </div>

          <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
            <Tarjeta titulo={`Calificaciones de ${e.nombre_persona}`} icono={NotebookPenIcon} enlace={{ texto: 'Ver boletín', ruta: '/evaluacion/cu24' }}>
              <Pendiente texto="Las calificaciones aparecerán aquí cuando se implemente el registro de notas (CU23)." />
            </Tarjeta>
            <Tarjeta titulo="Mensualidades" icono={WalletIcon} enlace={{ texto: 'Ver pagos', ruta: '/administracion/pagos' }}>
              {cuotas.length ? <ListaCuotas cuotas={cuotas} /> : <Pendiente texto="Todavía no hay cuotas generadas." />}
            </Tarjeta>
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            <Tarjeta titulo="Asistencia" icono={CalendarCheckIcon} enlace={{ texto: 'Historial', ruta: '/evaluacion/historial-asistencia' }}>
              {conAsistencia ? (
                <DetalleAsistencia asistencia={asistencia} periodo={gestion} />
              ) : (
                <Pendiente texto="Todavía no hay asistencia registrada." />
              )}
            </Tarjeta>
            <Tarjeta titulo="Próximas clases" icono={CalendarClockIcon} enlace={{ texto: 'Horario', ruta: '/horarios/consulta' }}>
              <ListaClases clases={proximasClases(horario)} detalle="docente" />
            </Tarjeta>
            <Tarjeta titulo="Comunicados" icono={MegaphoneIcon} enlace={{ texto: 'Ver todos', ruta: '/administracion/cu27' }}>
              <Pendiente texto="Los comunicados y citaciones aparecerán aquí cuando se implemente CU27." />
            </Tarjeta>
          </div>
        </>
      )}
    </div>
  )
}

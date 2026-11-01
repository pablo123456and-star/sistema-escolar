/**
 * Panel de inicio del estudiante: promedio, asistencia y pagos, calificaciones del
 * año (CU23), próximas clases y horario (CU20), asistencia (CU22), comunicados (CU27)
 * y accesos a autoevaluación, boletín (CU24), inscripciones (CU17) y pagos (CU25).
 *
 * Datos reales: horario (CU20), asistencia (CU22) y mensualidades (CU25). Las calificaciones
 * (CU23/CU24) y los comunicados (CU27) se muestran cuando se implementen esos casos de uso.
 */
import {
  BookOpenIcon,
  CalendarCheckIcon,
  CalendarClockIcon,
  CalendarDaysIcon,
  ClipboardCheckIcon,
  FileTextIcon,
  HistoryIcon,
  MegaphoneIcon,
  NotebookPenIcon,
  TrendingUpIcon,
  WalletIcon,
} from 'lucide-react'
import { bolivianos } from '@/lib/formato'
import { useSesion } from '@/nucleo/auth/contexto'
import { useMisCuotas } from '@/paquetes/administracion/api'
import { useHistorialAsistencia } from '@/paquetes/evaluacion/api'
import { useHorarioInicio, useOpcionesConsulta } from '@/paquetes/horarios/api'
import { cuotasDelPanel, porcentajeAsistencia, proximaCuota, proximasClases, resumenAsistencia } from './calculos'
import {
  AccesoRapido,
  AvisoPrototipo,
  Bienvenida,
  DetalleAsistencia,
  HorarioSemanal,
  Indicador,
  ListaClases,
  Pendiente,
  Tarjeta,
} from './componentes'
import { PERIODO_ACTUAL } from './datosEjemplo'

export default function PanelEstudiante() {
  const { usuario } = useSesion()
  const miCurso = useOpcionesConsulta().data?.cursos[0]
  const horario = useHorarioInicio(miCurso ? { id_curso: miCurso.id_curso } : null)
  const historial = useHistorialAsistencia(usuario?.ci ?? null, {})
  const cuenta = useMisCuotas().data?.[0]

  const asistencia = resumenAsistencia(historial.data)
  const conAsistencia = (historial.data?.general.total ?? 0) > 0
  const cuotas = cuotasDelPanel(cuenta)
  const cuota = proximaCuota(cuotas)
  const alDia = !cuotas.some((c) => c.estado === 'vencida')
  const materias = new Set(horario.map((b) => b.materia)).size
  const gestion = historial.data ? `Gestión ${historial.data.gestion}` : 'Gestión actual'

  return (
    <div className="space-y-6">
      <Bienvenida extra={historial.data?.estudiante.curso ?? cuenta?.estudiante.curso ?? undefined} />
      <AvisoPrototipo
        casos="CU23, CU24 y CU27"
        texto="La asistencia, las mensualidades y el horario son tus datos reales. Las calificaciones y los comunicados aparecerán cuando se implementen CU23, CU24 y CU27."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Indicador titulo="Promedio general" valor="—" detalle="Disponible con CU23" icono={TrendingUpIcon} tono="border-blue-100 bg-blue-50 text-blue-600" />
        <Indicador
          titulo="Asistencia"
          valor={conAsistencia ? `${porcentajeAsistencia(asistencia)}%` : '—'}
          detalle={conAsistencia ? gestion : 'Sin registros'}
          icono={CalendarCheckIcon}
          tono="border-emerald-100 bg-emerald-50 text-emerald-600"
        />
        <Indicador titulo="Materias" valor={materias || '—'} detalle={PERIODO_ACTUAL} icono={BookOpenIcon} tono="border-violet-100 bg-violet-50 text-violet-600" />
        <Indicador
          titulo="Mensualidades"
          valor={!cuotas.length ? '—' : alDia ? 'Al día' : 'Con deuda'}
          detalle={cuota ? `${cuota.mes}: ${bolivianos(cuota.monto)}` : cuotas.length ? 'Sin cuotas pendientes' : 'Sin cuotas generadas'}
          icono={WalletIcon}
          tono={alDia ? 'border-orange-100 bg-orange-50 text-orange-600' : 'border-rose-100 bg-rose-50 text-rose-600'}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Tarjeta titulo="Mis calificaciones" icono={NotebookPenIcon} enlace={{ texto: 'Ver boletín', ruta: '/evaluacion/boletines' }}>
          <Pendiente texto="Tus calificaciones aparecerán aquí cuando se implemente el registro de notas (CU23)." />
        </Tarjeta>
        <Tarjeta titulo="Próximas clases" icono={CalendarClockIcon}>
          <ListaClases clases={proximasClases(horario)} detalle="docente" />
        </Tarjeta>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <AccesoRapido icono={ClipboardCheckIcon} titulo="Autoevaluación" descripcion={`Completar la del ${PERIODO_ACTUAL}`} ruta="/evaluacion/cu23" />
        <AccesoRapido icono={FileTextIcon} titulo="Boletín / libreta" descripcion="Notas y promedio por trimestre" ruta="/evaluacion/boletines" />
        <AccesoRapido icono={HistoryIcon} titulo="Mis inscripciones" descripcion="Historial por gestión" ruta="/academico/cu17" />
        <AccesoRapido icono={WalletIcon} titulo="Mis pagos" descripcion="Cuotas y comprobantes" ruta="/administracion/pagos" />
      </div>

      <Tarjeta titulo="Mi horario" icono={CalendarDaysIcon} enlace={{ texto: 'Ver horarios', ruta: '/horarios/consulta' }} sinRelleno>
        <HorarioSemanal bloques={horario} detalle="docente" />
      </Tarjeta>

      <div className="grid gap-6 lg:grid-cols-2">
        <Tarjeta titulo="Mi asistencia" icono={CalendarCheckIcon} enlace={{ texto: 'Ver historial', ruta: '/evaluacion/historial-asistencia' }}>
          {conAsistencia ? (
            <DetalleAsistencia asistencia={asistencia} periodo={gestion} />
          ) : (
            <Pendiente texto="Todavía no hay asistencia registrada." />
          )}
        </Tarjeta>
        <Tarjeta titulo="Comunicados" icono={MegaphoneIcon} enlace={{ texto: 'Ver todos', ruta: '/administracion/cu27' }}>
          <Pendiente texto="Los comunicados aparecerán aquí cuando se implemente CU27." />
        </Tarjeta>
      </div>
    </div>
  )
}

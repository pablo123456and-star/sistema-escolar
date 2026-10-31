/**
 * Panel de inicio del estudiante: promedio, asistencia y pagos, calificaciones del
 * año (CU23), próximas clases y horario (CU20), asistencia (CU22), comunicados (CU27)
 * y accesos a autoevaluación, boletín (CU24), inscripciones (CU17) y pagos (CU25).
 *
 * PROTOTIPO: el horario ya es real (CU20); el resto usa datosEjemplo.ts hasta implementar esos casos de uso.
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
import { useHorarioInicio, useOpcionesConsulta } from '@/paquetes/horarios/api'
import { porcentajeAsistencia, promedioGeneral, proximaCuota, proximasClases } from './calculos'
import {
  AccesoRapido,
  AvisoPrototipo,
  Bienvenida,
  DetalleAsistencia,
  HorarioSemanal,
  Indicador,
  ListaClases,
  ListaComunicados,
  TablaNotas,
  Tarjeta,
} from './componentes'
import { MATEO, PERIODO_ACTUAL } from './datosEjemplo'

export default function PanelEstudiante() {
  const e = MATEO
  const miCurso = useOpcionesConsulta().data?.cursos[0]
  const horario = useHorarioInicio(miCurso ? { id_curso: miCurso.id_curso } : null)
  const cuota = proximaCuota(e.cuotas)
  const alDia = !e.cuotas.some((c) => c.estado === 'vencida')

  return (
    <div className="space-y-6">
      <Bienvenida extra={e.curso} />
      <AvisoPrototipo casos="CU22, CU23, CU24, CU25 y CU27" />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Indicador titulo="Promedio general" valor={promedioGeneral(e.notas) ?? '—'} detalle="Sobre 100 puntos" icono={TrendingUpIcon} tono="border-blue-100 bg-blue-50 text-blue-600" />
        <Indicador titulo="Asistencia" valor={`${porcentajeAsistencia(e.asistencia)}%`} detalle="Mes de septiembre" icono={CalendarCheckIcon} tono="border-emerald-100 bg-emerald-50 text-emerald-600" />
        <Indicador titulo="Materias" valor={e.notas.length} detalle={PERIODO_ACTUAL} icono={BookOpenIcon} tono="border-violet-100 bg-violet-50 text-violet-600" />
        <Indicador
          titulo="Mensualidades"
          valor={alDia ? 'Al día' : 'Con deuda'}
          detalle={cuota && `${cuota.mes}: ${bolivianos(cuota.monto)}`}
          icono={WalletIcon}
          tono={alDia ? 'border-orange-100 bg-orange-50 text-orange-600' : 'border-rose-100 bg-rose-50 text-rose-600'}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Tarjeta titulo="Mis calificaciones" icono={NotebookPenIcon} enlace={{ texto: 'Ver boletín', ruta: '/evaluacion/cu24' }} sinRelleno>
          <TablaNotas notas={e.notas} />
        </Tarjeta>
        <Tarjeta titulo="Próximas clases" icono={CalendarClockIcon}>
          <ListaClases clases={proximasClases(horario)} detalle="docente" />
        </Tarjeta>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <AccesoRapido icono={ClipboardCheckIcon} titulo="Autoevaluación" descripcion={`Completar la del ${PERIODO_ACTUAL}`} ruta="/evaluacion/cu23" />
        <AccesoRapido icono={FileTextIcon} titulo="Boletín / libreta" descripcion="Notas de trimestres cerrados" ruta="/evaluacion/cu24" />
        <AccesoRapido icono={HistoryIcon} titulo="Mis inscripciones" descripcion="Historial por gestión" ruta="/academico/cu17" />
        <AccesoRapido icono={WalletIcon} titulo="Mis pagos" descripcion="Cuotas y comprobantes" ruta="/administracion/pagos" />
      </div>

      <Tarjeta titulo="Mi horario" icono={CalendarDaysIcon} enlace={{ texto: 'Ver horarios', ruta: '/horarios/consulta' }} sinRelleno>
        <HorarioSemanal bloques={horario} detalle="docente" />
      </Tarjeta>

      <div className="grid gap-6 lg:grid-cols-2">
        <Tarjeta titulo="Mi asistencia" icono={CalendarCheckIcon} enlace={{ texto: 'Ver historial', ruta: '/evaluacion/historial-asistencia' }}>
          <DetalleAsistencia asistencia={e.asistencia} />
        </Tarjeta>
        <Tarjeta titulo="Comunicados" icono={MegaphoneIcon} enlace={{ texto: 'Ver todos', ruta: '/administracion/cu27' }}>
          <ListaComunicados comunicados={e.comunicados} />
        </Tarjeta>
      </div>
    </div>
  )
}

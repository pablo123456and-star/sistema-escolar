/**
 * Panel de inicio del docente (rol profesor): próximas clases con accesos a tomar
 * asistencia (CU21) y registrar notas (CU23), pendientes, sus estudiantes, su horario
 * (CU20) y comunicados (CU27).
 *
 * PROTOTIPO: el horario ya es real (CU20); el resto usa datosEjemplo.ts hasta implementar CU21, CU23 y CU27.
 */
import { Link } from 'react-router'
import { cn } from 'cn'
import {
  BookOpenIcon,
  CalendarClockIcon,
  CalendarDaysIcon,
  ClipboardCheckIcon,
  ClipboardListIcon,
  GraduationCapIcon,
  MegaphoneIcon,
  NotebookPenIcon,
  UsersIcon,
} from 'lucide-react'
import { AvatarIniciales } from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { useSesion } from '@/nucleo/auth/contexto'
import { useHorarioInicio } from '@/paquetes/horarios/api'
import { proximasClases } from './calculos'
import {
  AvisoPrototipo,
  Barra,
  Bienvenida,
  HorarioSemanal,
  Indicador,
  ListaClases,
  ListaComunicados,
  Nota,
  Tarjeta,
} from './componentes'
import { DOCENTE } from './datosEjemplo'

const TONO_PENDIENTE = {
  rojo: 'border-rose-100 bg-rose-50 text-rose-600',
  ambar: 'border-amber-100 bg-amber-50 text-amber-600',
  azul: 'border-blue-100 bg-blue-50 text-blue-600',
}

export default function PanelDocente() {
  const { asignaciones, pendientes, comunicados } = DOCENTE
  const { usuario } = useSesion()
  const horario = useHorarioInicio(usuario ? { ci_profesor: usuario.ci } : null)
  const totalEstudiantes = asignaciones.reduce((t, a) => t + a.estudiantes.length, 0)
  const clases = proximasClases(horario)

  return (
    <div className="space-y-6">
      <Bienvenida />
      <AvisoPrototipo casos="CU21, CU23 y CU27" />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Indicador titulo="Cursos asignados" valor={asignaciones.length} detalle={asignaciones.map((a) => a.curso).join(', ')} icono={BookOpenIcon} tono="border-blue-100 bg-blue-50 text-blue-600" />
        <Indicador titulo="Mis estudiantes" valor={totalEstudiantes} icono={GraduationCapIcon} tono="border-emerald-100 bg-emerald-50 text-emerald-600" />
        <Indicador titulo="Clases por semana" valor={horario.length} icono={CalendarDaysIcon} tono="border-violet-100 bg-violet-50 text-violet-600" />
        <Indicador titulo="Pendientes" valor={pendientes.length} icono={ClipboardListIcon} tono="border-orange-100 bg-orange-50 text-orange-600" />
      </div>

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <Tarjeta titulo="Próximas clases" icono={CalendarClockIcon} enlace={{ texto: 'Ver horarios', ruta: '/horarios/consulta' }}>
          <ListaClases
            clases={clases}
            detalle="curso"
            acciones={() => (
              <>
                <Button asChild size="sm" variant="outline">
                  <Link to="/evaluacion/asistencia">
                    <ClipboardCheckIcon /> Asistencia
                  </Link>
                </Button>
                <Button asChild size="sm" variant="outline">
                  <Link to="/evaluacion/calificaciones">
                    <NotebookPenIcon /> Notas
                  </Link>
                </Button>
              </>
            )}
          />
        </Tarjeta>

        <Tarjeta titulo="Pendientes" icono={ClipboardListIcon}>
          <ul className="space-y-3">
            {pendientes.map((p) => (
              <li key={p.titulo}>
                <Link to={p.ruta} className={cn('block rounded-lg border p-3 transition-opacity hover:opacity-80', TONO_PENDIENTE[p.tono])}>
                  <p className="text-sm font-semibold">{p.titulo}</p>
                  <p className="text-sm text-slate-600">{p.detalle}</p>
                </Link>
              </li>
            ))}
          </ul>
        </Tarjeta>
      </div>

      {asignaciones.map((a) => (
        <Tarjeta
          key={`${a.materia}-${a.curso}`}
          titulo={`Mis estudiantes · ${a.materia} · ${a.curso}`}
          icono={UsersIcon}
          enlace={{ texto: 'Ver seguimiento', ruta: '/personas/cu07' }}
          sinRelleno
        >
          <Table>
            <TableHeader>
              <TableRow className="bg-slate-50">
                <TableHead className="pl-4">Estudiante</TableHead>
                <TableHead className="text-center">Promedio</TableHead>
                <TableHead className="w-40">Asistencia</TableHead>
                <TableHead className="pr-4">Estado</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {a.estudiantes.map((e) => (
                <TableRow key={e.ci}>
                  <TableCell className="pl-4">
                    <div className="flex items-center gap-3">
                      <AvatarIniciales nombre={e.nombre} />
                      <div>
                        <p className="font-medium text-slate-900">{e.nombre}</p>
                        <p className="text-xs text-slate-500">CI {e.ci}</p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-center"><Nota valor={e.promedio} /></TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Barra valor={e.asistencia} />
                      <span className="w-10 text-right text-xs text-slate-600">{e.asistencia}%</span>
                    </div>
                  </TableCell>
                  <TableCell className="pr-4">
                    {e.promedio < 51 ? (
                      <span className="rounded-md bg-rose-50 px-2 py-0.5 text-xs font-medium text-rose-700 ring-1 ring-rose-200 ring-inset">En riesgo</span>
                    ) : (
                      <span className="rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200 ring-inset">Regular</span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Tarjeta>
      ))}

      <div className="grid items-start gap-6 lg:grid-cols-[2fr_1fr]">
        <Tarjeta titulo="Mi horario semanal" icono={CalendarDaysIcon} sinRelleno>
          <HorarioSemanal bloques={horario} detalle="curso" />
        </Tarjeta>
        <Tarjeta titulo="Comunicados" icono={MegaphoneIcon} enlace={{ texto: 'Ver todos', ruta: '/administracion/cu27' }}>
          <ListaComunicados comunicados={comunicados} />
        </Tarjeta>
      </div>
    </div>
  )
}

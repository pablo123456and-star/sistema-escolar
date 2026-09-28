/**
 * Panel de inicio (CU01, postcondición): bienvenida, indicadores y, para el
 * administrador, actividades recientes (bitácora) y avisos (solicitudes de recuperación).
 */
import type { ReactNode } from 'react'
import { Link } from 'react-router'
import { cn } from 'cn'
import {
  BookOpenIcon,
  CalendarDaysIcon,
  CircleCheckIcon,
  GraduationCapIcon,
  InfoIcon,
  TriangleAlertIcon,
  UsersIcon,
  UsersRoundIcon,
  type LucideIcon,
} from 'lucide-react'
import { FilaMensaje } from '@/componentes/comunes'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { ETIQUETA_ROL, fechaHora } from '@/lib/formato'
import { useSesion } from '@/nucleo/auth/contexto'
import { useResumenInicio, useSolicitudesRecuperacion } from '@/paquetes/seguridad/api'

function Indicador({ titulo, valor, icono: Icono, tono }: { titulo: string; valor?: number | string; icono: LucideIcon; tono: string }) {
  return (
    <div className={cn('flex items-center gap-4 rounded-xl border p-5 shadow-sm', tono)}>
      <Icono className="size-10 shrink-0" strokeWidth={1.6} />
      <div>
        <p className="text-sm font-medium text-slate-600">{titulo}</p>
        <p className="text-2xl font-bold text-slate-900">{valor ?? '—'}</p>
      </div>
    </div>
  )
}

function Aviso({ icono: Icono, tono, titulo, children }: { icono: LucideIcon; tono: string; titulo: string; children: ReactNode }) {
  return (
    <div className={cn('flex gap-3 rounded-lg border p-3', tono)}>
      <Icono className="mt-0.5 size-5 shrink-0" />
      <div className="text-sm">
        <p className="font-semibold">{titulo}</p>
        <div className="text-slate-600">{children}</div>
      </div>
    </div>
  )
}

export default function PaginaInicio() {
  const { usuario } = useSesion()
  const esAdmin = usuario?.rol === 'administrador'
  const resumen = useResumenInicio()
  const solicitudes = useSolicitudesRecuperacion(esAdmin)
  const r = resumen.data

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Bienvenido, {usuario?.nombres}</h1>
        <p className="text-slate-500">
          Sistema de Gestión Académica · {usuario && (usuario.cargo ?? ETIQUETA_ROL[usuario.rol])}
          {r?.gestion && ` · ${r.gestion}`}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Indicador titulo="Usuarios activos" valor={r?.usuarios_activos} icono={UsersIcon} tono="border-blue-100 bg-blue-50 text-blue-600" />
        <Indicador titulo="Estudiantes" valor={r?.estudiantes_activos} icono={GraduationCapIcon} tono="border-emerald-100 bg-emerald-50 text-emerald-600" />
        <Indicador titulo="Padres y tutores" valor={r?.tutores} icono={UsersRoundIcon} tono="border-orange-100 bg-orange-50 text-orange-600" />
        <Indicador titulo="Cursos" valor={r?.cursos} icono={BookOpenIcon} tono="border-violet-100 bg-violet-50 text-violet-600" />
      </div>

      {esAdmin && (
        <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <div className="rounded-xl border bg-white shadow-sm">
            <div className="flex items-center justify-between border-b px-4 py-3">
              <h2 className="font-semibold">Actividades recientes</h2>
              <Link to="/seguridad/bitacora" className="text-sm text-blue-600 hover:underline">Ver bitácora</Link>
            </div>
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead className="pl-4">Fecha</TableHead>
                  <TableHead>Actividad</TableHead>
                  <TableHead className="pr-4">Usuario</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {resumen.isLoading ? (
                  <FilaMensaje columnas={3} cargando />
                ) : !r?.actividades.length ? (
                  <FilaMensaje columnas={3} mensaje="Sin actividades registradas." />
                ) : (
                  r.actividades.map((a, i) => (
                    <TableRow key={i}>
                      <TableCell className="pl-4 whitespace-nowrap">{fechaHora(a.fecha_hora)}</TableCell>
                      <TableCell className="max-w-xs truncate" title={a.accion}>{a.accion}</TableCell>
                      <TableCell className="pr-4">{a.nombre_usuario ?? 'Sistema'}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          <div className="space-y-3 rounded-xl border bg-white p-4 shadow-sm">
            <h2 className="font-semibold">Avisos importantes</h2>
            {r?.gestion ? (
              <Aviso icono={InfoIcon} tono="border-blue-100 bg-blue-50 text-blue-600" titulo="Gestión académica">
                {r.gestion} abierta para inscripciones.
              </Aviso>
            ) : (
              <Aviso icono={CalendarDaysIcon} tono="border-amber-100 bg-amber-50 text-amber-600" titulo="Gestión académica">
                No hay una gestión abierta.
              </Aviso>
            )}
            {solicitudes.data?.length ? (
              <Aviso icono={TriangleAlertIcon} tono="border-amber-100 bg-amber-50 text-amber-600" titulo="Recuperación de contraseñas">
                {solicitudes.data.length} solicitud(es) pendiente(s).{' '}
                <Link to="/seguridad/usuarios" className="text-blue-600 hover:underline">Atender</Link>
              </Aviso>
            ) : (
              <Aviso icono={CircleCheckIcon} tono="border-emerald-100 bg-emerald-50 text-emerald-600" titulo="Recuperación de contraseñas">
                No hay solicitudes pendientes.
              </Aviso>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

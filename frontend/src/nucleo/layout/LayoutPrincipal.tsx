/**
 * Estructura de todas las pantallas (como el prototipo): menú lateral azul con el
 * escudo, encabezado con el nombre de la unidad educativa, avisos y el menú del usuario
 * (Mi perfil, Cerrar sesión con confirmación). El menú se filtra por rol: el
 * administrador ve los módulos de gestión; docente, estudiante y padre/tutor, sus consultas.
 */
import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router'
import { cn } from 'cn'
import {
  BellIcon,
  CalendarCheckIcon,
  CalendarCogIcon,
  CalendarDaysIcon,
  CalendarRangeIcon,
  ChevronDownIcon,
  ClipboardCheckIcon,
  FileTextIcon,
  GraduationCapIcon,
  HeartPulseIcon,
  HistoryIcon,
  HouseIcon,
  LayersIcon,
  LogOutIcon,
  MegaphoneIcon,
  MenuIcon,
  NotebookPenIcon,
  PresentationIcon,
  ScrollTextIcon,
  ShieldCheckIcon,
  UserIcon,
  UserPlusIcon,
  UsersIcon,
  UsersRoundIcon,
  WalletIcon,
  XIcon,
  type LucideIcon,
} from 'lucide-react'
import Confirmar from '@/componentes/Confirmar'
import Escudo from '@/componentes/Escudo'
import { Button } from '@/componentes/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/componentes/ui/dropdown-menu'
import { ETIQUETA_ROL } from '@/lib/formato'
import { useSesion } from '@/nucleo/auth/contexto'
import { useSolicitudesRecuperacion } from '@/paquetes/seguridad/api'
import DialogoPerfil from '@/paquetes/seguridad/componentes/DialogoPerfil'
import type { Rol } from '@/paquetes/seguridad/schemas'

type ItemMenu = { ruta: string; texto: string; icono: LucideIcon; roles?: Rol[] }

// Opciones por rol según la matriz de permisos del CU03 (una misma ruta puede tener
// otro texto según el rol, pero cada rol la ve una sola vez).
const MENU: ItemMenu[] = [
  { ruta: '/', texto: 'Inicio', icono: HouseIcon },
  { ruta: '/seguridad/usuarios', texto: 'Usuarios', icono: UsersIcon, roles: ['administrador'] },
  { ruta: '/seguridad/roles', texto: 'Roles y permisos', icono: ShieldCheckIcon, roles: ['administrador'] },
  { ruta: '/seguridad/bitacora', texto: 'Bitácora', icono: ScrollTextIcon, roles: ['administrador'] },
  { ruta: '/personas/estudiantes', texto: 'Estudiantes', icono: GraduationCapIcon, roles: ['administrador'] },
  { ruta: '/personas/tutores', texto: 'Padres y tutores', icono: UsersRoundIcon, roles: ['administrador'] },
  // CU10 - Registrar docente
  { ruta: '/personas/docentes', texto: 'Docentes', icono: PresentationIcon, roles: ['administrador'] },
  // CU12 - Gestionar niveles educativos y cursos
  { ruta: '/academico/niveles-cursos', texto: 'Niveles y cursos', icono: LayersIcon, roles: ['administrador'] },
  // CU13 - Gestionar materias y plan de estudios
  { ruta: '/academico/materias', texto: 'Materias y plan de estudios', icono: NotebookPenIcon, roles: ['administrador'] },
  // CU14 - Asignar profesor a materia/curso
  { ruta: '/academico/asignaciones', texto: 'Asignación de profesores', icono: UsersIcon, roles: ['administrador'] },
  // CU15 - Gestionar gestión académica (año lectivo)
  { ruta: '/academico/gestiones', texto: 'Gestión académica', icono: CalendarRangeIcon, roles: ['administrador'] },
  // CU16 - Inscribir estudiante en gestión académica
  { ruta: '/academico/inscripciones', texto: 'Inscripciones', icono: UserPlusIcon, roles: ['administrador'] },
  // CU19 - Generar horario y CU20 - Consultar horarios
  { ruta: '/horarios/generar', texto: 'Generar horario', icono: CalendarCogIcon, roles: ['administrador'] },
  { ruta: '/horarios/consulta', texto: 'Consultar horarios', icono: CalendarDaysIcon, roles: ['administrador'] },
  // CU21 - Registrar asistencia (el administrador puede registrar o corregir cualquier clase)
  { ruta: '/evaluacion/asistencia', texto: 'Asistencia', icono: ClipboardCheckIcon, roles: ['administrador'] },
  // CU22 - Consultar historial de asistencia
  { ruta: '/evaluacion/historial-asistencia', texto: 'Historial de asistencia', icono: CalendarCheckIcon, roles: ['administrador'] },
  // CU23 - Registrar calificaciones (el administrador corrige cualquier clase y cierra o reabre trimestres)
  { ruta: '/evaluacion/calificaciones', texto: 'Calificaciones', icono: NotebookPenIcon, roles: ['administrador'] },
  // CU24 - Generar y consultar boletín/libreta
  { ruta: '/evaluacion/boletines', texto: 'Boletines', icono: FileTextIcon, roles: ['administrador'] },
  // Docente
  { ruta: '/horarios/consulta', texto: 'Mis horarios', icono: CalendarDaysIcon, roles: ['profesor'] },
  { ruta: '/evaluacion/asistencia', texto: 'Asistencia', icono: ClipboardCheckIcon, roles: ['profesor'] },
  { ruta: '/evaluacion/historial-asistencia', texto: 'Historial de asistencia', icono: CalendarCheckIcon, roles: ['profesor'] },
  { ruta: '/evaluacion/calificaciones', texto: 'Calificaciones', icono: NotebookPenIcon, roles: ['profesor'] },
  { ruta: '/personas/cu09', texto: 'Mis estudiantes', icono: GraduationCapIcon, roles: ['profesor'] },
  { ruta: '/personas/cu07', texto: 'Seguimiento', icono: HeartPulseIcon, roles: ['profesor'] },
  // Estudiante
  { ruta: '/horarios/consulta', texto: 'Mi horario', icono: CalendarDaysIcon, roles: ['estudiante'] },
  { ruta: '/evaluacion/calificaciones', texto: 'Mis calificaciones', icono: NotebookPenIcon, roles: ['estudiante'] },
  { ruta: '/evaluacion/boletines', texto: 'Boletín', icono: FileTextIcon, roles: ['estudiante'] },
  { ruta: '/evaluacion/historial-asistencia', texto: 'Mi asistencia', icono: CalendarCheckIcon, roles: ['estudiante'] },
  { ruta: '/academico/cu17', texto: 'Mis inscripciones', icono: HistoryIcon, roles: ['estudiante'] },
  // Padre/Tutor
  { ruta: '/personas/cu09', texto: 'Mis estudiantes', icono: UsersRoundIcon, roles: ['tutor'] },
  { ruta: '/horarios/consulta', texto: 'Horarios', icono: CalendarDaysIcon, roles: ['tutor'] },
  { ruta: '/evaluacion/boletines', texto: 'Boletín', icono: FileTextIcon, roles: ['tutor'] },
  { ruta: '/evaluacion/historial-asistencia', texto: 'Asistencia', icono: CalendarCheckIcon, roles: ['tutor'] },
  { ruta: '/academico/cu17', texto: 'Inscripciones', icono: HistoryIcon, roles: ['tutor'] },
  // Comunes a varios roles
  { ruta: '/administracion/pagos', texto: 'Pagos', icono: WalletIcon, roles: ['administrador', 'estudiante', 'tutor'] },
  { ruta: '/administracion/cu27', texto: 'Comunicados', icono: MegaphoneIcon, roles: ['profesor', 'estudiante', 'tutor'] },
]

function NombreInstitucion({ claro }: { claro?: boolean }) {
  return (
    <div className="leading-tight">
      <p className={cn('text-xs', claro ? 'text-blue-100' : 'text-slate-600')}>Unidad Educativa</p>
      <p className={cn('font-semibold', claro ? 'text-white' : 'text-[#12306B]')}>“Mariscal Sucre G”</p>
    </div>
  )
}

export default function LayoutPrincipal() {
  const { usuario, cerrarSesion } = useSesion()
  const navegar = useNavigate()
  const [menuMovil, setMenuMovil] = useState(false)
  const [confirmarSalida, setConfirmarSalida] = useState(false)
  const [perfil, setPerfil] = useState(false)
  const esAdmin = usuario?.rol === 'administrador'
  const solicitudes = useSolicitudesRecuperacion(esAdmin)
  const pendientes = solicitudes.data?.length ?? 0

  if (!usuario) return null
  const items = MENU.filter((m) => !m.roles || m.roles.includes(usuario.rol))

  const salir = () => {
    cerrarSesion()
    navegar('/login', { replace: true })
  }

  const menuLateral = (
    <nav className="flex min-h-0 flex-1 flex-col gap-1 overflow-y-auto px-3 py-4">
      {items.map(({ ruta, texto, icono: Icono }) => (
        <NavLink
          key={ruta}
          to={ruta}
          end={ruta === '/'}
          onClick={() => setMenuMovil(false)}
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
              isActive ? 'bg-blue-600 text-white shadow-sm' : 'text-blue-100 hover:bg-white/10 hover:text-white',
            )
          }
        >
          <Icono className="size-5" />
          {texto}
        </NavLink>
      ))}
    </nav>
  )

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Menú lateral (escritorio) */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col bg-[#0B2352] lg:flex print:hidden">
        <Link to="/" className="flex flex-col items-center gap-2 border-b border-white/10 px-4 py-5 text-center">
          <Escudo className="h-16 w-auto" />
          <NombreInstitucion claro />
        </Link>
        {menuLateral}
      </aside>

      {/* Menú lateral (celular) */}
      {menuMovil && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMenuMovil(false)} />
          <aside className="absolute inset-y-0 left-0 flex w-64 flex-col bg-[#0B2352]">
            <div className="flex items-center justify-between border-b border-white/10 p-4">
              <div className="flex items-center gap-2">
                <Escudo className="h-10 w-auto" />
                <NombreInstitucion claro />
              </div>
              <Button size="icon-sm" variant="ghost" className="text-white hover:bg-white/10" onClick={() => setMenuMovil(false)}>
                <XIcon />
              </Button>
            </div>
            {menuLateral}
          </aside>
        </div>
      )}

      <div className="lg:pl-64 print:pl-0">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b bg-white px-4 sm:px-6 print:hidden">
          <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setMenuMovil(true)} aria-label="Abrir menú">
            <MenuIcon />
          </Button>
          <div className="hidden sm:block">
            <NombreInstitucion />
          </div>
          <div className="ml-auto flex items-center gap-2">
            {esAdmin && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="relative" aria-label="Avisos">
                    <BellIcon className="size-5" />
                    {pendientes > 0 && (
                      <span className="absolute -top-0.5 -right-0.5 flex size-4 items-center justify-center rounded-full bg-rose-600 text-[10px] font-bold text-white">
                        {pendientes}
                      </span>
                    )}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-72">
                  <DropdownMenuLabel>Avisos</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  {pendientes === 0 ? (
                    <p className="px-2 py-3 text-sm text-slate-500">No hay avisos pendientes.</p>
                  ) : (
                    solicitudes.data?.map((s) => (
                      <DropdownMenuItem key={s.id_bitacora} onSelect={() => navegar('/seguridad/usuarios')}>
                        <div className="text-sm">
                          <p className="font-medium">Recuperación de contraseña</p>
                          <p className="text-slate-500">
                            {s.nombres} {s.apellidos} ({s.nombre_usuario})
                          </p>
                        </div>
                      </DropdownMenuItem>
                    ))
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            )}
            <div className="mx-1 h-8 w-px bg-slate-200" />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="h-10 gap-2 px-2">
                  <span className="flex size-8 items-center justify-center rounded-full bg-blue-600 text-white">
                    <UserIcon className="size-4" />
                  </span>
                  <span className="hidden text-left leading-tight sm:block">
                    <span className="block text-sm font-medium">{usuario.nombres}</span>
                    <span className="block text-xs text-slate-500">{usuario.cargo ?? ETIQUETA_ROL[usuario.rol]}</span>
                  </span>
                  <ChevronDownIcon className="size-4 text-slate-500" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onSelect={() => setPerfil(true)}>
                  <UserIcon /> Mi perfil
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem variant="destructive" onSelect={() => setConfirmarSalida(true)}>
                  <LogOutIcon /> Cerrar sesión
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        <main className="mx-auto max-w-7xl p-4 sm:p-6 print:p-0">
          <Outlet />
        </main>
      </div>

      <DialogoPerfil abierto={perfil} onCambiar={setPerfil} />
      <Confirmar
        abierto={confirmarSalida}
        onCambiar={setConfirmarSalida}
        titulo="Cerrar sesión"
        descripcion="¿Está seguro que desea cerrar sesión?"
        textoConfirmar="Cerrar sesión"
        icono={<LogOutIcon />}
        peligro
        onConfirmar={salir}
      />
    </div>
  )
}

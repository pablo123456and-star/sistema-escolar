/** Rutas del paquete evaluacion: una por caso de uso (roles según la matriz de permisos del CU03). */
import type { ReactNode } from 'react'
import type { RouteObject } from 'react-router'
import RutaProtegida from '@/nucleo/auth/RutaProtegida'
import type { Rol } from '@/paquetes/seguridad/schemas'
import CU21RegistrarAsistencia from './casos_uso/CU21RegistrarAsistencia'
import CU22ConsultarHistorialAsistencia from './casos_uso/CU22ConsultarHistorialAsistencia'
import CU23RegistrarCalificaciones from './casos_uso/CU23RegistrarCalificaciones'
import CU24GenerarConsultarBoletin from './casos_uso/CU24GenerarConsultarBoletin'

const para = (roles: Rol[], elemento: ReactNode) => <RutaProtegida roles={roles}>{elemento}</RutaProtegida>

export const rutasEvaluacion: RouteObject[] = [
  { path: 'evaluacion/asistencia', element: para(['administrador', 'profesor'], <CU21RegistrarAsistencia />) },
  { path: 'evaluacion/historial-asistencia', element: para(['administrador', 'profesor', 'estudiante', 'tutor'], <CU22ConsultarHistorialAsistencia />) },
  { path: 'evaluacion/cu23', element: para(['administrador', 'profesor', 'estudiante'], <CU23RegistrarCalificaciones />) },
  { path: 'evaluacion/boletines', element: para(['administrador', 'estudiante', 'tutor'], <CU24GenerarConsultarBoletin />) },
]

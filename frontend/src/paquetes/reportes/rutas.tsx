/** Rutas del paquete reportes (solo administrador: Director y Secretaría). */
import type { RouteObject } from 'react-router'
import RutaProtegida from '@/nucleo/auth/RutaProtegida'
import Reportes from './casos_uso/Reportes'

export const rutasReportes: RouteObject[] = [
  { path: 'reportes', element: <RutaProtegida roles={['administrador']}><Reportes /></RutaProtegida> },
]

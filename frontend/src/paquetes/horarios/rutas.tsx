/** Rutas del paquete horarios: una por caso de uso (roles según la matriz de permisos del CU03). */
import type { ReactNode } from 'react'
import type { RouteObject } from 'react-router'
import RutaProtegida from '@/nucleo/auth/RutaProtegida'
import CU18GestionarAulas from './casos_uso/CU18GestionarAulas'
import CU19GenerarHorario from './casos_uso/CU19GenerarHorario'
import CU20ConsultarHorarios from './casos_uso/CU20ConsultarHorarios'

const soloAdministrador = (elemento: ReactNode) => <RutaProtegida roles={['administrador']}>{elemento}</RutaProtegida>

export const rutasHorarios: RouteObject[] = [
  { path: 'horarios/cu18', element: soloAdministrador(<CU18GestionarAulas />) },
  { path: 'horarios/generar', element: soloAdministrador(<CU19GenerarHorario />) },
  { path: 'horarios/consulta', element: <CU20ConsultarHorarios /> },
]

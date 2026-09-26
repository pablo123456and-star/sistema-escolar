/** Rutas del paquete horarios: una por caso de uso. */
import type { RouteObject } from 'react-router'
import CU18GestionarAulas from './casos_uso/CU18GestionarAulas'
import CU19GenerarHorario from './casos_uso/CU19GenerarHorario'
import CU20ConsultarHorarios from './casos_uso/CU20ConsultarHorarios'

export const rutasHorarios: RouteObject[] = [
  { path: 'horarios/cu18', element: <CU18GestionarAulas /> },
  { path: 'horarios/cu19', element: <CU19GenerarHorario /> },
  { path: 'horarios/cu20', element: <CU20ConsultarHorarios /> },
]

/** Rutas del paquete evaluacion: una por caso de uso. */
import type { RouteObject } from 'react-router'
import CU21RegistrarAsistencia from './casos_uso/CU21RegistrarAsistencia'
import CU22ConsultarHistorialAsistencia from './casos_uso/CU22ConsultarHistorialAsistencia'
import CU23RegistrarCalificaciones from './casos_uso/CU23RegistrarCalificaciones'
import CU24GenerarConsultarBoletin from './casos_uso/CU24GenerarConsultarBoletin'

export const rutasEvaluacion: RouteObject[] = [
  { path: 'evaluacion/cu21', element: <CU21RegistrarAsistencia /> },
  { path: 'evaluacion/cu22', element: <CU22ConsultarHistorialAsistencia /> },
  { path: 'evaluacion/cu23', element: <CU23RegistrarCalificaciones /> },
  { path: 'evaluacion/cu24', element: <CU24GenerarConsultarBoletin /> },
]

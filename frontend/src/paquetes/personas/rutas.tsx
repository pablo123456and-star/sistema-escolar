/** Rutas del paquete personas: una por caso de uso. */
import type { RouteObject } from 'react-router'
import CU05RegistrarActualizarPersona from './casos_uso/CU05RegistrarActualizarPersona'
import CU06GestionarEstudiante from './casos_uso/CU06GestionarEstudiante'
import CU07RegistrarAntecedentesSeguimiento from './casos_uso/CU07RegistrarAntecedentesSeguimiento'
import CU08RegistrarAsociarTutor from './casos_uso/CU08RegistrarAsociarTutor'
import CU09ConsultarRelacionados from './casos_uso/CU09ConsultarRelacionados'
import CU10RegistrarDocente from './casos_uso/CU10RegistrarDocente'
import CU11RegistrarAdministrativo from './casos_uso/CU11RegistrarAdministrativo'

export const rutasPersonas: RouteObject[] = [
  { path: 'personas/cu05', element: <CU05RegistrarActualizarPersona /> },
  { path: 'personas/cu06', element: <CU06GestionarEstudiante /> },
  { path: 'personas/cu07', element: <CU07RegistrarAntecedentesSeguimiento /> },
  { path: 'personas/cu08', element: <CU08RegistrarAsociarTutor /> },
  { path: 'personas/cu09', element: <CU09ConsultarRelacionados /> },
  { path: 'personas/cu10', element: <CU10RegistrarDocente /> },
  { path: 'personas/cu11', element: <CU11RegistrarAdministrativo /> },
]

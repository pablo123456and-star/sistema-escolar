/** Rutas del paquete personas: una por caso de uso (roles según la matriz de permisos del CU03). */
import type { ReactNode } from 'react'
import type { RouteObject } from 'react-router'
import RutaProtegida from '@/nucleo/auth/RutaProtegida'
import type { Rol } from '@/paquetes/seguridad/schemas'
import CU05RegistrarActualizarPersona from './casos_uso/CU05RegistrarActualizarPersona'
import CU06GestionarEstudiante from './casos_uso/CU06GestionarEstudiante'
import CU07RegistrarAntecedentesSeguimiento from './casos_uso/CU07RegistrarAntecedentesSeguimiento'
import CU08RegistrarAsociarTutor from './casos_uso/CU08RegistrarAsociarTutor'
import CU09ConsultarRelacionados from './casos_uso/CU09ConsultarRelacionados'
import CU10RegistrarDocente from './casos_uso/CU10RegistrarDocente'
import CU11RegistrarAdministrativo from './casos_uso/CU11RegistrarAdministrativo'

const para = (roles: Rol[], elemento: ReactNode) => <RutaProtegida roles={roles}>{elemento}</RutaProtegida>
const soloAdministrador = (elemento: ReactNode) => para(['administrador'], elemento)

export const rutasPersonas: RouteObject[] = [
  { path: 'personas/cu05', element: soloAdministrador(<CU05RegistrarActualizarPersona />) },
  { path: 'personas/estudiantes', element: soloAdministrador(<CU06GestionarEstudiante />) },
  { path: 'personas/cu07', element: para(['administrador', 'profesor'], <CU07RegistrarAntecedentesSeguimiento />) },
  { path: 'personas/tutores', element: soloAdministrador(<CU08RegistrarAsociarTutor />) },
  { path: 'personas/cu09', element: <CU09ConsultarRelacionados /> },
  { path: 'personas/cu10', element: soloAdministrador(<CU10RegistrarDocente />) },
  { path: 'personas/cu11', element: soloAdministrador(<CU11RegistrarAdministrativo />) },
]

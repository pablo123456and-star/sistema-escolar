/** Rutas del paquete academico: una por caso de uso (roles según la matriz de permisos del CU03). */
import type { ReactNode } from 'react'
import type { RouteObject } from 'react-router'
import RutaProtegida from '@/nucleo/auth/RutaProtegida'
import type { Rol } from '@/paquetes/seguridad/schemas'
import CU12GestionarNivelesCursos from './casos_uso/CU12GestionarNivelesCursos'
import CU13GestionarMaterias from './casos_uso/CU13GestionarMaterias'
import CU14AsignarProfesor from './casos_uso/CU14AsignarProfesor'
import CU15GestionarGestionAcademica from './casos_uso/CU15GestionarGestionAcademica'
import CU16InscribirEstudiante from './casos_uso/CU16InscribirEstudiante'
import CU17ConsultarHistorialInscripciones from './casos_uso/CU17ConsultarHistorialInscripciones'

const para = (roles: Rol[], elemento: ReactNode) => <RutaProtegida roles={roles}>{elemento}</RutaProtegida>
const soloAdministrador = (elemento: ReactNode) => para(['administrador'], elemento)

export const rutasAcademico: RouteObject[] = [
  { path: 'academico/cu12', element: soloAdministrador(<CU12GestionarNivelesCursos />) },
  { path: 'academico/cu13', element: soloAdministrador(<CU13GestionarMaterias />) },
  { path: 'academico/cu14', element: soloAdministrador(<CU14AsignarProfesor />) },
  { path: 'academico/cu15', element: soloAdministrador(<CU15GestionarGestionAcademica />) },
  { path: 'academico/cu16', element: soloAdministrador(<CU16InscribirEstudiante />) },
  { path: 'academico/cu17', element: para(['administrador', 'estudiante', 'tutor'], <CU17ConsultarHistorialInscripciones />) },
]

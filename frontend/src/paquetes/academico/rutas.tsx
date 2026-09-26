/** Rutas del paquete academico: una por caso de uso. */
import type { RouteObject } from 'react-router'
import CU12GestionarNivelesCursos from './casos_uso/CU12GestionarNivelesCursos'
import CU13GestionarMaterias from './casos_uso/CU13GestionarMaterias'
import CU14AsignarProfesor from './casos_uso/CU14AsignarProfesor'
import CU15GestionarGestionAcademica from './casos_uso/CU15GestionarGestionAcademica'
import CU16InscribirEstudiante from './casos_uso/CU16InscribirEstudiante'
import CU17ConsultarHistorialInscripciones from './casos_uso/CU17ConsultarHistorialInscripciones'

export const rutasAcademico: RouteObject[] = [
  { path: 'academico/cu12', element: <CU12GestionarNivelesCursos /> },
  { path: 'academico/cu13', element: <CU13GestionarMaterias /> },
  { path: 'academico/cu14', element: <CU14AsignarProfesor /> },
  { path: 'academico/cu15', element: <CU15GestionarGestionAcademica /> },
  { path: 'academico/cu16', element: <CU16InscribirEstudiante /> },
  { path: 'academico/cu17', element: <CU17ConsultarHistorialInscripciones /> },
]

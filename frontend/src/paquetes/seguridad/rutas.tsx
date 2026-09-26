/** Rutas del paquete seguridad: una por caso de uso. */
import type { RouteObject } from 'react-router'
import CU01IniciarSesion from './casos_uso/CU01IniciarSesion'
import CU02GestionarUsuarios from './casos_uso/CU02GestionarUsuarios'
import CU03GestionarRolesPermisos from './casos_uso/CU03GestionarRolesPermisos'
import CU04ConsultarBitacora from './casos_uso/CU04ConsultarBitacora'

export const rutasSeguridad: RouteObject[] = [
  { path: 'seguridad/cu01', element: <CU01IniciarSesion /> },
  { path: 'seguridad/cu02', element: <CU02GestionarUsuarios /> },
  { path: 'seguridad/cu03', element: <CU03GestionarRolesPermisos /> },
  { path: 'seguridad/cu04', element: <CU04ConsultarBitacora /> },
]

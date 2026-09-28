/**
 * Rutas del paquete seguridad: una por caso de uso.
 * El CU01 (login y recuperar contraseña) se registra fuera del layout, en App.tsx.
 */
import type { ReactNode } from 'react'
import type { RouteObject } from 'react-router'
import RutaProtegida from '@/nucleo/auth/RutaProtegida'
import CU02GestionarUsuarios from './casos_uso/CU02GestionarUsuarios'
import CU03GestionarRolesPermisos from './casos_uso/CU03GestionarRolesPermisos'
import CU04ConsultarBitacora from './casos_uso/CU04ConsultarBitacora'

const soloAdministrador = (elemento: ReactNode) => <RutaProtegida roles={['administrador']}>{elemento}</RutaProtegida>

export const rutasSeguridad: RouteObject[] = [
  { path: 'seguridad/usuarios', element: soloAdministrador(<CU02GestionarUsuarios />) },
  { path: 'seguridad/roles', element: soloAdministrador(<CU03GestionarRolesPermisos />) },
  { path: 'seguridad/bitacora', element: soloAdministrador(<CU04ConsultarBitacora />) },
]

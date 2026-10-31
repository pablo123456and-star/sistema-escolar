/** Rutas del paquete administracion: una por caso de uso (roles según la matriz de permisos del CU03). */
import type { ReactNode } from 'react'
import type { RouteObject } from 'react-router'
import RutaProtegida from '@/nucleo/auth/RutaProtegida'
import type { Rol } from '@/paquetes/seguridad/schemas'
import CU25RegistrarPagoMensualidad from './casos_uso/CU25RegistrarPagoMensualidad'
import CU26GestionarInventario from './casos_uso/CU26GestionarInventario'
import CU27GestionarComunicados from './casos_uso/CU27GestionarComunicados'

const para = (roles: Rol[], elemento: ReactNode) => <RutaProtegida roles={roles}>{elemento}</RutaProtegida>

export const rutasAdministracion: RouteObject[] = [
  { path: 'administracion/pagos', element: para(['administrador', 'estudiante', 'tutor'], <CU25RegistrarPagoMensualidad />) },
  { path: 'administracion/cu26', element: para(['administrador'], <CU26GestionarInventario />) },
  { path: 'administracion/cu27', element: <CU27GestionarComunicados /> },
]

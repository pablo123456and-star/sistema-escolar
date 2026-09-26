/** Rutas del paquete administracion: una por caso de uso. */
import type { RouteObject } from 'react-router'
import CU25RegistrarPagoMensualidad from './casos_uso/CU25RegistrarPagoMensualidad'
import CU26GestionarInventario from './casos_uso/CU26GestionarInventario'
import CU27GestionarComunicados from './casos_uso/CU27GestionarComunicados'

export const rutasAdministracion: RouteObject[] = [
  { path: 'administracion/cu25', element: <CU25RegistrarPagoMensualidad /> },
  { path: 'administracion/cu26', element: <CU26GestionarInventario /> },
  { path: 'administracion/cu27', element: <CU27GestionarComunicados /> },
]

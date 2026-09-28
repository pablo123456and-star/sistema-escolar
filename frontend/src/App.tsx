import { createBrowserRouter, Navigate, Outlet, RouterProvider } from 'react-router'
import ProveedorSesion from '@/nucleo/auth/ProveedorSesion'
import RutaProtegida from '@/nucleo/auth/RutaProtegida'
import LayoutPrincipal from '@/nucleo/layout/LayoutPrincipal'
import PaginaInicio from '@/nucleo/PaginaInicio'
import { rutasPaquetes } from '@/nucleo/rutas'
import CU01IniciarSesion, { CU01RecuperarContrasena } from '@/paquetes/seguridad/casos_uso/CU01IniciarSesion'

const router = createBrowserRouter([
  {
    // La sesión necesita estar dentro del router (usa navegación al vencer)
    element: (
      <ProveedorSesion>
        <Outlet />
      </ProveedorSesion>
    ),
    children: [
      { path: '/login', element: <CU01IniciarSesion /> },
      { path: '/recuperar-contrasena', element: <CU01RecuperarContrasena /> },
      {
        path: '/',
        element: (
          <RutaProtegida>
            <LayoutPrincipal />
          </RutaProtegida>
        ),
        children: [{ index: true, element: <PaginaInicio /> }, ...rutasPaquetes],
      },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
])

export default function App() {
  return <RouterProvider router={router} />
}

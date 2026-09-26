import { createBrowserRouter, RouterProvider } from 'react-router'
import LayoutPrincipal from '@/nucleo/layout/LayoutPrincipal'
import PaginaInicio from '@/nucleo/PaginaInicio'
import { rutasPaquetes } from '@/nucleo/rutas'

const router = createBrowserRouter([
  {
    path: '/',
    element: <LayoutPrincipal />,
    children: [{ index: true, element: <PaginaInicio /> }, ...rutasPaquetes],
  },
])

export default function App() {
  return <RouterProvider router={router} />
}

/**
 * Estructura de todas las pantallas: encabezado + contenido.
 * PENDIENTE: menú lateral con una sección por paquete, filtrado por rol.
 */
import { Link, Outlet } from 'react-router'

export default function LayoutPrincipal() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b px-6 py-4">
        <Link to="/" className="font-semibold">
          Sistema de Información - Unidad Educativa
        </Link>
      </header>
      <main className="mx-auto max-w-5xl p-6">
        <Outlet />
      </main>
    </div>
  )
}

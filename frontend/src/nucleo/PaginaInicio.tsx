/** Página temporal: muestra la estructura de paquetes y casos de uso. */
import { Link } from 'react-router'
import { PAQUETES } from '@/nucleo/mapaCasosUso'

export default function PaginaInicio() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Estructura del sistema</h1>
      {PAQUETES.map((p) => (
        <section key={p.paquete} className="rounded-lg border p-4">
          <h2 className="font-medium">{p.titulo}</h2>
          <p className="text-sm text-muted-foreground">paquetes/{p.paquete}</p>
          <ul className="mt-2 grid gap-1 sm:grid-cols-2">
            {p.casos.map((c) => (
              <li key={c.codigo}>
                <Link to={c.ruta} className="text-sm underline-offset-4 hover:underline">
                  {c.codigo} - {c.nombre}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  )
}

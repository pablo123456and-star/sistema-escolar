/** Marcador reutilizable para los casos de uso que aún no se implementan. */
type Props = { codigo: string; nombre: string; paquete: string }

export default function CasoUsoPendiente({ codigo, nombre, paquete }: Props) {
  return (
    <div className="rounded-lg border border-dashed p-6">
      <p className="text-sm text-muted-foreground">paquetes/{paquete}</p>
      <h1 className="text-xl font-semibold">
        {codigo} - {nombre}
      </h1>
      <p className="mt-2 text-sm text-muted-foreground">Pendiente de implementar.</p>
    </div>
  )
}

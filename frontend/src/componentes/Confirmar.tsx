/** Ventana de confirmación para acciones importantes (cerrar sesión, desactivar, dar de baja...). */
import type { ReactNode } from 'react'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogMedia,
  AlertDialogTitle,
} from '@/componentes/ui/alert-dialog'

type Props = {
  abierto: boolean
  onCambiar: (abierto: boolean) => void
  titulo: string
  descripcion: ReactNode
  textoConfirmar: string
  icono?: ReactNode
  peligro?: boolean
  ocupado?: boolean
  onConfirmar: () => void
}

export default function Confirmar({
  abierto,
  onCambiar,
  titulo,
  descripcion,
  textoConfirmar,
  icono,
  peligro,
  ocupado,
  onConfirmar,
}: Props) {
  return (
    <AlertDialog open={abierto} onOpenChange={onCambiar}>
      <AlertDialogContent>
        <AlertDialogHeader>
          {icono && (
            <AlertDialogMedia className={peligro ? 'bg-rose-50 text-rose-600' : 'bg-blue-50 text-blue-600'}>
              {icono}
            </AlertDialogMedia>
          )}
          <AlertDialogTitle>{titulo}</AlertDialogTitle>
          <AlertDialogDescription>{descripcion}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={ocupado}>Cancelar</AlertDialogCancel>
          <AlertDialogAction
            disabled={ocupado}
            className={peligro ? 'bg-rose-600 text-white hover:bg-rose-700' : undefined}
            onClick={(e) => {
              e.preventDefault()
              onConfirmar()
            }}
          >
            {textoConfirmar}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

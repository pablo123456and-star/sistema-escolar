/**
 * Piezas de pantalla reutilizadas por todos los casos de uso:
 * encabezado, paginación, insignias de estado/rol, avatar con iniciales,
 * campo de formulario, filas de "cargando"/"sin datos" y botón de acción con tooltip.
 */
import type { ReactNode } from 'react'
import { cn } from 'cn'
import { ChevronLeftIcon, ChevronRightIcon, ChevronsLeftIcon, ChevronsRightIcon, Loader2Icon } from 'lucide-react'
import { Button } from '@/componentes/ui/button'
import { Label } from '@/componentes/ui/label'
import { TableCell, TableRow } from '@/componentes/ui/table'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/componentes/ui/tooltip'
import { ETIQUETA_ROL, iniciales } from '@/lib/formato'

export function EncabezadoPagina({ titulo, descripcion, accion }: { titulo: string; descripcion: string; accion?: ReactNode }) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">{titulo}</h1>
        <p className="text-sm text-slate-500">{descripcion}</p>
      </div>
      {accion}
    </div>
  )
}

export function Paginacion({
  pagina,
  tamano,
  total,
  etiqueta,
  onCambiar,
}: {
  pagina: number
  tamano: number
  total: number
  etiqueta: string
  onCambiar: (pagina: number) => void
}) {
  const paginas = Math.max(1, Math.ceil(total / tamano))
  const desde = total === 0 ? 0 : (pagina - 1) * tamano + 1
  const hasta = Math.min(total, pagina * tamano)
  const inicio = Math.max(1, Math.min(pagina - 2, paginas - 4))
  const visibles = Array.from({ length: Math.min(5, paginas) }, (_, i) => inicio + i)
  return (
    <div className="flex flex-col items-center justify-between gap-2 border-t px-4 py-3 text-sm text-slate-500 sm:flex-row">
      <span>
        Mostrando {desde} a {hasta} de {total} {etiqueta}
      </span>
      <div className="flex items-center gap-1">
        <Button variant="outline" size="icon-sm" disabled={pagina === 1} onClick={() => onCambiar(1)} aria-label="Primera">
          <ChevronsLeftIcon />
        </Button>
        <Button variant="outline" size="icon-sm" disabled={pagina === 1} onClick={() => onCambiar(pagina - 1)} aria-label="Anterior">
          <ChevronLeftIcon />
        </Button>
        {visibles.map((n) => (
          <Button key={n} variant={n === pagina ? 'default' : 'outline'} size="icon-sm" onClick={() => onCambiar(n)}>
            {n}
          </Button>
        ))}
        <Button variant="outline" size="icon-sm" disabled={pagina >= paginas} onClick={() => onCambiar(pagina + 1)} aria-label="Siguiente">
          <ChevronRightIcon />
        </Button>
        <Button variant="outline" size="icon-sm" disabled={pagina >= paginas} onClick={() => onCambiar(paginas)} aria-label="Última">
          <ChevronsRightIcon />
        </Button>
      </div>
    </div>
  )
}

const COLOR_ESTADO: Record<string, string> = {
  activo: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  inactivo: 'bg-rose-50 text-rose-700 ring-rose-200',
  bloqueado: 'bg-amber-50 text-amber-700 ring-amber-200',
  activa: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  retirada: 'bg-rose-50 text-rose-700 ring-rose-200',
  finalizada: 'bg-slate-100 text-slate-700 ring-slate-200',
  pagada: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  pendiente: 'bg-amber-50 text-amber-700 ring-amber-200',
  vencida: 'bg-rose-50 text-rose-700 ring-rose-200',
}

export function InsigniaEstado({ estado }: { estado: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium capitalize ring-1 ring-inset',
        COLOR_ESTADO[estado] ?? 'bg-slate-100 text-slate-700 ring-slate-200',
      )}
    >
      {estado}
    </span>
  )
}

const COLOR_ROL: Record<string, string> = {
  administrador: 'bg-blue-50 text-blue-700 ring-blue-200',
  profesor: 'bg-orange-50 text-orange-700 ring-orange-200',
  estudiante: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  tutor: 'bg-pink-50 text-pink-700 ring-pink-200',
}

export function InsigniaRol({ rol }: { rol: string }) {
  return (
    <span className={cn('inline-flex rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset', COLOR_ROL[rol])}>
      {ETIQUETA_ROL[rol] ?? rol}
    </span>
  )
}

const COLORES_AVATAR = ['bg-sky-100 text-sky-700', 'bg-rose-100 text-rose-700', 'bg-emerald-100 text-emerald-700',
  'bg-violet-100 text-violet-700', 'bg-amber-100 text-amber-700', 'bg-teal-100 text-teal-700']

export function AvatarIniciales({ nombre, className }: { nombre: string; className?: string }) {
  const indice = [...nombre].reduce((a, c) => a + c.charCodeAt(0), 0) % COLORES_AVATAR.length
  return (
    <span
      className={cn(
        'inline-flex size-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold',
        COLORES_AVATAR[indice],
        className,
      )}
    >
      {iniciales(nombre)}
    </span>
  )
}

export function Campo({
  etiqueta,
  error,
  htmlFor,
  children,
  className,
}: {
  etiqueta: string
  error?: string
  htmlFor?: string
  children: ReactNode
  className?: string
}) {
  return (
    <div className={cn('grid gap-1.5', className)}>
      <Label htmlFor={htmlFor}>{etiqueta}</Label>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  )
}

export function FilaMensaje({ columnas, cargando, mensaje }: { columnas: number; cargando?: boolean; mensaje?: string }) {
  return (
    <TableRow>
      <TableCell colSpan={columnas} className="h-24 text-center text-slate-500">
        {cargando ? (
          <span className="inline-flex items-center gap-2">
            <Loader2Icon className="size-4 animate-spin" /> Cargando...
          </span>
        ) : (
          mensaje
        )}
      </TableCell>
    </TableRow>
  )
}

const TONO_ACCION = {
  azul: 'bg-blue-50 text-blue-600 hover:bg-blue-100',
  ambar: 'bg-amber-50 text-amber-600 hover:bg-amber-100',
  rojo: 'bg-rose-50 text-rose-600 hover:bg-rose-100',
  verde: 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100',
  gris: 'bg-slate-50 text-slate-600 hover:bg-slate-100',
}

export function BotonAccion({
  etiqueta,
  tono,
  onClick,
  disabled,
  children,
}: {
  etiqueta: string
  tono: keyof typeof TONO_ACCION
  onClick: () => void
  disabled?: boolean
  children: ReactNode
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button size="icon-sm" className={TONO_ACCION[tono]} onClick={onClick} disabled={disabled} aria-label={etiqueta}>
          {children}
        </Button>
      </TooltipTrigger>
      <TooltipContent>{etiqueta}</TooltipContent>
    </Tooltip>
  )
}

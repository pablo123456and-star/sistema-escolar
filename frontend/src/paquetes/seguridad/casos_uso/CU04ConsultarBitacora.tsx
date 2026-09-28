/**
 * CU04 - Consultar bitácora de actividades
 * Paquete: seguridad
 *
 * Actores ........: Administrador
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/seguridad/casos_uso/cu04_consultar_bitacora.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Solo lectura: filtros por fechas, módulo, tabla, operación, usuario y texto; detalle
 * con los datos antes y después de cada cambio (las contraseñas llegan ocultas).
 *
 * Precondición:  Sesión iniciada como administrador.
 * Postcondición: Se muestran los registros de auditoría filtrados. No se modifica nada.
 *
 * Estado: IMPLEMENTADO.
 */
import { useState } from 'react'
import { EyeIcon, RotateCcwIcon, SearchIcon } from 'lucide-react'
import {
  BotonAccion,
  Campo,
  EncabezadoPagina,
  FilaMensaje,
  Paginacion,
} from '@/componentes/comunes'
import { TODOS, sinTodos } from '@/lib/filtros'
import { Button } from '@/componentes/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/componentes/ui/dialog'
import { Input } from '@/componentes/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { fechaHora } from '@/lib/formato'
import { useRetardo } from '@/lib/useRetardo'
import { mensajeError } from '@/nucleo/api'
import { useBitacora, useOpcionesBitacora } from '../api'
import type { RegistroBitacora } from '../schemas'

const TAMANO = 20

const COLOR_OPERACION: Record<string, string> = {
  INSERT: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  UPDATE: 'bg-blue-50 text-blue-700 ring-blue-200',
  DELETE: 'bg-rose-50 text-rose-700 ring-rose-200',
  OTRO: 'bg-slate-100 text-slate-700 ring-slate-200',
}

const FILTROS_VACIOS = { desde: '', hasta: '', modulo: TODOS, tabla: TODOS, operacion: TODOS, usuario: '', texto: '' }

export default function CU04ConsultarBitacora() {
  const [f, setF] = useState(FILTROS_VACIOS)
  const [pagina, setPagina] = useState(1)
  const [detalle, setDetalle] = useState<RegistroBitacora | null>(null)
  const opciones = useOpcionesBitacora()
  const usuario = useRetardo(f.usuario)
  const texto = useRetardo(f.texto)

  const lista = useBitacora({
    desde: f.desde || undefined,
    hasta: f.hasta || undefined,
    modulo: sinTodos(f.modulo),
    tabla: sinTodos(f.tabla),
    operacion: sinTodos(f.operacion),
    usuario: usuario || undefined,
    texto: texto || undefined,
    pagina,
    tamano: TAMANO,
  })

  const cambiar = (campo: keyof typeof FILTROS_VACIOS, valor: string) => {
    setF((x) => ({ ...x, [campo]: valor }))
    setPagina(1)
  }

  const selector = (campo: 'modulo' | 'tabla' | 'operacion', valores: string[] = []) => (
    <Select value={f[campo]} onValueChange={(v) => cambiar(campo, v)}>
      <SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
      <SelectContent>
        <SelectItem value={TODOS}>Todos</SelectItem>
        {valores.map((v) => (
          <SelectItem key={v} value={v}>{v}</SelectItem>
        ))}
      </SelectContent>
    </Select>
  )

  return (
    <div className="space-y-5">
      <EncabezadoPagina
        titulo="Bitácora de actividades"
        descripcion="Auditoría de las operaciones realizadas en el sistema. Los registros no se pueden modificar ni eliminar."
      />

      <div className="rounded-xl border bg-white shadow-sm">
        <div className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-8 xl:items-end">
          <Campo etiqueta="Desde">
            <Input type="date" value={f.desde} onChange={(e) => cambiar('desde', e.target.value)} />
          </Campo>
          <Campo etiqueta="Hasta">
            <Input type="date" value={f.hasta} onChange={(e) => cambiar('hasta', e.target.value)} />
          </Campo>
          <Campo etiqueta="Módulo">{selector('modulo', opciones.data?.modulos)}</Campo>
          <Campo etiqueta="Tabla">{selector('tabla', opciones.data?.tablas)}</Campo>
          <Campo etiqueta="Operación">{selector('operacion', opciones.data?.operaciones)}</Campo>
          <Campo etiqueta="Usuario">
            <Input value={f.usuario} onChange={(e) => cambiar('usuario', e.target.value)} placeholder="nombre de usuario" />
          </Campo>
          <Campo etiqueta="Acción">
            <div className="relative">
              <SearchIcon className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-slate-400" />
              <Input value={f.texto} onChange={(e) => cambiar('texto', e.target.value)} placeholder="Buscar..." className="pl-8" />
            </div>
          </Campo>
          <Button variant="outline" onClick={() => { setF(FILTROS_VACIOS); setPagina(1) }}>
            <RotateCcwIcon /> Limpiar
          </Button>
        </div>

        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50">
              <TableHead className="pl-4">Fecha y hora</TableHead>
              <TableHead>Usuario</TableHead>
              <TableHead>Módulo</TableHead>
              <TableHead>Operación</TableHead>
              <TableHead>Acción</TableHead>
              <TableHead>IP</TableHead>
              <TableHead className="pr-4 text-center">Detalle</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {lista.isLoading ? (
              <FilaMensaje columnas={7} cargando />
            ) : lista.isError ? (
              <FilaMensaje columnas={7} mensaje={mensajeError(lista.error)} />
            ) : !lista.data?.items.length ? (
              <FilaMensaje columnas={7} mensaje="No hay registros para los filtros elegidos." />
            ) : (
              lista.data.items.map((b) => (
                <TableRow key={b.id_bitacora}>
                  <TableCell className="pl-4 whitespace-nowrap">{fechaHora(b.fecha_hora)}</TableCell>
                  <TableCell>{b.nombre_usuario ?? <span className="text-slate-400">Sistema</span>}</TableCell>
                  <TableCell>{b.modulo ?? '—'}</TableCell>
                  <TableCell>
                    {b.operacion && (
                      <span className={`rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${COLOR_OPERACION[b.operacion] ?? COLOR_OPERACION.OTRO}`}>
                        {b.operacion}
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="max-w-md truncate" title={b.accion}>{b.accion}</TableCell>
                  <TableCell className="text-slate-500">{b.ip ?? '—'}</TableCell>
                  <TableCell className="pr-4">
                    <div className="flex justify-center">
                      <BotonAccion etiqueta="Ver detalle" tono="azul" onClick={() => setDetalle(b)}>
                        <EyeIcon />
                      </BotonAccion>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <Paginacion pagina={pagina} tamano={TAMANO} total={lista.data?.total ?? 0} etiqueta="registros" onCambiar={setPagina} />
      </div>

      <DetalleBitacora registro={detalle} onCerrar={() => setDetalle(null)} />
    </div>
  )
}

function mostrar(v: unknown): string {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

function DetalleBitacora({ registro, onCerrar }: { registro: RegistroBitacora | null; onCerrar: () => void }) {
  const antes = registro?.datos_anteriores ?? {}
  const despues = registro?.datos_nuevos ?? {}
  const campos = [...new Set([...Object.keys(antes), ...Object.keys(despues)])]
  return (
    <Dialog open={!!registro} onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Detalle del registro #{registro?.id_bitacora}</DialogTitle>
          <DialogDescription>
            {registro && `${fechaHora(registro.fecha_hora)} · ${registro.nombre_usuario ?? 'Sistema'} · ${registro.accion}`}
          </DialogDescription>
        </DialogHeader>
        {campos.length === 0 ? (
          <p className="text-sm text-slate-500">Esta acción no guarda datos de antes/después.</p>
        ) : (
          <div className="max-h-[60vh] overflow-auto rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead className="pl-3">Campo</TableHead>
                  <TableHead>Antes</TableHead>
                  <TableHead>Después</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {campos.map((c) => {
                  const cambio = mostrar(antes[c]) !== mostrar(despues[c]) && registro?.operacion === 'UPDATE'
                  return (
                    <TableRow key={c} className={cambio ? 'bg-amber-50' : undefined}>
                      <TableCell className="pl-3 font-medium">{c}</TableCell>
                      <TableCell className="max-w-56 whitespace-normal break-all text-slate-600">{mostrar(antes[c])}</TableCell>
                      <TableCell className="max-w-56 whitespace-normal break-all">{mostrar(despues[c])}</TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}

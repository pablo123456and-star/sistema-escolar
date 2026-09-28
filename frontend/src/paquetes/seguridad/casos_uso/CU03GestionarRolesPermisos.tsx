/**
 * CU03 - Gestionar roles y permisos
 * Paquete: seguridad
 *
 * Actores ........: Administrador
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/seguridad/casos_uso/cu03_gestionar_roles_permisos.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Listado de los 4 roles (fijos: solo se edita su descripción) y matriz de permisos por
 * rol. El rol de cada usuario se asigna desde "Gestión de usuarios" (CU02).
 *
 * Precondición:  Sesión iniciada como administrador.
 * Postcondición: La descripción del rol o el rol del usuario queda actualizado; sus permisos cambian con su rol.
 *
 * Estado: IMPLEMENTADO.
 */
import { useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import type { z } from 'zod'
import { CheckIcon, CrownIcon, GraduationCapIcon, InfoIcon, PencilIcon, UserRoundIcon, UsersRoundIcon, type LucideIcon } from 'lucide-react'
import {
  BotonAccion,
  Campo,
  EncabezadoPagina,
  FilaMensaje,
} from '@/componentes/comunes'
import { TODOS } from '@/lib/filtros'
import { Button } from '@/componentes/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/componentes/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { Textarea } from '@/componentes/ui/textarea'
import { ETIQUETA_ROL } from '@/lib/formato'
import { mensajeError } from '@/nucleo/api'
import { useActualizarRol, usePermisos, useRoles } from '../api'
import { esquemaRol, type Rol, type RolDetalle } from '../schemas'

const ROLES: Rol[] = ['administrador', 'profesor', 'estudiante', 'tutor']

const ESTILO_ROL: Record<Rol, { icono: LucideIcon; color: string }> = {
  administrador: { icono: CrownIcon, color: 'bg-blue-100 text-blue-700' },
  profesor: { icono: UserRoundIcon, color: 'bg-orange-100 text-orange-700' },
  estudiante: { icono: GraduationCapIcon, color: 'bg-emerald-100 text-emerald-700' },
  tutor: { icono: UsersRoundIcon, color: 'bg-pink-100 text-pink-700' },
}

const NOMBRE_PAQUETE: Record<string, string> = {
  seguridad: 'Seguridad',
  personas: 'Personas',
  academico: 'Académico',
  horarios: 'Horarios',
  evaluacion: 'Evaluación',
  administracion: 'Administración',
}

export default function CU03GestionarRolesPermisos() {
  const roles = useRoles()
  const permisos = usePermisos()
  const [editando, setEditando] = useState<RolDetalle | null>(null)
  const [modulo, setModulo] = useState(TODOS)

  const filas = useMemo(
    () => (permisos.data ?? []).filter((p) => modulo === TODOS || p.paquete === modulo),
    [permisos.data, modulo],
  )

  return (
    <div className="space-y-5">
      <EncabezadoPagina titulo="Roles y permisos" descripcion="Gestione los roles del sistema y los permisos de cada módulo." />

      <div className="rounded-xl border bg-white shadow-sm">
        <div className="border-b px-4 py-3">
          <h2 className="font-semibold">Listado de roles</h2>
        </div>
        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50">
              <TableHead className="w-10 pl-4">#</TableHead>
              <TableHead>Nombre del rol</TableHead>
              <TableHead>Descripción</TableHead>
              <TableHead className="text-center">Usuarios asignados</TableHead>
              <TableHead className="text-center">Estado</TableHead>
              <TableHead className="pr-4 text-center">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {roles.isLoading ? (
              <FilaMensaje columnas={6} cargando />
            ) : (
              roles.data?.map((r, i) => {
                const { icono: Icono, color } = ESTILO_ROL[r.nombre_rol]
                return (
                  <TableRow key={r.id_rol}>
                    <TableCell className="pl-4 text-slate-500">{i + 1}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <span className={`flex size-8 items-center justify-center rounded-full ${color}`}>
                          <Icono className="size-4" />
                        </span>
                        <span className="font-medium">{ETIQUETA_ROL[r.nombre_rol]}</span>
                      </div>
                    </TableCell>
                    <TableCell className="max-w-sm whitespace-normal text-slate-600">{r.descripcion_rol ?? '—'}</TableCell>
                    <TableCell className="text-center">
                      {r.usuarios_activos}
                      {r.usuarios_total > r.usuarios_activos && (
                        <span className="text-xs text-slate-400"> (+{r.usuarios_total - r.usuarios_activos} inactivos)</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      <span className="rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200">
                        Activo
                      </span>
                    </TableCell>
                    <TableCell className="pr-4">
                      <div className="flex justify-center">
                        <BotonAccion etiqueta="Editar descripción" tono="azul" onClick={() => setEditando(r)}>
                          <PencilIcon />
                        </BotonAccion>
                      </div>
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
        <p className="flex items-center gap-2 border-t px-4 py-3 text-xs text-slate-500">
          <InfoIcon className="size-4" />
          Los 4 roles del sistema son fijos. Dirección y Secretaría usan el rol Administrador (se distinguen por su cargo).
          El rol de cada usuario se asigna en “Usuarios”.
        </p>
      </div>

      <div className="rounded-xl border bg-white shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3">
          <h2 className="font-semibold">Permisos por rol</h2>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-slate-500">Módulo:</span>
            <Select value={modulo} onValueChange={setModulo}>
              <SelectTrigger className="w-48"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value={TODOS}>Todos los módulos</SelectItem>
                {Object.entries(NOMBRE_PAQUETE).map(([k, v]) => (
                  <SelectItem key={k} value={k}>{v}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50">
              <TableHead className="pl-4">Módulo / Funcionalidad</TableHead>
              {ROLES.map((r) => {
                const { icono: Icono } = ESTILO_ROL[r]
                return (
                  <TableHead key={r} className="text-center">
                    <span className="inline-flex items-center gap-1"><Icono className="size-4" /> {ETIQUETA_ROL[r]}</span>
                  </TableHead>
                )
              })}
            </TableRow>
          </TableHeader>
          <TableBody>
            {permisos.isLoading ? (
              <FilaMensaje columnas={5} cargando />
            ) : (
              filas.map((p) => (
                <TableRow key={p.codigo}>
                  <TableCell className="pl-4 whitespace-normal">
                    <span className="mr-2 text-xs text-slate-400">{p.codigo}</span>
                    {p.caso_uso}
                    <span className="ml-2 text-xs text-slate-400">({NOMBRE_PAQUETE[p.paquete]})</span>
                  </TableCell>
                  {ROLES.map((r) => (
                    <TableCell key={r} className="text-center">
                      <span
                        aria-label={p.roles.includes(r) ? 'Permitido' : 'Sin permiso'}
                        className={`inline-flex size-5 items-center justify-center rounded border ${
                          p.roles.includes(r) ? 'border-blue-600 bg-blue-600 text-white' : 'border-slate-300 bg-white'
                        }`}
                      >
                        {p.roles.includes(r) && <CheckIcon className="size-3.5" />}
                      </span>
                    </TableCell>
                  ))}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <p className="flex items-center gap-2 border-t px-4 py-3 text-xs text-slate-500">
          <InfoIcon className="size-4" />
          La matriz la aplica el backend en cada petición; cambia solo cuando se modifica el sistema.
        </p>
      </div>

      {editando && <DialogoRol rol={editando} onCerrar={() => setEditando(null)} />}
    </div>
  )
}

function DialogoRol({ rol, onCerrar }: { rol: RolDetalle; onCerrar: () => void }) {
  const actualizar = useActualizarRol()
  const form = useForm<z.infer<typeof esquemaRol>>({
    resolver: zodResolver(esquemaRol),
    defaultValues: { descripcion_rol: rol.descripcion_rol ?? '' },
  })
  const guardar = form.handleSubmit(async ({ descripcion_rol }) => {
    try {
      await actualizar.mutateAsync({ id: rol.id_rol, descripcion_rol })
      toast.success('Descripción actualizada.')
      onCerrar()
    } catch (e) {
      toast.error(mensajeError(e))
    }
  })
  return (
    <Dialog open onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Editar rol: {ETIQUETA_ROL[rol.nombre_rol]}</DialogTitle>
          <DialogDescription>El nombre del rol es fijo; solo se puede cambiar su descripción.</DialogDescription>
        </DialogHeader>
        <form id="form-rol" onSubmit={guardar}>
          <Campo etiqueta="Descripción" error={form.formState.errors.descripcion_rol?.message} htmlFor="descripcion_rol">
            <Textarea id="descripcion_rol" rows={3} maxLength={150} {...form.register('descripcion_rol')} />
          </Campo>
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={onCerrar}>Cancelar</Button>
          <Button type="submit" form="form-rol" disabled={actualizar.isPending}>Guardar</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

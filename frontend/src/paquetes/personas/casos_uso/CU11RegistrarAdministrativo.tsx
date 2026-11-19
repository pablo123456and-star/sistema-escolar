/**
 * CU11 - Registrar personal administrativo
 * Paquete: personas
 *
 * Actores ........: Administrador
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/personas/casos_uso/cu11_registrar_administrativo.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Listar con búsqueda (nombre/C.I.) y filtro de estado, registrar (reutilizando la persona si
 * ya existe), ver ficha de detalle, editar datos/cargo, dar de baja (lógica) y reactivar.
 *
 * Precondición:  Sesión iniciada como administrador.
 * Postcondición: El administrativo queda registrado y puede ser asignado a funciones administrativas.
 *
 * Estado: IMPLEMENTADO.
 */
import { useState } from 'react'
import { FormProvider, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import type { z } from 'zod'
import { EyeIcon, PencilIcon, PlusIcon, RotateCcwIcon, SearchIcon, TrashIcon, UserCheckIcon } from 'lucide-react'
import Confirmar from '@/componentes/Confirmar'
import {
  AvatarIniciales,
  BotonAccion,
  Campo,
  EncabezadoPagina,
  FilaMensaje,
  InsigniaEstado,
  Paginacion,
} from '@/componentes/comunes'
import { TODOS, sinTodos } from '@/lib/filtros'
import { Button } from '@/componentes/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/componentes/ui/dialog'
import { Input } from '@/componentes/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/componentes/ui/select'
import { Separator } from '@/componentes/ui/separator'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/componentes/ui/table'
import { documento, fecha, nombreCompleto } from '@/lib/formato'
import { useRetardo } from '@/lib/useRetardo'
import { mensajeError } from '@/nucleo/api'
import {
  useActualizarAdministrativo,
  useAdministrativo,
  useAdministrativos,
  useBajaAdministrativo,
  useReactivarAdministrativo,
  useRegistrarAdministrativo,
} from '../api'
import CamposPersona from '../componentes/CamposPersona'
import {
  PERSONA_VACIA,
  esquemaAdministrativo,
  esquemaBaja,
  personaAFormulario,
  personaParaApi,
  type Administrativo,
} from '../schemas'

const TAMANO = 10
type FormularioValores = z.infer<typeof esquemaAdministrativo>

export default function CU11RegistrarAdministrativo() {
  const [busqueda, setBusqueda] = useState('')
  const [estado, setEstado] = useState(TODOS)
  const [pagina, setPagina] = useState(1)
  const q = useRetardo(busqueda)

  const lista = useAdministrativos({ q: q || undefined, estado: sinTodos(estado), pagina, tamano: TAMANO })
  const reactivar = useReactivarAdministrativo()

  const [formulario, setFormulario] = useState<{ ci: string | null } | null>(null)
  const [viendo, setViendo] = useState<string | null>(null)
  const [aBaja, setABaja] = useState<Administrativo | null>(null)
  const [aReactivar, setAReactivar] = useState<Administrativo | null>(null)

  const confirmarReactivar = async () => {
    if (!aReactivar) return
    try {
      await reactivar.mutateAsync(aReactivar.ci)
      toast.success('Personal reactivado correctamente')
      setAReactivar(null)
    } catch (e) {
      toast.error(mensajeError(e))
    }
  }

  return (
    <div className="space-y-6">
      <EncabezadoPagina
        titulo="Personal administrativo"
        descripcion="Gestión del personal administrativo, secretaría, finanzas y apoyo institucional (CU11)."
        accion={
          <Button onClick={() => setFormulario({ ci: null })}>
            <PlusIcon /> Nuevo administrativo
          </Button>
        }
      />

      <div className="rounded-xl border bg-white shadow-sm">
        <div className="grid gap-3 p-4 md:grid-cols-[1fr_180px_auto] md:items-end">
          <Campo etiqueta="Buscar administrativo">
            <div className="relative">
              <SearchIcon className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" />
              <Input
                value={busqueda}
                onChange={(e) => {
                  setBusqueda(e.target.value)
                  setPagina(1)
                }}
                placeholder="Nombre o cédula..."
                className="pl-9"
              />
            </div>
          </Campo>
          <Campo etiqueta="Estado">
            <Select
              value={estado}
              onValueChange={(v) => {
                setEstado(v)
                setPagina(1)
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={TODOS}>Todos</SelectItem>
                <SelectItem value="activo">Activo</SelectItem>
                <SelectItem value="inactivo">Inactivo</SelectItem>
              </SelectContent>
            </Select>
          </Campo>
          <Button
            variant="outline"
            onClick={() => {
              setBusqueda('')
              setEstado(TODOS)
              setPagina(1)
            }}
          >
            <RotateCcwIcon /> Limpiar
          </Button>
        </div>

        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50">
              <TableHead className="w-10 pl-4">#</TableHead>
              <TableHead>Nombre completo</TableHead>
              <TableHead>Contacto</TableHead>
              <TableHead>Cargo / Función</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead className="pr-4 text-center">Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {lista.isLoading ? (
              <FilaMensaje columnas={6} cargando />
            ) : lista.isError ? (
              <FilaMensaje columnas={6} mensaje={mensajeError(lista.error)} />
            ) : !lista.data?.items.length ? (
              <FilaMensaje columnas={6} mensaje="No se encontró personal administrativo." />
            ) : (
              lista.data.items.map((a, i) => (
                <TableRow key={a.ci}>
                  <TableCell className="pl-4 text-slate-500">{(pagina - 1) * TAMANO + i + 1}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <AvatarIniciales
                        nombre={nombreCompleto(a)}
                        className={a.sexo === 'F' ? 'bg-rose-100 text-rose-700' : a.sexo === 'M' ? 'bg-sky-100 text-sky-700' : undefined}
                      />
                      <div>
                        <p className="font-medium">{a.apellidos}, {a.nombre_persona}</p>
                        <p className="text-xs text-slate-500">C.I. {documento(a.ci, a.expedido)}</p>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <p>{a.telefono ?? '—'}</p>
                    <p className="text-xs text-slate-500">{a.email ?? ''}</p>
                  </TableCell>
                  <TableCell>
                    <span className="font-medium text-slate-800">{a.cargo ?? 'Sin cargo asignado'}</span>
                  </TableCell>
                  <TableCell>
                    <InsigniaEstado estado={a.estado_persona} />
                  </TableCell>
                  <TableCell className="pr-4">
                    <div className="flex justify-center gap-1.5">
                      <BotonAccion etiqueta="Ver" tono="azul" onClick={() => setViendo(a.ci)}>
                        <EyeIcon />
                      </BotonAccion>
                      <BotonAccion etiqueta="Editar" tono="ambar" onClick={() => setFormulario({ ci: a.ci })}>
                        <PencilIcon />
                      </BotonAccion>
                      {a.estado_persona === 'activo' ? (
                        <BotonAccion etiqueta="Dar de baja" tono="rojo" onClick={() => setABaja(a)}>
                          <TrashIcon />
                        </BotonAccion>
                      ) : (
                        <BotonAccion etiqueta="Reactivar" tono="verde" onClick={() => setAReactivar(a)}>
                          <UserCheckIcon />
                        </BotonAccion>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>

        <Paginacion
          pagina={pagina}
          tamano={TAMANO}
          total={lista.data?.total ?? 0}
          etiqueta="administrativos"
          onCambiar={setPagina}
        />
      </div>

      {formulario && <DialogoAdministrativo ci={formulario.ci} onCerrar={() => setFormulario(null)} />}
      <DialogoDetalle ci={viendo} onCerrar={() => setViendo(null)} />
      {aBaja && <DialogoBaja administrativo={aBaja} onCerrar={() => setABaja(null)} />}
      <Confirmar
        abierto={!!aReactivar}
        onCambiar={(v) => !v && setAReactivar(null)}
        titulo="Reactivar personal administrativo"
        descripcion={`${aReactivar ? nombreCompleto(aReactivar) : ''} volverá a estar activo (y su cuenta de usuario, si tiene).`}
        textoConfirmar="Reactivar"
        icono={<UserCheckIcon />}
        ocupado={reactivar.isPending}
        onConfirmar={confirmarReactivar}
      />
    </div>
  )
}

function DialogoDetalle({ ci, onCerrar }: { ci: string | null; onCerrar: () => void }) {
  const detalle = useAdministrativo(ci)
  const d = detalle.data

  return (
    <Dialog open={ci !== null} onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>Ficha de personal administrativo</DialogTitle>
          <DialogDescription>Información registrada en el sistema escolar.</DialogDescription>
        </DialogHeader>
        {detalle.isLoading ? (
          <div className="py-8 text-center text-sm text-slate-500">Cargando información...</div>
        ) : d ? (
          <div className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-3 rounded-lg border bg-slate-50 p-4">
              <div>
                <span className="text-xs text-slate-500">Cédula de Identidad:</span>
                <p className="font-semibold text-slate-900">{documento(d.ci, d.expedido)}</p>
              </div>
              <div>
                <span className="text-xs text-slate-500">Estado:</span>
                <div>
                  <InsigniaEstado estado={d.estado_persona} />
                </div>
              </div>
              <div>
                <span className="text-xs text-slate-500">Nombre completo:</span>
                <p className="font-medium text-slate-900">{nombreCompleto(d)}</p>
              </div>
              <div>
                <span className="text-xs text-slate-500">Cargo:</span>
                <p className="font-medium text-slate-900">{d.cargo ?? 'No especificado'}</p>
              </div>
              <div>
                <span className="text-xs text-slate-500">Teléfono:</span>
                <p className="text-slate-700">{d.telefono ?? '—'}</p>
              </div>
              <div>
                <span className="text-xs text-slate-500">Correo electrónico:</span>
                <p className="text-slate-700">{d.email ?? '—'}</p>
              </div>
              <div>
                <span className="text-xs text-slate-500">Fecha de nacimiento:</span>
                <p className="text-slate-700">{fecha(d.fecha_nacimiento) || '—'}</p>
              </div>
              <div>
                <span className="text-xs text-slate-500">Cuenta de usuario:</span>
                <p className="font-medium text-slate-700">
                  {d.tiene_usuario ? 'Asociada en el sistema' : 'Sin cuenta activa'}
                </p>
              </div>
            </div>
            {d.direccion && (
              <div className="rounded-lg border p-3">
                <span className="text-xs text-slate-500">Dirección de domicilio:</span>
                <p className="text-slate-700">{d.direccion}</p>
              </div>
            )}
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}

function DialogoAdministrativo({ ci, onCerrar }: { ci: string | null; onCerrar: () => void }) {
  const edicion = ci !== null
  const existente = useAdministrativo(ci)
  const registrar = useRegistrarAdministrativo()
  const actualizar = useActualizarAdministrativo()

  const form = useForm<FormularioValores>({
    resolver: zodResolver(esquemaAdministrativo),
    defaultValues: { persona: PERSONA_VACIA, cargo: '' },
    values: existente.data
      ? {
          persona: personaAFormulario(existente.data),
          cargo: existente.data.cargo ?? '',
        }
      : undefined,
  })

  const guardar = form.handleSubmit(async (d) => {
    try {
      if (edicion && ci) {
        await actualizar.mutateAsync({
          ci,
          cuerpo: {
            persona: personaParaApi(d.persona),
            cargo: d.cargo || null,
          },
        })
        toast.success('Datos actualizados correctamente')
      } else {
        await registrar.mutateAsync({
          persona: personaParaApi(d.persona),
          cargo: d.cargo || null,
        })
        toast.success('Personal administrativo registrado con éxito')
      }
      onCerrar()
    } catch (e) {
      toast.error(mensajeError(e))
    }
  })

  const ocupado = registrar.isPending || actualizar.isPending

  return (
    <Dialog open onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{edicion ? 'Editar administrativo' : 'Nuevo personal administrativo'}</DialogTitle>
          <DialogDescription>
            {edicion
              ? 'Actualice los datos o el cargo del funcionario.'
              : 'Complete los datos personales y cargo. Si el CI ya existe, se reutilizarán sus datos.'}
          </DialogDescription>
        </DialogHeader>

        <FormProvider {...form}>
          <form onSubmit={guardar} className="space-y-4">
            <CamposPersona edicion={edicion} />

            <Separator />
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-slate-900">Datos del puesto</h4>
              <Campo
                etiqueta="Cargo o función administrativa"
                error={form.formState.errors.cargo?.message}
              >
                <Input
                  {...form.register('cargo')}
                  placeholder="Ej. Secretaria de Dirección, Contador, Auxiliar..."
                />
              </Campo>
            </div>

            <DialogFooter className="pt-2">
              <Button type="button" variant="outline" onClick={onCerrar} disabled={ocupado}>
                Cancelar
              </Button>
              <Button type="submit" disabled={ocupado}>
                {ocupado ? 'Guardando...' : edicion ? 'Guardar cambios' : 'Registrar administrativo'}
              </Button>
            </DialogFooter>
          </form>
        </FormProvider>
      </DialogContent>
    </Dialog>
  )
}

function DialogoBaja({
  administrativo,
  onCerrar,
}: {
  administrativo: Administrativo
  onCerrar: () => void
}) {
  const darBaja = useBajaAdministrativo()
  const form = useForm<{ motivo: string }>({
    resolver: zodResolver(esquemaBaja),
    defaultValues: { motivo: '' },
  })

  const guardar = form.handleSubmit(async (v) => {
    try {
      await darBaja.mutateAsync({ ci: administrativo.ci, motivo: v.motivo })
      toast.success('Personal dado de baja correctamente')
      onCerrar()
    } catch (e) {
      toast.error(mensajeError(e))
    }
  })

  return (
    <Dialog open onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Dar de baja a personal administrativo</DialogTitle>
          <DialogDescription>
            {nombreCompleto(administrativo)} y su usuario asociado pasarán a estado inactivo. No se borrará ningún registro histórico.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={guardar} className="space-y-4">
          <Campo etiqueta="Motivo de la baja" error={form.formState.errors.motivo?.message}>
            <Input {...form.register('motivo')} placeholder="Ej. Renuncia voluntaria, fin de contrato..." />
          </Campo>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onCerrar} disabled={darBaja.isPending}>
              Cancelar
            </Button>
            <Button type="submit" variant="destructive" disabled={darBaja.isPending}>
              {darBaja.isPending ? 'Procesando...' : 'Confirmar baja'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

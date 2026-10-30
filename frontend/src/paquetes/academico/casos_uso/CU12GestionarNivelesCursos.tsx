/**
 * CU12 - Gestionar niveles educativos y cursos
 * Paquete: academico
 *
 * Actores ........: Admin. académico
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/academico/casos_uso/cu12_gestionar_niveles_cursos.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Una pestaña por nivel educativo; dentro, sus grados en orden y los paralelos de cada
 * grado con la ocupación (inscritos de la gestión abierta / cupo). Registrar, modificar y
 * eliminar niveles, grados y paralelos; lo que está en uso no se elimina (el backend explica por qué).
 *
 * Precondición:  Sesión iniciada como administrador.
 * Postcondición: El catálogo de niveles, grados y cursos (paralelos y cupos) queda actualizado.
 *
 * Estado: IMPLEMENTADO.
 */
import { useState, type ReactNode } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'
import { cn } from 'cn'
import { BookOpenIcon, LayersIcon, PencilIcon, PlusIcon, Trash2Icon } from 'lucide-react'
import Confirmar from '@/componentes/Confirmar'
import { BotonAccion, Campo, EncabezadoPagina } from '@/componentes/comunes'
import { Button } from '@/componentes/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/componentes/ui/dialog'
import { Input } from '@/componentes/ui/input'
import { mensajeError } from '@/nucleo/api'
import {
  type ElementoEstructura,
  useEliminarEstructura,
  useEstructura,
  useGuardarCurso,
  useGuardarGrado,
  useGuardarNivel,
} from '../api'
import {
  type CursoEstructura,
  type DatosCurso,
  type DatosGrado,
  type DatosNivel,
  esquemaCurso,
  esquemaGrado,
  esquemaNivel,
  type GradoEstructura,
  type NivelEstructura,
} from '../schemas'

type Edicion =
  | { tipo: 'nivel'; nivel?: NivelEstructura }
  | { tipo: 'grado'; id_nivel: number; nombre_nivel: string; grado?: GradoEstructura; orden_sugerido: number }
  | { tipo: 'curso'; grado: GradoEstructura; curso?: CursoEstructura }

type Eliminacion = { tipo: ElementoEstructura; id: number; nombre: string }

const suma = (valores: number[]) => valores.reduce((a, b) => a + b, 0)

/** Primera letra libre (A, B, C...) para sugerir el siguiente paralelo. */
function paraleloSugerido(grado: GradoEstructura) {
  const usados = new Set(grado.cursos.map((c) => c.paralelo))
  return [...'ABCDEFGHIJKLMNOPQRSTUVWXYZ'].find((l) => !usados.has(l)) ?? ''
}

export default function CU12GestionarNivelesCursos() {
  const estructura = useEstructura()
  const [idNivel, setIdNivel] = useState<number | null>(null)
  const [edicion, setEdicion] = useState<Edicion | null>(null)
  const [eliminacion, setEliminacion] = useState<Eliminacion | null>(null)
  const eliminar = useEliminarEstructura()

  const niveles = estructura.data?.niveles ?? []
  const nivel = niveles.find((n) => n.id_nivel === idNivel) ?? niveles[0]

  const confirmarEliminar = async () => {
    if (!eliminacion) return
    try {
      await eliminar.mutateAsync({ tipo: eliminacion.tipo, id: eliminacion.id })
      toast.success(`Se eliminó ${eliminacion.nombre}.`)
    } catch (e) {
      toast.error(mensajeError(e))
    }
    setEliminacion(null)
  }

  return (
    <div className="space-y-5">
      <EncabezadoPagina
        titulo="Niveles educativos y cursos"
        descripcion="Organice los niveles, sus grados y los paralelos de cada grado con su cupo."
        accion={
          <Button onClick={() => setEdicion({ tipo: 'nivel' })}>
            <PlusIcon /> Nuevo nivel
          </Button>
        }
      />

      {estructura.isLoading ? (
        <p className="py-10 text-center text-slate-500">Cargando...</p>
      ) : estructura.isError ? (
        <p className="py-10 text-center text-slate-500">{mensajeError(estructura.error)}</p>
      ) : !nivel ? (
        <div className="rounded-xl border border-dashed bg-white py-12 text-center text-slate-500">
          Todavía no hay niveles educativos. Registre el primero con <b>Nuevo nivel</b>.
        </div>
      ) : (
        <>
          <div className="flex flex-wrap gap-2" role="tablist">
            {niveles.map((n) => (
              <button
                key={n.id_nivel}
                role="tab"
                aria-selected={n.id_nivel === nivel.id_nivel}
                onClick={() => setIdNivel(n.id_nivel)}
                className={cn(
                  'rounded-lg border px-4 py-2 text-sm font-medium transition-colors',
                  n.id_nivel === nivel.id_nivel
                    ? 'border-primary bg-primary text-primary-foreground shadow-sm'
                    : 'bg-white text-slate-600 hover:bg-slate-50',
                )}
              >
                {n.nombre_nivel}
                <span className="ml-2 text-xs opacity-75">{n.grados.length} grados</span>
              </button>
            ))}
          </div>

          <PanelNivel
            nivel={nivel}
            gestion={estructura.data?.gestion ?? null}
            onEditar={setEdicion}
            onEliminar={setEliminacion}
          />
        </>
      )}

      {edicion?.tipo === 'nivel' && <DialogoNivel edicion={edicion} onCerrar={() => setEdicion(null)} />}
      {edicion?.tipo === 'grado' && <DialogoGrado edicion={edicion} onCerrar={() => setEdicion(null)} />}
      {edicion?.tipo === 'curso' && <DialogoCurso edicion={edicion} onCerrar={() => setEdicion(null)} />}

      <Confirmar
        abierto={eliminacion !== null}
        onCambiar={(v) => !v && setEliminacion(null)}
        titulo="Confirmar eliminación"
        descripcion={`¿Eliminar ${eliminacion?.nombre ?? ''}? Esta acción no se puede deshacer.`}
        textoConfirmar="Eliminar"
        icono={<Trash2Icon />}
        peligro
        ocupado={eliminar.isPending}
        onConfirmar={confirmarEliminar}
      />
    </div>
  )
}

function PanelNivel({
  nivel,
  gestion,
  onEditar,
  onEliminar,
}: {
  nivel: NivelEstructura
  gestion: number | null
  onEditar: (e: Edicion) => void
  onEliminar: (e: Eliminacion) => void
}) {
  const cursos = nivel.grados.flatMap((g) => g.cursos)
  const ordenSugerido = Math.max(0, ...nivel.grados.map((g) => g.orden_grado)) + 1
  const nuevoGrado = () =>
    onEditar({ tipo: 'grado', id_nivel: nivel.id_nivel, nombre_nivel: nivel.nombre_nivel, orden_sugerido: ordenSugerido })

  return (
    <div className="rounded-xl border bg-white shadow-sm">
      <div className="flex flex-col gap-3 border-b p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <span className="inline-flex size-10 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
            <LayersIcon className="size-5" />
          </span>
          <div>
            <h2 className="text-lg font-semibold text-slate-900">{nivel.nombre_nivel}</h2>
            <p className="text-sm text-slate-500">
              {nivel.grados.length} grados · {cursos.length} paralelos ·{' '}
              {gestion
                ? `${suma(cursos.map((c) => c.inscritos))} inscritos de ${suma(cursos.map((c) => c.cupo_maximo))} cupos (gestión ${gestion})`
                : `${suma(cursos.map((c) => c.cupo_maximo))} cupos (sin gestión abierta)`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <BotonAccion etiqueta="Renombrar nivel" tono="ambar" onClick={() => onEditar({ tipo: 'nivel', nivel })}>
            <PencilIcon />
          </BotonAccion>
          <BotonAccion
            etiqueta="Eliminar nivel"
            tono="rojo"
            onClick={() => onEliminar({ tipo: 'niveles', id: nivel.id_nivel, nombre: `el nivel ${nivel.nombre_nivel}` })}
          >
            <Trash2Icon />
          </BotonAccion>
          <Button variant="outline" className="ml-1.5" onClick={nuevoGrado}>
            <PlusIcon /> Nuevo grado
          </Button>
        </div>
      </div>

      {!nivel.grados.length ? (
        <p className="py-12 text-center text-sm text-slate-500">Este nivel aún no tiene grados.</p>
      ) : (
        <ul className="divide-y">
          {nivel.grados.map((grado) => (
            <FilaGrado key={grado.id_grado} grado={grado} nivel={nivel} onEditar={onEditar} onEliminar={onEliminar} />
          ))}
        </ul>
      )}
    </div>
  )
}

function FilaGrado({
  grado,
  nivel,
  onEditar,
  onEliminar,
}: {
  grado: GradoEstructura
  nivel: NivelEstructura
  onEditar: (e: Edicion) => void
  onEliminar: (e: Eliminacion) => void
}) {
  const nombre = `${grado.nombre_grado} de ${nivel.nombre_nivel}`
  return (
    <li className="space-y-3 p-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <span className="inline-flex size-8 shrink-0 items-center justify-center rounded-full bg-slate-100 text-sm font-semibold text-slate-700">
            {grado.orden_grado}
          </span>
          <div className="min-w-0">
            <p className="truncate font-medium text-slate-900">{grado.nombre_grado}</p>
            <p className="flex items-center gap-1 text-xs text-slate-500">
              <BookOpenIcon className="size-3" /> {grado.materias} materias en el plan de estudios
            </p>
          </div>
        </div>
        <div className="flex shrink-0 gap-1.5">
          <BotonAccion
            etiqueta="Modificar grado"
            tono="ambar"
            onClick={() =>
              onEditar({ tipo: 'grado', id_nivel: nivel.id_nivel, nombre_nivel: nivel.nombre_nivel, grado, orden_sugerido: grado.orden_grado })
            }
          >
            <PencilIcon />
          </BotonAccion>
          <BotonAccion
            etiqueta="Eliminar grado"
            tono="rojo"
            onClick={() => onEliminar({ tipo: 'grados', id: grado.id_grado, nombre: `el grado ${nombre}` })}
          >
            <Trash2Icon />
          </BotonAccion>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-5 sm:pl-11">
        {grado.cursos.map((curso) => (
          <TarjetaParalelo
            key={curso.id_curso}
            curso={curso}
            onEditar={() => onEditar({ tipo: 'curso', grado, curso })}
            onEliminar={() =>
              onEliminar({ tipo: 'cursos', id: curso.id_curso, nombre: `el paralelo ${curso.paralelo} de ${nombre}` })
            }
          />
        ))}
        <button
          onClick={() => onEditar({ tipo: 'curso', grado })}
          className="flex min-h-24 flex-col items-center justify-center gap-1 rounded-lg border border-dashed text-sm text-slate-500 transition-colors hover:border-primary hover:bg-blue-50/50 hover:text-primary"
        >
          <PlusIcon className="size-4" /> Paralelo
        </button>
      </div>
    </li>
  )
}

function TarjetaParalelo({ curso, onEditar, onEliminar }: { curso: CursoEstructura; onEditar: () => void; onEliminar: () => void }) {
  const ocupacion = Math.min(1, curso.inscritos / curso.cupo_maximo)
  const lleno = curso.inscritos >= curso.cupo_maximo
  const tono = lleno ? 'bg-rose-500' : ocupacion >= 0.8 ? 'bg-amber-500' : 'bg-emerald-500'
  return (
    <div className="flex min-h-24 flex-col justify-between rounded-lg border bg-slate-50/50 p-3">
      <div className="flex items-start justify-between gap-1">
        <div>
          <p className="text-[11px] tracking-wide text-slate-500 uppercase">Paralelo</p>
          <p className="text-2xl leading-none font-bold text-slate-900">{curso.paralelo}</p>
        </div>
        <div className="flex gap-1">
          <BotonAccion etiqueta="Modificar paralelo o cupo" tono="ambar" onClick={onEditar}>
            <PencilIcon />
          </BotonAccion>
          <BotonAccion etiqueta="Eliminar paralelo" tono="rojo" onClick={onEliminar}>
            <Trash2Icon />
          </BotonAccion>
        </div>
      </div>
      <div className="mt-3 space-y-1">
        <div className="h-1.5 overflow-hidden rounded-full bg-slate-200">
          <div className={cn('h-full rounded-full', tono)} style={{ width: `${ocupacion * 100}%` }} />
        </div>
        <p className="text-xs text-slate-600">
          {curso.inscritos} / {curso.cupo_maximo} inscritos
          {lleno && <span className="ml-1 font-medium text-rose-600">· lleno</span>}
        </p>
      </div>
    </div>
  )
}

// ------------------------------------------------------------
// Diálogos de registro y modificación
// ------------------------------------------------------------

function DialogoFormulario({
  titulo,
  descripcion,
  ocupado,
  onCerrar,
  onGuardar,
  children,
}: {
  titulo: string
  descripcion: string
  ocupado: boolean
  onCerrar: () => void
  onGuardar: () => void
  children: ReactNode
}) {
  return (
    <Dialog open onOpenChange={(v) => !v && onCerrar()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{titulo}</DialogTitle>
          <DialogDescription>{descripcion}</DialogDescription>
        </DialogHeader>
        <form
          id="form-cu12"
          className="grid gap-3"
          noValidate
          onSubmit={(e) => {
            e.preventDefault()
            onGuardar()
          }}
        >
          {children}
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={onCerrar}>Cancelar</Button>
          <Button type="submit" form="form-cu12" disabled={ocupado}>Guardar</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

/** Guarda, avisa y cierra; si el backend rechaza, muestra su mensaje y deja el diálogo abierto. */
async function guardarYCerrar(guardar: () => Promise<unknown>, exito: string, onCerrar: () => void) {
  try {
    await guardar()
    toast.success(exito)
    onCerrar()
  } catch (e) {
    toast.error(mensajeError(e))
  }
}

function DialogoNivel({ edicion, onCerrar }: { edicion: Extract<Edicion, { tipo: 'nivel' }>; onCerrar: () => void }) {
  const guardar = useGuardarNivel()
  const form = useForm<DatosNivel>({
    resolver: zodResolver(esquemaNivel),
    defaultValues: { nombre_nivel: edicion.nivel?.nombre_nivel ?? '' },
  })
  const enviar = form.handleSubmit((datos) =>
    guardarYCerrar(
      () => guardar.mutateAsync({ id: edicion.nivel?.id_nivel, datos }),
      edicion.nivel ? 'Nivel actualizado.' : `Nivel ${datos.nombre_nivel} registrado.`,
      onCerrar,
    ),
  )
  return (
    <DialogoFormulario
      titulo={edicion.nivel ? 'Renombrar nivel' : 'Nuevo nivel educativo'}
      descripcion="Ej.: Inicial, Primaria, Secundaria."
      ocupado={guardar.isPending}
      onCerrar={onCerrar}
      onGuardar={enviar}
    >
      <Campo etiqueta="Nombre del nivel" htmlFor="nombre_nivel" error={form.formState.errors.nombre_nivel?.message}>
        <Input id="nombre_nivel" autoFocus maxLength={50} {...form.register('nombre_nivel')} />
      </Campo>
    </DialogoFormulario>
  )
}

function DialogoGrado({ edicion, onCerrar }: { edicion: Extract<Edicion, { tipo: 'grado' }>; onCerrar: () => void }) {
  const guardar = useGuardarGrado()
  const form = useForm<DatosGrado>({
    resolver: zodResolver(esquemaGrado),
    defaultValues: { nombre_grado: edicion.grado?.nombre_grado ?? '', orden_grado: edicion.orden_sugerido },
  })
  const e = form.formState.errors
  const enviar = form.handleSubmit((datos) =>
    guardarYCerrar(
      () => guardar.mutateAsync({ id: edicion.grado?.id_grado, id_nivel: edicion.id_nivel, datos }),
      edicion.grado ? 'Grado actualizado.' : `Grado ${datos.nombre_grado} registrado.`,
      onCerrar,
    ),
  )
  return (
    <DialogoFormulario
      titulo={edicion.grado ? 'Modificar grado' : 'Nuevo grado'}
      descripcion={`Nivel ${edicion.nombre_nivel}. El orden define cómo se listan los grados (1, 2, 3...).`}
      ocupado={guardar.isPending}
      onCerrar={onCerrar}
      onGuardar={enviar}
    >
      <div className="grid grid-cols-[1fr_7rem] gap-3">
        <Campo etiqueta="Nombre del grado" htmlFor="nombre_grado" error={e.nombre_grado?.message}>
          <Input id="nombre_grado" autoFocus maxLength={50} placeholder="Ej.: 1ro" {...form.register('nombre_grado')} />
        </Campo>
        <Campo etiqueta="Orden" htmlFor="orden_grado" error={e.orden_grado?.message}>
          <Input id="orden_grado" type="number" min={1} max={99} {...form.register('orden_grado', { valueAsNumber: true })} />
        </Campo>
      </div>
    </DialogoFormulario>
  )
}

function DialogoCurso({ edicion, onCerrar }: { edicion: Extract<Edicion, { tipo: 'curso' }>; onCerrar: () => void }) {
  const guardar = useGuardarCurso()
  const { curso, grado } = edicion
  const form = useForm<DatosCurso>({
    resolver: zodResolver(esquemaCurso),
    defaultValues: { paralelo: curso?.paralelo ?? paraleloSugerido(grado), cupo_maximo: curso?.cupo_maximo ?? 35 },
  })
  const e = form.formState.errors
  const enviar = form.handleSubmit((datos) =>
    guardarYCerrar(
      () => guardar.mutateAsync({ id: curso?.id_curso, id_grado: grado.id_grado, datos }),
      curso ? 'Paralelo actualizado.' : `Paralelo ${datos.paralelo} registrado.`,
      onCerrar,
    ),
  )
  return (
    <DialogoFormulario
      titulo={curso ? `Modificar paralelo ${curso.paralelo}` : 'Nuevo paralelo'}
      descripcion={`Grado ${grado.nombre_grado}.${curso?.inscritos ? ` Tiene ${curso.inscritos} inscritos: el cupo no puede ser menor.` : ''}`}
      ocupado={guardar.isPending}
      onCerrar={onCerrar}
      onGuardar={enviar}
    >
      <div className="grid grid-cols-2 gap-3">
        <Campo etiqueta="Paralelo" htmlFor="paralelo" error={e.paralelo?.message}>
          <Input id="paralelo" autoFocus maxLength={5} className="uppercase" placeholder="A" {...form.register('paralelo')} />
        </Campo>
        <Campo etiqueta="Cupo máximo" htmlFor="cupo_maximo" error={e.cupo_maximo?.message}>
          <Input
            id="cupo_maximo"
            type="number"
            min={Math.max(1, curso?.inscritos ?? 1)}
            max={100}
            {...form.register('cupo_maximo', { valueAsNumber: true })}
          />
        </Campo>
      </div>
    </DialogoFormulario>
  )
}

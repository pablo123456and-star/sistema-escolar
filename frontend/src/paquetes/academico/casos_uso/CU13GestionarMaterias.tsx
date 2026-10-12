/**
 * CU13 - Gestionar materias y plan de estudios
 * Paquete: academico
 *
 * Actores: Administrador académico
 * Rol del sistema: administrador
 *
 * Backend:
 * backend/app/paquetes/academico/casos_uso/cu13_gestionar_materias.py
 *
 * Funcionalidades:
 * - Listar y buscar materias.
 * - Registrar, modificar y eliminar materias.
 * - Consultar niveles y grados.
 * - Consultar el plan de estudios.
 * - Agregar y quitar materias del plan.
 *
 * Tablas: materia, materia_grado, nivel_educativo, grado.
 *
 * Estado: IMPLEMENTADO.
 */

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { toast } from 'sonner'

import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  SearchIcon,
  RotateCcwIcon,
  BookOpenIcon,
} from 'lucide-react'

import Confirmar from '@/componentes/Confirmar'

import {
  EncabezadoPagina,
  Campo,
  BotonAccion,
  FilaMensaje,
  Paginacion,
} from '@/componentes/comunes'

import { Button } from '@/componentes/ui/button'
import { Input } from '@/componentes/ui/input'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/componentes/ui/dialog'

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/componentes/ui/select'

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/componentes/ui/table'

import { TODOS } from '@/lib/filtros'
import { useRetardo } from '@/lib/useRetardo'
import { mensajeError } from '@/nucleo/api'

import {
  useMaterias,
  useRegistrarMateria,
  useActualizarMateria,
  useEliminarMateria,
  useOpcionesPlan,
  usePlanEstudios,
  useAgregarMateriaPlan,
  useQuitarMateriaPlan,
} from '../api'

import {
  esquemaMateria,
  type Materia,
  type DatosMateria,
} from '../schemas'


const TAMANO = 10


// ============================================================
// PANTALLA PRINCIPAL DEL CU13
// ============================================================

export default function CU13GestionarMaterias() {

  // Estados de materias

  const [busqueda, setBusqueda] = useState('')
  const [pagina, setPagina] = useState(1)

  const [formulario, setFormulario] = useState<{
    materia: Materia | null
  } | null>(null)

  const [materiaEliminar, setMateriaEliminar] =
    useState<Materia | null>(null)

  // Estados del plan de estudios

  const [nivel, setNivel] = useState(TODOS)
  const [grado, setGrado] = useState(TODOS)
  const [materiaSeleccionada, setMateriaSeleccionada] =
    useState(TODOS)

  const [materiaQuitar, setMateriaQuitar] =
    useState<Materia | null>(null)

  // Consultas al backend

  const q = useRetardo(busqueda)

  const lista = useMaterias({
    q,
    pagina,
    tamano: TAMANO,
  })

  const opciones = useOpcionesPlan()

  const idGrado = grado === TODOS ? null : Number(grado)

  const plan = usePlanEstudios(idGrado)

  // Mutaciones

  const eliminar = useEliminarMateria()
  const agregarPlan = useAgregarMateriaPlan()
  const quitarPlan = useQuitarMateriaPlan()

  // Grados del nivel seleccionado

  const grados = opciones.data?.grados.filter(
    (g) => g.id_nivel_educativo_grado === Number(nivel)
  ) ?? []


  // ----------------------------------------------------------
  // ELIMINAR MATERIA
  // ----------------------------------------------------------

  const confirmarEliminar = async () => {

    if (!materiaEliminar) return

    try {

      await eliminar.mutateAsync(
        materiaEliminar.id_materia
      )

      toast.success('Materia eliminada correctamente.')

      setMateriaEliminar(null)

    } catch (error) {

      toast.error(mensajeError(error))

    }
  }


  // ----------------------------------------------------------
  // AGREGAR MATERIA AL PLAN
  // ----------------------------------------------------------

  const agregarAlPlan = async () => {

    if (idGrado === null || materiaSeleccionada === TODOS) {
      return
    }

    try {

      await agregarPlan.mutateAsync({
        id_grado: idGrado,
        datos: {
          id_materia: Number(materiaSeleccionada),
        },
      })

      toast.success(
        'Materia agregada al plan de estudios.'
      )

      setMateriaSeleccionada(TODOS)

    } catch (error) {

      toast.error(mensajeError(error))

    }
  }


  // ----------------------------------------------------------
  // QUITAR MATERIA DEL PLAN
  // ----------------------------------------------------------

  const confirmarQuitar = async () => {

    if (idGrado === null || !materiaQuitar) return

    try {

      await quitarPlan.mutateAsync({
        id_grado: idGrado,
        id_materia: materiaQuitar.id_materia,
      })

      toast.success(
        'Materia quitada del plan de estudios.'
      )

      setMateriaQuitar(null)

    } catch (error) {

      toast.error(mensajeError(error))

    }
  }


  // ==========================================================
  // INTERFAZ
  // ==========================================================

  return (

    <div className="space-y-5">

      <EncabezadoPagina
        titulo="Gestión de materias"
        descripcion="Administre las materias y los planes de estudios de la institución."
        accion={
          <Button
            size="lg"
            onClick={() => setFormulario({ materia: null })}
          >
            <PlusIcon />
            Nueva materia
          </Button>
        }
      />


      {/* ====================================================
          SECCIÓN 1: MATERIAS
      ==================================================== */}

      <section className="rounded-xl border bg-white shadow-sm">

        <div className="border-b p-4">

          <h2 className="font-semibold text-slate-800">
            Materias registradas
          </h2>

          <p className="text-sm text-slate-500">
            Consulte y administre las materias del colegio.
          </p>

        </div>


        {/* Buscador */}

        <div className="flex flex-col gap-3 p-4 sm:flex-row">

          <div className="relative flex-1">

            <SearchIcon
              className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400"
            />

            <Input
              value={busqueda}
              placeholder="Buscar materia..."
              className="pl-9"
              onChange={(e) => {
                setBusqueda(e.target.value)
                setPagina(1)
              }}
            />

          </div>

          <Button
            variant="outline"
            onClick={() => {
              setBusqueda('')
              setPagina(1)
            }}
          >
            <RotateCcwIcon />
            Limpiar
          </Button>

        </div>


        {/* Tabla para computadoras */}

        <div className="hidden md:block">

          <Table>

            <TableHeader>

              <TableRow className="bg-slate-50">

                <TableHead className="pl-4">
                  #
                </TableHead>

                <TableHead>
                  Materia
                </TableHead>

                <TableHead>
                  Carga horaria
                </TableHead>

                <TableHead className="text-center">
                  Acciones
                </TableHead>

              </TableRow>

            </TableHeader>


            <TableBody>

              {lista.isLoading ? (

                <FilaMensaje columnas={4} cargando />

              ) : lista.isError ? (

                <FilaMensaje
                  columnas={4}
                  mensaje={mensajeError(lista.error)}
                />

              ) : !lista.data?.items.length ? (

                <FilaMensaje
                  columnas={4}
                  mensaje="No se encontraron materias."
                />

              ) : (

                lista.data.items.map((materia, indice) => (

                  <TableRow key={materia.id_materia}>

                    <TableCell className="pl-4 text-slate-500">

                      {(pagina - 1) * TAMANO + indice + 1}

                    </TableCell>

                    <TableCell className="font-medium">

                      {materia.nombre_materia}

                    </TableCell>

                    <TableCell>

                      {materia.carga_horaria ?? '—'}

                    </TableCell>

                    <TableCell>

                      <div className="flex justify-center gap-2">

                        <BotonAccion
                          etiqueta="Editar"
                          tono="ambar"
                          onClick={() =>
                            setFormulario({ materia })
                          }
                        >
                          <PencilIcon />
                        </BotonAccion>

                        <BotonAccion
                          etiqueta="Eliminar"
                          tono="rojo"
                          onClick={() =>
                            setMateriaEliminar(materia)
                          }
                        >
                          <TrashIcon />
                        </BotonAccion>

                      </div>

                    </TableCell>

                  </TableRow>

                ))

              )}

            </TableBody>

          </Table>

        </div>


        {/* Lista adaptable a celulares */}

        <div className="divide-y md:hidden">

          {lista.isLoading ? (

            <p className="p-4 text-sm text-slate-500">
              Cargando materias...
            </p>

          ) : lista.isError ? (

            <p className="p-4 text-sm text-rose-600">
              {mensajeError(lista.error)}
            </p>

          ) : !lista.data?.items.length ? (

            <p className="p-4 text-sm text-slate-500">
              No se encontraron materias.
            </p>

          ) : (

            lista.data.items.map((materia) => (

              <div
                key={materia.id_materia}
                className="flex items-center justify-between gap-3 p-4"
              >

                <div className="min-w-0">

                  <p className="break-words font-medium">
                    {materia.nombre_materia}
                  </p>

                  <p className="text-sm text-slate-500">
                    Carga horaria: {materia.carga_horaria ?? '—'}
                  </p>

                </div>

                <div className="flex shrink-0 gap-2">

                  <BotonAccion
                    etiqueta="Editar"
                    tono="ambar"
                    onClick={() =>
                      setFormulario({ materia })
                    }
                  >
                    <PencilIcon />
                  </BotonAccion>

                  <BotonAccion
                    etiqueta="Eliminar"
                    tono="rojo"
                    onClick={() =>
                      setMateriaEliminar(materia)
                    }
                  >
                    <TrashIcon />
                  </BotonAccion>

                </div>

              </div>

            ))

          )}

        </div>


        <Paginacion
          pagina={pagina}
          tamano={TAMANO}
          total={lista.data?.total ?? 0}
          etiqueta="materias"
          onCambiar={setPagina}
        />

      </section>


      {/* ====================================================
          SECCIÓN 2: PLAN DE ESTUDIOS
      ==================================================== */}

      <section className="rounded-xl border bg-white shadow-sm">

        <div className="border-b p-4">

          <div className="flex items-center gap-2">

            <BookOpenIcon className="size-5 text-slate-600" />

            <h2 className="font-semibold text-slate-800">
              Plan de estudios
            </h2>

          </div>

          <p className="mt-1 text-sm text-slate-500">
            Seleccione un nivel y un grado para administrar sus materias.
          </p>

        </div>


        {/* Selección de nivel y grado */}

        <div className="grid gap-4 p-4 sm:grid-cols-2">

          <Campo etiqueta="Nivel educativo">

            <Select
              value={nivel}
              onValueChange={(valor) => {
                setNivel(valor)
                setGrado(TODOS)
                setMateriaSeleccionada(TODOS)
              }}
            >

              <SelectTrigger className="w-full">
                <SelectValue placeholder="Seleccione nivel" />
              </SelectTrigger>

              <SelectContent>

                <SelectItem value={TODOS}>
                  Seleccione nivel
                </SelectItem>

                {opciones.data?.niveles.map((n) => (

                  <SelectItem
                    key={n.id_nivel}
                    value={String(n.id_nivel)}
                  >
                    {n.nombre_nivel}
                  </SelectItem>

                ))}

              </SelectContent>

            </Select>

          </Campo>


          <Campo etiqueta="Grado">

            <Select
              value={grado}
              disabled={nivel === TODOS}
              onValueChange={(valor) => {
                setGrado(valor)
                setMateriaSeleccionada(TODOS)
              }}
            >

              <SelectTrigger className="w-full">
                <SelectValue placeholder="Seleccione grado" />
              </SelectTrigger>

              <SelectContent>

                <SelectItem value={TODOS}>
                  Seleccione grado
                </SelectItem>

                {grados.map((g) => (

                  <SelectItem
                    key={g.id_grado}
                    value={String(g.id_grado)}
                  >
                    {g.nombre_grado}
                  </SelectItem>

                ))}

              </SelectContent>

            </Select>

          </Campo>

        </div>


        {opciones.isError && (
          <p className="px-4 pb-4 text-sm text-rose-600">
            {mensajeError(opciones.error)}
          </p>
        )}


        {idGrado === null ? (

          <div className="border-t p-8 text-center text-slate-500">

            Seleccione un nivel educativo y un grado
            para consultar el plan de estudios.

          </div>

        ) : (

          <div className="space-y-4 border-t p-4">


            {/* Agregar materia */}

            <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">

              <Campo etiqueta="Agregar materia al plan">

                <Select
                  value={materiaSeleccionada}
                  onValueChange={setMateriaSeleccionada}
                >

                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Seleccione materia" />
                  </SelectTrigger>

                  <SelectContent>

                    <SelectItem value={TODOS}>
                      Seleccione materia
                    </SelectItem>

                    {plan.data?.materias_disponibles.map((m) => (

                      <SelectItem
                        key={m.id_materia}
                        value={String(m.id_materia)}
                      >
                        {m.nombre_materia}
                      </SelectItem>

                    ))}

                  </SelectContent>

                </Select>

              </Campo>


              <Button
                disabled={
                  materiaSeleccionada === TODOS ||
                  agregarPlan.isPending
                }
                onClick={agregarAlPlan}
              >

                <PlusIcon />
                Agregar

              </Button>

            </div>


            {/* Materias del plan */}

            <div className="rounded-lg border">

              <div className="border-b bg-slate-50 px-4 py-3">

                <h3 className="text-sm font-semibold">
                  Materias del grado
                </h3>

              </div>


              {plan.isLoading ? (

                <p className="p-4 text-sm text-slate-500">
                  Cargando plan de estudios...
                </p>

              ) : plan.isError ? (

                <p className="p-4 text-sm text-rose-600">
                  {mensajeError(plan.error)}
                </p>

              ) : !plan.data?.materias_plan.length ? (

                <p className="p-4 text-sm text-slate-500">
                  Este grado no tiene materias registradas.
                </p>

              ) : (

                <div className="divide-y">

                  {plan.data.materias_plan.map((materia) => (

                    <div
                      key={materia.id_materia}
                      className="flex items-center justify-between gap-3 p-3 sm:px-4"
                    >

                      <div className="min-w-0">

                        <p className="break-words text-sm font-medium">
                          {materia.nombre_materia}
                        </p>

                        <p className="text-xs text-slate-500">
                          Carga horaria: {materia.carga_horaria ?? '—'}
                        </p>

                      </div>


                      <BotonAccion
                        etiqueta="Quitar del plan"
                        tono="rojo"
                        onClick={() =>
                          setMateriaQuitar(materia)
                        }
                      >
                        <TrashIcon />
                      </BotonAccion>

                    </div>

                  ))}

                </div>

              )}

            </div>

          </div>

        )}

      </section>


      {/* ====================================================
          FORMULARIO DE REGISTRO Y EDICIÓN
      ==================================================== */}

      {formulario && (

        <DialogoMateria
          materia={formulario.materia}
          onCerrar={() => setFormulario(null)}
        />

      )}


      {/* Confirmación para eliminar materia */}

      <Confirmar
        abierto={!!materiaEliminar}
        onCambiar={(abierto) =>
          !abierto && setMateriaEliminar(null)
        }
        titulo="Eliminar materia"
        descripcion={
          `¿Desea eliminar la materia "${materiaEliminar?.nombre_materia ?? ''}"? No será posible si pertenece a un plan de estudios o tiene asignaciones.`
        }
        textoConfirmar="Eliminar"
        peligro
        icono={<TrashIcon />}
        ocupado={eliminar.isPending}
        onConfirmar={confirmarEliminar}
      />


      {/* Confirmación para quitar materia del plan */}

      <Confirmar
        abierto={!!materiaQuitar}
        onCambiar={(abierto) =>
          !abierto && setMateriaQuitar(null)
        }
        titulo="Quitar materia del plan"
        descripcion={
          `¿Desea quitar "${materiaQuitar?.nombre_materia ?? ''}" del plan de estudios?`
        }
        textoConfirmar="Quitar materia"
        peligro
        icono={<TrashIcon />}
        ocupado={quitarPlan.isPending}
        onConfirmar={confirmarQuitar}
      />

    </div>

  )
}


// ============================================================
// FORMULARIO DE MATERIA
// ============================================================

function DialogoMateria({
  materia,
  onCerrar,
}: {
  materia: Materia | null
  onCerrar: () => void
}) {

  const edicion = materia !== null

  const registrar = useRegistrarMateria()
  const actualizar = useActualizarMateria()

  const form = useForm<DatosMateria>({
    resolver: zodResolver(esquemaMateria),

    defaultValues: {
      nombre_materia: materia?.nombre_materia ?? '',
      carga_horaria: materia?.carga_horaria ?? 1,
    },
  })


  // Guardar registro o modificación

  const guardar = form.handleSubmit(async (datos) => {

    try {

      if (materia) {

        await actualizar.mutateAsync({
          id_materia: materia.id_materia,
          datos,
        })

        toast.success('Materia actualizada correctamente.')

      } else {

        await registrar.mutateAsync(datos)

        toast.success('Materia registrada correctamente.')

      }

      onCerrar()

    } catch (error) {

      toast.error(mensajeError(error))

    }

  })


  const ocupado =
    registrar.isPending || actualizar.isPending


  return (

    <Dialog
      open
      onOpenChange={(abierto) => !abierto && onCerrar()}
    >

      <DialogContent className="sm:max-w-md">

        <DialogHeader>

          <DialogTitle>

            {edicion ? 'Editar materia' : 'Nueva materia'}

          </DialogTitle>

          <DialogDescription>

            {edicion
              ? 'Modifique la información de la materia.'
              : 'Complete los datos para registrar una materia.'}

          </DialogDescription>

        </DialogHeader>


        <form
          id="form-materia"
          onSubmit={guardar}
          className="space-y-4"
        >

          <Campo
            etiqueta="Nombre de la materia"
            htmlFor="nombre_materia"
            error={
              form.formState.errors.nombre_materia?.message
            }
          >

            <Input
              id="nombre_materia"
              placeholder="Ej. Matemáticas"
              {...form.register('nombre_materia')}
            />

          </Campo>


          <Campo
            etiqueta="Carga horaria"
            htmlFor="carga_horaria"
            error={
              form.formState.errors.carga_horaria?.message
            }
          >

            <Input
              id="carga_horaria"
              type="number"
              min={1}
              step={1}
              {...form.register('carga_horaria', {
                valueAsNumber: true,
              })}
            />

          </Campo>

        </form>


        <DialogFooter>

          <Button
            variant="outline"
            onClick={onCerrar}
            disabled={ocupado}
          >
            Cancelar
          </Button>

          <Button
            type="submit"
            form="form-materia"
            disabled={ocupado}
          >

            {edicion ? 'Guardar cambios' : 'Registrar materia'}

          </Button>

        </DialogFooter>

      </DialogContent>

    </Dialog>

  )
}

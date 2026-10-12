/**
 * CU14 - Asignar profesor a materia/curso
 * Paquete: academico
 *
 * Actor: Administrador académico
 * Rol del sistema: administrador
 *
 * Funcionalidades:
 * - Consultar cursos de la gestión abierta.
 * - Consultar materias del curso.
 * - Asignar profesor y aula.
 * - Modificar asignaciones.
 * - Eliminar asignaciones permitidas.
 *
 * Estado: IMPLEMENTADO.
 */

import { useState } from 'react'

import { Controller, useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'

import { toast } from 'sonner'

import {
  BookOpenIcon,
  GraduationCapIcon,
  PencilIcon,
  PlusIcon,
  TrashIcon,
  UsersIcon,
} from 'lucide-react'

import Confirmar from '@/componentes/Confirmar'

import {
  EncabezadoPagina,
  Campo,
  BotonAccion,
  FilaMensaje,
} from '@/componentes/comunes'

import { Button } from '@/componentes/ui/button'

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
import { mensajeError } from '@/nucleo/api'

import {
  useOpcionesAsignacion,
  useMateriasCursoAsignacion,
  useRegistrarAsignacion,
  useActualizarAsignacion,
  useEliminarAsignacion,
} from '../api'

import {
  esquemaAsignacionCrear,
  type DatosAsignacionCrear,
  type MateriaCursoAsignacion,
  type ProfesorOpcionAsignacion,
  type AulaOpcionAsignacion,
} from '../schemas'


// ============================================================
// VALIDACIÓN DEL FORMULARIO
// ============================================================

const esquemaFormulario = esquemaAsignacionCrear.pick({
  ci_profesor: true,
  id_aula: true,
})

type DatosFormulario = Pick<
  DatosAsignacionCrear,
  'ci_profesor' | 'id_aula'
>


// ============================================================
// PANTALLA PRINCIPAL DEL CU14
// ============================================================

export default function CU14AsignarProfesor() {

  // ----------------------------------------------------------
  // ESTADOS
  // ----------------------------------------------------------

  const [cursoSeleccionado, setCursoSeleccionado] =
    useState<string>(TODOS)

  const [materiaFormulario, setMateriaFormulario] =
    useState<MateriaCursoAsignacion | null>(null)

  const [materiaEliminar, setMateriaEliminar] =
    useState<MateriaCursoAsignacion | null>(null)


  // ----------------------------------------------------------
  // CONSULTAS
  // ----------------------------------------------------------

  const opciones = useOpcionesAsignacion()

  const idCurso =
    cursoSeleccionado === TODOS
      ? null
      : Number(cursoSeleccionado)

  const consultaMaterias =
    useMateriasCursoAsignacion(idCurso)

  const eliminar = useEliminarAsignacion()


  // ----------------------------------------------------------
  // DATOS CALCULADOS
  // ----------------------------------------------------------

  const cursoActual = opciones.data?.cursos.find(
    (curso) => curso.id_curso === idCurso
  )

  const materias = consultaMaterias.data?.materias ?? []

  const cantidadAsignadas = materias.filter(
    (materia) => materia.id_asignacion !== null
  ).length

  const cantidadPendientes =
    materias.length - cantidadAsignadas


  // ----------------------------------------------------------
  // ELIMINAR ASIGNACIÓN
  // ----------------------------------------------------------

  const confirmarEliminar = async () => {

    if (
      !materiaEliminar ||
      materiaEliminar.id_asignacion === null
    ) {
      return
    }

    try {

      await eliminar.mutateAsync(
        materiaEliminar.id_asignacion
      )

      toast.success(
        'Asignación eliminada correctamente.'
      )

      setMateriaEliminar(null)

    } catch (error) {

      toast.error(mensajeError(error))

    }
  }


  // ==========================================================
  // INTERFAZ
  // ==========================================================

  return (

    <div className="space-y-5">

      {/* ENCABEZADO */}

      <EncabezadoPagina
        titulo="Asignación de profesores"
        descripcion="Administre los profesores y aulas asignados a las materias de cada curso."
      />


      {/* ====================================================
          SECCIÓN 1: SELECCIONAR CURSO
      ==================================================== */}

      <section className="rounded-xl border bg-card shadow-sm">

        <div className="border-b p-4">

          <div className="flex items-center gap-2">

            <GraduationCapIcon className="size-5 text-slate-600" />

            <h2 className="font-semibold">
              Seleccionar curso
            </h2>

          </div>

          <p className="mt-1 text-sm text-muted-foreground">
            Seleccione el curso para consultar sus materias
            y asignaciones.
          </p>

        </div>


        <div className="grid gap-4 p-4 sm:grid-cols-2">

          {/* GESTIÓN ACADÉMICA */}

          <Campo etiqueta="Gestión académica">

            <div className="flex h-9 items-center rounded-md border bg-muted/40 px-3 text-sm">

              {opciones.isLoading
                ? 'Cargando...'
                : opciones.data?.anio_gestion
                  ?? 'Sin gestión abierta'}

            </div>

          </Campo>


          {/* CURSO */}

          <Campo etiqueta="Curso">

            <Select
              value={cursoSeleccionado}
              disabled={
                opciones.isLoading ||
                opciones.isError
              }
              onValueChange={(valor) => {
                setCursoSeleccionado(valor)
                setMateriaFormulario(null)
              }}
            >

              <SelectTrigger className="w-full">
                <SelectValue placeholder="Seleccione un curso" />
              </SelectTrigger>

              <SelectContent>

                <SelectItem value={TODOS}>
                  Seleccione un curso
                </SelectItem>

                {opciones.data?.cursos.map((curso) => (

                  <SelectItem
                    key={curso.id_curso}
                    value={String(curso.id_curso)}
                  >
                    {curso.nombre_curso}
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

      </section>


      {/* ====================================================
          SECCIÓN 2: MATERIAS DEL CURSO
      ==================================================== */}

      <section className="rounded-xl border bg-card shadow-sm">

        <div className="border-b p-4">

          <div className="flex items-center gap-2">

            <BookOpenIcon className="size-5 text-slate-600" />

            <h2 className="font-semibold">
              Materias y profesores asignados
            </h2>

          </div>

          <p className="mt-1 text-sm text-muted-foreground">

            {cursoActual
              ? `Curso: ${cursoActual.nombre_curso}`
              : 'Seleccione un curso para visualizar sus materias.'}

          </p>

        </div>


        {/* RESUMEN */}

        {idCurso !== null && !consultaMaterias.isError && (

          <div className="grid gap-3 border-b p-4 sm:grid-cols-3">

            <div className="rounded-lg border bg-muted/30 p-3">

              <p className="text-sm text-muted-foreground">
                Total de materias
              </p>

              <p className="text-2xl font-semibold">
                {materias.length}
              </p>

            </div>


            <div className="rounded-lg border bg-muted/30 p-3">

              <p className="text-sm text-muted-foreground">
                Con profesor asignado
              </p>

              <p className="text-2xl font-semibold">
                {cantidadAsignadas}
              </p>

            </div>


            <div className="rounded-lg border bg-muted/30 p-3">

              <p className="text-sm text-muted-foreground">
                Pendientes de asignación
              </p>

              <p className="text-2xl font-semibold">
                {cantidadPendientes}
              </p>

            </div>

          </div>

        )}


        {/* MENSAJE INICIAL */}

        {idCurso === null ? (

          <div className="p-10 text-center">

            <UsersIcon
              className="mx-auto mb-3 size-10 text-muted-foreground"
            />

            <p className="text-sm text-muted-foreground">
              Seleccione un curso para administrar
              las asignaciones de profesores.
            </p>

          </div>

        ) : (

          <>

            {/* TABLA PARA COMPUTADORAS */}

            <div className="hidden md:block">

              <Table>

                <TableHeader>

                  <TableRow className="bg-muted/40">

                    <TableHead className="pl-4">
                      Materia
                    </TableHead>

                    <TableHead>
                      Profesor
                    </TableHead>

                    <TableHead>
                      Aula
                    </TableHead>

                    <TableHead>
                      Estado
                    </TableHead>

                    <TableHead className="text-center">
                      Acciones
                    </TableHead>

                  </TableRow>

                </TableHeader>


                <TableBody>

                  {consultaMaterias.isLoading ? (

                    <FilaMensaje columnas={5} cargando />

                  ) : consultaMaterias.isError ? (

                    <FilaMensaje
                      columnas={5}
                      mensaje={mensajeError(consultaMaterias.error)}
                    />

                  ) : materias.length === 0 ? (

                    <FilaMensaje
                      columnas={5}
                      mensaje="Este curso no tiene materias en su plan de estudios."
                    />

                  ) : (

                    materias.map((materia) => (

                      <TableRow key={materia.id_materia}>

                        <TableCell className="pl-4 font-medium">

                          {materia.nombre_materia}

                        </TableCell>


                        <TableCell>

                          {materia.nombre_profesor
                            ?? 'Sin profesor'}

                        </TableCell>


                        <TableCell>

                          {materia.numero_aula ?? '—'}

                        </TableCell>


                        <TableCell>

                          {materia.id_asignacion === null ? (

                            <span className="rounded-md bg-amber-100 px-2 py-1 text-xs font-medium text-amber-800">
                              Sin asignar
                            </span>

                          ) : (

                            <span className="rounded-md bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-800">
                              Asignada
                            </span>

                          )}

                        </TableCell>


                        <TableCell>

                          <div className="flex justify-center gap-2">

                            {materia.id_asignacion === null ? (

                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() =>
                                  setMateriaFormulario(materia)
                                }
                              >

                                <PlusIcon />
                                Asignar

                              </Button>

                            ) : (

                              <>

                                <BotonAccion
                                  etiqueta="Modificar asignación"
                                  tono="ambar"
                                  onClick={() =>
                                    setMateriaFormulario(materia)
                                  }
                                >
                                  <PencilIcon />
                                </BotonAccion>


                                <BotonAccion
                                  etiqueta="Eliminar asignación"
                                  tono="rojo"
                                  onClick={() =>
                                    setMateriaEliminar(materia)
                                  }
                                >
                                  <TrashIcon />
                                </BotonAccion>

                              </>

                            )}

                          </div>

                        </TableCell>

                      </TableRow>

                    ))

                  )}

                </TableBody>

              </Table>

            </div>


            {/* VISTA PARA CELULARES */}

            <div className="divide-y md:hidden">

              {consultaMaterias.isLoading ? (

                <p className="p-4 text-sm text-muted-foreground">
                  Cargando materias...
                </p>

              ) : consultaMaterias.isError ? (

                <p className="p-4 text-sm text-rose-600">
                  {mensajeError(consultaMaterias.error)}
                </p>

              ) : materias.length === 0 ? (

                <p className="p-4 text-sm text-muted-foreground">
                  Este curso no tiene materias registradas.
                </p>

              ) : (

                materias.map((materia) => (

                  <div
                    key={materia.id_materia}
                    className="space-y-3 p-4"
                  >

                    <div>

                      <p className="font-medium">
                        {materia.nombre_materia}
                      </p>

                      <p className="mt-1 text-sm text-muted-foreground">

                        Profesor: {
                          materia.nombre_profesor ?? 'Sin asignar'
                        }

                      </p>

                      <p className="text-sm text-muted-foreground">

                        Aula: {materia.numero_aula ?? '—'}

                      </p>

                    </div>


                    {materia.id_asignacion === null ? (

                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          setMateriaFormulario(materia)
                        }
                      >

                        <PlusIcon />
                        Asignar profesor

                      </Button>

                    ) : (

                      <div className="flex gap-2">

                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() =>
                            setMateriaFormulario(materia)
                          }
                        >
                          <PencilIcon />
                          Modificar
                        </Button>


                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() =>
                            setMateriaEliminar(materia)
                          }
                        >
                          <TrashIcon />
                          Eliminar
                        </Button>

                      </div>

                    )}

                  </div>

                ))

              )}

            </div>

          </>

        )}

      </section>


      {/* ====================================================
          FORMULARIO DE ASIGNACIÓN
      ==================================================== */}

      {materiaFormulario && idCurso !== null && (

        <DialogoAsignacion
          key={`${idCurso}-${materiaFormulario.id_materia}`}
          idCurso={idCurso}
          materia={materiaFormulario}
          profesores={opciones.data?.profesores ?? []}
          aulas={opciones.data?.aulas ?? []}
          onCerrar={() => setMateriaFormulario(null)}
        />

      )}


      {/* ====================================================
          CONFIRMACIÓN PARA ELIMINAR
      ==================================================== */}

      <Confirmar
        abierto={!!materiaEliminar}
        onCambiar={(abierto) =>
          !abierto && setMateriaEliminar(null)
        }
        titulo="Eliminar asignación"
        descripcion={
          `¿Desea eliminar la asignación de "${materiaEliminar?.nombre_materia ?? ''}"? No se permitirá si tiene asistencias o calificaciones registradas.`
        }
        textoConfirmar="Eliminar"
        peligro
        icono={<TrashIcon />}
        ocupado={eliminar.isPending}
        onConfirmar={confirmarEliminar}
      />

    </div>

  )
}


// ============================================================
// FORMULARIO PARA ASIGNAR O MODIFICAR PROFESOR
// ============================================================

function DialogoAsignacion({
  idCurso,
  materia,
  profesores,
  aulas,
  onCerrar,
}: {
  idCurso: number
  materia: MateriaCursoAsignacion
  profesores: ProfesorOpcionAsignacion[]
  aulas: AulaOpcionAsignacion[]
  onCerrar: () => void
}) {

  const esEdicion = materia.id_asignacion !== null

  const registrar = useRegistrarAsignacion()
  const actualizar = useActualizarAsignacion()


  // ----------------------------------------------------------
  // FORMULARIO
  // ----------------------------------------------------------

  const form = useForm<DatosFormulario>({

    resolver: zodResolver(esquemaFormulario),

    defaultValues: {
      ci_profesor: materia.ci_profesor ?? '',
      id_aula: materia.id_aula ?? 0,
    },

  })


  // ----------------------------------------------------------
  // GUARDAR
  // ----------------------------------------------------------

  const guardar = form.handleSubmit(async (datos) => {

    try {

      if (materia.id_asignacion !== null) {

        await actualizar.mutateAsync({

          id_asignacion: materia.id_asignacion,

          datos: {
            ci_profesor: datos.ci_profesor,
            id_aula: datos.id_aula,
          },

        })

        toast.success(
          'Asignación modificada correctamente.'
        )

      } else {

        await registrar.mutateAsync({

          id_curso: idCurso,

          id_materia: materia.id_materia,

          ci_profesor: datos.ci_profesor,

          id_aula: datos.id_aula,

        })

        toast.success(
          'Profesor asignado correctamente.'
        )

      }

      onCerrar()

    } catch (error) {

      toast.error(mensajeError(error))

    }

  })


  const ocupado =
    registrar.isPending || actualizar.isPending


  // ==========================================================
  // INTERFAZ DEL FORMULARIO
  // ==========================================================

  return (

    <Dialog
      open
      onOpenChange={(abierto) => {
        if (!abierto && !ocupado) {
          onCerrar()
        }
      }}
    >

      <DialogContent className="sm:max-w-md">

        <DialogHeader>

          <DialogTitle>

            {esEdicion
              ? 'Modificar asignación'
              : 'Asignar profesor'}

          </DialogTitle>


          <DialogDescription>

            Materia: {materia.nombre_materia}

          </DialogDescription>

        </DialogHeader>


        <form
          id="formulario-asignacion"
          onSubmit={guardar}
          className="space-y-4"
        >

          {/* PROFESOR */}

          <Campo
            etiqueta="Profesor"
            error={
              form.formState.errors.ci_profesor?.message
            }
          >

            <Controller
              name="ci_profesor"
              control={form.control}
              render={({ field }) => (

                <Select
                  value={field.value}
                  onValueChange={field.onChange}
                >

                  <SelectTrigger className="w-full">

                    <SelectValue
                      placeholder="Seleccione un profesor"
                    />

                  </SelectTrigger>


                  <SelectContent>

                    {profesores.map((profesor) => (

                      <SelectItem
                        key={profesor.ci_profesor}
                        value={profesor.ci_profesor}
                      >

                        {profesor.nombre_profesor}

                      </SelectItem>

                    ))}

                  </SelectContent>

                </Select>

              )}
            />

          </Campo>


          {/* AULA */}

          <Campo
            etiqueta="Aula"
            error={
              form.formState.errors.id_aula?.message
            }
          >

            <Controller
              name="id_aula"
              control={form.control}
              render={({ field }) => (

                <Select
                  value={
                    field.value
                      ? String(field.value)
                      : ''
                  }
                  onValueChange={(valor) =>
                    field.onChange(Number(valor))
                  }
                >

                  <SelectTrigger className="w-full">

                    <SelectValue
                      placeholder="Seleccione un aula"
                    />

                  </SelectTrigger>


                  <SelectContent>

                    {aulas.map((aula) => (

                      <SelectItem
                        key={aula.id_aula}
                        value={String(aula.id_aula)}
                      >

                        {aula.numero}

                        {aula.capacidad !== null
                          ? ` - Capacidad: ${aula.capacidad}`
                          : ''}

                      </SelectItem>

                    ))}

                  </SelectContent>

                </Select>

              )}
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
            form="formulario-asignacion"
            disabled={ocupado}
          >

            {esEdicion
              ? 'Guardar cambios'
              : 'Registrar asignación'}

          </Button>

        </DialogFooter>

      </DialogContent>

    </Dialog>

  )
}

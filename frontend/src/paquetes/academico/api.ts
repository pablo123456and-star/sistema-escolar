/**
 * Llamadas al backend del paquete academico (/api/v1/academico/...) y hooks de TanStack Query.
 * Compartido por todos sus casos de uso.
 *
 * PENDIENTE.
 */
// ============================================================
// CU13 - GESTIONAR MATERIAS Y PLAN DE ESTUDIOS
// ============================================================

import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'

import { api, type Pagina } from '@/nucleo/api'

import type {
  //CU13 - Gestionar materias y plan de estudios
  Materia,
  DatosMateria,
  MateriaActualizacion,
  OpcionesPlan,
  PlanEstudios,
  DatosMateriaPlan,
  //CU14 - Asignar materias a cursos
  Asignacion,
  DatosAsignacionCrear,
  DatosAsignacionActualizar,
  OpcionesAsignacion,
  MateriasCursoAsignacion,
  //CU16 - Inscribir estudiante
  Boleta,
  DatosInscripcion,
  EstudianteInscripcion,
} from './schemas'


// ------------------------------------------------------------
// CONFIGURACIÓN
// ------------------------------------------------------------

const RUTA_ACADEMICO = '/academico'

function useInvalidarAcademico() {
  const cliente = useQueryClient()

  return () =>
    cliente.invalidateQueries({
      queryKey: ['academico'],
    })
}


// ------------------------------------------------------------
// 1. LISTAR Y BUSCAR MATERIAS
// ------------------------------------------------------------

export type FiltrosMaterias = {
  q?: string
  pagina: number
  tamano: number
}

export function useMaterias(filtros: FiltrosMaterias) {
  return useQuery({
    queryKey: ['academico', 'materias', filtros],

    queryFn: () =>
      api<Pagina<Materia>>(
        `${RUTA_ACADEMICO}/materias`,
        { params: filtros }
      ),

    placeholderData: keepPreviousData,
  })
}


// ------------------------------------------------------------
// 2. CONSULTAR UNA MATERIA
// ------------------------------------------------------------

export function useMateria(id_materia: number | null) {
  return useQuery({
    queryKey: ['academico', 'materia', id_materia],

    queryFn: () =>
      api<Materia>(
        `${RUTA_ACADEMICO}/materias/${id_materia}`
      ),

    enabled: id_materia !== null,
  })
}


// ------------------------------------------------------------
// 3. REGISTRAR MATERIA
// ------------------------------------------------------------

export function useRegistrarMateria() {
  const invalidar = useInvalidarAcademico()

  return useMutation({
    mutationFn: (datos: DatosMateria) =>
      api<Materia>(
        `${RUTA_ACADEMICO}/materias`,
        {
          metodo: 'POST',
          cuerpo: datos,
        }
      ),

    onSuccess: invalidar,
  })
}


// ------------------------------------------------------------
// 4. MODIFICAR MATERIA
// ------------------------------------------------------------

export function useActualizarMateria() {
  const invalidar = useInvalidarAcademico()

  return useMutation({
    mutationFn: ({
      id_materia,
      datos,
    }: {
      id_materia: number
      datos: MateriaActualizacion
    }) =>
      api<Materia>(
        `${RUTA_ACADEMICO}/materias/${id_materia}`,
        {
          metodo: 'PATCH',
          cuerpo: datos,
        }
      ),

    onSuccess: invalidar,
  })
}


// ------------------------------------------------------------
// 5. ELIMINAR MATERIA
// ------------------------------------------------------------

export function useEliminarMateria() {
  const invalidar = useInvalidarAcademico()

  return useMutation({
    mutationFn: (id_materia: number) =>
      api<void>(
        `${RUTA_ACADEMICO}/materias/${id_materia}`,
        {
          metodo: 'DELETE',
        }
      ),

    onSuccess: invalidar,
  })
}


// ------------------------------------------------------------
// 6. CONSULTAR NIVELES Y GRADOS
// ------------------------------------------------------------

export function useOpcionesPlan() {
  return useQuery({
    queryKey: ['academico', 'niveles-grados'],

    queryFn: () =>
      api<OpcionesPlan>(
        `${RUTA_ACADEMICO}/niveles-grados`
      ),
  })
}


// ------------------------------------------------------------
// 7. CONSULTAR PLAN DE ESTUDIOS
// ------------------------------------------------------------

export function usePlanEstudios(id_grado: number | null) {
  return useQuery({
    queryKey: ['academico', 'plan-estudios', id_grado],

    queryFn: () =>
      api<PlanEstudios>(
        `${RUTA_ACADEMICO}/grados/${id_grado}/materias`
      ),

    enabled: id_grado !== null,
  })
}


// ------------------------------------------------------------
// 8. AGREGAR MATERIA AL PLAN
// ------------------------------------------------------------

export function useAgregarMateriaPlan() {
  const invalidar = useInvalidarAcademico()

  return useMutation({
    mutationFn: ({
      id_grado,
      datos,
    }: {
      id_grado: number
      datos: DatosMateriaPlan
    }) =>
      api<PlanEstudios>(
        `${RUTA_ACADEMICO}/grados/${id_grado}/materias`,
        {
          metodo: 'POST',
          cuerpo: datos,
        }
      ),

    onSuccess: invalidar,
  })
}


// ------------------------------------------------------------
// 9. QUITAR MATERIA DEL PLAN
// ------------------------------------------------------------

export function useQuitarMateriaPlan() {
  const invalidar = useInvalidarAcademico()

  return useMutation({
    mutationFn: ({
      id_grado,
      id_materia,
    }: {
      id_grado: number
      id_materia: number
    }) =>
      api<PlanEstudios>(
        `${RUTA_ACADEMICO}/grados/${id_grado}/materias/${id_materia}`,
        {
          metodo: 'DELETE',
        }
      ),

    onSuccess: invalidar,
  })
}

// ============================================================
// CU14 - ASIGNAR PROFESOR A MATERIA/CURSO
// ============================================================


// ------------------------------------------------------------
// 1. CONSULTAR CURSOS, PROFESORES Y AULAS
// ------------------------------------------------------------

export function useOpcionesAsignacion() {
  return useQuery({
    queryKey: ['academico', 'cu14', 'opciones'],

    queryFn: () =>
      api<OpcionesAsignacion>(
        `${RUTA_ACADEMICO}/asignaciones/opciones`
      ),
  })
}


// ------------------------------------------------------------
// 2. CONSULTAR MATERIAS Y ASIGNACIONES DE UN CURSO
// ------------------------------------------------------------

export function useMateriasCursoAsignacion(
  id_curso: number | null
) {
  return useQuery({
    queryKey: [
      'academico',
      'cu14',
      'materias-curso',
      id_curso,
    ],

    queryFn: () =>
      api<MateriasCursoAsignacion>(
        `${RUTA_ACADEMICO}/cursos/${id_curso}/asignaciones`
      ),

    enabled: id_curso !== null,
  })
}


// ------------------------------------------------------------
// 3. CONSULTAR UNA ASIGNACION
// ------------------------------------------------------------

export function useAsignacion(
  id_asignacion: number | null
) {
  return useQuery({
    queryKey: [
      'academico',
      'cu14',
      'asignacion',
      id_asignacion,
    ],

    queryFn: () =>
      api<Asignacion>(
        `${RUTA_ACADEMICO}/asignaciones/${id_asignacion}`
      ),

    enabled: id_asignacion !== null,
  })
}


// ------------------------------------------------------------
// 4. REGISTRAR ASIGNACION
// ------------------------------------------------------------

export function useRegistrarAsignacion() {
  const invalidar = useInvalidarAcademico()

  return useMutation({
    mutationFn: (datos: DatosAsignacionCrear) =>
      api<Asignacion>(
        `${RUTA_ACADEMICO}/asignaciones`,
        {
          metodo: 'POST',
          cuerpo: datos,
        }
      ),

    onSuccess: invalidar,
  })
}


// ------------------------------------------------------------
// 5. MODIFICAR ASIGNACION
// ------------------------------------------------------------

export function useActualizarAsignacion() {
  const invalidar = useInvalidarAcademico()

  return useMutation({
    mutationFn: ({
      id_asignacion,
      datos,
    }: {
      id_asignacion: number
      datos: DatosAsignacionActualizar
    }) =>
      api<Asignacion>(
        `${RUTA_ACADEMICO}/asignaciones/${id_asignacion}`,
        {
          metodo: 'PATCH',
          cuerpo: datos,
        }
      ),

    onSuccess: invalidar,
  })
}


// ------------------------------------------------------------
// 6. ELIMINAR ASIGNACION
// ------------------------------------------------------------

export function useEliminarAsignacion() {
  const invalidar = useInvalidarAcademico()

  return useMutation({
    mutationFn: (id_asignacion: number) =>
      api<void>(
        `${RUTA_ACADEMICO}/asignaciones/${id_asignacion}`,
        {
          metodo: 'DELETE',
        }
      ),

    onSuccess: invalidar,
  })
}


// ============================================================
// CU16 - INSCRIBIR ESTUDIANTE EN GESTIÓN ACADÉMICA
// ============================================================

export type FiltrosEstudiantesInscripcion = { q?: string; pagina: number; tamano: number }

export function useEstudiantesInscripcion(f: FiltrosEstudiantesInscripcion) {
  return useQuery({
    queryKey: ['academico', 'inscripciones-estudiantes', f],
    queryFn: () => api<Pagina<EstudianteInscripcion>>(`${RUTA_ACADEMICO}/inscripciones/estudiantes`, { params: f }),
    placeholderData: keepPreviousData,
  })
}

export function useBoleta(id_inscripcion: number | null) {
  return useQuery({
    queryKey: ['academico', 'boleta', id_inscripcion],
    queryFn: () => api<Boleta>(`${RUTA_ACADEMICO}/inscripciones/${id_inscripcion}/boleta`),
    enabled: id_inscripcion !== null,
  })
}

export function useInscribir() {
  const cliente = useQueryClient()
  return useMutation({
    mutationFn: (datos: DatosInscripcion) => api<Boleta>(`${RUTA_ACADEMICO}/inscripciones`, { metodo: 'POST', cuerpo: datos }),
    // También cambia el cupo de los cursos y la inscripción que muestra el CU06 (paquete personas)
    onSuccess: () => cliente.invalidateQueries({ predicate: (q) => ['academico', 'personas'].includes(String(q.queryKey[0])) }),
  })
}

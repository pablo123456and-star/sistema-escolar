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
  //CU12 - Gestionar niveles educativos y cursos
  DatosCurso,
  DatosGrado,
  DatosNivel,
  Estructura,
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

// ============================================================
// CU12 - GESTIONAR NIVELES EDUCATIVOS Y CURSOS
// ============================================================

export function useEstructura() {
  return useQuery({
    queryKey: ['academico', 'estructura'],
    queryFn: () => api<Estructura>(`${RUTA_ACADEMICO}/estructura`),
  })
}

/** Cambiar niveles, grados o paralelos afecta los selectores de otros paquetes (CU06, CU19, CU20...). */
function useMutacionEstructura<T>(mutationFn: (datos: T) => Promise<unknown>) {
  const cliente = useQueryClient()
  return useMutation({ mutationFn, onSuccess: () => cliente.invalidateQueries() })
}

export const useGuardarNivel = () =>
  useMutacionEstructura(({ id, datos }: { id?: number; datos: DatosNivel }) =>
    api(id ? `${RUTA_ACADEMICO}/niveles/${id}` : `${RUTA_ACADEMICO}/niveles`, { metodo: id ? 'PATCH' : 'POST', cuerpo: datos }),
  )

export const useGuardarGrado = () =>
  useMutacionEstructura(({ id, id_nivel, datos }: { id?: number; id_nivel: number; datos: DatosGrado }) =>
    api(id ? `${RUTA_ACADEMICO}/grados/${id}` : `${RUTA_ACADEMICO}/grados`, {
      metodo: id ? 'PATCH' : 'POST',
      cuerpo: id ? datos : { ...datos, id_nivel },
    }),
  )

export const useGuardarCurso = () =>
  useMutacionEstructura(({ id, id_grado, datos }: { id?: number; id_grado: number; datos: DatosCurso }) =>
    api(id ? `${RUTA_ACADEMICO}/cursos/${id}` : `${RUTA_ACADEMICO}/cursos`, {
      metodo: id ? 'PATCH' : 'POST',
      cuerpo: id ? datos : { ...datos, id_grado },
    }),
  )

export type ElementoEstructura = 'niveles' | 'grados' | 'cursos'

export const useEliminarEstructura = () =>
  useMutacionEstructura(({ tipo, id }: { tipo: ElementoEstructura; id: number }) =>
    api<void>(`${RUTA_ACADEMICO}/${tipo}/${id}`, { metodo: 'DELETE' }),
  )


// ============================================================
// CU15 - GESTIONAR GESTIÓN ACADÉMICA (AÑO LECTIVO)
// ============================================================

import type {
  CierreGestion,
  DatosDimension,
  DatosGestion,
  DatosPeriodo,
  Dimensiones,
  Gestion,
  Periodo,
  ResumenGestion,
} from './schemas'

export const useGestiones = () =>
  useQuery({ queryKey: ['academico', 'gestiones'], queryFn: () => api<Gestion[]>(`${RUTA_ACADEMICO}/gestiones`) })

export const useResumenGestion = (id: number | null) =>
  useQuery({
    queryKey: ['academico', 'gestiones', id, 'resumen'],
    queryFn: () => api<ResumenGestion>(`${RUTA_ACADEMICO}/gestiones/${id}/resumen`),
    enabled: id !== null,
  })

export const usePeriodos = (id: number | null) =>
  useQuery({
    queryKey: ['academico', 'gestiones', id, 'periodos'],
    queryFn: () => api<Periodo[]>(`${RUTA_ACADEMICO}/gestiones/${id}/periodos`),
    enabled: id !== null,
  })

export const useDimensiones = (id: number | null) =>
  useQuery({
    queryKey: ['academico', 'gestiones', id, 'dimensiones'],
    queryFn: () => api<Dimensiones>(`${RUTA_ACADEMICO}/gestiones/${id}/dimensiones`),
    enabled: id !== null,
  })

/** Cambiar la gestión afecta inscripciones, horarios y evaluación: se refresca todo. */
function useMutacionGestion<T, R = unknown>(mutationFn: (datos: T) => Promise<R>) {
  const cliente = useQueryClient()
  return useMutation({ mutationFn, onSuccess: () => cliente.invalidateQueries() })
}

export const useGuardarGestion = () =>
  useMutacionGestion(({ id, datos }: { id?: number; datos: DatosGestion }) =>
    api<Gestion>(id ? `${RUTA_ACADEMICO}/gestiones/${id}` : `${RUTA_ACADEMICO}/gestiones`, {
      metodo: id ? 'PATCH' : 'POST',
      cuerpo: datos,
    }),
  )

export const useGuardarPeriodo = () =>
  useMutacionGestion(({ id, id_gestion, datos }: { id?: number; id_gestion: number; datos: DatosPeriodo }) =>
    api<Periodo>(id ? `${RUTA_ACADEMICO}/periodos/${id}` : `${RUTA_ACADEMICO}/gestiones/${id_gestion}/periodos`, {
      metodo: id ? 'PATCH' : 'POST',
      cuerpo: datos,
    }),
  )

export const useEliminarPeriodo = () =>
  useMutacionGestion((id: number) => api<void>(`${RUTA_ACADEMICO}/periodos/${id}`, { metodo: 'DELETE' }))

export const useGuardarDimensiones = () =>
  useMutacionGestion(({ id_gestion, dimensiones }: { id_gestion: number; dimensiones: DatosDimension[] }) =>
    api<Dimensiones>(`${RUTA_ACADEMICO}/gestiones/${id_gestion}/dimensiones`, {
      metodo: 'PUT',
      cuerpo: { dimensiones },
    }),
  )

export const useCerrarGestion = () =>
  useMutacionGestion((id: number) => api<CierreGestion>(`${RUTA_ACADEMICO}/gestiones/${id}/cerrar`, { metodo: 'POST' }))

/** Junta las rutas de los 6 paquetes. */
import type { RouteObject } from 'react-router'
import { rutasSeguridad } from '@/paquetes/seguridad/rutas'
import { rutasPersonas } from '@/paquetes/personas/rutas'
import { rutasAcademico } from '@/paquetes/academico/rutas'
import { rutasHorarios } from '@/paquetes/horarios/rutas'
import { rutasEvaluacion } from '@/paquetes/evaluacion/rutas'
import { rutasAdministracion } from '@/paquetes/administracion/rutas'

export const rutasPaquetes: RouteObject[] = [
  ...rutasSeguridad,
  ...rutasPersonas,
  ...rutasAcademico,
  ...rutasHorarios,
  ...rutasEvaluacion,
  ...rutasAdministracion,
]

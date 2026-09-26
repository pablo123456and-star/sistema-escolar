/**
 * CU23 - Registrar calificaciones y evaluaciones (incluye autoevaluación y cierre de periodo)
 * Paquete: evaluacion
 *
 * Actores ........: Docente (Estudiante para su autoevaluación, Administrador para cerrar periodo)
 * Rol del sistema : profesor, estudiante, administrador
 * Backend ........: backend/app/paquetes/evaluacion/casos_uso/cu23_registrar_calificaciones.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  El docente dicta la materia al estudiante. El periodo está abierto. Cada puntaje no supera el máximo de su dimensión.
 * Postcondición: Las notas quedan guardadas por dimensión y la nota final se calcula sola. Al cerrar el periodo se emiten los boletines.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU23RegistrarCalificaciones() {
  return <CasoUsoPendiente codigo="CU23" nombre="Registrar calificaciones y evaluaciones (incluye autoevaluación y cierre de periodo)" paquete="evaluacion" />
}

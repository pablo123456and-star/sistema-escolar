/**
 * CU13 - Gestionar materias y asignarlas a cursos
 * Paquete: academico
 *
 * Actores ........: Admin. académico
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/academico/casos_uso/cu13_gestionar_materias.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  Sesión iniciada como administrador. El grado existe.
 * Postcondición: La materia queda registrada y el plan de estudios del grado actualizado.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU13GestionarMaterias() {
  return <CasoUsoPendiente codigo="CU13" nombre="Gestionar materias y asignarlas a cursos" paquete="academico" />
}

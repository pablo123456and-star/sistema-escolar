/**
 * CU14 - Asignar profesor a materia/curso
 * Paquete: academico
 *
 * Actores ........: Admin. académico
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/academico/casos_uso/cu14_asignar_profesor.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  La materia está en el plan del grado del curso, el aula está disponible, el profesor está activo y la gestión existe.
 * Postcondición: La asignación (profesor + materia + curso + aula + gestión) queda creada y lista para recibir horarios.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU14AsignarProfesor() {
  return <CasoUsoPendiente codigo="CU14" nombre="Asignar profesor a materia/curso" paquete="academico" />
}

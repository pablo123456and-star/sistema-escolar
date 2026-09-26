/**
 * CU06 - Registrar y gestionar estudiante
 * Paquete: personas
 *
 * Actores ........: Administrativo
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/personas/casos_uso/cu06_gestionar_estudiante.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  Sesión iniciada como administrador. El CI no está registrado como estudiante.
 * Postcondición: La persona y el estudiante quedan registrados (opcionalmente con su tutor principal y su inscripción).
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU06GestionarEstudiante() {
  return <CasoUsoPendiente codigo="CU06" nombre="Registrar y gestionar estudiante" paquete="personas" />
}

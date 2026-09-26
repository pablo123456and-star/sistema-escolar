/**
 * CU07 - Registrar antecedentes médicos y seguimiento del estudiante
 * Paquete: personas
 *
 * Actores ........: Administrativo, Docente
 * Rol del sistema : administrador, profesor
 * Backend ........: backend/app/paquetes/personas/casos_uso/cu07_registrar_antecedentes_seguimiento.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  El estudiante existe. Un docente solo registra seguimiento de sus propios estudiantes.
 * Postcondición: La observación médica o el seguimiento queda guardado y visible para sus tutores.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU07RegistrarAntecedentesSeguimiento() {
  return <CasoUsoPendiente codigo="CU07" nombre="Registrar antecedentes médicos y seguimiento del estudiante" paquete="personas" />
}

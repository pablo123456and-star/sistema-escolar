/**
 * CU22 - Consultar historial de asistencia
 * Paquete: evaluacion
 *
 * Actores ........: Tutor, Administrativo
 * Rol del sistema : tutor, administrador, estudiante, profesor
 * Backend ........: backend/app/paquetes/evaluacion/casos_uso/cu22_consultar_historial_asistencia.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  Sesión iniciada. Un tutor solo consulta a sus estudiantes.
 * Postcondición: Se muestra el detalle de asistencia y el porcentaje por materia. No se modifica nada.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU22ConsultarHistorialAsistencia() {
  return <CasoUsoPendiente codigo="CU22" nombre="Consultar historial de asistencia" paquete="evaluacion" />
}

/**
 * CU17 - Consultar historial de inscripciones
 * Paquete: academico
 *
 * Actores ........: Tutor, Administrativo
 * Rol del sistema : tutor, administrador, estudiante
 * Backend ........: backend/app/paquetes/academico/casos_uso/cu17_consultar_historial_inscripciones.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  Sesión iniciada. Un tutor solo consulta a sus estudiantes.
 * Postcondición: Se muestran las gestiones cursadas. No se modifica nada.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU17ConsultarHistorialInscripciones() {
  return <CasoUsoPendiente codigo="CU17" nombre="Consultar historial de inscripciones" paquete="academico" />
}

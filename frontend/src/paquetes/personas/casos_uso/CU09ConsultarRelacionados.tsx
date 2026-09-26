/**
 * CU09 - Consultar estudiantes/tutores relacionados
 * Paquete: personas
 *
 * Actores ........: Tutor, Administrativo
 * Rol del sistema : tutor, administrador, estudiante, profesor
 * Backend ........: backend/app/paquetes/personas/casos_uso/cu09_consultar_relacionados.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  Sesión iniciada.
 * Postcondición: Se muestra la lista de estudiantes del tutor (o de tutores del estudiante). No se modifica nada.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU09ConsultarRelacionados() {
  return <CasoUsoPendiente codigo="CU09" nombre="Consultar estudiantes/tutores relacionados" paquete="personas" />
}

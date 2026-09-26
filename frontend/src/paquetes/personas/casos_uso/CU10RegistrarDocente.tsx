/**
 * CU10 - Registrar docente
 * Paquete: personas
 *
 * Actores ........: Administrador
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/personas/casos_uso/cu10_registrar_docente.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  Sesión iniciada como administrador.
 * Postcondición: El profesor queda registrado y puede recibir asignaciones y una cuenta de usuario.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU10RegistrarDocente() {
  return <CasoUsoPendiente codigo="CU10" nombre="Registrar docente" paquete="personas" />
}

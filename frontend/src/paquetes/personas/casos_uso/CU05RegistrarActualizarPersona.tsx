/**
 * CU05 - Registrar y actualizar datos de persona
 * Paquete: personas
 *
 * Actores ........: Administrativo
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/personas/casos_uso/cu05_registrar_actualizar_persona.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  Sesión iniciada como administrador. Para actualizar o dar de baja: la persona existe.
 * Postcondición: Los datos quedan actualizados, o la persona queda inactiva con su usuario desactivado. Queda en la bitácora.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU05RegistrarActualizarPersona() {
  return <CasoUsoPendiente codigo="CU05" nombre="Registrar y actualizar datos de persona" paquete="personas" />
}

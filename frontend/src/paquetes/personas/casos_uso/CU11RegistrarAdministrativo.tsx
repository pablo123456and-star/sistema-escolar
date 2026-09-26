/**
 * CU11 - Registrar personal administrativo
 * Paquete: personas
 *
 * Actores ........: Administrador
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/personas/casos_uso/cu11_registrar_administrativo.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  Sesión iniciada como administrador.
 * Postcondición: El administrativo queda registrado y puede cobrar pagos, mover inventario y tener cuenta de administrador.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU11RegistrarAdministrativo() {
  return <CasoUsoPendiente codigo="CU11" nombre="Registrar personal administrativo" paquete="personas" />
}

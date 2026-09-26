/**
 * CU01 - Iniciar sesión (autenticación)
 * Paquete: seguridad
 *
 * Actores ........: Todos
 * Rol del sistema : administrador, profesor, estudiante, tutor
 * Backend ........: backend/app/paquetes/seguridad/casos_uso/cu01_iniciar_sesion.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  El usuario existe, está 'activo' y su persona está 'activo'.
 * Postcondición: El usuario recibe un token válido; el sistema conoce su rol y le muestra el menú que le corresponde.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU01IniciarSesion() {
  return <CasoUsoPendiente codigo="CU01" nombre="Iniciar sesión (autenticación)" paquete="seguridad" />
}

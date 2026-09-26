/**
 * CU02 - Gestionar usuarios (CRUD)
 * Paquete: seguridad
 *
 * Actores ........: Administrador
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/seguridad/casos_uso/cu02_gestionar_usuarios.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  Sesión iniciada como administrador. La persona está registrada con la especialización del rol.
 * Postcondición: El usuario queda creado, actualizado o desactivado, y la acción queda en la bitácora.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU02GestionarUsuarios() {
  return <CasoUsoPendiente codigo="CU02" nombre="Gestionar usuarios (CRUD)" paquete="seguridad" />
}

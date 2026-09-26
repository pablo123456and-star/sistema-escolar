/**
 * CU18 - Gestionar aulas
 * Paquete: horarios
 *
 * Actores ........: Administrador
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/horarios/casos_uso/cu18_gestionar_aulas.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  Sesión iniciada como administrador.
 * Postcondición: El aula queda registrada o actualizada. Un aula en mantenimiento o inactiva no se puede asignar.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU18GestionarAulas() {
  return <CasoUsoPendiente codigo="CU18" nombre="Gestionar aulas" paquete="horarios" />
}

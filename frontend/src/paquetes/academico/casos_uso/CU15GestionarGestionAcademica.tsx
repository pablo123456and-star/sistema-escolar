/**
 * CU15 - Gestionar gestión académica (año lectivo)
 * Paquete: academico
 *
 * Actores ........: Administrador
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/academico/casos_uso/cu15_gestionar_gestion_academica.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  Sesión iniciada como administrador. Para cerrar: la gestión está abierta.
 * Postcondición: La gestión, sus periodos y dimensiones quedan configurados. Al cerrarla, cada estudiante queda promovido o reprobado.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU15GestionarGestionAcademica() {
  return <CasoUsoPendiente codigo="CU15" nombre="Gestionar gestión académica (año lectivo)" paquete="academico" />
}

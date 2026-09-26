/**
 * CU08 - Registrar tutor y asociarlo a estudiante
 * Paquete: personas
 *
 * Actores ........: Administrativo
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/personas/casos_uso/cu08_registrar_asociar_tutor.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  Sesión iniciada como administrador. El estudiante existe.
 * Postcondición: El tutor queda registrado y vinculado con su parentesco; cada estudiante tiene a lo sumo un tutor principal.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU08RegistrarAsociarTutor() {
  return <CasoUsoPendiente codigo="CU08" nombre="Registrar tutor y asociarlo a estudiante" paquete="personas" />
}

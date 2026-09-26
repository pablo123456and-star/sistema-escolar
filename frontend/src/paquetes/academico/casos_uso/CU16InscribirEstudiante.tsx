/**
 * CU16 - Inscribir estudiante en gestión académica
 * Paquete: academico
 *
 * Actores ........: Administrativo
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/academico/casos_uso/cu16_inscribir_estudiante.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  El estudiante está activo, sin cuotas vencidas previas y no inscrito en esa gestión; la gestión está abierta y el curso tiene cupo.
 * Postcondición: La inscripción queda activa (o registrado el cambio de curso o el retiro con fecha y motivo).
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU16InscribirEstudiante() {
  return <CasoUsoPendiente codigo="CU16" nombre="Inscribir estudiante en gestión académica" paquete="academico" />
}

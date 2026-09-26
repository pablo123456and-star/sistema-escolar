/**
 * CU21 - Registrar asistencia de estudiantes
 * Paquete: evaluacion
 *
 * Actores ........: Docente
 * Rol del sistema : profesor, administrador
 * Backend ........: backend/app/paquetes/evaluacion/casos_uso/cu21_registrar_asistencia.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  El docente dicta esa clase. La fecha no es futura y está dentro de la gestión.
 * Postcondición: La asistencia de la clase queda registrada o corregida y auditada.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU21RegistrarAsistencia() {
  return <CasoUsoPendiente codigo="CU21" nombre="Registrar asistencia de estudiantes" paquete="evaluacion" />
}

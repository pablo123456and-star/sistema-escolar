/**
 * CU24 - Generar y consultar boletín/libreta (incluye centralizador)
 * Paquete: evaluacion
 *
 * Actores ........: Tutor, Estudiante (genera: Administrativo)
 * Rol del sistema : tutor, estudiante, administrador
 * Backend ........: backend/app/paquetes/evaluacion/casos_uso/cu24_generar_consultar_boletin.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  El estudiante tiene calificaciones en el periodo. Tutor y estudiante solo consultan lo suyo.
 * Postcondición: El boletín queda emitido con su promedio; la libreta queda disponible para consulta.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU24GenerarConsultarBoletin() {
  return <CasoUsoPendiente codigo="CU24" nombre="Generar y consultar boletín/libreta (incluye centralizador)" paquete="evaluacion" />
}

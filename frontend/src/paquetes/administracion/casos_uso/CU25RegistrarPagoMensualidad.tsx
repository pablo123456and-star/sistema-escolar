/**
 * CU25 - Registrar pago de mensualidad (incluye aranceles, becas, cuotas y morosos)
 * Paquete: administracion
 *
 * Actores ........: Administrativo
 * Rol del sistema : administrador (tutor y estudiante consultan)
 * Backend ........: backend/app/paquetes/administracion/casos_uso/cu25_registrar_pago_mensualidad.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  La cuota está pendiente y quien cobra es un administrativo.
 * Postcondición: La cuota queda pagada con número de recibo único y fecha; queda registrado en la bitácora.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU25RegistrarPagoMensualidad() {
  return <CasoUsoPendiente codigo="CU25" nombre="Registrar pago de mensualidad (incluye aranceles, becas, cuotas y morosos)" paquete="administracion" />
}

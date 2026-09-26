/**
 * CU26 - Gestionar inventario (registrar, actualizar, consultar bienes)
 * Paquete: administracion
 *
 * Actores ........: Administrativo
 * Rol del sistema : administrador
 * Backend ........: backend/app/paquetes/administracion/casos_uso/cu26_gestionar_inventario.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  Sesión iniciada como administrador. Para una salida: hay stock suficiente.
 * Postcondición: El artículo queda registrado y su stock se actualiza con cada movimiento.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU26GestionarInventario() {
  return <CasoUsoPendiente codigo="CU26" nombre="Gestionar inventario (registrar, actualizar, consultar bienes)" paquete="administracion" />
}

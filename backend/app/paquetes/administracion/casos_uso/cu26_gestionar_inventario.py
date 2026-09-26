"""
CU26 - Gestionar inventario (registrar, actualizar, consultar bienes)
Paquete: administracion

Actores ........: Administrativo
Rol del sistema : administrador
Tablas .........: inventario, movimiento_inventario
Usa de la BD ...: Trigger fn_tg_aplicar_movimiento, trigger de auditoría

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Un artículo nuevo empieza con cantidad 0; el stock solo cambia registrando movimientos.
    - No se puede sacar más de lo que hay (lo asegura la BD).
    - Los movimientos no se editan ni se borran: se corrigen con un movimiento contrario.
    - El responsable del movimiento es el administrativo conectado.

Precondición:
    Sesión iniciada como administrador. Para una salida: hay stock suficiente.

Postcondición:
    El artículo queda registrado y su stock se actualiza con cada movimiento.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

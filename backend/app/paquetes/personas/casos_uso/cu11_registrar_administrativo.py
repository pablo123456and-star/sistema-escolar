"""
CU11 - Registrar personal administrativo
Paquete: personas

Actores ........: Administrador
Rol del sistema : administrador
Tablas .........: persona, administrativo
Usa de la BD ...: Trigger de auditoría de persona

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Registrar persona + administrativo (reutilizando la persona si ya existe).

Precondición:
    Sesión iniciada como administrador.

Postcondición:
    El administrativo queda registrado y puede cobrar pagos, mover inventario y tener cuenta de administrador.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

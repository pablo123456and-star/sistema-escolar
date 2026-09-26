"""
CU10 - Registrar docente
Paquete: personas

Actores ........: Administrador
Rol del sistema : administrador
Tablas .........: persona, profesor
Usa de la BD ...: Trigger de auditoría de persona

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Registrar persona + profesor (reutilizando la persona si ya existe); actualización parcial.
    - Años de experiencia no negativos (lo asegura la BD).

Precondición:
    Sesión iniciada como administrador.

Postcondición:
    El profesor queda registrado y puede recibir asignaciones y una cuenta de usuario.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

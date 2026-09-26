"""
CU06 - Registrar y gestionar estudiante
Paquete: personas

Actores ........: Administrativo
Rol del sistema : administrador
Tablas .........: persona, estudiante, tutor_estudiante, inscripcion
Usa de la BD ...: Trigger de auditoría de persona y estudiante

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Registrar persona + estudiante en una sola transacción; si la persona ya existe, reutilizarla.
    - Opcional en el mismo paso: vincular tutor principal (reglas del CU08) e inscribir (reglas del CU16).
    - RUDE único (lo asegura la BD).

Precondición:
    Sesión iniciada como administrador. El CI no está registrado como estudiante.

Postcondición:
    La persona y el estudiante quedan registrados (opcionalmente con su tutor principal y su inscripción).

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

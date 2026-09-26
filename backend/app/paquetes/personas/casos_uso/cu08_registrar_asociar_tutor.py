"""
CU08 - Registrar tutor y asociarlo a estudiante
Paquete: personas

Actores ........: Administrativo
Rol del sistema : administrador
Tablas .........: persona, tutor, tutor_estudiante
Usa de la BD ...: Trigger de auditoría de tutor_estudiante

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Registrar persona + tutor (reutilizando la persona si ya existe).
    - Si el vínculo se marca como principal, quitar la marca al principal anterior (la BD solo permite uno).
    - No se puede desvincular un tutor que ya tiene pagos de ese estudiante (FK): mostrar mensaje claro.

Precondición:
    Sesión iniciada como administrador. El estudiante existe.

Postcondición:
    El tutor queda registrado y vinculado con su parentesco; cada estudiante tiene a lo sumo un tutor principal.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

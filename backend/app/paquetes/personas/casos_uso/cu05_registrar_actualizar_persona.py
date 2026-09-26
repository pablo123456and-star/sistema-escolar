"""
CU05 - Registrar y actualizar datos de persona
Paquete: personas

Actores ........: Administrativo
Rol del sistema : administrador
Tablas .........: persona, usuario, inscripcion
Usa de la BD ...: Triggers de auditoría y actualizado_en

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Actualización parcial: solo cambian los campos enviados.
    - Dar de baja (baja lógica): persona 'inactivo' + su usuario 'inactivo' + sus inscripciones activas pasan a 'retirada' con fecha de hoy y motivo. Todo en una transacción.
    - Reactivar: persona 'activo' y su usuario 'inactivo' vuelve a 'activo'.

Precondición:
    Sesión iniciada como administrador. Para actualizar o dar de baja: la persona existe.

Postcondición:
    Los datos quedan actualizados, o la persona queda inactiva con su usuario desactivado. Queda en la bitácora.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

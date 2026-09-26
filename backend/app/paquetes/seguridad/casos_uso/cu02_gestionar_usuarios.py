"""
CU02 - Gestionar usuarios (CRUD)
Paquete: seguridad

Actores ........: Administrador
Rol del sistema : administrador
Tablas .........: usuario, rol, persona, administrativo, profesor, estudiante, tutor
Usa de la BD ...: Trigger de auditoría de usuario

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - El rol debe coincidir con la especialización de la persona: administrador↔administrativo, profesor↔profesor, estudiante↔estudiante, tutor↔tutor.
    - Guardar la contraseña como hash bcrypt; nunca en texto.
    - Una persona tiene como máximo un usuario y nombre_usuario es único (lo asegura la BD).
    - Preferir estado 'inactivo'/'bloqueado' antes que borrar.

Precondición:
    Sesión iniciada como administrador. La persona está registrada con la especialización del rol.

Postcondición:
    El usuario queda creado, actualizado o desactivado, y la acción queda en la bitácora.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

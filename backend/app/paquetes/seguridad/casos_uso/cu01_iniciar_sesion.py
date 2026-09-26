"""
CU01 - Iniciar sesión (autenticación)
Paquete: seguridad

Actores ........: Todos
Rol del sistema : administrador, profesor, estudiante, tutor
Tablas .........: usuario, rol, persona
Usa de la BD ...: Trigger de auditoría de usuario (registra el acceso al actualizar ultimo_acceso)

Reglas de negocio que implementa este caso de uso (backend):
    - Buscar el usuario por nombre_usuario y verificar la contraseña contra password_hash (bcrypt).
    - Rechazar si el usuario no está 'activo' o su persona está 'inactivo' (mismo mensaje que clave incorrecta).
    - Emitir un token JWT con id_usuario y rol (nucleo/seguridad.py) y actualizar ultimo_acceso.
    - Endpoints: POST /seguridad/sesion (login) y GET /seguridad/perfil (datos del usuario conectado).

Precondición:
    El usuario existe, está 'activo' y su persona está 'activo'.

Postcondición:
    El usuario recibe un token válido; el sistema conoce su rol y le muestra el menú que le corresponde.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

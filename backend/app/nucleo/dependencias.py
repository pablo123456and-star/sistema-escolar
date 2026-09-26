"""
Dependencias de FastAPI reutilizables.

PENDIENTE:
  - usuario_actual(): lee 'Authorization: Bearer <token>', valida el JWT y
    devuelve id_usuario, ci y rol (401 si falta o no es válido);
  - requiere_rol("administrador", ...): 403 si el rol no está permitido;
  - sesion_bd(): la sesión de nucleo/bd.py ya identificada con el usuario.
"""

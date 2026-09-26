"""
Endpoints del paquete seguridad: /api/v1/seguridad/...

Cada endpoint llama a su caso de uso en casos_uso/.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/seguridad", tags=["seguridad"])

# PENDIENTE: endpoints de
#   cu01_iniciar_sesion
#   cu02_gestionar_usuarios
#   cu03_gestionar_roles_permisos
#   cu04_consultar_bitacora

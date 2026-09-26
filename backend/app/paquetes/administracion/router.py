"""
Endpoints del paquete administracion: /api/v1/administracion/...

Cada endpoint llama a su caso de uso en casos_uso/.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/administracion", tags=["administracion"])

# PENDIENTE: endpoints de
#   cu25_registrar_pago_mensualidad
#   cu26_gestionar_inventario
#   cu27_gestionar_comunicados

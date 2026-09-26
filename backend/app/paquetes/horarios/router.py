"""
Endpoints del paquete horarios: /api/v1/horarios/...

Cada endpoint llama a su caso de uso en casos_uso/.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/horarios", tags=["horarios"])

# PENDIENTE: endpoints de
#   cu18_gestionar_aulas
#   cu19_generar_horario
#   cu20_consultar_horarios

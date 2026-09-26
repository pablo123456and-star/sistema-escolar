"""
Endpoints del paquete evaluacion: /api/v1/evaluacion/...

Cada endpoint llama a su caso de uso en casos_uso/.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/evaluacion", tags=["evaluacion"])

# PENDIENTE: endpoints de
#   cu21_registrar_asistencia
#   cu22_consultar_historial_asistencia
#   cu23_registrar_calificaciones
#   cu24_generar_consultar_boletin

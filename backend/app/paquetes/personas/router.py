"""
Endpoints del paquete personas: /api/v1/personas/...

Cada endpoint llama a su caso de uso en casos_uso/.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/personas", tags=["personas"])

# PENDIENTE: endpoints de
#   cu05_registrar_actualizar_persona
#   cu06_gestionar_estudiante
#   cu07_registrar_antecedentes_seguimiento
#   cu08_registrar_asociar_tutor
#   cu09_consultar_relacionados
#   cu10_registrar_docente
#   cu11_registrar_administrativo

"""
Endpoints del paquete academico: /api/v1/academico/...

Cada endpoint llama a su caso de uso en casos_uso/.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/academico", tags=["academico"])

# PENDIENTE: endpoints de
#   cu12_gestionar_niveles_cursos
#   cu13_gestionar_materias
#   cu14_asignar_profesor
#   cu15_gestionar_gestion_academica
#   cu16_inscribir_estudiante
#   cu17_consultar_historial_inscripciones

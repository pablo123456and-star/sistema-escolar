"""
Punto de entrada de la API.

Levantar en local:  uvicorn app.main:app --reload
Documentación:      http://localhost:8000/docs
"""
from fastapi import FastAPI

from app.paquetes.seguridad.router import router as router_seguridad
from app.paquetes.personas.router import router as router_personas
from app.paquetes.academico.router import router as router_academico
from app.paquetes.horarios.router import router as router_horarios
from app.paquetes.evaluacion.router import router as router_evaluacion
from app.paquetes.administracion.router import router as router_administracion

PREFIJO_API = "/api/v1"

app = FastAPI(
    title="Sistema de Información - Unidad Educativa",
    version="0.1.0",
    description="API del sistema académico y administrativo (6 paquetes, 27 casos de uso).",
)

for router in (router_seguridad, router_personas, router_academico, router_horarios, router_evaluacion, router_administracion):
    app.include_router(router, prefix=PREFIJO_API)


@app.get(f"{PREFIJO_API}/salud", tags=["salud"])
def salud() -> dict[str, str]:
    """Comprueba que la API está levantada."""
    return {"estado": "ok"}

"""
Punto de entrada de la API.

Levantar en local:  uvicorn app.main:app --reload
Documentación:      http://localhost:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.nucleo.config import obtener_config
from app.nucleo.errores import registrar_manejadores
from app.paquetes.seguridad.router import router as router_seguridad
from app.paquetes.personas.router import router as router_personas
from app.paquetes.academico.router import router as router_academico
from app.paquetes.horarios.router import router as router_horarios
from app.paquetes.evaluacion.router import router as router_evaluacion
from app.paquetes.administracion.router import router as router_administracion

PREFIJO_API = "/api/v1"


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI):
    """Al arrancar: detiene el servidor con un mensaje claro si falta configuración en el .env."""
    cfg = obtener_config()
    faltan = [nombre for nombre, valor in (("DATABASE_URL", cfg.DATABASE_URL), ("JWT_SECRETO", cfg.JWT_SECRETO)) if not valor]
    if faltan:
        raise RuntimeError(f"Faltan variables en backend/.env: {', '.join(faltan)} (ver .env.example)")
    yield


app = FastAPI(
    lifespan=ciclo_de_vida,
    title="Sistema de Información - Unidad Educativa",
    version="0.2.0",
    description="API del sistema académico y administrativo (6 paquetes, 27 casos de uso). "
                "Ciclo 1 implementado: seguridad (CU01-CU04) y personas (CU06, CU08).",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=obtener_config().origenes_cors,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
registrar_manejadores(app)

for router in (router_seguridad, router_personas, router_academico, router_horarios, router_evaluacion, router_administracion):
    app.include_router(router, prefix=PREFIJO_API)


@app.get(f"{PREFIJO_API}/salud", tags=["salud"])
def salud() -> dict[str, str]:
    """Comprueba que la API está levantada."""
    return {"estado": "ok"}

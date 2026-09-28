"""
Configuración de pytest.

Las pruebas de los casos de uso usan una base local creada con los scripts
01 a 08 de basededato/sql (datos de prueba incluidos). Se indica con la
variable TEST_DATABASE_URL, por ejemplo (PowerShell):

    $env:TEST_DATABASE_URL = "postgresql+asyncpg://postgres:TU_CONTRASENA@localhost:5432/escuela_prueba"
    pytest

Cada prueba corre dentro de una transacción que se deshace al terminar:
la base queda igual que antes. Sin TEST_DATABASE_URL esas pruebas se omiten.
"""
import os

import pytest
from httpx2 import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

os.environ.setdefault("JWT_SECRETO", "clave-solo-para-pruebas-automaticas-0123456789")

from app.nucleo import bd  # noqa: E402
from app.main import app  # noqa: E402

URL_PRUEBAS = os.environ.get("TEST_DATABASE_URL")

# Usuarios de 08_datos_prueba.sql (todos con la misma contraseña de prueba)
CONTRASENA_PRUEBA = "Escuela2026"
USUARIOS = {"administrador": "direccion", "profesor": "rflores", "estudiante": "mquispe", "tutor": "marioq"}


@pytest.fixture
async def cliente():
    """Cliente HTTP de la API conectado a la base de pruebas, dentro de una transacción que se deshace."""
    if not URL_PRUEBAS:
        pytest.skip("Defina TEST_DATABASE_URL para ejecutar las pruebas con base de datos")
    motor = create_async_engine(URL_PRUEBAS, poolclass=NullPool)
    async with motor.connect() as conexion:
        transaccion = await conexion.begin()
        fabrica_original = bd._fabrica
        bd._fabrica = async_sessionmaker(
            bind=conexion, class_=AsyncSession, expire_on_commit=False, join_transaction_mode="create_savepoint"
        )
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://prueba/api/v1") as c:
                yield c
        finally:
            bd._fabrica = fabrica_original
            await transaccion.rollback()
    await motor.dispose()


async def iniciar(cliente: AsyncClient, usuario: str, contrasena: str = CONTRASENA_PRUEBA) -> dict:
    r = await cliente.post("/seguridad/sesion", json={"identificador": usuario, "contrasena": contrasena})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture
async def admin(cliente):
    return await iniciar(cliente, USUARIOS["administrador"])


@pytest.fixture
async def profesor(cliente):
    return await iniciar(cliente, USUARIOS["profesor"])

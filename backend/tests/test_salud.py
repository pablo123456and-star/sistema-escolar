"""Prueba de humo: la API arranca y responde."""
from fastapi.testclient import TestClient

from app.main import app


def test_salud_responde_ok():
    respuesta = TestClient(app).get("/api/v1/salud")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "ok"}

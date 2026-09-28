"""
Configuración: lee las variables de entorno (.env) con pydantic-settings.

Las variables del sistema tienen prioridad sobre el archivo .env.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    DATABASE_URL: str = ""
    JWT_SECRETO: str = ""
    JWT_MINUTOS: int = 480
    # Duración de la sesión cuando el usuario marca "Recordar sesión"
    JWT_DIAS_RECORDAR: int = 7
    CORS_ORIGINS: str = "http://localhost:5173"
    ZONA_HORARIA: str = "America/La_Paz"

    @property
    def origenes_cors(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def obtener_config() -> Settings:
    return Settings()

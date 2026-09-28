"""
Conexión a PostgreSQL con SQLAlchemy (async) + asyncpg.

- Una sesión (transacción) por petición: commit si la petición termina bien,
  rollback si hubo error.
- Al empezar, la transacción informa a la BD quién hace el cambio (para la
  bitácora) y fija la zona horaria de Bolivia:
      set_config('app.id_usuario', ...), set_config('app.ip', ...),
      set_config('timezone', 'America/La_Paz')
- Compatible con el "Transaction pooler" de Supabase (PgBouncer): sin caché de
  sentencias preparadas.
"""
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.nucleo.config import obtener_config


class Base(DeclarativeBase):
    """Base de los modelos ORM de todos los paquetes."""


_motor: AsyncEngine | None = None
_fabrica: async_sessionmaker[AsyncSession] | None = None


def motor() -> AsyncEngine:
    global _motor
    if _motor is None:
        cfg = obtener_config()
        if not cfg.DATABASE_URL:
            raise RuntimeError("Falta DATABASE_URL en el archivo .env del backend")
        url = make_url(cfg.DATABASE_URL).update_query_dict({"prepared_statement_cache_size": "0"})
        _motor = create_async_engine(
            url,
            pool_pre_ping=True,
            connect_args={
                "statement_cache_size": 0,
                "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
            },
        )
    return _motor


def fabrica() -> async_sessionmaker[AsyncSession]:
    global _fabrica
    if _fabrica is None:
        _fabrica = async_sessionmaker(motor(), expire_on_commit=False)
    return _fabrica


async def identificar(sesion: AsyncSession, id_usuario: int | None, ip: str | None = None) -> None:
    """Fija el usuario (y, si se indica, la IP) que la bitácora registra en esta transacción."""
    await sesion.execute(
        text("SELECT set_config('app.id_usuario', :u, true)"),
        {"u": "" if id_usuario is None else str(id_usuario)},
    )
    if ip is not None:
        await sesion.execute(text("SELECT set_config('app.ip', :ip, true)"), {"ip": ip})


@asynccontextmanager
async def abrir_sesion(id_usuario: int | None, ip: str | None) -> AsyncIterator[AsyncSession]:
    """Abre la transacción de una petición ya identificada."""
    async with fabrica()() as sesion:
        async with sesion.begin():
            await sesion.execute(
                text("SELECT set_config('timezone', :tz, true)"), {"tz": obtener_config().ZONA_HORARIA}
            )
            await identificar(sesion, id_usuario, ip or "")
            yield sesion

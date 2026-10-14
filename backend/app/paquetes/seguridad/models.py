"""
Modelos SQLAlchemy (ORM) del paquete seguridad (compartido).

Tablas (lectura y escritura): usuario, rol, bitacora (solo inserción: la BD
impide modificarla o borrarla).
"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.nucleo.bd import Base


class Rol(Base):
    __tablename__ = "rol"

    id_rol: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_rol: Mapped[str] = mapped_column(String(50))
    descripcion_rol: Mapped[str | None] = mapped_column(String(150))


class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_usuario: Mapped[str] = mapped_column(String(50))
    password_hash: Mapped[str] = mapped_column(String(255))
    estado_usuario: Mapped[str] = mapped_column(String(20), server_default="activo")
    ultimo_acceso: Mapped[datetime | None]
    id_rol_usuario: Mapped[int] = mapped_column(ForeignKey("rol.id_rol"))
    ci_persona: Mapped[str] = mapped_column(ForeignKey("persona.ci"))
    creado_en: Mapped[datetime] = mapped_column(server_default="now()")
    actualizado_en: Mapped[datetime] = mapped_column(server_default="now()")

    # Bloqueo progresivo por intentos fallidos
    intentos_fallidos: Mapped[int] = mapped_column(Integer, server_default="0", default=0)
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    bloqueos_consecutivos: Mapped[int] = mapped_column(Integer, server_default="0", default=0)
    ultimo_intento_fallido: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class TokenRecuperacion(Base):
    __tablename__ = "token_recuperacion"

    id_recuperacion: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuario.id_usuario", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    usado: Mapped[bool] = mapped_column(server_default="false", default=False)
    usado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ip_solicitud: Mapped[str | None] = mapped_column(String(45))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default="now()")


class Bitacora(Base):
    __tablename__ = "bitacora"

    id_bitacora: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    accion: Mapped[str] = mapped_column(Text)
    operacion: Mapped[str | None] = mapped_column(String(10))
    tabla_afectada: Mapped[str | None] = mapped_column(String(50))
    registro_id: Mapped[str | None] = mapped_column(Text)
    datos_anteriores: Mapped[dict | None] = mapped_column(JSONB)
    datos_nuevos: Mapped[dict | None] = mapped_column(JSONB)
    fecha_hora: Mapped[datetime] = mapped_column(server_default="now()")
    ip: Mapped[str | None] = mapped_column(INET)
    modulo: Mapped[str | None] = mapped_column(String(50))
    id_usuario_bitacora: Mapped[int | None] = mapped_column(ForeignKey("usuario.id_usuario"))

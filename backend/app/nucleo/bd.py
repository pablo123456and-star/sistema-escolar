"""
Conexión a PostgreSQL con SQLAlchemy (async) + asyncpg.

PENDIENTE:
  - engine con la zona horaria de Bolivia en cada conexión:
        connect_args={"server_settings": {"timezone": "America/La_Paz"}}
  - una sesión (transacción) por petición que, al empezar, informa a la BD
    quién hace el cambio para la bitácora:
        SELECT set_config('app.id_usuario', :id, true), set_config('app.ip', :ip, true)
  - commit al terminar bien la petición; rollback si hubo error.
"""

"""
Traducción de errores a respuestas HTTP.

PENDIENTE:
    ReglaNegocioError (de politicas/casos de uso) -> 400 / 409
    Violación de CHECK / UNIQUE / FK de la BD      -> 409 con mensaje claro
    RAISE EXCEPTION de triggers y procedimientos    -> 400 con su mensaje
    Sin token / token inválido -> 401     Rol no permitido -> 403
Formato de respuesta: {"detalle": ..., "codigo": ...}
"""

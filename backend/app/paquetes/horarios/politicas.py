"""
Reglas de negocio comunes del paquete horarios (compartido).

    - Solo el administrador gestiona aulas y horarios.
    - Un aula en 'mantenimiento' o 'inactiva' no se asigna.
    - Los choques de horario los impide la BD (trigger): el backend muestra su mensaje.
    - Cualquier usuario con sesión puede consultar horarios.

Las reglas propias de cada caso de uso están en el encabezado de su archivo en casos_uso/.

PENDIENTE.
"""

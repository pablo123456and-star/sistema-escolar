"""
Reglas de negocio comunes del paquete personas (compartido).

    - Quién ve a una persona: administrador (todos); profesor (sus estudiantes y los tutores de ellos); tutor (sus estudiantes); estudiante (a sí mismo y a sus tutores); los nombres del personal son visibles para todos.
    - Solo el administrador registra o modifica personas.
    - Baja lógica: no se borran personas (la BD lo impide si tienen historial); se marcan 'inactivo'.
    - Si la persona ya existe (p. ej. un tutor que ahora es profesor), se reutiliza.

Las reglas propias de cada caso de uso están en el encabezado de su archivo en casos_uso/.

PENDIENTE.
"""

"""
Reglas de negocio comunes del paquete academico (compartido).

    - Solo el administrador modifica la estructura académica.
    - Una gestión 'cerrada' ya no admite inscripciones ni cambios.
    - La materia de una asignación debe estar en el plan de estudios (materia_grado) del grado del curso.
    - Un registro en uso no se elimina: la BD lo impide (FK) y el backend muestra un mensaje claro.

Las reglas propias de cada caso de uso están en el encabezado de su archivo en casos_uso/.

PENDIENTE.
"""

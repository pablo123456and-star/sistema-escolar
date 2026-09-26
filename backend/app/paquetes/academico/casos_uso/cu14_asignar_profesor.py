"""
CU14 - Asignar profesor a materia/curso
Paquete: academico

Actores ........: Admin. académico
Rol del sistema : administrador
Tablas .........: asignacion_profesor_clase, materia_grado, aula, profesor, persona
Usa de la BD ...: —

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - La materia debe estar en el plan de estudios del grado del curso.
    - El aula debe estar 'disponible'; el profesor debe estar activo.
    - Una asignación por curso + materia + gestión (lo asegura la BD).
    - Consulta: materias del plan que aún no tienen profesor.

Precondición:
    La materia está en el plan del grado del curso, el aula está disponible, el profesor está activo y la gestión existe.

Postcondición:
    La asignación (profesor + materia + curso + aula + gestión) queda creada y lista para recibir horarios.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

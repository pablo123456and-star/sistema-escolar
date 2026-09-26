"""
CU13 - Gestionar materias y asignarlas a cursos
Paquete: academico

Actores ........: Admin. académico
Rol del sistema : administrador
Tablas .........: materia, materia_grado
Usa de la BD ...: —

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Nombre de materia único (lo asegura la BD).
    - Plan de estudios: agregar o quitar una materia de un grado (materia_grado).

Precondición:
    Sesión iniciada como administrador. El grado existe.

Postcondición:
    La materia queda registrada y el plan de estudios del grado actualizado.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

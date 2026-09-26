"""
CU09 - Consultar estudiantes/tutores relacionados
Paquete: personas

Actores ........: Tutor, Administrativo
Rol del sistema : tutor, administrador, estudiante, profesor
Tablas .........: tutor_estudiante, persona
Usa de la BD ...: —

Reglas de negocio que implementa este caso de uso (backend):
    - Administrador: todos. Tutor: sus estudiantes. Estudiante: sus tutores. Profesor: tutores de sus estudiantes.
    - Solo lectura.

Precondición:
    Sesión iniciada.

Postcondición:
    Se muestra la lista de estudiantes del tutor (o de tutores del estudiante). No se modifica nada.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

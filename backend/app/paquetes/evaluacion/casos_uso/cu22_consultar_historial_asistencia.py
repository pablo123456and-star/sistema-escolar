"""
CU22 - Consultar historial de asistencia
Paquete: evaluacion

Actores ........: Tutor, Administrativo
Rol del sistema : tutor, administrador, estudiante, profesor
Tablas .........: asistencia, asignacion_profesor_clase, materia
Usa de la BD ...: —

Reglas de negocio que implementa este caso de uso (backend):
    - Administrador: todos. Profesor: sus estudiantes. Tutor: sus estudiantes. Estudiante: el suyo.
    - Porcentaje por materia = (presente + tardanza) / total de clases registradas.

Precondición:
    Sesión iniciada. Un tutor solo consulta a sus estudiantes.

Postcondición:
    Se muestra el detalle de asistencia y el porcentaje por materia. No se modifica nada.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

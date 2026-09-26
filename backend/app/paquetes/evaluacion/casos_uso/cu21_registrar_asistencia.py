"""
CU21 - Registrar asistencia de estudiantes
Paquete: evaluacion

Actores ........: Docente
Rol del sistema : profesor, administrador
Tablas .........: asistencia, asignacion_profesor_clase, inscripcion
Usa de la BD ...: Trigger de auditoría de asistencia

Reglas de negocio que implementa este caso de uso (backend):
    - Solo el profesor de esa asignación (o administrador).
    - La fecha no puede ser futura (hora de Bolivia) y debe estar dentro de la gestión.
    - Cada estudiante debe estar inscrito (no retirado) en el curso de la clase.
    - Un registro por estudiante, clase y día (lo asegura la BD): si ya existe, se corrige.
    - Registrar toda la clase en una sola operación.

Precondición:
    El docente dicta esa clase. La fecha no es futura y está dentro de la gestión.

Postcondición:
    La asistencia de la clase queda registrada o corregida y auditada.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

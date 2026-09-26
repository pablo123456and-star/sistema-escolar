"""
CU07 - Registrar antecedentes médicos y seguimiento del estudiante
Paquete: personas

Actores ........: Administrativo, Docente
Rol del sistema : administrador, profesor
Tablas .........: estudiante, seguimiento_estudiante
Usa de la BD ...: Trigger de auditoría de estudiante y seguimiento

Reglas de negocio que implementa este caso de uso (backend):
    - Observación médica: solo administrador.
    - Seguimiento: administrador o un profesor que dicta alguna materia al estudiante en la gestión actual.
    - El autor del seguimiento es el usuario conectado.
    - Tipos: conducta, academico, salud, merito, otro; 'gravedad' solo para conducta (lo asegura la BD).

Precondición:
    El estudiante existe. Un docente solo registra seguimiento de sus propios estudiantes.

Postcondición:
    La observación médica o el seguimiento queda guardado y visible para sus tutores.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

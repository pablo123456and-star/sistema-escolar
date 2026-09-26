"""
CU20 - Consultar horarios
Paquete: horarios

Actores ........: Docente, Estudiante, Tutor
Rol del sistema : profesor, estudiante, tutor, administrador
Tablas .........: horario (vía v_horario)
Usa de la BD ...: Vista v_horario

Reglas de negocio que implementa este caso de uso (backend):
    - Cualquier usuario con sesión.
    - Horario semanal por curso o por profesor, ordenado por día y hora.

Precondición:
    Sesión iniciada.

Postcondición:
    Se muestra el horario semanal del curso o del profesor. No se modifica nada.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

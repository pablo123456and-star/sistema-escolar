"""
CU19 - Generar horario de clases (aula, profesor, materia)
Paquete: horarios

Actores ........: Admin. académico
Rol del sistema : administrador
Tablas .........: horario, asignacion_profesor_clase
Usa de la BD ...: Trigger fn_tg_validar_horario

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - La asignación debe existir.
    - Día válido y hora final > hora inicial (lo asegura la BD).
    - Los choques de profesor, aula o curso los impide la BD: mostrar su mensaje al usuario.

Precondición:
    La asignación existe.

Postcondición:
    El bloque de horario queda registrado sin choques de profesor, aula ni curso en la misma gestión.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

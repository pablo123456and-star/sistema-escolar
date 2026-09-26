"""
CU15 - Gestionar gestión académica (año lectivo)
Paquete: academico

Actores ........: Administrador
Rol del sistema : administrador
Tablas .........: gestion, periodo, dimension_evaluacion, inscripcion
Usa de la BD ...: Procedimiento sp_cerrar_gestion

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - El periodo debe estar dentro de las fechas de su gestión y no solaparse con otro periodo.
    - Las dimensiones de evaluación de una gestión deben sumar 100.
    - Cerrar la gestión: CALL sp_cerrar_gestion (promovido/reprobado de cada estudiante).
    - Resumen para el panel (inscritos, retirados, promedio, cobrado, vencido).

Precondición:
    Sesión iniciada como administrador. Para cerrar: la gestión está abierta.

Postcondición:
    La gestión, sus periodos y dimensiones quedan configurados. Al cerrarla, cada estudiante queda promovido o reprobado.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

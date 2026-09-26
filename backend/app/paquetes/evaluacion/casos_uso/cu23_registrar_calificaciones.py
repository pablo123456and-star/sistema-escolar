"""
CU23 - Registrar calificaciones y evaluaciones (incluye autoevaluación y cierre de periodo)
Paquete: evaluacion

Actores ........: Docente (Estudiante para su autoevaluación, Administrador para cerrar periodo)
Rol del sistema : profesor, estudiante, administrador
Tablas .........: calificacion, calificacion_detalle, dimension_evaluacion, periodo, inscripcion
Usa de la BD ...: Vista v_nota_final, procedimiento sp_emitir_boletines, trigger de auditoría

Reglas de negocio que implementa este caso de uso (backend):
    - Profesor: solo si dicta esa materia al estudiante en la gestión del periodo (o administrador).
    - El estudiante debe estar inscrito (no retirado) en un curso que tenga esa materia.
    - Periodo 'abierto'; si está 'cerrado', solo el administrador modifica.
    - La dimensión debe ser de la gestión del periodo y el puntaje <= su puntaje_maximo.
    - La fecha de la calificación debe estar dentro de la gestión.
    - Autoevaluación: solo el propio estudiante y solo la dimensión es_autoevaluacion.
    - Cerrar periodo (administrador): estado 'cerrado' + CALL sp_emitir_boletines.

Precondición:
    El docente dicta la materia al estudiante. El periodo está abierto. Cada puntaje no supera el máximo de su dimensión.

Postcondición:
    Las notas quedan guardadas por dimensión y la nota final se calcula sola. Al cerrar el periodo se emiten los boletines.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

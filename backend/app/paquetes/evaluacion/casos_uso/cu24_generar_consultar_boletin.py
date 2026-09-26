"""
CU24 - Generar y consultar boletín/libreta (incluye centralizador)
Paquete: evaluacion

Actores ........: Tutor, Estudiante (genera: Administrativo)
Rol del sistema : tutor, estudiante, administrador
Tablas .........: boletin, libreta, calificacion
Usa de la BD ...: Procedimiento sp_emitir_boletines, vista v_nota_final

Reglas de negocio que implementa este caso de uso (backend):
    - Emitir boletines: solo administrador (CALL sp_emitir_boletines).
    - Consultar: estudiante el suyo; tutor sus estudiantes; administrador todos.
    - Centralizador: notas de todo un curso en un periodo, por materia, con promedio.
    - Libreta: guardar la ruta/URL del PDF (dónde se almacena se decide al implementar).

Precondición:
    El estudiante tiene calificaciones en el periodo. Tutor y estudiante solo consultan lo suyo.

Postcondición:
    El boletín queda emitido con su promedio; la libreta queda disponible para consulta.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

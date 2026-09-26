"""
CU17 - Consultar historial de inscripciones
Paquete: academico

Actores ........: Tutor, Administrativo
Rol del sistema : tutor, administrador, estudiante
Tablas .........: inscripcion, gestion
Usa de la BD ...: Vistas v_curso y v_nota_final

Reglas de negocio que implementa este caso de uso (backend):
    - Administrador: todos. Tutor: sus estudiantes. Estudiante: el suyo.
    - Por gestión: curso, estado, resultado final y promedio anual (promedio de v_nota_final).

Precondición:
    Sesión iniciada. Un tutor solo consulta a sus estudiantes.

Postcondición:
    Se muestran las gestiones cursadas. No se modifica nada.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

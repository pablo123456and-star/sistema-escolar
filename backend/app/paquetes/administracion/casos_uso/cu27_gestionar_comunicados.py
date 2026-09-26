"""
CU27 - Gestionar comunicados y citaciones
Paquete: administracion

Actores ........: Administrativo, Docente (publican); Tutor, Estudiante (leen)
Rol del sistema : administrador, profesor, tutor, estudiante
Tablas .........: comunicado, comunicado_lectura
Usa de la BD ...: —

Reglas de negocio que implementa este caso de uso (backend):
    - Administrador: publica a todos, a un curso o a un estudiante.
    - Profesor: solo a los cursos donde enseña o a sus estudiantes; nunca a 'todos'.
    - Citación: dirigida a un estudiante (sus tutores) y con fecha (lo asegura la BD).
    - Cada usuario ve solo los comunicados dirigidos a él; el autor es el usuario conectado.
    - Marcar como leído: una vez por persona (lo asegura la BD).

Precondición:
    Un docente solo publica a sus cursos o a sus estudiantes.

Postcondición:
    El comunicado queda visible para sus destinatarios y se registra quién lo leyó.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

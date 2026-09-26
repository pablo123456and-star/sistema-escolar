"""
CU12 - Gestionar niveles educativos y cursos
Paquete: academico

Actores ........: Admin. académico
Rol del sistema : administrador
Tablas .........: nivel_educativo, grado, curso
Usa de la BD ...: Vista v_curso (nombre legible del curso)

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Paralelo único por grado y cupo mayor a 0 (lo asegura la BD).
    - No eliminar lo que está en uso (FK): mostrar mensaje claro.

Precondición:
    Sesión iniciada como administrador.

Postcondición:
    El catálogo de niveles, grados y cursos (paralelos y cupos) queda actualizado.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

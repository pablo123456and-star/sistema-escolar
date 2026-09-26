"""
CU18 - Gestionar aulas
Paquete: horarios

Actores ........: Administrador
Rol del sistema : administrador
Tablas .........: aula
Usa de la BD ...: —

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Número de aula único y capacidad > 0 (lo asegura la BD).
    - No eliminar un aula con asignaciones (FK): sugerir estado 'inactiva'.

Precondición:
    Sesión iniciada como administrador.

Postcondición:
    El aula queda registrada o actualizada. Un aula en mantenimiento o inactiva no se puede asignar.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

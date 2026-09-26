"""
CU03 - Gestionar roles y permisos
Paquete: seguridad

Actores ........: Administrador
Rol del sistema : administrador
Tablas .........: rol, usuario
Usa de la BD ...: Trigger de auditoría de rol y usuario

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Los 4 roles son fijos (CHECK en la BD): solo se edita su descripción.
    - Asignar o cambiar el rol y el estado de un usuario (aplicando la regla de especialización del CU02).
    - La matriz de permisos por rol es la de politicas.py de cada paquete (documentarla en pantalla).

Precondición:
    Sesión iniciada como administrador.

Postcondición:
    La descripción del rol o el rol/estado del usuario queda actualizado; sus permisos cambian con su rol.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

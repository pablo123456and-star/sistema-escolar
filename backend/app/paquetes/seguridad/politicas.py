"""
Reglas de negocio comunes del paquete seguridad (compartido).

    - Solo el administrador gestiona usuarios, roles y consulta la bitácora.
    - Los 4 roles son fijos (administrador, profesor, estudiante, tutor): no se crean ni se renombran.
    - Un usuario 'inactivo' o 'bloqueado', o cuya persona está inactiva, no puede iniciar sesión.

Las reglas propias de cada caso de uso están en el encabezado de su archivo en casos_uso/.

PENDIENTE.
"""

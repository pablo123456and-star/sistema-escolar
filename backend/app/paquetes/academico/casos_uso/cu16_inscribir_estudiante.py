"""
CU16 - Inscribir estudiante en gestión académica
Paquete: academico

Actores ........: Administrativo
Rol del sistema : administrador
Tablas .........: inscripcion, curso, gestion, persona, pago_mensualidad
Usa de la BD ...: Trigger de auditoría de inscripción

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - La gestión debe estar 'abierta' y la persona 'activo'.
    - Cupo: inscripciones activas del curso en la gestión < cupo_maximo.
    - Sin cuotas vencidas ('pendiente' y vencidas) de gestiones anteriores.
    - Una inscripción por estudiante y gestión (lo asegura la BD).
    - Cambio de curso: vuelve a validar el cupo. Retiro: fecha y motivo (la BD exige la fecha).

Precondición:
    El estudiante está activo, sin cuotas vencidas previas y no inscrito en esa gestión; la gestión está abierta y el curso tiene cupo.

Postcondición:
    La inscripción queda activa (o registrado el cambio de curso o el retiro con fecha y motivo).

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

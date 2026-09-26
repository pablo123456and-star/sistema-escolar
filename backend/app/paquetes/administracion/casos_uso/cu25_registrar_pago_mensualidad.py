"""
CU25 - Registrar pago de mensualidad (incluye aranceles, becas, cuotas y morosos)
Paquete: administracion

Actores ........: Administrativo
Rol del sistema : administrador (tutor y estudiante consultan)
Tablas .........: arancel, beca, pago_mensualidad, tutor_estudiante
Usa de la BD ...: Procedimiento sp_generar_cuotas_mes, vista v_estado_pagos, trigger de auditoría

Reglas de negocio que implementa este caso de uso (backend):
    - Aranceles y becas: solo administrador (uno por nivel y gestión; beca entre 0 y 100 %: lo asegura la BD).
    - Generar cuotas del mes: CALL sp_generar_cuotas_mes.
    - Cobrar: solo una cuota 'pendiente'; el cajero es el administrativo conectado.
    - Tutor que paga: debe ser tutor de ese estudiante (lo asegura la BD); por defecto el responsable de pago.
    - Fecha de pago no futura (hora de Bolivia); número de recibo = nextval('seq_numero_recibo').
    - Anular: estado 'anulado' + motivo; un pago anulado ya no se modifica.
    - Morosos: cuotas atrasadas de v_estado_pagos con el teléfono del tutor.

Precondición:
    La cuota está pendiente y quien cobra es un administrativo.

Postcondición:
    La cuota queda pagada con número de recibo único y fecha; queda registrado en la bitácora.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

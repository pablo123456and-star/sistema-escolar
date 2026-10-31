-- =====================================================================
-- 10 - PAGO EN LINEA (OPCIONAL)  -  SISTEMA ESCUELA MODELO
-- Requiere: 01 a 07
-- =====================================================================
-- Un pago cobrado debe tener cajero (CHECK de pago_mensualidad). Los pagos
-- en linea con tarjeta (Stripe, CU25) no los cobra una persona: quedan a
-- nombre de este administrativo "Pagos en linea", que no tiene usuario
-- (nadie inicia sesion con el). El backend lo usa con PAGO_EN_LINEA_CI.
-- Se puede ejecutar mas de una vez sin duplicar nada.
-- =====================================================================

BEGIN;

INSERT INTO persona (ci, nombre_persona, apellidos)
VALUES ('PAGO-EN-LINEA', 'Pagos en linea', 'Pasarela Stripe')
ON CONFLICT (ci) DO NOTHING;

INSERT INTO administrativo (ci_administrativo, cargo)
VALUES ('PAGO-EN-LINEA', 'Pasarela de pago')
ON CONFLICT (ci_administrativo) DO NOTHING;

COMMIT;

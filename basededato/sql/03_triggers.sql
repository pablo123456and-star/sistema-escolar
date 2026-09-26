-- =====================================================================
-- 03 - TRIGGERS  -  SISTEMA ESCUELA MODELO
-- Requiere: 01_esquema.sql, 02_funciones.sql
-- =====================================================================
-- Engancha las 5 funciones de trigger de 02_funciones.sql a las tablas:
--   1. actualizado_en automático ............ 6 tablas
--   2. auditoría hacia BITACORA ............. 15 tablas (datos sensibles)
--   3. bitácora inmutable ................... bitacora
--   4. choques de horario ................... horario
--   5. stock de inventario .................. movimiento_inventario
-- =====================================================================

BEGIN;

-- 1. actualizado_en ----------------------------------------------------
CREATE TRIGGER trg_persona_actualizado      BEFORE UPDATE ON persona          FOR EACH ROW EXECUTE FUNCTION fn_tg_actualizado_en();
CREATE TRIGGER trg_usuario_actualizado      BEFORE UPDATE ON usuario          FOR EACH ROW EXECUTE FUNCTION fn_tg_actualizado_en();
CREATE TRIGGER trg_inscripcion_actualizado  BEFORE UPDATE ON inscripcion      FOR EACH ROW EXECUTE FUNCTION fn_tg_actualizado_en();
CREATE TRIGGER trg_calificacion_actualizado BEFORE UPDATE ON calificacion     FOR EACH ROW EXECUTE FUNCTION fn_tg_actualizado_en();
CREATE TRIGGER trg_pago_actualizado         BEFORE UPDATE ON pago_mensualidad FOR EACH ROW EXECUTE FUNCTION fn_tg_actualizado_en();
CREATE TRIGGER trg_inventario_actualizado   BEFORE UPDATE ON inventario       FOR EACH ROW EXECUTE FUNCTION fn_tg_actualizado_en();

-- 2. Auditoría (argumentos: columnas clave, módulo) ---------------------
CREATE TRIGGER trg_auditar_rol          AFTER INSERT OR UPDATE OR DELETE ON rol                    FOR EACH ROW EXECUTE FUNCTION fn_tg_auditar('id_rol', 'SEGURIDAD');
CREATE TRIGGER trg_auditar_usuario      AFTER INSERT OR UPDATE OR DELETE ON usuario                FOR EACH ROW EXECUTE FUNCTION fn_tg_auditar('id_usuario', 'SEGURIDAD');
CREATE TRIGGER trg_auditar_persona      AFTER INSERT OR UPDATE OR DELETE ON persona                FOR EACH ROW EXECUTE FUNCTION fn_tg_auditar('ci', 'PERSONAS');
CREATE TRIGGER trg_auditar_estudiante   AFTER INSERT OR UPDATE OR DELETE ON estudiante             FOR EACH ROW EXECUTE FUNCTION fn_tg_auditar('ci_estudiante', 'PERSONAS');
CREATE TRIGGER trg_auditar_tutor_est    AFTER INSERT OR UPDATE OR DELETE ON tutor_estudiante       FOR EACH ROW EXECUTE FUNCTION fn_tg_auditar('ci_tutor_tutorestudiante,ci_estudiante_tutorestudiante', 'PERSONAS');
CREATE TRIGGER trg_auditar_seguimiento  AFTER INSERT OR UPDATE OR DELETE ON seguimiento_estudiante FOR EACH ROW EXECUTE FUNCTION fn_tg_auditar('id_seguimiento', 'PERSONAS');
CREATE TRIGGER trg_auditar_inscripcion  AFTER INSERT OR UPDATE OR DELETE ON inscripcion            FOR EACH ROW EXECUTE FUNCTION fn_tg_auditar('id_inscripcion', 'ACADEMICO');
CREATE TRIGGER trg_auditar_asistencia   AFTER INSERT OR UPDATE OR DELETE ON asistencia             FOR EACH ROW EXECUTE FUNCTION fn_tg_auditar('id_asistencia', 'EVALUACION');
CREATE TRIGGER trg_auditar_calificacion AFTER INSERT OR UPDATE OR DELETE ON calificacion           FOR EACH ROW EXECUTE FUNCTION fn_tg_auditar('id_calificacion', 'EVALUACION');
CREATE TRIGGER trg_auditar_cal_detalle  AFTER INSERT OR UPDATE OR DELETE ON calificacion_detalle   FOR EACH ROW EXECUTE FUNCTION fn_tg_auditar('id_calificacion_detalle,id_dimension_detalle', 'EVALUACION');
CREATE TRIGGER trg_auditar_boletin      AFTER INSERT OR UPDATE OR DELETE ON boletin                FOR EACH ROW EXECUTE FUNCTION fn_tg_auditar('id_boletin', 'EVALUACION');
CREATE TRIGGER trg_auditar_arancel      AFTER INSERT OR UPDATE OR DELETE ON arancel                FOR EACH ROW EXECUTE FUNCTION fn_tg_auditar('id_arancel', 'ADMINISTRACION');
CREATE TRIGGER trg_auditar_beca         AFTER INSERT OR UPDATE OR DELETE ON beca                   FOR EACH ROW EXECUTE FUNCTION fn_tg_auditar('id_beca', 'ADMINISTRACION');
CREATE TRIGGER trg_auditar_pago         AFTER INSERT OR UPDATE OR DELETE ON pago_mensualidad       FOR EACH ROW EXECUTE FUNCTION fn_tg_auditar('id_pago', 'ADMINISTRACION');
CREATE TRIGGER trg_auditar_movimiento   AFTER INSERT OR UPDATE OR DELETE ON movimiento_inventario  FOR EACH ROW EXECUTE FUNCTION fn_tg_auditar('id_movimiento', 'ADMINISTRACION');

-- 3. Bitácora inmutable -------------------------------------------------
CREATE TRIGGER trg_bitacora_inmutable
BEFORE UPDATE OR DELETE ON bitacora
FOR EACH ROW EXECUTE FUNCTION fn_tg_bitacora_inmutable();

-- 4. Choques de horario --------------------------------------------------
CREATE TRIGGER trg_validar_horario
BEFORE INSERT OR UPDATE ON horario
FOR EACH ROW EXECUTE FUNCTION fn_tg_validar_horario();

-- 5. Stock de inventario -------------------------------------------------
CREATE TRIGGER trg_aplicar_movimiento
BEFORE INSERT ON movimiento_inventario
FOR EACH ROW EXECUTE FUNCTION fn_tg_aplicar_movimiento();

COMMIT;

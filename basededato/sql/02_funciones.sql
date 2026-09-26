-- =====================================================================
-- 02 - FUNCIONES  -  SISTEMA ESCUELA MODELO
-- Requiere: 01_esquema.sql
-- =====================================================================
-- Solo lo que DEBE vivir en la base de datos porque tiene que cumplirse
-- siempre, sin importar desde dónde se escriba (backend, SQL Editor,
-- scripts de carga):
--
--   fn_registrar_bitacora        auxiliar: escribe una fila en la bitácora
--   fn_tg_actualizado_en         trigger: fecha de última modificación
--   fn_tg_auditar                trigger: auditoría de cambios
--   fn_tg_bitacora_inmutable     trigger: la bitácora no se edita ni se borra
--   fn_tg_validar_horario        trigger: sin choques de profesor/aula/curso
--   fn_tg_aplicar_movimiento     trigger: stock de inventario
--
-- Las demás reglas de negocio (inscripciones, notas, asistencia, pagos,
-- permisos por rol...) están en el backend: backend/app/paquetes/*/politicas.py
-- y casos_uso/.
--
-- ¿Quién hizo el cambio? El backend, al abrir cada transacción, ejecuta:
--     SELECT set_config('app.id_usuario', '<id del usuario>', true),
--            set_config('app.ip',         '<ip del cliente>',  true);
-- Si no lo fija (SQL Editor, scripts), la bitácora guarda usuario NULL.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- Auxiliar: registrar una acción en la bitácora
-- (la usan fn_tg_auditar y los procedimientos de 04)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_registrar_bitacora(
    p_accion TEXT, p_modulo VARCHAR,
    p_operacion VARCHAR DEFAULT 'OTRO', p_tabla VARCHAR DEFAULT NULL, p_registro_id TEXT DEFAULT NULL,
    p_datos_anteriores JSONB DEFAULT NULL, p_datos_nuevos JSONB DEFAULT NULL
)
RETURNS VOID
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
DECLARE
    v_ip INET;
BEGIN
    BEGIN
        v_ip := nullif(current_setting('app.ip', true), '')::inet;
    EXCEPTION WHEN invalid_text_representation THEN
        v_ip := NULL;   -- una IP mal formada no debe impedir la operación
    END;

    INSERT INTO bitacora (accion, operacion, tabla_afectada, registro_id,
                          datos_anteriores, datos_nuevos, ip, modulo, id_usuario_bitacora)
    VALUES (p_accion, p_operacion, p_tabla, p_registro_id,
            p_datos_anteriores, p_datos_nuevos, v_ip, p_modulo,
            nullif(current_setting('app.id_usuario', true), '')::INTEGER);
END;
$$;

-- ---------------------------------------------------------------------
-- Trigger 1: actualizado_en automático
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_tg_actualizado_en()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
BEGIN
    NEW.actualizado_en := now();
    RETURN NEW;
END;
$$;

-- ---------------------------------------------------------------------
-- Trigger 2: auditoría genérica -> bitacora
-- Argumentos del trigger: (columnas_clave, modulo)
--   columnas_clave: una o varias separadas por coma, ej. 'id_pago'
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_tg_auditar()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
DECLARE
    v_fila     JSONB := CASE WHEN TG_OP = 'DELETE' THEN to_jsonb(OLD) ELSE to_jsonb(NEW) END;
    v_registro TEXT;
BEGIN
    SELECT string_agg(v_fila ->> trim(col), '|')
      INTO v_registro
      FROM unnest(string_to_array(TG_ARGV[0], ',')) AS col;

    PERFORM fn_registrar_bitacora(
        format('%s en %s (%s)', TG_OP, TG_TABLE_NAME, v_registro),
        TG_ARGV[1],
        TG_OP,
        TG_TABLE_NAME::VARCHAR,
        v_registro,
        CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN to_jsonb(OLD) END,
        CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW) END
    );
    RETURN NULL;  -- trigger AFTER: el valor de retorno se ignora
END;
$$;

-- ---------------------------------------------------------------------
-- Trigger 3: la bitácora no se modifica ni se borra (solo se agrega)
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_tg_bitacora_inmutable()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
BEGIN
    -- Se permite el SET NULL automático cuando se borra un usuario
    IF TG_OP = 'UPDATE'
       AND NEW.id_usuario_bitacora IS NULL
       AND (to_jsonb(NEW) - 'id_usuario_bitacora') = (to_jsonb(OLD) - 'id_usuario_bitacora') THEN
        RETURN NEW;
    END IF;
    RAISE EXCEPTION 'La bitacora no se puede modificar ni eliminar';
END;
$$;

-- ---------------------------------------------------------------------
-- Trigger 4: choques de horario (profesor, aula y curso) en la misma gestión
-- Se queda en la BD porque dos usuarios guardando a la vez podrían
-- pasar una validación hecha solo en el backend.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_tg_validar_horario()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
DECLARE
    n        asignacion_profesor_clase%ROWTYPE;
    v_choque RECORD;
BEGIN
    SELECT * INTO n FROM asignacion_profesor_clase WHERE id_asignacion = NEW.id_asignacion_horario;

    SELECT h.hora_inicio_h, h.hora_final_f,
           a.ci_profesor_asignacion, a.id_aula_asignacion, a.id_curso_asignacion
      INTO v_choque
      FROM horario h
      JOIN asignacion_profesor_clase a ON a.id_asignacion = h.id_asignacion_horario
     WHERE a.id_gestion_asignacion = n.id_gestion_asignacion
       AND h.id_horario <> coalesce(NEW.id_horario, -1)
       AND h.dia = NEW.dia
       AND h.hora_inicio_h < NEW.hora_final_f
       AND NEW.hora_inicio_h < h.hora_final_f
       AND (a.ci_profesor_asignacion = n.ci_profesor_asignacion
            OR a.id_aula_asignacion  = n.id_aula_asignacion
            OR a.id_curso_asignacion = n.id_curso_asignacion)
     ORDER BY (a.ci_profesor_asignacion = n.ci_profesor_asignacion) DESC,
              (a.id_aula_asignacion = n.id_aula_asignacion) DESC
     LIMIT 1;

    IF FOUND THEN
        RAISE EXCEPTION 'Choque de horario el % de % a %: %',
            NEW.dia, v_choque.hora_inicio_h, v_choque.hora_final_f,
            CASE
                WHEN v_choque.ci_profesor_asignacion = n.ci_profesor_asignacion
                    THEN 'el profesor ' || n.ci_profesor_asignacion || ' ya tiene clase'
                WHEN v_choque.id_aula_asignacion = n.id_aula_asignacion
                    THEN 'el aula ' || n.id_aula_asignacion || ' ya esta ocupada'
                ELSE 'el curso ' || n.id_curso_asignacion || ' ya tiene otra materia'
            END;
    END IF;

    RETURN NEW;
END;
$$;

-- ---------------------------------------------------------------------
-- Trigger 5: cada movimiento de inventario suma o resta al stock
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fn_tg_aplicar_movimiento()
RETURNS TRIGGER
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
DECLARE
    v_stock INTEGER;
BEGIN
    SELECT cantidad_inventario INTO v_stock
      FROM inventario WHERE id_inventario = NEW.id_inventario_movimiento
       FOR UPDATE;

    IF NEW.tipo_accion_inventario = 'salida' AND NEW.cantidad_movimiento > v_stock THEN
        RAISE EXCEPTION 'Stock insuficiente: hay % y se quiere sacar %', v_stock, NEW.cantidad_movimiento;
    END IF;

    UPDATE inventario
       SET cantidad_inventario = cantidad_inventario
           + CASE WHEN NEW.tipo_accion_inventario = 'entrada' THEN NEW.cantidad_movimiento
                  ELSE -NEW.cantidad_movimiento END
     WHERE id_inventario = NEW.id_inventario_movimiento;

    RETURN NEW;
END;
$$;

COMMIT;

-- =====================================================================
-- 99 - REINICIAR (BORRA TODO EL SISTEMA ESCUELA MODELO)
-- =====================================================================
-- CUIDADO: elimina todas las tablas, datos, vistas, funciones y
-- procedimientos de este proyecto. Útil mientras desarrollas para volver
-- a ejecutar 01..08 desde cero. No toca otras tablas que tengas en el
-- esquema public ni la extensión pgcrypto (esquema extensions).
-- =====================================================================

BEGIN;

DO $$
DECLARE
    v_nombre TEXT;
BEGIN
    -- Vistas
    FOREACH v_nombre IN ARRAY ARRAY['v_horario', 'v_estado_pagos', 'v_nota_final', 'v_curso'] LOOP
        EXECUTE format('DROP VIEW IF EXISTS public.%I CASCADE', v_nombre);
    END LOOP;

    -- Tablas
    FOREACH v_nombre IN ARRAY ARRAY[
        'comunicado_lectura', 'comunicado', 'seguimiento_estudiante',
        'movimiento_inventario', 'inventario',
        'pago_mensualidad', 'beca', 'arancel', 'tutor_estudiante',
        'libreta', 'boletin', 'calificacion_detalle', 'calificacion',
        'asistencia', 'inscripcion', 'dimension_evaluacion',
        'horario', 'asignacion_profesor_clase', 'aula', 'materia_grado', 'materia',
        'curso', 'periodo', 'gestion', 'grado', 'nivel_educativo',
        'bitacora', 'usuario', 'tutor', 'administrativo', 'estudiante', 'profesor',
        'persona', 'rol'
    ] LOOP
        EXECUTE format('DROP TABLE IF EXISTS public.%I CASCADE', v_nombre);
    END LOOP;

    DROP SEQUENCE IF EXISTS public.seq_numero_recibo;

    -- Funciones y procedimientos del proyecto (prefijos sp_ y fn_)
    FOR v_nombre IN
        SELECT p.oid::regprocedure::TEXT
          FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
         WHERE n.nspname = 'public'
           AND (p.proname LIKE 'sp\_%' OR p.proname LIKE 'fn\_%')
    LOOP
        EXECUTE format('DROP ROUTINE IF EXISTS %s CASCADE', v_nombre);
    END LOOP;
END;
$$;

COMMIT;

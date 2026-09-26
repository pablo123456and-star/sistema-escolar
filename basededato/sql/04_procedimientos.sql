-- =====================================================================
-- 04 - PROCEDIMIENTOS ALMACENADOS  -  SISTEMA ESCUELA MODELO
-- Requiere: 01_esquema, 02_funciones, 03_triggers (y 05_vistas para ejecutarlos)
-- =====================================================================
-- Solo operaciones MASIVAS, que procesan muchas filas en una sola
-- sentencia y conviene ejecutar dentro de la base:
--
--   sp_generar_cuotas_mes   cuotas del mes para todos los inscritos
--   sp_emitir_boletines     boletines de un periodo (todo o un curso)
--   sp_cerrar_gestion       resultado final del año y cierre
--
-- Son PROCEDURE: el backend los ejecuta con CALL y lee el resultado
-- del parámetro INOUT. Ejemplo:
--     CALL sp_generar_cuotas_mes(1, 3, NULL);   -- devuelve p_cuotas_creadas
--
-- Quién puede ejecutarlos (solo administrador) lo controla el backend.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- Genera la cuota de un mes para cada estudiante con inscripción activa,
-- según el arancel de su nivel y su beca. No duplica cuotas ya generadas
-- (UNIQUE estudiante+gestión+mes). Beca del 100 %: no se genera cuota.
-- ---------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_generar_cuotas_mes(
    p_id_gestion INTEGER, p_mes INTEGER, INOUT p_cuotas_creadas INTEGER DEFAULT NULL
)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
DECLARE
    v_anio       INTEGER;
    v_sin_tarifa TEXT;
BEGIN
    SELECT anio INTO v_anio FROM gestion WHERE id_gestion = p_id_gestion;
    IF v_anio IS NULL THEN
        RAISE EXCEPTION 'No existe GESTION con id=%', p_id_gestion;
    END IF;

    -- Todos los niveles con inscritos deben tener arancel
    SELECT string_agg(DISTINCT n.nombre_nivel, ', ') INTO v_sin_tarifa
      FROM inscripcion i
      JOIN curso c           ON c.id_curso = i.id_curso_inscripcion
      JOIN grado g           ON g.id_grado = c.id_grado_curso
      JOIN nivel_educativo n ON n.id_nivel = g.id_nivel_educativo_grado
      LEFT JOIN arancel ar   ON ar.id_gestion_arancel = p_id_gestion AND ar.id_nivel_arancel = n.id_nivel
     WHERE i.id_gestion_inscripcion = p_id_gestion
       AND i.estado_inscripcion = 'activa'
       AND ar.id_arancel IS NULL;
    IF v_sin_tarifa IS NOT NULL THEN
        RAISE EXCEPTION 'Falta registrar el arancel de: %', v_sin_tarifa;
    END IF;

    INSERT INTO pago_mensualidad (ci_estudiante_pago, id_gestion_pago, mes, monto, descuento_aplicado, fecha_vencimiento)
    SELECT i.ci_estudiante_inscripcion,
           p_id_gestion,
           p_mes,
           round(ar.monto_mensual * (1 - coalesce(b.porcentaje_descuento, 0) / 100), 2),
           round(ar.monto_mensual * coalesce(b.porcentaje_descuento, 0) / 100, 2),
           make_date(v_anio, p_mes, ar.dia_vencimiento)
      FROM inscripcion i
      JOIN curso c     ON c.id_curso = i.id_curso_inscripcion
      JOIN grado g     ON g.id_grado = c.id_grado_curso
      JOIN arancel ar  ON ar.id_gestion_arancel = p_id_gestion
                      AND ar.id_nivel_arancel   = g.id_nivel_educativo_grado
      LEFT JOIN beca b ON b.ci_estudiante_beca = i.ci_estudiante_inscripcion
                      AND b.id_gestion_beca    = p_id_gestion
     WHERE i.id_gestion_inscripcion = p_id_gestion
       AND i.estado_inscripcion = 'activa'
       AND coalesce(b.porcentaje_descuento, 0) < 100
    ON CONFLICT (ci_estudiante_pago, id_gestion_pago, mes) DO NOTHING;

    GET DIAGNOSTICS p_cuotas_creadas = ROW_COUNT;
END;
$$;

-- ---------------------------------------------------------------------
-- Emite (o vuelve a emitir) los boletines de un periodo: promedio de las
-- notas finales de cada estudiante (vista v_nota_final). Si se indica
-- p_id_curso, solo los de ese curso. Una sola sentencia, sin bucles.
-- Cerrar el periodo (periodo.estado_periodo) lo hace el backend (CU23).
-- ---------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_emitir_boletines(
    p_id_periodo INTEGER, p_id_curso INTEGER DEFAULT NULL, INOUT p_boletines INTEGER DEFAULT NULL
)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM periodo WHERE id_periodo = p_id_periodo) THEN
        RAISE EXCEPTION 'No existe PERIODO con id=%', p_id_periodo;
    END IF;

    INSERT INTO boletin (ci_estudiante_boletin, id_periodo_boletin, promedio_general_b)
    SELECT nf.ci_estudiante, p_id_periodo, round(avg(nf.nota_final), 2)
      FROM v_nota_final nf
      JOIN inscripcion i ON i.ci_estudiante_inscripcion = nf.ci_estudiante
                        AND i.id_gestion_inscripcion    = nf.id_gestion
     WHERE nf.id_periodo = p_id_periodo
       AND i.estado_inscripcion <> 'retirada'
       AND (p_id_curso IS NULL OR i.id_curso_inscripcion = p_id_curso)
     GROUP BY nf.ci_estudiante
    ON CONFLICT (id_periodo_boletin, ci_estudiante_boletin) DO UPDATE SET
        promedio_general_b = EXCLUDED.promedio_general_b,
        fecha_emision_b    = CURRENT_DATE;

    GET DIAGNOSTICS p_boletines = ROW_COUNT;

    PERFORM fn_registrar_bitacora(format('Emision de %s boletines del periodo %s', p_boletines, p_id_periodo),
                                  'EVALUACION', 'OTRO', 'boletin', p_id_periodo::TEXT);
END;
$$;

-- ---------------------------------------------------------------------
-- Cierra la gestión en una sola operación:
--   1. Cada inscripción activa pasa a 'finalizada' con resultado
--      'promovido' si el promedio anual de TODAS las materias de su curso
--      es >= nota_minima_aprobacion (una materia sin notas cuenta como 0),
--      o 'reprobado' en caso contrario.
--   2. Cierra todos los periodos y la gestión.
-- Devuelve {"promovidos": n, "reprobados": m} en p_resultado.
-- ---------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE sp_cerrar_gestion(
    p_id_gestion INTEGER, INOUT p_resultado JSONB DEFAULT NULL
)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
DECLARE
    v_minima     NUMERIC;
    v_promovidos INTEGER;
    v_reprobados INTEGER;
BEGIN
    SELECT nota_minima_aprobacion INTO v_minima
      FROM gestion WHERE id_gestion = p_id_gestion AND estado_gestion = 'abierta';
    IF v_minima IS NULL THEN
        RAISE EXCEPTION 'No existe una gestion ABIERTA con id=%', p_id_gestion;
    END IF;

    WITH promedio_materia AS (          -- promedio anual por inscripción y materia
        SELECT i.id_inscripcion,
               coalesce(avg(nf.nota_final), 0) AS promedio
          FROM inscripcion i
          JOIN asignacion_profesor_clase a
            ON a.id_curso_asignacion   = i.id_curso_inscripcion
           AND a.id_gestion_asignacion = i.id_gestion_inscripcion
          LEFT JOIN v_nota_final nf
            ON nf.ci_estudiante = i.ci_estudiante_inscripcion
           AND nf.id_materia    = a.id_materia_asignacion
           AND nf.id_gestion    = i.id_gestion_inscripcion
         WHERE i.id_gestion_inscripcion = p_id_gestion
           AND i.estado_inscripcion = 'activa'
         GROUP BY i.id_inscripcion, a.id_materia_asignacion
    ),
    resultado AS (                      -- materias reprobadas por inscripción
        SELECT i.id_inscripcion,
               count(pm.id_inscripcion) FILTER (WHERE pm.promedio < v_minima) AS reprobadas
          FROM inscripcion i
          LEFT JOIN promedio_materia pm ON pm.id_inscripcion = i.id_inscripcion
         WHERE i.id_gestion_inscripcion = p_id_gestion
           AND i.estado_inscripcion = 'activa'
         GROUP BY i.id_inscripcion
    ),
    actualizadas AS (
        UPDATE inscripcion i
           SET estado_inscripcion = 'finalizada',
               resultado_final    = CASE WHEN r.reprobadas = 0 THEN 'promovido' ELSE 'reprobado' END
          FROM resultado r
         WHERE i.id_inscripcion = r.id_inscripcion
        RETURNING i.resultado_final
    )
    SELECT count(*) FILTER (WHERE resultado_final = 'promovido'),
           count(*) FILTER (WHERE resultado_final = 'reprobado')
      INTO v_promovidos, v_reprobados
      FROM actualizadas;

    UPDATE periodo SET estado_periodo = 'cerrado' WHERE id_gestion_periodo = p_id_gestion;
    UPDATE gestion SET estado_gestion = 'cerrada' WHERE id_gestion = p_id_gestion;

    PERFORM fn_registrar_bitacora(
        format('Cierre de gestion %s: %s promovidos, %s reprobados', p_id_gestion, v_promovidos, v_reprobados),
        'ACADEMICO', 'OTRO', 'gestion', p_id_gestion::TEXT);

    p_resultado := jsonb_build_object('promovidos', v_promovidos, 'reprobados', v_reprobados);
END;
$$;

COMMIT;

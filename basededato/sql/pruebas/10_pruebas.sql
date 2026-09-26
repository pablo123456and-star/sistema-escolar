-- =====================================================================
-- PRUEBAS AUTOMÁTICAS DE LA BASE DE DATOS  -  SISTEMA ESCUELA MODELO
-- Se ejecutan después de 00_roles_api + 01..08 (ver ejecutar_pruebas.ps1)
-- Cada prueba imprime "OK ..." o detiene el script con "FALLO: ...".
-- Las pruebas que modifican datos van dentro de BEGIN ... ROLLBACK.
--
-- Aquí se prueba SOLO lo que vive en la base: restricciones (datos y
-- relaciones), triggers, procedimientos, vistas y el bloqueo de acceso.
-- Las reglas de negocio se prueban en backend/tests/ con cada caso de uso.
-- =====================================================================
\set ON_ERROR_STOP on
\pset tuples_only on
\pset format unaligned
SET client_min_messages = notice;

-- ---------------------------------------------------------------------
-- Utilidades de prueba
-- ---------------------------------------------------------------------
CREATE SCHEMA pruebas;

CREATE FUNCTION pruebas.ok(p_cond BOOLEAN, p_msg TEXT)
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    IF p_cond IS NOT TRUE THEN
        RAISE EXCEPTION 'FALLO: %', p_msg;
    END IF;
    RAISE NOTICE 'OK    %', p_msg;
END;
$$;

-- Ejecuta p_sql y exige que falle con un SQLSTATE (5 caracteres) o con
-- un texto contenido en el mensaje de error.
CREATE FUNCTION pruebas.error(p_sql TEXT, p_esperado TEXT, p_msg TEXT)
RETURNS VOID LANGUAGE plpgsql AS $$
BEGIN
    BEGIN
        EXECUTE p_sql;
    EXCEPTION WHEN OTHERS THEN
        IF (p_esperado ~ '^[0-9A-Z]{5}$' AND SQLSTATE = p_esperado)
           OR position(lower(p_esperado) IN lower(SQLERRM)) > 0 THEN
            RAISE NOTICE 'OK    % -> %', p_msg, SQLERRM;
            RETURN;
        END IF;
        RAISE EXCEPTION 'FALLO: % -> error inesperado [%] %', p_msg, SQLSTATE, SQLERRM;
    END;
    RAISE EXCEPTION 'FALLO: % -> se esperaba un error y no hubo', p_msg;
END;
$$;

GRANT USAGE ON SCHEMA pruebas TO anon, authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA pruebas TO anon, authenticated;

-- Identificadores (variables de psql)
SELECT id_gestion AS g FROM gestion WHERE anio = 2026 \gset
SELECT id_periodo AS t1 FROM periodo WHERE nombre_periodo = '1er Trimestre' \gset
SELECT id_periodo AS t2 FROM periodo WHERE nombre_periodo = '2do Trimestre' \gset
SELECT id_periodo AS t3 FROM periodo WHERE nombre_periodo = '3er Trimestre' \gset
SELECT id_curso AS sec FROM v_curso WHERE nombre_nivel = 'Secundaria' AND orden_grado = 1 AND paralelo = 'A' \gset
SELECT id_curso AS pri FROM v_curso WHERE nombre_nivel = 'Primaria' AND orden_grado = 6 AND paralelo = 'A' \gset
SELECT id_materia AS mat FROM materia WHERE nombre_materia = 'Matematica' \gset
SELECT id_materia AS mus FROM materia WHERE nombre_materia = 'Educacion Musical' \gset
SELECT id_aula AS cancha FROM aula WHERE numero = 'CANCHA' \gset
SELECT id_aula AS b201 FROM aula WHERE numero = 'B-201' \gset
SELECT id_asignacion AS a_pri_com FROM asignacion_profesor_clase a JOIN materia m ON m.id_materia = a.id_materia_asignacion
 WHERE a.id_curso_asignacion = :pri AND m.nombre_materia = 'Comunicacion y Lenguajes' \gset
SELECT id_usuario AS u_admin FROM usuario WHERE nombre_usuario = 'direccion' \gset
SELECT id_usuario AS u_prof6 FROM usuario WHERE nombre_usuario = 'erojas' \gset
SELECT id_pago AS pago_pend FROM pago_mensualidad WHERE ci_estudiante_pago = '4500005' AND mes = 7 \gset

\echo '=== 1. Qué quedó en la base ==='
SELECT pruebas.ok((SELECT count(*) FROM pg_tables WHERE schemaname = 'public') = 34, '34 tablas');
SELECT pruebas.ok((SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
                    WHERE n.nspname = 'public' AND p.prokind = 'f') = 6, '6 funciones (1 auxiliar + 5 de trigger)');
SELECT pruebas.ok((SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
                    WHERE n.nspname = 'public' AND p.prokind = 'p') = 3, '3 procedimientos (PROCEDURE)');
SELECT pruebas.ok((SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = 'public' AND NOT t.tgisinternal) = 24, '24 triggers');
SELECT pruebas.ok((SELECT count(*) FROM pg_views WHERE schemaname = 'public') = 4, '4 vistas');
SELECT pruebas.ok(NOT EXISTS (SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
                               WHERE n.nspname = 'public' AND c.relkind = 'r' AND NOT c.relrowsecurity),
                  'RLS activado en todas las tablas');
SELECT pruebas.ok((SELECT count(*) FROM pg_policies WHERE schemaname = 'public') = 0, 'Sin políticas RLS (solo el backend accede)');

\echo '=== 2. Datos de prueba ==='
SELECT pruebas.ok((SELECT count(*) FROM persona) = 26, '26 personas');
SELECT pruebas.ok((SELECT count(*) FROM inscripcion WHERE estado_inscripcion = 'activa') = 12, '12 inscripciones activas');
SELECT pruebas.ok((SELECT count(*) FROM horario) = 14, '14 bloques de horario');
SELECT pruebas.ok((SELECT count(*) FROM calificacion) = 126, '126 calificaciones');
SELECT pruebas.ok((SELECT sum(puntaje_maximo) FROM dimension_evaluacion WHERE id_gestion_dimension = :g) = 100, 'Las dimensiones suman 100');
SELECT pruebas.ok((SELECT count(*) FROM boletin) = 12, '12 boletines del 1er trimestre');
SELECT pruebas.ok((SELECT count(*) FROM pago_mensualidad) = 88, '88 cuotas (11 estudiantes x 8 meses)');
SELECT pruebas.ok((SELECT count(*) FROM pago_mensualidad WHERE estado_pago = 'pagado') = 81, '81 cuotas pagadas');
SELECT pruebas.ok((SELECT count(DISTINCT numero_recibo) = 81 AND max(numero_recibo) = 81 FROM pago_mensualidad), 'Recibos correlativos 1..81');
SELECT pruebas.ok((SELECT last_value FROM seq_numero_recibo) = 81, 'La secuencia de recibos sigue en 81');
SELECT pruebas.ok(NOT EXISTS (SELECT 1 FROM pago_mensualidad WHERE ci_estudiante_pago = '4500009'), 'Beca 100 %: sin cuotas');
SELECT pruebas.ok((SELECT min(monto) = 275 AND max(monto) = 275 FROM pago_mensualidad WHERE ci_estudiante_pago = '4500003'), 'Beca 50 %: paga 275');
SELECT pruebas.ok((SELECT cantidad_inventario FROM inventario WHERE nombre_inventario = 'Balones de futbol') = 12, 'Stock por movimientos (15 - 3)');
SELECT pruebas.ok((SELECT count(*) FROM usuario) = 6, '6 usuarios de prueba');

\echo '=== 3. Contraseñas (bcrypt) ==='
SELECT pruebas.ok((SELECT bool_and(password_hash LIKE '$2a$10$%') FROM usuario), 'Todas las contraseñas están en bcrypt');
SELECT pruebas.ok((SELECT extensions.crypt('Escuela2026', password_hash) = password_hash FROM usuario WHERE nombre_usuario = 'direccion'),
                  'La contraseña correcta coincide con el hash');
SELECT pruebas.ok((SELECT extensions.crypt('otra', password_hash) <> password_hash FROM usuario WHERE nombre_usuario = 'direccion'),
                  'Una contraseña incorrecta no coincide');

\echo '=== 4. Restricciones: datos y relaciones ==='
SELECT pruebas.error($$INSERT INTO rol (nombre_rol) VALUES ('director')$$, '23514', 'Solo existen los 4 roles del sistema');
SELECT pruebas.error($$UPDATE rol SET nombre_rol = 'docente' WHERE nombre_rol = 'profesor'$$, '23514', 'No se puede renombrar un rol');
SELECT pruebas.error($$INSERT INTO usuario (nombre_usuario, id_rol_usuario, ci_persona) VALUES ('x', 1, '4500002')$$, '23502', 'Un usuario exige password_hash');
SELECT pruebas.error($$INSERT INTO usuario (nombre_usuario, password_hash, id_rol_usuario, ci_persona) VALUES ('direccion', 'h', 1, '4500002')$$, '23505', 'nombre_usuario único');
SELECT pruebas.error($$INSERT INTO persona (ci, nombre_persona, apellidos, expedido) VALUES ('9', 'a', 'b', 'XX')$$, '23514', 'expedido válido');
SELECT pruebas.error(format($$INSERT INTO inscripcion (ci_estudiante_inscripcion, id_gestion_inscripcion, id_curso_inscripcion) VALUES ('4500001', %s, %s)$$, :g, :pri), '23505', 'Una inscripción por estudiante y gestión');
SELECT pruebas.error($$UPDATE inscripcion SET estado_inscripcion = 'retirada' WHERE ci_estudiante_inscripcion = '4500001'$$, '23514', 'Retiro exige fecha de retiro');
SELECT pruebas.error($$UPDATE inscripcion SET resultado_final = 'promovido' WHERE ci_estudiante_inscripcion = '4500001'$$, '23514', 'Resultado final solo si la inscripción está finalizada');
SELECT pruebas.error(format($$INSERT INTO calificacion (ci_estudiante_calificacion, id_materia_calificacion, id_periodo_calificacion) VALUES ('4500001', %s, %s)$$, :mat, :t1), '23505', 'Una calificación por estudiante, materia y periodo');
SELECT pruebas.error($$UPDATE calificacion_detalle SET puntaje = -1 WHERE id_calificacion_detalle = (SELECT min(id_calificacion) FROM calificacion)$$, '23514', 'Puntaje no negativo');
SELECT pruebas.error($$UPDATE pago_mensualidad SET estado_pago = 'pagado' WHERE ci_estudiante_pago = '4500005' AND mes = 7$$, '23514', 'Pago cobrado exige fecha, recibo, cajero y método');
SELECT pruebas.error($$UPDATE pago_mensualidad SET fecha_pago = CURRENT_DATE WHERE ci_estudiante_pago = '4500005' AND mes = 7$$, '23514', 'Pago pendiente sin fecha de pago');
SELECT pruebas.error($$UPDATE pago_mensualidad SET mes = 13 WHERE ci_estudiante_pago = '4500005' AND mes = 7$$, '23514', 'Mes entre 1 y 12');
SELECT pruebas.error($$UPDATE pago_mensualidad SET ci_tutor_pago = '3000003' WHERE ci_estudiante_pago = '4500005' AND mes = 7$$, '23503', 'El tutor que paga debe ser tutor de ese estudiante');
SELECT pruebas.error($$UPDATE tutor_estudiante SET es_principal = true WHERE ci_tutor_tutorestudiante = '3000002' AND ci_estudiante_tutorestudiante = '4500001'$$, '23505', 'Un solo tutor principal');
SELECT pruebas.error(format($$INSERT INTO comunicado (titulo, contenido, tipo_comunicado, alcance, id_gestion_comunicado, ci_estudiante_comunicado, ci_autor) VALUES ('x', 'y', 'citacion', 'estudiante', %s, '4500001', '1000001')$$, :g), '23514', 'Citación exige fecha');
SELECT pruebas.error(format($$INSERT INTO comunicado (titulo, contenido, alcance, id_gestion_comunicado, ci_autor) VALUES ('x', 'y', 'curso', %s, '1000001')$$, :g), '23514', 'Alcance "curso" exige curso');
SELECT pruebas.error($$INSERT INTO gestion (anio, fecha_inicio_g, fecha_final_g) VALUES (2030, '2031-02-01', '2031-12-01')$$, '23514', 'El año coincide con la fecha de inicio');
SELECT pruebas.error(format($$INSERT INTO horario (id_asignacion_horario, dia, hora_inicio_h, hora_final_f) VALUES (%s, 'sabado', '10:00', '09:00')$$, :a_pri_com), '23514', 'Hora final mayor que inicial');
SELECT pruebas.error($$DELETE FROM persona WHERE ci = '4500001'$$, '23001', 'No se borra una persona con historial (RESTRICT)');
SELECT pruebas.error($$UPDATE inventario SET cantidad_inventario = -5 WHERE nombre_inventario = 'Pupitres'$$, '23514', 'Stock no negativo');
BEGIN;
UPDATE persona SET ci = '4500099' WHERE ci = '4500012';
SELECT pruebas.ok(EXISTS (SELECT 1 FROM inscripcion WHERE ci_estudiante_inscripcion = '4500099')
                  AND EXISTS (SELECT 1 FROM calificacion WHERE ci_estudiante_calificacion = '4500099'),
                  'Corregir un CI se propaga a todas las tablas (ON UPDATE CASCADE)');
ROLLBACK;

\echo '=== 5. Triggers ==='
BEGIN;
SELECT set_config('app.id_usuario', :'u_admin', true), set_config('app.ip', '181.115.1.2', true);
UPDATE persona SET telefono = '79999999' WHERE ci = '4500001';
SELECT pruebas.ok((SELECT actualizado_en > creado_en FROM persona WHERE ci = '4500001'), 'actualizado_en se actualiza solo');
SELECT pruebas.ok(EXISTS (SELECT 1 FROM bitacora
                           WHERE tabla_afectada = 'persona' AND registro_id = '4500001' AND operacion = 'UPDATE'
                             AND id_usuario_bitacora = :u_admin AND ip = '181.115.1.2'
                             AND datos_anteriores ->> 'telefono' IS DISTINCT FROM datos_nuevos ->> 'telefono'),
                  'Auditoría: guarda usuario, IP y datos antes/después (lo que envía el backend)');
UPDATE estudiante SET observacion_medica = 'Alergia a la penicilina' WHERE ci_estudiante = '4500003';
SELECT pruebas.ok(EXISTS (SELECT 1 FROM bitacora WHERE tabla_afectada = 'estudiante' AND registro_id = '4500003'),
                  'Auditoría también en estudiante (observación médica)');
ROLLBACK;
BEGIN;
UPDATE persona SET telefono = '70000000' WHERE ci = '4500002';
SELECT pruebas.ok((SELECT id_usuario_bitacora IS NULL FROM bitacora WHERE registro_id = '4500002' ORDER BY id_bitacora DESC LIMIT 1),
                  'Sin app.id_usuario (SQL Editor) la bitácora queda sin usuario');
SELECT set_config('app.ip', 'no-es-una-ip', true);
UPDATE persona SET telefono = '70000001' WHERE ci = '4500002';
SELECT pruebas.ok(true, 'Una IP mal formada no impide la operación');
ROLLBACK;
BEGIN;
SELECT set_config('app.id_usuario', '999999', true);
SELECT pruebas.error($$UPDATE persona SET telefono = '1' WHERE ci = '4500002'$$, '23503', 'app.id_usuario debe ser un usuario real');
ROLLBACK;
SELECT pruebas.error($$DELETE FROM bitacora$$, 'no se puede modificar', 'La bitácora no se borra');
SELECT pruebas.error($$UPDATE bitacora SET accion = 'x'$$, 'no se puede modificar', 'La bitácora no se edita');
BEGIN;
SELECT set_config('app.id_usuario', :'u_prof6', true);
UPDATE persona SET telefono = '71111111' WHERE ci = '2000006';
SELECT set_config('app.id_usuario', '', true);
DELETE FROM usuario WHERE id_usuario = :u_prof6;
SELECT pruebas.ok(EXISTS (SELECT 1 FROM bitacora WHERE registro_id = '2000006' AND id_usuario_bitacora IS NULL),
                  'Al borrar un usuario su historial queda (SET NULL permitido)');
ROLLBACK;

-- Horarios
SELECT pruebas.error(format($$INSERT INTO horario (id_asignacion_horario, dia, hora_inicio_h, hora_final_f) VALUES (%s, 'lunes', '10:00', '10:30')$$, :a_pri_com),
                     'el profesor', 'Choque: el profesor ya tiene clase');
BEGIN;
INSERT INTO asignacion_profesor_clase (ci_profesor_asignacion, id_materia_asignacion, id_curso_asignacion, id_aula_asignacion, id_gestion_asignacion)
VALUES ('2000006', :mus, :sec, :cancha, :g) RETURNING id_asignacion AS a_nueva \gset
SELECT pruebas.error(format($$INSERT INTO horario (id_asignacion_horario, dia, hora_inicio_h, hora_final_f) VALUES (%s, 'martes', '10:00', '10:30')$$, :a_nueva),
                     'el aula', 'Choque: el aula ya está ocupada');
SELECT pruebas.error(format($$INSERT INTO horario (id_asignacion_horario, dia, hora_inicio_h, hora_final_f) VALUES (%s, 'jueves', '08:30', '09:00')$$, :a_nueva),
                     'el curso', 'Choque: el curso ya tiene otra materia');
INSERT INTO horario (id_asignacion_horario, dia, hora_inicio_h, hora_final_f) VALUES (:a_nueva, 'miercoles', '11:30', '12:15');
SELECT pruebas.ok(true, 'Horario sin choques se registra');
ROLLBACK;
BEGIN;
INSERT INTO gestion (anio, fecha_inicio_g, fecha_final_g) VALUES (2027, '2027-02-01', '2027-12-03') RETURNING id_gestion AS g2027 \gset
INSERT INTO asignacion_profesor_clase (ci_profesor_asignacion, id_materia_asignacion, id_curso_asignacion, id_aula_asignacion, id_gestion_asignacion)
VALUES ('2000001', :mat, :sec, :b201, :g2027) RETURNING id_asignacion AS a2027 \gset
INSERT INTO horario (id_asignacion_horario, dia, hora_inicio_h, hora_final_f) VALUES (:a2027, 'lunes', '08:00', '09:30');
SELECT pruebas.ok(true, 'El mismo horario en OTRA gestión no choca');
ROLLBACK;

-- Inventario
BEGIN;
INSERT INTO movimiento_inventario (id_inventario_movimiento, tipo_accion_inventario, cantidad_movimiento, ci_administrativo_movimiento)
SELECT id_inventario, 'entrada', 5, '1000001' FROM inventario WHERE nombre_inventario = 'Balones de futbol';
SELECT pruebas.ok((SELECT cantidad_inventario FROM inventario WHERE nombre_inventario = 'Balones de futbol') = 17, 'Una entrada suma al stock');
ROLLBACK;
SELECT pruebas.error($$INSERT INTO movimiento_inventario (id_inventario_movimiento, tipo_accion_inventario, cantidad_movimiento, ci_administrativo_movimiento)
                       SELECT id_inventario, 'salida', 1000, '1000001' FROM inventario WHERE nombre_inventario = 'Balones de futbol'$$,
                     'Stock insuficiente', 'No se saca más de lo que hay');

\echo '=== 6. Procedimientos ==='
BEGIN;
CALL sp_generar_cuotas_mes(:g, 10, NULL);
SELECT pruebas.ok((SELECT count(*) FROM pago_mensualidad WHERE mes = 10) = 11, 'sp_generar_cuotas_mes crea 11 cuotas de octubre');
CALL sp_generar_cuotas_mes(:g, 10, NULL);
SELECT pruebas.ok((SELECT count(*) FROM pago_mensualidad WHERE mes = 10) = 11, 'Ejecutarlo dos veces no duplica cuotas');
ROLLBACK;
BEGIN;
DELETE FROM arancel WHERE id_nivel_arancel = (SELECT id_nivel FROM nivel_educativo WHERE nombre_nivel = 'Secundaria');
SELECT pruebas.error(format('CALL sp_generar_cuotas_mes(%s, 10, NULL)', :g), 'Falta registrar el arancel', 'Avisa si falta el arancel de un nivel');
ROLLBACK;
BEGIN;
CALL sp_emitir_boletines(:t2, :sec, NULL);
SELECT pruebas.ok((SELECT count(*) FROM boletin WHERE id_periodo_boletin = :t2) = 6, 'sp_emitir_boletines: 6 boletines del curso indicado');
SELECT pruebas.ok((SELECT b.promedio_general_b = round(avg(nf.nota_final), 2)
                     FROM boletin b JOIN v_nota_final nf ON nf.ci_estudiante = b.ci_estudiante_boletin AND nf.id_periodo = b.id_periodo_boletin
                    WHERE b.id_periodo_boletin = :t2 AND b.ci_estudiante_boletin = '4500001'
                    GROUP BY b.promedio_general_b), 'El promedio del boletín es el de sus notas finales');
ROLLBACK;
SELECT pruebas.error('CALL sp_emitir_boletines(999999, NULL, NULL)', 'No existe PERIODO', 'Periodo inexistente');
BEGIN;
CALL sp_cerrar_gestion(:g, NULL);
SELECT pruebas.ok((SELECT resultado_final FROM inscripcion WHERE ci_estudiante_inscripcion = '4500006') = 'reprobado', 'Cierre: 4500006 reprobado');
SELECT pruebas.ok((SELECT resultado_final FROM inscripcion WHERE ci_estudiante_inscripcion = '4500007') = 'promovido', 'Cierre: 4500007 promovido');
SELECT pruebas.ok((SELECT resultado_final FROM inscripcion WHERE ci_estudiante_inscripcion = '4500011') = 'reprobado', 'Cierre: 4500011 reprobado (Matemática)');
SELECT pruebas.ok(NOT EXISTS (SELECT 1 FROM inscripcion WHERE estado_inscripcion = 'activa'), 'Todas las inscripciones quedan finalizadas');
SELECT pruebas.ok((SELECT estado_gestion FROM gestion WHERE id_gestion = :g) = 'cerrada'
                  AND NOT EXISTS (SELECT 1 FROM periodo WHERE estado_periodo = 'abierto'), 'Gestión y periodos cerrados');
SELECT pruebas.ok(EXISTS (SELECT 1 FROM bitacora WHERE tabla_afectada = 'gestion' AND accion LIKE 'Cierre de gestion%'), 'El cierre queda en la bitácora');
SELECT pruebas.error(format('CALL sp_cerrar_gestion(%s, NULL)', :g), 'No existe una gestion ABIERTA', 'No se cierra dos veces');
ROLLBACK;

\echo '=== 7. Vistas ==='
SELECT pruebas.ok((SELECT count(*) FROM v_curso) = 20, 'v_curso: 20 cursos');
SELECT pruebas.ok((SELECT count(*) FROM v_horario) = 14, 'v_horario: 14 bloques');
SELECT pruebas.ok((SELECT count(*) FROM v_estado_pagos WHERE estado_actual = 'atrasado') = 7, 'v_estado_pagos: 7 cuotas atrasadas');
SELECT pruebas.ok(EXISTS (SELECT 1 FROM v_nota_final WHERE id_periodo = :t3 AND dimensiones_registradas < dimensiones_totales),
                  'v_nota_final detecta notas incompletas');

\echo '=== 8. Solo el backend accede ==='
BEGIN;
SET LOCAL ROLE anon;
SELECT pruebas.error('SELECT count(*) FROM persona', '42501', 'anon no lee tablas');
SELECT pruebas.error('SELECT * FROM v_estado_pagos', '42501', 'anon no lee vistas');
ROLLBACK;
BEGIN;
SET LOCAL ROLE authenticated;
SELECT pruebas.error('SELECT count(*) FROM usuario', '42501', 'authenticated no lee tablas');
SELECT pruebas.error($$INSERT INTO rol (nombre_rol) VALUES ('tutor')$$, '42501', 'authenticated no escribe');
SELECT pruebas.error(format('CALL sp_generar_cuotas_mes(%s, 11, NULL)', :g), '42501', 'authenticated no ejecuta procedimientos');
SELECT pruebas.error($$SELECT fn_registrar_bitacora('falsa', 'X')$$, '42501', 'authenticated no ejecuta funciones');
ROLLBACK;

\echo ''
\echo '=============================================='
\echo '  TODAS LAS PRUEBAS PASARON'
\echo '=============================================='

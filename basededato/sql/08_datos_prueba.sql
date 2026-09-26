-- =====================================================================
-- 08 - DATOS DE PRUEBA (OPCIONAL)  -  SISTEMA ESCUELA MODELO
-- Requiere: 01 a 07
-- =====================================================================
-- Escenario de demostración:
--   * 2 administrativos, 6 profesores, 6 tutores, 12 estudiantes
--   * Cursos: 1ro A Secundaria (4500001-4500006) y 6to A Primaria (4500007-4500012)
--   * 5 materias asignadas por curso con su horario semanal
--   * Notas del 1er trimestre (cerrado, con boletines) y 2do trimestre;
--     el 3er trimestre solo tiene "Saber" de Matemática en Secundaria
--   * Asistencia del 1 al 24 de septiembre de 2026
--   * Becas, cuotas de febrero a septiembre y pagos (con algunos morosos)
--   * Inventario, seguimiento y comunicados
--   * 6 usuarios para iniciar sesión (tabla al final)
--
-- Estudiantes "especiales" para probar reportes:
--   4500006 -> notas bajas (reprobaría)       4500005 -> debe jul-sep
--   4500011 -> debe ago-sep, bajo en Matemática
--   4500003 -> beca 50 %    4500009 -> beca 100 % (no genera cuotas)
--
-- Se cargan con INSERT directos: las reglas de negocio (cupo, deudas,
-- permisos...) las aplica el backend, y este escenario ya las respeta.
-- =====================================================================

BEGIN;

-- pgcrypto: solo para guardar las contraseñas de prueba en bcrypt.
-- (En Supabase ya existe en el esquema "extensions"; en local se crea ahí.)
CREATE SCHEMA IF NOT EXISTS extensions;
CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions;

DO $$
DECLARE
    v_g   INTEGER;
    v_t1  INTEGER;
    v_t2  INTEGER;
    v_t3  INTEGER;
    v_sec INTEGER;
    v_pri INTEGER;
    v_mes INTEGER;
    v_n   INTEGER;   -- recibe el resultado (INOUT) de los procedimientos
BEGIN
    SELECT id_gestion INTO v_g FROM gestion WHERE anio = 2026;
    SELECT id_periodo INTO v_t1 FROM periodo WHERE id_gestion_periodo = v_g AND nombre_periodo = '1er Trimestre';
    SELECT id_periodo INTO v_t2 FROM periodo WHERE id_gestion_periodo = v_g AND nombre_periodo = '2do Trimestre';
    SELECT id_periodo INTO v_t3 FROM periodo WHERE id_gestion_periodo = v_g AND nombre_periodo = '3er Trimestre';
    SELECT id_curso INTO v_sec FROM v_curso WHERE nombre_nivel = 'Secundaria' AND orden_grado = 1 AND paralelo = 'A';
    SELECT id_curso INTO v_pri FROM v_curso WHERE nombre_nivel = 'Primaria'   AND orden_grado = 6 AND paralelo = 'A';

    -- -----------------------------------------------------------------
    -- Personas
    -- -----------------------------------------------------------------
    INSERT INTO persona (ci, expedido, nombre_persona, apellidos, sexo, fecha_nacimiento, telefono, email) VALUES
        ('1000001', 'LP', 'Juana',     'Rivero Salinas',    'F', NULL, '71000001', 'direccion@escuelamodelo.edu.bo'),
        ('1000002', 'LP', 'Carla',     'Mendoza Quispe',    'F', NULL, '71000002', NULL),
        ('2000001', 'LP', 'Roberto',   'Flores Mamani',     'M', NULL, NULL, NULL),
        ('2000002', 'LP', 'Patricia',  'Vargas Choque',     'F', NULL, NULL, NULL),
        ('2000003', 'OR', 'Miguel',    'Torrez Apaza',      'M', NULL, NULL, NULL),
        ('2000004', 'LP', 'Sandra',    'Gutierrez Limachi', 'F', NULL, NULL, NULL),
        ('2000005', 'LP', 'Jorge',     'Condori Ticona',    'M', NULL, NULL, NULL),
        ('2000006', 'CB', 'Elena',     'Rojas Huanca',      'F', NULL, NULL, NULL),
        ('3000001', NULL, 'Mario',     'Quispe Laura',      'M', NULL, '72000001', NULL),
        ('3000002', NULL, 'Rosa',      'Mamani Cruz',       'F', NULL, '72000002', NULL),
        ('3000003', NULL, 'Luis',      'Choque Poma',       'M', NULL, '72000003', NULL),
        ('3000004', NULL, 'Ana',       'Apaza Villca',      'F', NULL, '72000004', NULL),
        ('3000005', NULL, 'Pedro',     'Limachi Nina',      'M', NULL, '72000005', NULL),
        ('3000006', NULL, 'Silvia',    'Ticona Aruquipa',   'F', NULL, '72000006', NULL),
        ('4500001', 'LP', 'Mateo',     'Quispe Mamani',     'M', '2014-03-12', NULL, NULL),
        ('4500002', 'LP', 'Diego',     'Choque Rojas',      'M', '2014-06-02', NULL, NULL),
        ('4500003', 'LP', 'Camila',    'Apaza Flores',      'F', '2014-01-25', NULL, NULL),
        ('4500004', 'LP', 'Daniel',    'Limachi Soria',     'M', '2014-09-30', NULL, NULL),
        ('4500005', 'LP', 'Santiago',  'Ticona Vega',       'M', '2014-04-18', NULL, NULL),
        ('4500006', 'LP', 'Mariana',   'Ticona Vega',       'F', '2014-04-18', NULL, NULL),
        ('4500007', 'LP', 'Sofia',     'Quispe Mamani',     'F', '2015-07-07', NULL, NULL),
        ('4500008', 'LP', 'Valeria',   'Choque Rojas',      'F', '2015-02-14', NULL, NULL),
        ('4500009', 'LP', 'Lucas',     'Apaza Flores',      'M', '2015-11-03', NULL, NULL),
        ('4500010', 'LP', 'Isabella',  'Limachi Soria',     'F', '2015-05-21', NULL, NULL),
        ('4500011', 'LP', 'Nicolas',   'Ticona Vega',       'M', '2015-08-09', NULL, NULL),
        ('4500012', 'LP', 'Valentina', 'Ticona Vega',       'F', '2015-12-01', NULL, NULL);

    INSERT INTO administrativo (ci_administrativo, cargo) VALUES ('1000001', 'Directora'), ('1000002', 'Secretaria');

    INSERT INTO profesor (ci_profesor, titulo_academico, fecha_contrato, anios_experiencia) VALUES
        ('2000001', 'Lic. en Matematica',          '2018-02-01', 12),
        ('2000002', 'Lic. en Linguistica',         '2019-02-01', 9),
        ('2000003', 'Lic. en Biologia',            '2020-02-03', 7),
        ('2000004', 'Lic. en Ciencias Sociales',   '2017-02-01', 14),
        ('2000005', 'Lic. en Educacion Fisica',    '2021-02-01', 5),
        ('2000006', 'Prof. de Educacion Primaria', '2016-02-01', 16);

    INSERT INTO tutor (ci_tutor, ocupacion) VALUES
        ('3000001', 'Comerciante'), ('3000002', 'Enfermera'), ('3000003', 'Ingeniero'),
        ('3000004', 'Contadora'),   ('3000005', 'Chofer'),    ('3000006', 'Profesora');

    INSERT INTO estudiante (ci_estudiante, rude, observacion_medica)
    SELECT ci, 'RUDE-' || ci, CASE WHEN ci = '4500002' THEN 'Asma leve: usa inhalador' END
      FROM persona WHERE ci LIKE '45%';

    -- Tutor principal (y responsable de pago) de cada estudiante
    INSERT INTO tutor_estudiante (ci_tutor_tutorestudiante, ci_estudiante_tutorestudiante, parentesco,
                                  es_principal, es_responsable_pago)
    SELECT t.tutor, t.est, t.parentesco, true, true
      FROM (VALUES
            ('3000001', '4500001', 'padre'), ('3000003', '4500002', 'padre'), ('3000004', '4500003', 'madre'),
            ('3000005', '4500004', 'padre'), ('3000006', '4500005', 'madre'), ('3000006', '4500006', 'madre'),
            ('3000001', '4500007', 'padre'), ('3000003', '4500008', 'padre'), ('3000004', '4500009', 'madre'),
            ('3000005', '4500010', 'padre'), ('3000006', '4500011', 'madre'), ('3000006', '4500012', 'madre')
           ) AS t(tutor, est, parentesco);
    -- Segunda tutora (madre) de los hermanos Quispe, no principal
    INSERT INTO tutor_estudiante (ci_tutor_tutorestudiante, ci_estudiante_tutorestudiante, parentesco)
    VALUES ('3000002', '4500001', 'madre'), ('3000002', '4500007', 'madre');

    -- -----------------------------------------------------------------
    -- Inscripciones
    -- -----------------------------------------------------------------
    INSERT INTO inscripcion (ci_estudiante_inscripcion, id_gestion_inscripcion, id_curso_inscripcion, fecha_inscripcion)
    SELECT ci, v_g, CASE WHEN ci <= '4500006' THEN v_sec ELSE v_pri END, DATE '2026-01-20'
      FROM persona WHERE ci LIKE '45%';

    -- -----------------------------------------------------------------
    -- Asignaciones y horarios (el trigger valida que no haya choques)
    -- -----------------------------------------------------------------
    INSERT INTO asignacion_profesor_clase (ci_profesor_asignacion, id_materia_asignacion, id_curso_asignacion,
                                           id_aula_asignacion, id_gestion_asignacion)
    SELECT a.profesor, m.id_materia, CASE a.curso WHEN 'sec' THEN v_sec ELSE v_pri END, au.id_aula, v_g
      FROM (VALUES
            ('sec', '2000001', 'Matematica',                  'B-201'),
            ('sec', '2000002', 'Comunicacion y Lenguajes',    'B-201'),
            ('sec', '2000003', 'Biologia-Geografia',          'LAB-1'),
            ('sec', '2000004', 'Ciencias Sociales',           'B-201'),
            ('sec', '2000005', 'Educacion Fisica y Deportes', 'CANCHA'),
            ('pri', '2000006', 'Matematica',                  'A-106'),
            ('pri', '2000003', 'Ciencias Naturales',          'A-106'),
            ('pri', '2000002', 'Comunicacion y Lenguajes',    'A-106'),
            ('pri', '2000005', 'Educacion Fisica y Deportes', 'CANCHA'),
            ('pri', '2000004', 'Ciencias Sociales',           'A-106')
           ) AS a(curso, profesor, materia, aula)
      JOIN materia m ON m.nombre_materia = a.materia
      JOIN aula au   ON au.numero = a.aula;

    INSERT INTO horario (id_asignacion_horario, dia, hora_inicio_h, hora_final_f)
    SELECT ap.id_asignacion, h.dia, h.inicio::TIME, h.fin::TIME
      FROM (VALUES
            ('sec', 'Matematica',                  'lunes',     '08:00', '09:30'),
            ('sec', 'Matematica',                  'jueves',    '08:00', '09:30'),
            ('sec', 'Comunicacion y Lenguajes',    'lunes',     '09:45', '11:15'),
            ('sec', 'Comunicacion y Lenguajes',    'viernes',   '08:00', '09:30'),
            ('sec', 'Biologia-Geografia',          'martes',    '08:00', '09:30'),
            ('sec', 'Ciencias Sociales',           'martes',    '09:45', '11:15'),
            ('sec', 'Educacion Fisica y Deportes', 'miercoles', '08:00', '09:30'),
            ('pri', 'Matematica',                  'lunes',     '08:00', '09:30'),
            ('pri', 'Matematica',                  'jueves',    '09:45', '11:15'),
            ('pri', 'Ciencias Naturales',          'lunes',     '09:45', '11:15'),
            ('pri', 'Ciencias Naturales',          'viernes',   '09:45', '11:15'),
            ('pri', 'Comunicacion y Lenguajes',    'martes',    '08:00', '09:30'),
            ('pri', 'Educacion Fisica y Deportes', 'martes',    '09:45', '11:15'),
            ('pri', 'Ciencias Sociales',           'miercoles', '09:45', '11:15')
           ) AS h(curso, materia, dia, inicio, fin)
      JOIN materia m ON m.nombre_materia = h.materia
      JOIN asignacion_profesor_clase ap
        ON ap.id_materia_asignacion = m.id_materia
       AND ap.id_curso_asignacion   = CASE h.curso WHEN 'sec' THEN v_sec ELSE v_pri END;

    -- -----------------------------------------------------------------
    -- Calificaciones: 1er y 2do trimestre, todas las dimensiones
    -- (puntajes deterministas; "bajo" siempre queda por debajo de 51)
    -- -----------------------------------------------------------------
    INSERT INTO calificacion (ci_estudiante_calificacion, id_materia_calificacion, id_periodo_calificacion, fecha_calificacion)
    SELECT i.ci_estudiante_inscripcion, a.id_materia_asignacion, t.id_periodo, t.fecha
      FROM inscripcion i
      JOIN asignacion_profesor_clase a ON a.id_curso_asignacion = i.id_curso_inscripcion
                                      AND a.id_gestion_asignacion = i.id_gestion_inscripcion
      CROSS JOIN (VALUES (v_t1, DATE '2026-05-08'), (v_t2, DATE '2026-08-21')) AS t(id_periodo, fecha)
     WHERE i.id_gestion_inscripcion = v_g;

    INSERT INTO calificacion_detalle (id_calificacion_detalle, id_dimension_detalle, puntaje)
    SELECT c.id_calificacion, d.id_dimension,
           CASE WHEN b.bajo THEN
                    CASE d.nombre_dimension WHEN 'Ser' THEN 4 + x.h % 3  WHEN 'Saber' THEN 10 + x.h % 6
                                            WHEN 'Hacer' THEN 10 + x.h % 6 WHEN 'Decidir' THEN 4 + x.h % 3
                                            ELSE 6 + x.h % 3 END
                ELSE
                    CASE d.nombre_dimension WHEN 'Ser' THEN 7 + x.h % 4  WHEN 'Saber' THEN 22 + x.h % 14
                                            WHEN 'Hacer' THEN 22 + x.h % 14 WHEN 'Decidir' THEN 7 + x.h % 4
                                            ELSE 8 + x.h % 3 END
           END
      FROM calificacion c
      JOIN materia m ON m.id_materia = c.id_materia_calificacion
      JOIN dimension_evaluacion d ON d.id_gestion_dimension = v_g
      CROSS JOIN LATERAL (SELECT c.ci_estudiante_calificacion = '4500006'
                              OR (c.ci_estudiante_calificacion = '4500011' AND m.nombre_materia = 'Matematica') AS bajo) b
      CROSS JOIN LATERAL (SELECT abs(hashtext(c.ci_estudiante_calificacion || c.id_materia_calificacion
                                              || c.id_periodo_calificacion || d.nombre_dimension)) AS h) x
     WHERE c.id_periodo_calificacion IN (v_t1, v_t2);

    -- 3er trimestre en curso: solo "Saber" de Matemática en Secundaria
    INSERT INTO calificacion (ci_estudiante_calificacion, id_materia_calificacion, id_periodo_calificacion, fecha_calificacion)
    SELECT i.ci_estudiante_inscripcion, m.id_materia, v_t3, DATE '2026-09-18'
      FROM inscripcion i JOIN materia m ON m.nombre_materia = 'Matematica'
     WHERE i.id_curso_inscripcion = v_sec AND i.id_gestion_inscripcion = v_g;

    INSERT INTO calificacion_detalle (id_calificacion_detalle, id_dimension_detalle, puntaje)
    SELECT c.id_calificacion, d.id_dimension, 20 + abs(hashtext(c.ci_estudiante_calificacion || 't3')) % 16
      FROM calificacion c
      JOIN dimension_evaluacion d ON d.id_gestion_dimension = v_g AND d.nombre_dimension = 'Saber'
     WHERE c.id_periodo_calificacion = v_t3;

    -- Cierre del 1er trimestre: boletines (procedimiento) + periodo cerrado
    CALL sp_emitir_boletines(v_t1, NULL, v_n);
    UPDATE periodo SET estado_periodo = 'cerrado' WHERE id_periodo = v_t1;

    -- -----------------------------------------------------------------
    -- Asistencia: 1 al 24 de septiembre, según el día de cada horario
    -- -----------------------------------------------------------------
    INSERT INTO asistencia (id_asignacion_asistencia, ci_estudiante_asistencia, fecha_asistencia,
                            estado_asistencia, observacion_asistencia)
    SELECT a.id_asignacion, i.ci_estudiante_inscripcion, d::DATE,
           CASE WHEN x.n < 85 THEN 'presente'
                WHEN x.n < 91 THEN 'tardanza'
                WHEN x.n < 97 THEN 'ausente'
                ELSE 'justificado' END,
           CASE WHEN x.n >= 97 THEN 'Presento certificado medico' END
      FROM asignacion_profesor_clase a
      JOIN horario h     ON h.id_asignacion_horario = a.id_asignacion
      JOIN inscripcion i ON i.id_curso_inscripcion = a.id_curso_asignacion
                        AND i.id_gestion_inscripcion = a.id_gestion_asignacion
      CROSS JOIN generate_series(DATE '2026-09-01', DATE '2026-09-24', INTERVAL '1 day') AS d
      CROSS JOIN LATERAL (SELECT abs(hashtext(i.ci_estudiante_inscripcion || a.id_asignacion || d::DATE)) % 100 AS n) x
     WHERE a.id_gestion_asignacion = v_g
       AND EXTRACT(ISODOW FROM d) = array_position(
               ARRAY['lunes','martes','miercoles','jueves','viernes','sabado','domingo'], h.dia);

    -- -----------------------------------------------------------------
    -- Becas, cuotas (feb-sep, procedimiento) y pagos
    -- -----------------------------------------------------------------
    INSERT INTO beca (ci_estudiante_beca, id_gestion_beca, porcentaje_descuento, motivo_beca) VALUES
        ('4500003', v_g, 50,  'Rendimiento academico'),
        ('4500009', v_g, 100, 'Convenio institucional');

    FOR v_mes IN 2..9 LOOP
        CALL sp_generar_cuotas_mes(v_g, v_mes, v_n);
    END LOOP;

    -- Pagan todos salvo los morosos; recibos correlativos por fecha
    WITH pagados AS (
        SELECT pm.id_pago, pm.mes, pm.fecha_vencimiento, pm.ci_estudiante_pago,
               row_number() OVER (ORDER BY pm.fecha_vencimiento, pm.ci_estudiante_pago) AS recibo
          FROM pago_mensualidad pm
         WHERE pm.id_gestion_pago = v_g
           AND NOT (pm.ci_estudiante_pago = '4500005' AND pm.mes >= 7)
           AND NOT (pm.ci_estudiante_pago = '4500011' AND pm.mes >= 8)
           AND NOT (pm.ci_estudiante_pago IN ('4500002', '4500008') AND pm.mes = 9)
    )
    UPDATE pago_mensualidad pm SET
        estado_pago            = 'pagado',
        metodo_pago            = (ARRAY['efectivo', 'qr', 'transferencia'])[1 + p.mes % 3],
        fecha_pago             = p.fecha_vencimiento - (abs(hashtext(p.ci_estudiante_pago || p.mes)) % 8),
        numero_recibo          = p.recibo,
        ci_administrativo_pago = '1000002',
        ci_tutor_pago          = (SELECT te.ci_tutor_tutorestudiante FROM tutor_estudiante te
                                   WHERE te.ci_estudiante_tutorestudiante = p.ci_estudiante_pago
                                     AND te.es_responsable_pago)
      FROM pagados p
     WHERE pm.id_pago = p.id_pago;

    PERFORM setval('seq_numero_recibo', (SELECT max(numero_recibo) FROM pago_mensualidad));

    -- -----------------------------------------------------------------
    -- Inventario (el trigger actualiza el stock con cada movimiento)
    -- -----------------------------------------------------------------
    INSERT INTO inventario (nombre_inventario, observacion_inventario) VALUES
        ('Pupitres', NULL), ('Sillas', NULL), ('Proyector multimedia', 'Uno en reparacion'),
        ('Balones de futbol', NULL), ('Resmas de papel bond', NULL), ('Marcadores de pizarra', NULL);

    INSERT INTO movimiento_inventario (id_inventario_movimiento, tipo_accion_inventario, cantidad_movimiento,
                                       motivo_movimiento, destino_movimiento, ci_administrativo_movimiento)
    SELECT inv.id_inventario, mv.tipo, mv.cantidad, mv.motivo, mv.destino, mv.responsable
      FROM (VALUES
            (1, 'Pupitres',              'entrada', 120, 'Compra inicial de la gestion', NULL,                 '1000001'),
            (2, 'Sillas',                'entrada', 150, 'Compra inicial de la gestion', NULL,                 '1000001'),
            (3, 'Proyector multimedia',  'entrada',   4, 'Compra inicial de la gestion', NULL,                 '1000001'),
            (4, 'Balones de futbol',     'entrada',  15, 'Compra inicial de la gestion', NULL,                 '1000001'),
            (5, 'Resmas de papel bond',  'entrada',  40, 'Compra inicial de la gestion', NULL,                 '1000001'),
            (6, 'Marcadores de pizarra', 'entrada', 100, 'Compra inicial de la gestion', NULL,                 '1000001'),
            (7, 'Balones de futbol',     'salida',    3, 'Entrega a Educacion Fisica',   'CANCHA',             '1000001'),
            (8, 'Marcadores de pizarra', 'salida',   20, 'Dotacion mensual',             'Sala de profesores', '1000002'),
            (9, 'Resmas de papel bond',  'salida',   12, 'Impresion de examenes',        'Secretaria',         '1000002')
           ) AS mv(orden, articulo, tipo, cantidad, motivo, destino, responsable)
      JOIN inventario inv ON inv.nombre_inventario = mv.articulo
     ORDER BY mv.orden;

    -- -----------------------------------------------------------------
    -- Seguimiento y comunicados
    -- -----------------------------------------------------------------
    INSERT INTO seguimiento_estudiante (ci_estudiante_seguimiento, tipo_seguimiento, gravedad,
                                        descripcion_seguimiento, accion_tomada, fecha_seguimiento, ci_registrado_por) VALUES
        ('4500006', 'academico', NULL,   'Bajo rendimiento en el 1er y 2do trimestre en todas las materias',
         'Se cita a la tutora para acordar un plan de refuerzo', '2026-08-25', '2000001'),
        ('4500004', 'conducta',  'leve', 'Interrumpe la clase de forma reiterada',
         'Llamada de atencion verbal', '2026-09-08', '2000004'),
        ('4500007', 'merito',    NULL,   'Primer lugar en la feria de ciencias', NULL, '2026-09-15', '2000003');

    INSERT INTO comunicado (titulo, contenido, tipo_comunicado, alcance, fecha_citacion,
                            id_gestion_comunicado, id_curso_comunicado, ci_estudiante_comunicado, ci_autor) VALUES
        ('Inicio del 3er Trimestre',
         'Se recuerda a toda la comunidad educativa que el 3er trimestre inicia el 31 de agosto.',
         'general', 'todos', NULL, v_g, NULL, NULL, '1000001'),
        ('Examen de Matematica',
         'El examen del tema "Numeros enteros" sera el jueves 1 de octubre.',
         'general', 'curso', NULL, v_g, v_sec, NULL, '2000001'),
        ('Citacion a la tutora de Mariana Ticona',
         'Se solicita su presencia para conversar sobre el rendimiento academico de la estudiante.',
         'citacion', 'estudiante', '2026-09-30 10:00:00-04', v_g, NULL, '4500006', '2000001');

    -- -----------------------------------------------------------------
    -- Usuarios de prueba (contraseña en bcrypt, la misma para todos)
    -- -----------------------------------------------------------------
    INSERT INTO usuario (nombre_usuario, password_hash, id_rol_usuario, ci_persona)
    SELECT u.usuario, extensions.crypt('Escuela2026', extensions.gen_salt('bf', 10)), r.id_rol, u.ci
      FROM (VALUES
            ('direccion',  'administrador', '1000001'),
            ('secretaria', 'administrador', '1000002'),
            ('rflores',    'profesor',      '2000001'),
            ('erojas',     'profesor',      '2000006'),
            ('mquispe',    'estudiante',    '4500001'),
            ('marioq',     'tutor',         '3000001')
           ) AS u(usuario, rol, ci)
      JOIN rol r ON r.nombre_rol = u.rol;
END;
$$;

COMMIT;

-- =====================================================================
-- USUARIOS DE PRUEBA  (contraseña de todos: Escuela2026)
-- SOLO para desarrollo: no cargar este archivo en producción.
-- =====================================================================
--   usuario      rol             persona
--   direccion    administrador   Juana Rivero (Directora)
--   secretaria   administrador   Carla Mendoza (Secretaria)
--   rflores      profesor        Roberto Flores (Matemática, 1ro A Sec.)
--   erojas       profesor        Elena Rojas (Matemática, 6to A Pri.)
--   mquispe      estudiante      Mateo Quispe (1ro A Sec.)
--   marioq       tutor           Mario Quispe (padre de Mateo y Sofía)

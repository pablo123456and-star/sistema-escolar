-- =====================================================================
-- 07 - DATOS INICIALES (CATALOGOS)  -  SISTEMA ESCUELA MODELO
-- Requiere: 01 a 06
-- =====================================================================
-- Carga lo minimo para empezar a usar el sistema: roles, niveles,
-- grados, gestion 2026 con sus trimestres, dimensiones de evaluacion,
-- materias con su plan de estudios, cursos, aulas y aranceles.
-- Revisa y ajusta fechas, montos y ponderaciones a tu escuela.
-- =====================================================================

BEGIN;

-- ---------------------------------------------------------------------
-- Roles (las politicas RLS usan exactamente estos nombres)
-- ---------------------------------------------------------------------
INSERT INTO rol (nombre_rol, descripcion_rol) VALUES
    ('administrador', 'Direccion y secretaria: acceso completo'),
    ('profesor',      'Registra notas, asistencia y seguimiento de sus clases'),
    ('estudiante',    'Consulta sus notas, asistencia, boletines y pagos'),
    ('tutor',         'Consulta la informacion de los estudiantes a su cargo');

-- ---------------------------------------------------------------------
-- Niveles y grados
-- ---------------------------------------------------------------------
INSERT INTO nivel_educativo (nombre_nivel) VALUES ('Inicial'), ('Primaria'), ('Secundaria');

INSERT INTO grado (nombre_grado, orden_grado, id_nivel_educativo_grado)
SELECT g.nombre, g.orden, n.id_nivel
  FROM (VALUES
        ('Inicial',    '1ra Seccion', 1), ('Inicial',    '2da Seccion', 2),
        ('Primaria',   '1ro', 1), ('Primaria',   '2do', 2), ('Primaria',   '3ro', 3),
        ('Primaria',   '4to', 4), ('Primaria',   '5to', 5), ('Primaria',   '6to', 6),
        ('Secundaria', '1ro', 1), ('Secundaria', '2do', 2), ('Secundaria', '3ro', 3),
        ('Secundaria', '4to', 4), ('Secundaria', '5to', 5), ('Secundaria', '6to', 6)
       ) AS g(nivel, nombre, orden)
  JOIN nivel_educativo n ON n.nombre_nivel = g.nivel;

-- ---------------------------------------------------------------------
-- Gestion 2026 y trimestres
-- ---------------------------------------------------------------------
INSERT INTO gestion (anio, fecha_inicio_g, fecha_final_g, nota_minima_aprobacion)
VALUES (2026, '2026-02-02', '2026-12-04', 51);

INSERT INTO periodo (nombre_periodo, tipo, fecha_inicio_p, fecha_final_p, id_gestion_periodo)
SELECT p.nombre, 'trimestre', p.inicio::DATE, p.final::DATE, g.id_gestion
  FROM (VALUES
        ('1er Trimestre', '2026-02-02', '2026-05-15'),
        ('2do Trimestre', '2026-05-18', '2026-08-28'),
        ('3er Trimestre', '2026-08-31', '2026-12-04')
       ) AS p(nombre, inicio, final)
  CROSS JOIN gestion g
 WHERE g.anio = 2026;

-- ---------------------------------------------------------------------
-- Dimensiones de evaluacion 2026 (deben sumar 100)
-- VALORES DE EJEMPLO: ajustalos a la Resolucion Ministerial vigente.
-- ---------------------------------------------------------------------
INSERT INTO dimension_evaluacion (nombre_dimension, puntaje_maximo, es_autoevaluacion, orden_dimension, id_gestion_dimension)
SELECT d.nombre, d.maximo, d.auto, d.orden, g.id_gestion
  FROM (VALUES
        ('Ser',            10, false, 1),
        ('Saber',          35, false, 2),
        ('Hacer',          35, false, 3),
        ('Decidir',        10, false, 4),
        ('Autoevaluacion', 10, true,  5)
       ) AS d(nombre, maximo, auto, orden)
  CROSS JOIN gestion g
 WHERE g.anio = 2026;

-- ---------------------------------------------------------------------
-- Materias (carga horaria semanal referencial)
-- ---------------------------------------------------------------------
INSERT INTO materia (nombre_materia, carga_horaria) VALUES
    ('Comunicacion y Lenguajes',                 6),
    ('Lengua Extranjera',                        2),
    ('Lengua Originaria',                        2),
    ('Ciencias Sociales',                        4),
    ('Educacion Fisica y Deportes',              3),
    ('Educacion Musical',                        2),
    ('Artes Plasticas y Visuales',               2),
    ('Matematica',                               6),
    ('Tecnica Tecnologica',                      2),
    ('Ciencias Naturales',                       4),
    ('Biologia-Geografia',                       4),
    ('Fisica',                                   3),
    ('Quimica',                                  3),
    ('Cosmovisiones, Filosofia y Psicologia',    2),
    ('Valores, Espiritualidades y Religiones',   2);

-- ---------------------------------------------------------------------
-- Plan de estudios (que materias lleva cada grado)
-- ---------------------------------------------------------------------
-- Inicial
INSERT INTO materia_grado (id_grado_mg, id_materia_mg)
SELECT g.id_grado, m.id_materia
  FROM grado g
  JOIN nivel_educativo n ON n.id_nivel = g.id_nivel_educativo_grado AND n.nombre_nivel = 'Inicial'
  JOIN materia m ON m.nombre_materia IN ('Comunicacion y Lenguajes', 'Matematica', 'Ciencias Naturales',
                                         'Educacion Fisica y Deportes', 'Educacion Musical',
                                         'Artes Plasticas y Visuales');
-- Primaria
INSERT INTO materia_grado (id_grado_mg, id_materia_mg)
SELECT g.id_grado, m.id_materia
  FROM grado g
  JOIN nivel_educativo n ON n.id_nivel = g.id_nivel_educativo_grado AND n.nombre_nivel = 'Primaria'
  JOIN materia m ON m.nombre_materia IN ('Comunicacion y Lenguajes', 'Lengua Extranjera', 'Lengua Originaria',
                                         'Ciencias Sociales', 'Educacion Fisica y Deportes', 'Educacion Musical',
                                         'Artes Plasticas y Visuales', 'Matematica', 'Tecnica Tecnologica',
                                         'Ciencias Naturales', 'Valores, Espiritualidades y Religiones');
-- Secundaria (Fisica y Quimica desde 3ro)
INSERT INTO materia_grado (id_grado_mg, id_materia_mg)
SELECT g.id_grado, m.id_materia
  FROM grado g
  JOIN nivel_educativo n ON n.id_nivel = g.id_nivel_educativo_grado AND n.nombre_nivel = 'Secundaria'
  JOIN materia m ON m.nombre_materia IN ('Comunicacion y Lenguajes', 'Lengua Extranjera', 'Lengua Originaria',
                                         'Ciencias Sociales', 'Educacion Fisica y Deportes', 'Educacion Musical',
                                         'Artes Plasticas y Visuales', 'Matematica', 'Tecnica Tecnologica',
                                         'Biologia-Geografia', 'Cosmovisiones, Filosofia y Psicologia',
                                         'Valores, Espiritualidades y Religiones')
                 OR (m.nombre_materia IN ('Fisica', 'Quimica') AND g.orden_grado >= 3);

-- ---------------------------------------------------------------------
-- Cursos: paralelo A en todos los grados, y B en Secundaria
-- ---------------------------------------------------------------------
INSERT INTO curso (paralelo, id_grado_curso, cupo_maximo)
SELECT 'A', g.id_grado, CASE WHEN n.nombre_nivel = 'Inicial' THEN 25 ELSE 35 END
  FROM grado g JOIN nivel_educativo n ON n.id_nivel = g.id_nivel_educativo_grado;

INSERT INTO curso (paralelo, id_grado_curso, cupo_maximo)
SELECT 'B', g.id_grado, 35
  FROM grado g JOIN nivel_educativo n ON n.id_nivel = g.id_nivel_educativo_grado
 WHERE n.nombre_nivel = 'Secundaria';

-- ---------------------------------------------------------------------
-- Aulas
-- ---------------------------------------------------------------------
INSERT INTO aula (numero, capacidad, tipo_aula) VALUES
    ('I-01', 25, 'aula'), ('I-02', 25, 'aula'),
    ('A-101', 35, 'aula'), ('A-102', 35, 'aula'), ('A-103', 35, 'aula'),
    ('A-104', 35, 'aula'), ('A-105', 35, 'aula'), ('A-106', 35, 'aula'),
    ('B-201', 35, 'aula'), ('B-202', 35, 'aula'), ('B-203', 35, 'aula'),
    ('B-204', 35, 'aula'), ('B-205', 35, 'aula'), ('B-206', 35, 'aula'),
    ('LAB-1', 30, 'laboratorio'),
    ('COMP-1', 30, 'sala de computacion'),
    ('MUS-1', 30, 'sala de musica'),
    ('CANCHA', 80, 'cancha deportiva');

-- ---------------------------------------------------------------------
-- Aranceles 2026 (Bs por mes, vencen el dia 10)
-- ---------------------------------------------------------------------
INSERT INTO arancel (monto_mensual, dia_vencimiento, id_gestion_arancel, id_nivel_arancel)
SELECT a.monto, 10, g.id_gestion, n.id_nivel
  FROM (VALUES ('Inicial', 450), ('Primaria', 500), ('Secundaria', 550)) AS a(nivel, monto)
  JOIN nivel_educativo n ON n.nombre_nivel = a.nivel
  CROSS JOIN gestion g
 WHERE g.anio = 2026;

COMMIT;

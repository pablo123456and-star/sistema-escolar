-- =====================================================================
-- 05 - VISTAS  -  SISTEMA ESCUELA MODELO
-- Requiere: 01_esquema.sql
-- =====================================================================
-- Consultas guardadas que el backend lee como si fueran tablas
-- (models.py / repository.py). No contienen reglas de negocio: solo
-- juntan tablas o calculan datos derivados.
--
--   v_curso         nombre legible de cada curso ("1ro A - Secundaria")
--   v_nota_final    nota final = suma de los puntajes por dimensión
--   v_estado_pagos  pagos con el estado real a la fecha (atrasado)
--   v_horario       horario completo con materia, profesor, aula y curso
--
-- Los reportes (centralizador, morosos, historial, porcentaje de
-- asistencia...) se arman en el backend a partir de estas vistas.
-- =====================================================================

BEGIN;

CREATE OR REPLACE VIEW v_curso AS
SELECT c.id_curso,
       g.nombre_grado || ' ' || c.paralelo || ' - ' || n.nombre_nivel AS nombre_curso,
       c.paralelo, c.cupo_maximo,
       g.id_grado, g.nombre_grado, g.orden_grado,
       n.id_nivel, n.nombre_nivel
  FROM curso c
  JOIN grado g           ON g.id_grado = c.id_grado_curso
  JOIN nivel_educativo n ON n.id_nivel = g.id_nivel_educativo_grado;

-- La nota final no se guarda (3FN): se calcula sumando el detalle.
CREATE OR REPLACE VIEW v_nota_final AS
SELECT c.id_calificacion,
       c.ci_estudiante_calificacion AS ci_estudiante,
       c.id_materia_calificacion    AS id_materia,
       c.id_periodo_calificacion    AS id_periodo,
       p.id_gestion_periodo         AS id_gestion,
       coalesce(sum(d.puntaje), 0)::NUMERIC(5,2) AS nota_final,
       count(d.id_dimension_detalle)             AS dimensiones_registradas,
       (SELECT count(*) FROM dimension_evaluacion de
         WHERE de.id_gestion_dimension = p.id_gestion_periodo) AS dimensiones_totales
  FROM calificacion c
  JOIN periodo p ON p.id_periodo = c.id_periodo_calificacion
  LEFT JOIN calificacion_detalle d ON d.id_calificacion_detalle = c.id_calificacion
 GROUP BY c.id_calificacion, p.id_gestion_periodo;

-- 'atrasado' no se guarda porque cambia con el tiempo: se calcula aquí.
CREATE OR REPLACE VIEW v_estado_pagos AS
SELECT pm.id_pago, pm.ci_estudiante_pago AS ci_estudiante,
       pe.apellidos || ' ' || pe.nombre_persona AS estudiante,
       g.anio, pm.id_gestion_pago AS id_gestion, pm.mes,
       pm.monto, pm.descuento_aplicado, pm.fecha_vencimiento, pm.fecha_pago,
       pm.metodo_pago, pm.numero_recibo,
       pm.estado_pago,
       CASE WHEN pm.estado_pago = 'pendiente' AND pm.fecha_vencimiento < CURRENT_DATE
            THEN 'atrasado' ELSE pm.estado_pago END AS estado_actual,
       CASE WHEN pm.estado_pago = 'pendiente' AND pm.fecha_vencimiento < CURRENT_DATE
            THEN CURRENT_DATE - pm.fecha_vencimiento ELSE 0 END AS dias_atraso
  FROM pago_mensualidad pm
  JOIN persona pe ON pe.ci = pm.ci_estudiante_pago
  JOIN gestion g  ON g.id_gestion = pm.id_gestion_pago;

CREATE OR REPLACE VIEW v_horario AS
SELECT h.id_horario, h.dia,
       array_position(ARRAY['lunes','martes','miercoles','jueves','viernes','sabado','domingo'], h.dia) AS dia_orden,
       h.hora_inicio_h AS hora_inicio, h.hora_final_f AS hora_final,
       a.id_asignacion, a.id_gestion_asignacion AS id_gestion,
       a.id_curso_asignacion AS id_curso, vc.nombre_curso,
       a.id_materia_asignacion AS id_materia, m.nombre_materia,
       a.ci_profesor_asignacion AS ci_profesor, pp.nombre_persona || ' ' || pp.apellidos AS profesor,
       a.id_aula_asignacion AS id_aula, au.numero AS aula
  FROM horario h
  JOIN asignacion_profesor_clase a ON a.id_asignacion = h.id_asignacion_horario
  JOIN v_curso vc  ON vc.id_curso = a.id_curso_asignacion
  JOIN materia m   ON m.id_materia = a.id_materia_asignacion
  JOIN persona pp  ON pp.ci = a.ci_profesor_asignacion
  JOIN aula au     ON au.id_aula = a.id_aula_asignacion;

COMMIT;

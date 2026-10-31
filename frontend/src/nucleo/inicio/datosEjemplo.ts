/**
 * PROTOTIPO - Datos de ejemplo para el panel del docente (los de estudiante y tutor ya usan datos reales).
 *
 * Imitan el escenario de basededato/sql/08_datos_prueba.sql (rflores, mquispe, marioq).
 * Se reemplazan por los hooks del api.ts de cada paquete cuando se implementen:
 *   horario -> CU20 · asistencia -> CU21/CU22 · calificaciones -> CU23 · boletín -> CU24
 *   pagos -> CU25 · comunicados -> CU27 · estudiantes del tutor -> CU09
 */

export type Dia = 'lunes' | 'martes' | 'miercoles' | 'jueves' | 'viernes'

export type BloqueHorario = {
  dia: Dia
  inicio: string
  fin: string
  materia: string
  curso: string
  aula: string
  docente?: string
}

/** Nota final por trimestre (escala 1-100, se aprueba con 51). null = aún sin nota. */
export type NotaMateria = { materia: string; docente: string; t1: number | null; t2: number | null; t3: number | null }

export type ResumenAsistencia = {
  presentes: number
  atrasos: number
  faltas: number
  licencias: number
  recientes: { fecha: string; materia: string; tipo: 'falta' | 'atraso' | 'licencia' }[]
}

export type Cuota = { mes: string; monto: number; vence: string; estado: 'pagada' | 'pendiente' | 'vencida'; pagado_en?: string }

export type Comunicado = {
  titulo: string
  contenido: string
  tipo: 'general' | 'citacion'
  autor: string
  fecha: string
  fecha_citacion?: string
}

export const PERIODO_ACTUAL = '3er Trimestre'

// ---- Comunicados (CU27) -------------------------------------------------------
const INICIO_TRIMESTRE: Comunicado = {
  titulo: 'Inicio del 3er Trimestre',
  contenido: 'Se recuerda a toda la comunidad educativa que el 3er trimestre inicia el 31 de agosto.',
  tipo: 'general',
  autor: 'Juana Rivero (Directora)',
  fecha: '2026-08-28',
}
const EXAMEN_MATEMATICA: Comunicado = {
  titulo: 'Examen de Matemática',
  contenido: 'El examen del tema "Números enteros" será el jueves 1 de octubre.',
  tipo: 'general',
  autor: 'Roberto Flores (Matemática)',
  fecha: '2026-09-24',
}

// ---- Horarios (CU20) ------------------------------------------------------------
const HORARIO_1RO_SEC: BloqueHorario[] = [
  { dia: 'lunes', inicio: '08:00', fin: '09:30', materia: 'Matemática', curso: '1ro A Secundaria', aula: 'B-201', docente: 'Roberto Flores' },
  { dia: 'lunes', inicio: '09:45', fin: '11:15', materia: 'Comunicación y Lenguajes', curso: '1ro A Secundaria', aula: 'B-201', docente: 'Patricia Vargas' },
  { dia: 'martes', inicio: '08:00', fin: '09:30', materia: 'Biología-Geografía', curso: '1ro A Secundaria', aula: 'LAB-1', docente: 'Miguel Torrez' },
  { dia: 'martes', inicio: '09:45', fin: '11:15', materia: 'Ciencias Sociales', curso: '1ro A Secundaria', aula: 'B-201', docente: 'Sandra Gutierrez' },
  { dia: 'miercoles', inicio: '08:00', fin: '09:30', materia: 'Educación Física', curso: '1ro A Secundaria', aula: 'CANCHA', docente: 'Jorge Condori' },
  { dia: 'jueves', inicio: '08:00', fin: '09:30', materia: 'Matemática', curso: '1ro A Secundaria', aula: 'B-201', docente: 'Roberto Flores' },
  { dia: 'viernes', inicio: '08:00', fin: '09:30', materia: 'Comunicación y Lenguajes', curso: '1ro A Secundaria', aula: 'B-201', docente: 'Patricia Vargas' },
]

// ---- Docente (Roberto Flores, Matemática) ------------------------------------
export type EstudianteCurso = { ci: string; nombre: string; promedio: number; asistencia: number }

export type AsignacionDocente = {
  materia: string
  curso: string
  aula: string
  horario: BloqueHorario[]
  estudiantes: EstudianteCurso[]
}

export type PendienteDocente = { titulo: string; detalle: string; ruta: string; tono: 'ambar' | 'rojo' | 'azul' }

export const DOCENTE = {
  asignaciones: [
    {
      materia: 'Matemática',
      curso: '1ro A Secundaria',
      aula: 'B-201',
      horario: HORARIO_1RO_SEC.filter((b) => b.materia === 'Matemática'),
      estudiantes: [
        { ci: '4500001', nombre: 'Mateo Quispe Mamani', promedio: 80, asistencia: 94 },
        { ci: '4500002', nombre: 'Diego Choque Rojas', promedio: 76, asistencia: 100 },
        { ci: '4500003', nombre: 'Camila Apaza Flores', promedio: 85, asistencia: 100 },
        { ci: '4500004', nombre: 'Daniel Limachi Soria', promedio: 72, asistencia: 89 },
        { ci: '4500005', nombre: 'Santiago Ticona Vega', promedio: 69, asistencia: 94 },
        { ci: '4500006', nombre: 'Mariana Ticona Vega', promedio: 38, asistencia: 83 },
      ],
    },
  ] satisfies AsignacionDocente[],
  pendientes: [
    {
      titulo: 'Asistencia sin registrar',
      detalle: 'Matemática · 1ro A Secundaria · lunes 28/09',
      ruta: '/evaluacion/asistencia',
      tono: 'rojo',
    },
    {
      titulo: `Notas del ${PERIODO_ACTUAL}`,
      detalle: 'Registrado: Saber. Falta: Ser, Hacer y Decidir.',
      ruta: '/evaluacion/cu23',
      tono: 'ambar',
    },
    {
      titulo: 'Citación programada',
      detalle: 'Tutora de Mariana Ticona · 30/09 a las 10:00',
      ruta: '/administracion/cu27',
      tono: 'azul',
    },
  ] satisfies PendienteDocente[],
  comunicados: [
    EXAMEN_MATEMATICA,
    {
      titulo: 'Citación a la tutora de Mariana Ticona',
      contenido: 'Se solicita su presencia para conversar sobre el rendimiento académico de la estudiante.',
      tipo: 'citacion',
      autor: 'Roberto Flores (Matemática)',
      fecha: '2026-09-25',
      fecha_citacion: '2026-09-30T10:00:00-04:00',
    },
    INICIO_TRIMESTRE,
  ] satisfies Comunicado[],
}

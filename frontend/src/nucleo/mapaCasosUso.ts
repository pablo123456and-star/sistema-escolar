/**
 * Los 6 paquetes del sistema y sus casos de uso (mismo orden que el backend).
 * Ciclo 1 implementado: CU01-CU04 (seguridad), CU06 y CU08 (personas).
 */
export type CasoUso = { codigo: string; nombre: string; ruta: string }
export type Paquete = { paquete: string; titulo: string; casos: CasoUso[] }

export const PAQUETES: Paquete[] = [
  {
    paquete: 'seguridad',
    titulo: 'Seguridad: acceso y auditoría',
    casos: [
      { codigo: 'CU01', nombre: 'Iniciar sesión (incluye recuperar contraseña)', ruta: '/login' },
      { codigo: 'CU02', nombre: 'Gestionar usuarios (CRUD)', ruta: '/seguridad/usuarios' },
      { codigo: 'CU03', nombre: 'Gestionar roles y permisos', ruta: '/seguridad/roles' },
      { codigo: 'CU04', nombre: 'Consultar bitácora de actividades', ruta: '/seguridad/bitacora' },
    ],
  },
  {
    paquete: 'personas',
    titulo: 'Personas: estudiantes, tutores, docentes y administrativos',
    casos: [
      { codigo: 'CU05', nombre: 'Registrar y actualizar datos de persona', ruta: '/personas/cu05' },
      { codigo: 'CU06', nombre: 'Registrar y gestionar estudiante', ruta: '/personas/estudiantes' },
      { codigo: 'CU07', nombre: 'Registrar antecedentes médicos y seguimiento del estudiante', ruta: '/personas/cu07' },
      { codigo: 'CU08', nombre: 'Registrar tutor y asociarlo a estudiante', ruta: '/personas/tutores' },
      { codigo: 'CU09', nombre: 'Consultar estudiantes/tutores relacionados', ruta: '/personas/cu09' },
      { codigo: 'CU10', nombre: 'Registrar docente', ruta: '/personas/cu10' },
      { codigo: 'CU11', nombre: 'Registrar personal administrativo', ruta: '/personas/cu11' },
    ],
  },
  {
    paquete: 'academico',
    titulo: 'Académico: estructura, gestión e inscripciones',
    casos: [
      { codigo: 'CU12', nombre: 'Gestionar niveles educativos y cursos', ruta: '/academico/cu12' },
      { codigo: 'CU13', nombre: 'Gestionar materias y asignarlas a cursos', ruta: '/academico/materias' },
      { codigo: 'CU14', nombre: 'Asignar profesor a materia/curso', ruta: '/academico/asignaciones' },
      { codigo: 'CU15', nombre: 'Gestionar gestión académica (año lectivo)', ruta: '/academico/cu15' },
      { codigo: 'CU16', nombre: 'Inscribir estudiante en gestión académica', ruta: '/academico/cu16' },
      { codigo: 'CU17', nombre: 'Consultar historial de inscripciones', ruta: '/academico/cu17' },
    ],
  },
  {
    paquete: 'horarios',
    titulo: 'Horarios: aulas y horarios de clase',
    casos: [
      { codigo: 'CU18', nombre: 'Gestionar aulas', ruta: '/horarios/cu18' },
      { codigo: 'CU19', nombre: 'Generar horario de clases (aula, profesor, materia)', ruta: '/horarios/cu19' },
      { codigo: 'CU20', nombre: 'Consultar horarios', ruta: '/horarios/cu20' },
    ],
  },
  {
    paquete: 'evaluacion',
    titulo: 'Evaluación: asistencia, calificaciones y boletines',
    casos: [
      { codigo: 'CU21', nombre: 'Registrar asistencia de estudiantes', ruta: '/evaluacion/cu21' },
      { codigo: 'CU22', nombre: 'Consultar historial de asistencia', ruta: '/evaluacion/cu22' },
      { codigo: 'CU23', nombre: 'Registrar calificaciones y evaluaciones (incluye autoevaluación y cierre de periodo)', ruta: '/evaluacion/cu23' },
      { codigo: 'CU24', nombre: 'Generar y consultar boletín/libreta (incluye centralizador)', ruta: '/evaluacion/cu24' },
    ],
  },
  {
    paquete: 'administracion',
    titulo: 'Administración: pagos, inventario y comunicados',
    casos: [
      { codigo: 'CU25', nombre: 'Registrar pago de mensualidad (incluye aranceles, becas, cuotas y morosos)', ruta: '/administracion/cu25' },
      { codigo: 'CU26', nombre: 'Gestionar inventario (registrar, actualizar, consultar bienes)', ruta: '/administracion/cu26' },
      { codigo: 'CU27', nombre: 'Gestionar comunicados y citaciones', ruta: '/administracion/cu27' },
    ],
  },
]

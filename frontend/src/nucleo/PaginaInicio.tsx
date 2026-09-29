/**
 * Panel de inicio (CU01, postcondición): cada rol ve su propio panel.
 *   administrador -> indicadores de la institución, actividades recientes y avisos
 *   profesor      -> próximas clases, pendientes, sus estudiantes y horario
 *   estudiante    -> calificaciones, asistencia, horario, pagos y comunicados
 *   tutor         -> lo mismo, por cada estudiante vinculado
 * Los paneles de profesor, estudiante y tutor son un prototipo con datos de ejemplo
 * (nucleo/inicio/datosEjemplo.ts) hasta implementar los casos de uso que los alimentan.
 */
import { useSesion } from '@/nucleo/auth/contexto'
import PanelAdministrador from '@/nucleo/inicio/PanelAdministrador'
import PanelDocente from '@/nucleo/inicio/PanelDocente'
import PanelEstudiante from '@/nucleo/inicio/PanelEstudiante'
import PanelTutor from '@/nucleo/inicio/PanelTutor'

export default function PaginaInicio() {
  const { usuario } = useSesion()
  switch (usuario?.rol) {
    case 'administrador':
      return <PanelAdministrador />
    case 'profesor':
      return <PanelDocente />
    case 'estudiante':
      return <PanelEstudiante />
    case 'tutor':
      return <PanelTutor />
    default:
      return null
  }
}

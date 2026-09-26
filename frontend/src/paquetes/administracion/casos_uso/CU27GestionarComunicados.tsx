/**
 * CU27 - Gestionar comunicados y citaciones
 * Paquete: administracion
 *
 * Actores ........: Administrativo, Docente (publican); Tutor, Estudiante (leen)
 * Rol del sistema : administrador, profesor, tutor, estudiante
 * Backend ........: backend/app/paquetes/administracion/casos_uso/cu27_gestionar_comunicados.py
 *                   (ahí están las reglas de negocio que aplica el backend)
 *
 * Precondición:  Un docente solo publica a sus cursos o a sus estudiantes.
 * Postcondición: El comunicado queda visible para sus destinatarios y se registra quién lo leyó.
 *
 * Estado: PENDIENTE DE IMPLEMENTAR.
 */
import CasoUsoPendiente from '@/componentes/CasoUsoPendiente'

export default function CU27GestionarComunicados() {
  return <CasoUsoPendiente codigo="CU27" nombre="Gestionar comunicados y citaciones" paquete="administracion" />
}

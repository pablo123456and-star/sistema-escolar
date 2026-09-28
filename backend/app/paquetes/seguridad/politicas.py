"""
Reglas de negocio comunes del paquete seguridad (compartido).

    - Solo el administrador gestiona usuarios, roles y consulta la bitácora.
    - Los 4 roles son fijos (administrador, profesor, estudiante, tutor): no se crean ni se renombran.
    - Un usuario 'inactivo' o 'bloqueado', o cuya persona está inactiva, no puede iniciar sesión.
    - El rol de un usuario debe coincidir con la especialización de su persona.
    - El administrador no puede desactivar su propia cuenta ni quitarse el rol administrador.

Las reglas propias de cada caso de uso están en el encabezado de su archivo en casos_uso/.
"""
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.errores import ErrorNegocio
from app.paquetes.personas.models import Administrativo, Estudiante, Profesor, Tutor

ROLES = ("administrador", "profesor", "estudiante", "tutor")
ESTADOS_USUARIO = ("activo", "inactivo", "bloqueado")

# rol -> (tabla de especialización que debe tener la persona, columna CI, nombre legible)
ESPECIALIZACION = {
    "administrador": (Administrativo, Administrativo.ci_administrativo, "personal administrativo"),
    "profesor": (Profesor, Profesor.ci_profesor, "docente"),
    "estudiante": (Estudiante, Estudiante.ci_estudiante, "estudiante"),
    "tutor": (Tutor, Tutor.ci_tutor, "padre o tutor"),
}

# Acciones que el CU01 y el CU02 registran en la bitácora
ACCION_SOLICITUD = "Solicitud de recuperación de contraseña"
ACCION_RESTABLECIDA = "Contraseña restablecida por el administrador"
ACCION_CAMBIO_PROPIO = "Cambio de contraseña por el propio usuario"

# Matriz de permisos por rol: lo que ve el CU03. Es la que aplican los
# routers de cada paquete con requiere_rol(...).
A, P, E, T = ROLES
MATRIZ_PERMISOS = [
    ("seguridad", "CU01", "Iniciar sesión (incluye recuperar contraseña)", (A, P, E, T)),
    ("seguridad", "CU02", "Gestionar usuarios", (A,)),
    ("seguridad", "CU03", "Gestionar roles y permisos", (A,)),
    ("seguridad", "CU04", "Consultar bitácora de actividades", (A,)),
    ("personas", "CU05", "Registrar y actualizar datos de persona", (A,)),
    ("personas", "CU06", "Registrar y gestionar estudiante", (A,)),
    ("personas", "CU07", "Registrar antecedentes médicos y seguimiento", (A, P)),
    ("personas", "CU08", "Registrar tutor y asociarlo a estudiante", (A,)),
    ("personas", "CU09", "Consultar estudiantes/tutores relacionados", (A, P, E, T)),
    ("personas", "CU10", "Registrar docente", (A,)),
    ("personas", "CU11", "Registrar personal administrativo", (A,)),
    ("academico", "CU12", "Gestionar niveles educativos y cursos", (A,)),
    ("academico", "CU13", "Gestionar materias y asignarlas a cursos", (A,)),
    ("academico", "CU14", "Asignar profesor a materia/curso", (A,)),
    ("academico", "CU15", "Gestionar gestión académica", (A,)),
    ("academico", "CU16", "Inscribir estudiante", (A,)),
    ("academico", "CU17", "Consultar historial de inscripciones", (A, E, T)),
    ("horarios", "CU18", "Gestionar aulas", (A,)),
    ("horarios", "CU19", "Generar horario de clases", (A,)),
    ("horarios", "CU20", "Consultar horarios", (A, P, E, T)),
    ("evaluacion", "CU21", "Registrar asistencia", (A, P)),
    ("evaluacion", "CU22", "Consultar historial de asistencia", (A, P, E, T)),
    ("evaluacion", "CU23", "Registrar calificaciones", (A, P, E)),
    ("evaluacion", "CU24", "Generar y consultar boletín/libreta", (A, E, T)),
    ("administracion", "CU25", "Registrar pago de mensualidad", (A, E, T)),
    ("administracion", "CU26", "Gestionar inventario", (A,)),
    ("administracion", "CU27", "Gestionar comunicados y citaciones", (A, P, E, T)),
]


async def validar_especializacion(sesion: AsyncSession, ci_persona: str, nombre_rol: str) -> None:
    """El rol debe coincidir con la especialización de la persona (administrador ↔ administrativo, etc.)."""
    if nombre_rol not in ESPECIALIZACION:
        raise ErrorNegocio("Rol no válido.")
    _, columna, legible = ESPECIALIZACION[nombre_rol]
    if not await sesion.scalar(select(exists().where(columna == ci_persona))):
        raise ErrorNegocio(f"Para el rol {nombre_rol} la persona debe estar registrada como {legible}.")


def validar_no_es_uno_mismo(id_usuario: int, id_admin: int, accion: str) -> None:
    if id_usuario == id_admin:
        raise ErrorNegocio(f"No puede {accion} su propia cuenta.")

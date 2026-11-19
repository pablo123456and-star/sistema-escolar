"""
Consultas que el asistente puede hacer (CU28): SOLO rutas GET de la propia API.

El asistente no lee la base de datos directamente: llama a estas rutas con el token del usuario que
pregunta, así que se aplican exactamente los mismos permisos que en las pantallas (un estudiante no
ve las notas de otro, un docente solo ve a los estudiantes de sus clases, un tutor solo a sus hijos;
si no le corresponde, la API responde 403 y el asistente lo explica).
Cada entrada: (ruta con {parametros}, parámetros de consulta (con * los obligatorios), para qué sirve).
"""
import re

CATALOGO: list[tuple[str, str, str]] = [
    # --- general ---------------------------------------------------------------------------------
    ("/seguridad/perfil", "", "Datos del usuario que pregunta (nombre, rol, CI)."),
    ("/seguridad/inicio", "", "Panel de inicio del usuario: resumen de lo más importante según su rol."),
    ("/academico/gestiones", "", "Gestiones (años lectivos) y cuál está abierta."),
    ("/academico/gestiones/{id_gestion}/periodos", "", "Trimestres de una gestión con sus fechas y estado."),
    ("/academico/gestiones/{id_gestion}/resumen", "", "Resumen de una gestión: inscritos, cursos, etc. (administrador)."),
    ("/academico/estructura", "", "Niveles, grados y paralelos con sus inscritos (administrador)."),
    # --- horarios --------------------------------------------------------------------------------
    ("/horarios/consulta/opciones", "", "Cursos y docentes cuyo horario puede consultar el usuario (da los id_curso y CI)."),
    ("/horarios/consulta", "id_curso, ci_profesor", "Horario semanal de un curso o de un docente."),
    ("/horarios/aulas", "", "Aulas con su capacidad, estado y clases asignadas (administrador)."),
    # --- personas --------------------------------------------------------------------------------
    ("/personas/estudiantes", "q, estado, pagina, tamano", "Buscar estudiantes por nombre o CI (administrador)."),
    ("/personas/estudiantes/{ci}", "", "Ficha de un estudiante con sus tutores e inscripción (administrador)."),
    ("/personas/tutores", "q, estado, pagina, tamano", "Buscar tutores (administrador)."),
    ("/personas/tutores/{ci}", "", "Tutor con sus estudiantes (administrador)."),
    ("/personas/docentes", "q, estado, pagina, tamano", "Buscar docentes (administrador)."),
    ("/personas/docentes/{ci}", "", "Docente con sus materias asignadas (administrador)."),
    ("/personas/seguimiento/estudiantes", "q, pagina, tamano",
     "Estudiantes cuyo seguimiento puede ver el usuario (docente: sus estudiantes; tutor: sus hijos)."),
    ("/personas/seguimiento/estudiantes/{ci}", "", "Antecedentes médicos y anotaciones de seguimiento de un estudiante."),
    # --- académico -------------------------------------------------------------------------------
    ("/academico/materias", "q, pagina, tamano", "Materias registradas."),
    ("/academico/niveles-grados", "", "Niveles educativos y grados."),
    ("/academico/grados/{id_grado}/materias", "", "Plan de estudios (materias) de un grado."),
    ("/academico/asignaciones/opciones", "", "Cursos, profesores y aulas de la gestión abierta (administrador)."),
    ("/academico/cursos/{id_curso}/asignaciones", "", "Materias de un curso y qué docente dicta cada una."),
    ("/academico/inscripciones/historial/estudiantes", "buscar", "Estudiantes cuyo historial de inscripciones puede ver el usuario."),
    ("/academico/inscripciones/historial/{ci}", "", "Historial de inscripciones (gestiones y cursos) de un estudiante."),
    # --- evaluación ------------------------------------------------------------------------------
    ("/evaluacion/asistencia/clases", "", "Clases (materia y curso) del docente conectado, con su id_asignacion."),
    ("/evaluacion/asistencia/{id_asignacion}", "fecha", "Lista de asistencia de una clase en una fecha (AAAA-MM-DD; hoy por defecto)."),
    ("/evaluacion/asistencia/historial/estudiantes", "", "Estudiantes cuyo historial de asistencia puede ver el usuario."),
    ("/evaluacion/asistencia/historial/{ci_estudiante}", "id_gestion, desde, hasta, id_materia",
     "Historial de asistencia de un estudiante con faltas, atrasos y porcentaje por materia."),
    ("/evaluacion/calificaciones/clases", "", "Clases del docente con sus trimestres (id_periodo) y dimensiones."),
    ("/evaluacion/calificaciones/planilla/{id_asignacion}", "id_periodo*",
     "Notas de todos los estudiantes de una clase en un trimestre (docente de esa clase o administrador)."),
    ("/evaluacion/calificaciones/mias", "id_periodo", "Notas del estudiante conectado en un trimestre (solo estudiantes)."),
    ("/evaluacion/boletines/opciones/periodos", "", "Trimestres de todas las gestiones, con su id_periodo."),
    ("/evaluacion/boletines/opciones/cursos", "", "Cursos para boletines y centralizador."),
    ("/evaluacion/boletines/opciones/estudiantes", "id_periodo*, id_curso", "Estudiantes cuyo boletín puede ver el usuario en un trimestre."),
    ("/evaluacion/boletines/{ci_estudiante}", "id_periodo*", "Boletín de un estudiante en un trimestre: notas por materia y promedio."),
    ("/evaluacion/centralizador", "id_curso*, id_periodo*", "Centralizador de notas de un curso en un trimestre."),
    # --- administración --------------------------------------------------------------------------
    ("/administracion/mis-cuotas", "", "Cuotas del estudiante conectado o de los hijos del tutor (pagadas, pendientes, atrasadas)."),
    ("/administracion/cuotas", "ci_estudiante*", "Estado de cuenta de un estudiante (administrador)."),
    ("/administracion/pagos/estudiantes", "buscar", "Buscar estudiantes con sus cuotas pendientes (administrador)."),
    ("/administracion/morosos", "", "Estudiantes con cuotas atrasadas (administrador)."),
    ("/administracion/aranceles", "", "Mensualidad por nivel en la gestión abierta (administrador)."),
    ("/administracion/becas", "", "Becas de la gestión abierta (administrador)."),
    ("/administracion/inventario", "buscar, estado", "Bienes del inventario con su stock; estado: sin_stock, bajo o normal (administrador)."),
    ("/administracion/inventario/{id_inventario}/movimientos", "", "Entradas y salidas de un bien (administrador)."),
    ("/administracion/comunicados", "tipo", "Comunicados y citaciones que ve el usuario, con si los leyó; tipo: general o citacion."),
    ("/administracion/comunicados/{id_comunicado}", "", "Detalle de un comunicado."),
    ("/administracion/comunicados/{id_comunicado}/lecturas", "", "Quién leyó un comunicado y quién no (autor o administrador)."),
    # --- seguridad y reportes (administrador) ----------------------------------------------------
    ("/seguridad/usuarios", "q, estado, pagina, tamano", "Cuentas de usuario del sistema (administrador)."),
    ("/seguridad/bitacora", "desde, hasta, modulo, texto, pagina, tamano", "Bitácora de actividades (administrador)."),
    ("/reportes/estaticos", "", "Catálogo de reportes fijos disponibles (administrador)."),
    ("/reportes/estaticos/{clave}", "id_gestion, id_curso, id_periodo", "Datos de un reporte fijo (administrador)."),
]


def _regex(ruta: str) -> re.Pattern:
    return re.compile("^" + re.sub(r"\{[a-z_]+\}", r"[A-Za-z0-9_.\\-]+", ruta) + "$")


_PERMITIDAS = [_regex(r) for r, _, _ in CATALOGO]


def ruta_permitida(ruta: str) -> bool:
    return ".." not in ruta and any(p.match(ruta) for p in _PERMITIDAS)


def descripcion(rol: str) -> str:
    """Catálogo en texto para el modelo: solo las rutas que el rol puede usar (ahorra tokens)."""
    lineas = []
    for ruta, params, para_que in CATALOGO:
        solo_admin = para_que.endswith("(administrador).")
        if solo_admin and rol != "administrador":
            continue
        texto = para_que.removesuffix(" (administrador).").rstrip(".")
        lineas.append(f"{ruta}{' ?' + params if params else ''}: {texto}")
    return "\n".join(lineas)

"""
CU17 - Consultar historial de inscripciones
Paquete: academico

Actores ........: Tutor, Estudiante, Administrador
Rol del sistema : tutor, estudiante, administrador
Tablas .........: inscripcion, gestion, estudiante, persona
Usa de la BD ...: Vistas v_curso y v_nota_final

Reglas de negocio que implementa este caso de uso (backend):
    - Administrador: consulta a cualquiera.
    - Tutor: solo a sus tutelados (tutor_estudiante) -> 403 si es ajeno.
    - Estudiante: solo su propio CI -> 403 si es ajeno.
    - Otros roles (profesor, etc.): 403.
    - Si el estudiante no existe en la BD -> 404 (validado para roles con permiso).
    - Por gestión: curso, estado, fecha_inscripcion, retiro (fecha y motivo),
      resultado final y promedio anual (calculado con AVG(nota_final) de v_nota_final).
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import NoEncontrado, SinPermiso
from app.paquetes.academico import repository as repo
from app.paquetes.academico.schemas import (
    EstudianteHistorialItem,
    HistorialEstudianteSalida,
    HistorialInscripcionItem,
)


def _verificar_acceso_estudiante(usuario: UsuarioActual, ci_estudiante: str):
    """Valida los permisos a nivel de rol antes de operar."""
    if usuario.rol not in ("administrador", "tutor", "estudiante"):
        raise SinPermiso("No tiene permiso para consultar el historial de inscripciones.")
    if usuario.rol == "estudiante" and usuario.ci != ci_estudiante:
        raise SinPermiso("Solo puede consultar su propio historial de inscripciones.")


async def listar_estudiantes_permitidos(
    sesion: AsyncSession, usuario: UsuarioActual, buscar: str | None = None
) -> list[EstudianteHistorialItem]:
    """Retorna la lista de estudiantes que el usuario en sesión puede consultar."""
    if usuario.rol not in ("administrador", "tutor", "estudiante"):
        raise SinPermiso("No tiene permiso para consultar estudiantes.")

    filas = await repo.listar_estudiantes_visibles_cu17(
        sesion, rol=usuario.rol, ci_usuario=usuario.ci, buscar=buscar
    )
    return [
        EstudianteHistorialItem(
            ci=f.ci,
            nombre_completo=f.nombre_completo,
            nombre_persona=f.nombre_persona,
            apellidos=f.apellidos,
            codigo_rude=f.codigo_rude,
            curso_actual=f.curso_actual,
        )
        for f in filas
    ]


async def consultar_historial(
    sesion: AsyncSession, usuario: UsuarioActual, ci_estudiante: str
) -> HistorialEstudianteSalida:
    """Consulta el historial académico/inscripciones de un estudiante."""
    ci = ci_estudiante.strip()
    _verificar_acceso_estudiante(usuario, ci)

    if usuario.rol == "tutor":
        es_suyo = await repo.es_hijo_de_tutor_cu17(sesion, usuario.ci, ci)
        if not es_suyo:
            raise SinPermiso("Este estudiante no está registrado a su cargo.")

    # Verificar si existe el estudiante
    estudiante = await repo.obtener_estudiante_cu17(sesion, ci)
    if not estudiante:
        raise NoEncontrado(f"No existe ningún estudiante registrado con CI '{ci}'.")

    filas_historial = await repo.historial_inscripciones_cu17(sesion, ci)

    inscripciones = [
        HistorialInscripcionItem(
            id_inscripcion=f.id_inscripcion,
            id_gestion=f.id_gestion,
            anio=f.anio,
            curso=f.curso,
            estado_inscripcion=f.estado_inscripcion,
            fecha_inscripcion=f.fecha_inscripcion,
            fecha_retiro=f.fecha_retiro,
            motivo_retiro=f.motivo_retiro,
            resultado_final=f.resultado_final,
            promedio_anual=f.promedio_anual,
        )
        for f in filas_historial
    ]

    return HistorialEstudianteSalida(
        ci=estudiante.ci,
        nombre_completo=f"{estudiante.apellidos} {estudiante.nombre_persona}",
        codigo_rude=estudiante.codigo_rude,
        inscripciones=inscripciones,
    )

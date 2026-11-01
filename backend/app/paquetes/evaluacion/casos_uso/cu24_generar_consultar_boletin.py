"""
CU24 - Generar y consultar boletín/libreta (incluye centralizador)
Paquete: evaluacion

Actores ........: Tutor, Estudiante (genera: Administrativo)
Rol del sistema : tutor, estudiante, administrador
Tablas .........: boletin, libreta, calificacion
Usa de la BD ...: Procedimiento sp_emitir_boletines, vista v_nota_final

Reglas de negocio que implementa este caso de uso (backend):
    - Emitir boletines: solo administrador (CALL sp_emitir_boletines), de todo el periodo o de un curso.
      La cantidad informada es la que devuelve el procedimiento (INOUT p_boletines). Se puede emitir
      un trimestre abierto (decisión del grupo) y reemitir actualiza el promedio y la fecha.
    - Consultar: estudiante el suyo; tutor sus estudiantes; administrador todos. Se verifica el permiso
      antes de buscar el boletín. Se pueden consultar boletines de gestiones anteriores.
    - Centralizador: notas de todo un curso en un periodo; columnas = todas las materias del curso
      (asignadas o con notas), con promedio por estudiante.
    - El boletín se imprime desde el navegador (no se guarda un PDF).

Precondición:
    El estudiante tiene calificaciones en el periodo. Tutor y estudiante solo consultan lo suyo.

Postcondición:
    El boletín queda emitido con su promedio y disponible para consulta e impresión.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import NoEncontrado, SinPermiso
from app.paquetes.evaluacion import repository as repo
from app.paquetes.evaluacion.schemas import (
    BoletinSalida,
    CentralizadorSalida,
    CursoOpcionCU24,
    EmitirBoletinesSalida,
    EstudianteOpcionCU24,
    MateriaColumnaCU24,
    PeriodoOpcionCU24,
)


async def emitir_boletines(sesion: AsyncSession, usuario: UsuarioActual, id_periodo: int, id_curso: int | None) -> EmitirBoletinesSalida:
    """Emite (o reemite) boletines de un periodo. Solo administrador."""
    if usuario.rol != "administrador":
        raise SinPermiso("Solo el administrador puede emitir boletines.")

    periodo = await repo.periodo_cu24(sesion, id_periodo)
    if not periodo:
        raise NoEncontrado("No existe ese periodo.")
    if id_curso is not None and not await repo.curso_cu24(sesion, id_curso):
        raise NoEncontrado("No existe ese curso.")

    cantidad = await repo.emitir_boletines_cu24(sesion, id_periodo, id_curso)
    return EmitirBoletinesSalida(
        cantidad=cantidad,
        periodo=periodo.nombre_periodo,
        fecha_emision=await repo.hoy(sesion),
    )


async def consultar_boletin(sesion: AsyncSession, usuario: UsuarioActual, ci_estudiante: str, id_periodo: int) -> BoletinSalida:
    """Consulta el boletín de un estudiante en un periodo. Valida permisos."""
    ci_estudiante = ci_estudiante.strip()

    # Primero el permiso (así no se revela si existe el boletín de alguien ajeno)
    if usuario.rol == "estudiante" and ci_estudiante != usuario.ci:
        raise SinPermiso("Solo puede consultar su propio boletín.")
    if usuario.rol == "tutor" and not await repo.es_mi_estudiante_cu24(sesion, usuario.ci, ci_estudiante):
        raise SinPermiso("Este estudiante no está a su cargo.")
    if usuario.rol not in ("administrador", "tutor", "estudiante"):
        raise SinPermiso("Su rol no puede consultar boletines.")

    boletin = await repo.boletin_cu24(sesion, ci_estudiante, id_periodo)
    if not boletin:
        raise NoEncontrado("El boletín de este periodo aún no ha sido emitido.")
    return boletin


async def periodos(sesion: AsyncSession) -> list[PeriodoOpcionCU24]:
    """Periodos de todas las gestiones (la más reciente primero) para las listas desplegables."""
    return [PeriodoOpcionCU24.model_validate(r, from_attributes=True) for r in await repo.periodos_cu24(sesion)]


async def estudiantes(sesion: AsyncSession, usuario: UsuarioActual, id_periodo: int,
                      id_curso: int | None) -> list[EstudianteOpcionCU24]:
    """Estudiantes que el usuario puede consultar en la gestión de ese periodo."""
    if usuario.rol not in ("administrador", "tutor", "estudiante"):
        raise SinPermiso("Su rol no puede consultar boletines.")
    if not await repo.periodo_cu24(sesion, id_periodo):
        raise NoEncontrado("No existe ese periodo.")
    filas = await repo.estudiantes_cu24(sesion, id_periodo, usuario.rol, usuario.ci, id_curso)
    return [EstudianteOpcionCU24.model_validate(f, from_attributes=True) for f in filas]


async def cursos(sesion: AsyncSession) -> list[CursoOpcionCU24]:
    """Retorna todos los cursos con su información para las listas desplegables."""
    result = await repo.cursos_cu24(sesion)
    return [CursoOpcionCU24(id_curso=r[0], nombre_curso=r[1]) for r in result]


async def centralizador(sesion: AsyncSession, usuario: UsuarioActual, id_curso: int, id_periodo: int) -> CentralizadorSalida:
    """Genera el centralizador de un curso en un periodo. Solo administrador."""
    if usuario.rol != "administrador":
        raise SinPermiso("Solo el administrador puede consultar el centralizador.")

    curso = await repo.curso_cu24(sesion, id_curso)
    if not curso:
        raise NoEncontrado("No existe ese curso.")

    periodo = await repo.periodo_cu24(sesion, id_periodo)
    if not periodo:
        raise NoEncontrado("No existe ese periodo.")

    materias = await repo.materias_centralizador_cu24(sesion, id_curso, id_periodo)
    filas_raw = await repo.centralizador_cu24(sesion, id_curso, id_periodo)
    if not filas_raw or len(filas_raw) == 0:
        raise NoEncontrado("No hay estudiantes inscritos o no hay notas registradas para ese curso y periodo.")

    filas = [
        {
            "ci": f[0],
            "nombre_persona": f[1],
            "apellidos": f[2],
            "notas": f[3] or [],
            "promedio_estudiante": f[4],
        }
        for f in filas_raw
    ]

    return CentralizadorSalida(
        curso=curso.nombre_curso,
        periodo=periodo.nombre_periodo,
        anio=periodo.anio,
        nota_minima=float(periodo.nota_minima_aprobacion),
        materias=[MateriaColumnaCU24(id_materia=m.id_materia, materia=m.materia) for m in materias],
        filas=filas,
    )

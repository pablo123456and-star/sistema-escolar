"""
CU24 - Generar y consultar boletín/libreta (incluye centralizador)
Paquete: evaluacion

Actores ........: Tutor, Estudiante (genera: Administrativo)
Rol del sistema : tutor, estudiante, administrador
Tablas .........: boletin, libreta, calificacion
Usa de la BD ...: Procedimiento sp_emitir_boletines, vista v_nota_final

Reglas de negocio que implementa este caso de uso (backend):
    - Emitir boletines: solo administrador (CALL sp_emitir_boletines).
    - Consultar: estudiante el suyo; tutor sus estudiantes; administrador todos.
    - Centralizador: notas de todo un curso en un periodo, por materia, con promedio.
    - Libreta: guardar la ruta/URL del PDF (dónde se almacena se decide al implementar).

Precondición:
    El estudiante tiene calificaciones en el periodo. Tutor y estudiante solo consultan lo suyo.

Postcondición:
    El boletín queda emitido con su promedio; la libreta queda disponible para consulta.

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
    PeriodoOpcionCU24,
)


async def emitir_boletines(sesion: AsyncSession, usuario: UsuarioActual, id_periodo: int, id_curso: int | None) -> EmitirBoletinesSalida:
    """Emite (o reemite) boletines de un periodo. Solo administrador."""
    if usuario.rol != "administrador":
        raise SinPermiso("Solo el administrador puede emitir boletines.")

    periodo = await repo.periodo_cu24(sesion, id_periodo)
    if not periodo:
        raise NoEncontrado("No existe ese periodo.")

    cantidad = await repo.emitir_boletines_cu24(sesion, id_periodo, id_curso)
    return EmitirBoletinesSalida(
        cantidad=cantidad,
        periodo=periodo.nombre_periodo,
        fecha_emision=await repo.hoy(sesion),
    )


async def consultar_boletin(sesion: AsyncSession, usuario: UsuarioActual, ci_estudiante: str, id_periodo: int) -> BoletinSalida:
    """Consulta el boletín de un estudiante en un periodo. Valida permisos."""
    ci_estudiante = ci_estudiante.strip()

    # Validar que el boletín existe
    boletin = await repo.boletin_cu24(sesion, ci_estudiante, id_periodo)
    if not boletin:
        raise NoEncontrado("El boletín de este periodo aún no ha sido emitido.")

    # Validar permisos: estudiante (suyo), tutor (sus estudiantes), administrador (todos)
    if usuario.rol == "estudiante" and ci_estudiante != usuario.ci:
        raise SinPermiso("Solo puede consultar su propio boletín.")
    elif usuario.rol == "tutor":
        es_mi_estudiante = await repo.es_mi_estudiante_cu24(sesion, usuario.ci, ci_estudiante)
        if not es_mi_estudiante:
            raise SinPermiso("Este estudiante no está a su cargo.")
    elif usuario.rol not in ("administrador", "tutor", "estudiante"):
        raise SinPermiso("Su rol no puede consultar boletines.")

    return boletin


async def periodos(sesion: AsyncSession) -> list[PeriodoOpcionCU24]:
    """Retorna los períodos de la gestión actual/vigente para las listas desplegables."""
    result = await repo.periodos_cu24(sesion)
    return [PeriodoOpcionCU24(id_periodo=r[0], nombre_periodo=r[1]) for r in result]


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
        filas=filas,
    )

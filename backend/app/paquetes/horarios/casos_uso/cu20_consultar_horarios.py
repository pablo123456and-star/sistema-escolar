"""
CU20 - Consultar horarios
Paquete: horarios

Actores ........: Docente, Estudiante, Tutor, Administrativo
Rol del sistema : profesor, estudiante, tutor, administrador
Tablas .........: horario (vía v_horario), asignacion_profesor_clase, inscripcion, tutor_estudiante
Usa de la BD ...: Vistas v_horario y v_curso

Reglas de negocio que implementa este caso de uso (backend):
    - Cualquier usuario con sesión, pero solo ve lo que su rol permite (el rol viene de la BD):
        - administrador: cualquier curso o cualquier docente.
        - profesor: su propio horario y el de los cursos donde dicta.
        - estudiante: el horario de su curso (inscripción activa en la gestión abierta).
        - tutor: el horario del curso de cada uno de sus estudiantes (tutor_estudiante).
    - Si pide un horario que su rol no permite: error de permiso (403).
    - Horario semanal por curso o por docente de la gestión abierta, ordenado por día y hora.

Precondición:
    Sesión iniciada.

Postcondición:
    Se muestra el horario semanal del curso o del profesor. No se modifica nada.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import ErrorNegocio, NoEncontrado
from app.paquetes.academico.politicas import gestion_abierta
from app.paquetes.horarios import politicas
from app.paquetes.horarios import repository as repo
from app.paquetes.horarios.schemas import (
    CursoOpcionConsulta, DocenteOpcionConsulta, EstudianteOpcionConsulta, HorarioConsultaSalida, HorarioSalida,
    OpcionesConsultaSalida,
)


async def opciones(sesion: AsyncSession, usuario: UsuarioActual) -> OpcionesConsultaSalida:
    """Cursos, docentes o estudiantes que el usuario puede elegir según su rol."""
    gestion = await gestion_abierta(sesion)
    salida = OpcionesConsultaSalida(rol=usuario.rol, gestion=gestion.anio if gestion else None,
                                    cursos=[], docentes=[], estudiantes=[])
    if gestion is None:
        return salida
    g = gestion.id_gestion

    def curso(c) -> CursoOpcionConsulta:
        return CursoOpcionConsulta(id_curso=c.id_curso, nombre_curso=c.nombre_curso)

    if usuario.rol == "administrador":
        salida.cursos = [curso(c) for c in await repo.cursos_de_la_gestion(sesion, g)]
        salida.docentes = [DocenteOpcionConsulta.model_validate(d._asdict())
                           for d in await repo.docentes_de_la_gestion(sesion, g)]
    elif usuario.rol == "profesor":
        salida.cursos = [curso(c) for c in await repo.cursos_del_profesor(sesion, usuario.ci, g)]
        salida.docentes = [DocenteOpcionConsulta(ci=usuario.ci, nombre=await repo.nombre_persona(sesion, usuario.ci))]
    elif usuario.rol == "estudiante":
        propio = await repo.curso_del_estudiante(sesion, usuario.ci, g)
        salida.cursos = [curso(propio)] if propio else []
    elif usuario.rol == "tutor":
        salida.estudiantes = [EstudianteOpcionConsulta.model_validate(e._asdict())
                              for e in await repo.estudiantes_del_tutor(sesion, usuario.ci, g)]
    return salida


async def consultar(sesion: AsyncSession, usuario: UsuarioActual, *, id_curso: int | None,
                    ci_profesor: str | None) -> HorarioConsultaSalida:
    if (id_curso is None) == (ci_profesor is None):
        raise ErrorNegocio("Indique un curso o un docente.")
    gestion = await politicas.exigir_gestion_abierta(sesion)

    if id_curso is not None:
        await politicas.puede_ver_curso(sesion, usuario, id_curso, gestion)
        titulo = await repo.nombre_curso(sesion, id_curso)
        if titulo is None:
            raise NoEncontrado("Curso no encontrado.")
        bloques, tipo = await repo.bloques_del_curso(sesion, id_curso, gestion.id_gestion), "curso"
    else:
        politicas.puede_ver_profesor(usuario, ci_profesor)
        titulo = await repo.nombre_persona(sesion, ci_profesor)
        if titulo is None:
            raise NoEncontrado("Docente no encontrado.")
        bloques, tipo = await repo.bloques_del_profesor(sesion, ci_profesor, gestion.id_gestion), "docente"

    return HorarioConsultaSalida(
        tipo=tipo, titulo=titulo, gestion=gestion.anio,
        bloques=[HorarioSalida.model_validate(b._asdict()) for b in bloques],
    )

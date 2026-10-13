"""
CU16 - Inscribir estudiante en gestión académica
Paquete: academico

Actores ........: Administrativo (Secretaría)
Rol del sistema : administrador
Tablas .........: inscripcion, curso, gestion, persona, estudiante, pago_mensualidad,
                  materia_grado, materia, asignacion_profesor_clase, aula
Usa de la BD ...: Trigger de auditoría de inscripción; vistas v_curso y v_horario

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Buscar al estudiante por CI, RUDE o nombre.
    - Inscribir con politicas.inscribir (la misma que usa el CU06):
        - La gestión debe estar 'abierta' y el estudiante 'activo'.
        - Cupo: inscripciones activas del curso en la gestión < cupo_maximo.
        - Sin cuotas vencidas ('pendiente' y vencidas) de gestiones anteriores.
        - Una inscripción por estudiante y gestión (lo asegura la BD).
        - Fecha de inscripción = hoy (la pone la BD).
    - Boleta: datos del estudiante, gestión, curso, materias del plan con su docente y aula,
      y horario semanal del curso (v_horario). Se puede volver a emitir.

Precondición:
    El estudiante está activo, sin cuotas vencidas previas y no inscrito en esa gestión; la gestión está abierta y el curso tiene cupo.

Postcondición:
    La inscripción queda activa y se emite la boleta de inscripción.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.errores import NoEncontrado
from app.nucleo.esquemas import Pagina
from app.paquetes.academico import politicas
from app.paquetes.academico import repository as repo
from app.paquetes.academico.schemas import (
    BloqueBoletaSalida, BoletaSalida, EstudianteInscripcionSalida, InscripcionCrear, MateriaBoletaSalida,
)


async def buscar_estudiantes(sesion: AsyncSession, *, q: str | None, pagina: int,
                             tamano: int) -> Pagina[EstudianteInscripcionSalida]:
    filas, total = await repo.buscar_estudiantes_cu16(sesion, q=q, pagina=pagina, tamano=tamano)
    return Pagina[EstudianteInscripcionSalida](
        items=[EstudianteInscripcionSalida.model_validate(f._asdict()) for f in filas],
        total=total, pagina=pagina, tamano=tamano,
    )


async def emitir_boleta(sesion: AsyncSession, id_inscripcion: int) -> BoletaSalida:
    datos = await repo.datos_boleta_cu16(sesion, id_inscripcion)
    if datos is None:
        raise NoEncontrado("No existe esa inscripción.")
    datos = datos._asdict()
    id_curso, id_gestion = datos.pop("id_curso"), datos.pop("id_gestion")
    return BoletaSalida(
        **datos,
        materias=[MateriaBoletaSalida.model_validate(m._asdict())
                  for m in await repo.materias_boleta_cu16(sesion, id_curso, id_gestion)],
        horario=[BloqueBoletaSalida.model_validate(b._asdict())
                 for b in await repo.horario_boleta_cu16(sesion, id_curso, id_gestion)],
    )


async def inscribir(sesion: AsyncSession, datos: InscripcionCrear) -> BoletaSalida:
    inscripcion = await politicas.inscribir(sesion, datos.ci_estudiante, datos.id_curso)
    return await emitir_boleta(sesion, inscripcion.id_inscripcion)

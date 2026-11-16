"""
CU27 - Gestionar comunicados y citaciones
Paquete: administracion

Actores ........: Administrativo, Docente (publican); Tutor, Estudiante (leen)
Rol del sistema : administrador, profesor, tutor, estudiante
Tablas .........: comunicado, comunicado_lectura
Usa de la BD ...: CHECK de comunicado (destinatario según alcance; citación = estudiante + fecha),
                  PK de comunicado_lectura (una lectura por persona)

Reglas de negocio que implementa este caso de uso (backend):
    - Administrador: publica a todos, a un curso o a un estudiante.
    - Profesor: solo a los cursos donde enseña o a sus estudiantes; nunca a 'todos'.
    - Citación: dirigida a un estudiante (sus tutores) y con fecha (lo asegura la BD);
      la fecha de la citación debe ser futura.
    - El comunicado se publica en la gestión abierta; el autor es el usuario conectado.
    - Cada usuario ve solo los comunicados dirigidos a él:
        'todos'      -> toda la comunidad
        'curso'      -> los estudiantes inscritos en el curso y sus tutores
        'estudiante' -> el estudiante y sus tutores (una citación, solo sus tutores)
      El administrador ve todos; el profesor además ve los suyos y los de los cursos donde enseña.
    - Marcar como leído: solo un destinatario, una vez por persona (lo asegura la BD);
      marcarlo otra vez no cambia la primera fecha de lectura.
    - Registro de lectura (quién lo leyó y quién no) y eliminar: solo el autor o el administrador.

Precondición:
    Un docente solo publica a sus cursos o a sus estudiantes.

Postcondición:
    El comunicado queda visible para sus destinatarios y se registra quién lo leyó.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import ErrorNegocio, NoEncontrado
from app.nucleo.esquemas import Mensaje
from app.paquetes.academico.politicas import gestion_abierta
from app.paquetes.administracion import politicas
from app.paquetes.administracion import repository as repo
from app.paquetes.administracion.models import Comunicado
from app.paquetes.administracion.schemas import (
    BandejaSalida, ComunicadoCrear, ComunicadoSalida, CursoDestinoSalida, DestinosSalida,
    EstudianteDestinoSalida, LecturasSalida, LectorSalida,
)


def _salida(usuario: UsuarioActual, fila) -> ComunicadoSalida:
    datos = fila._asdict()
    # El conteo de lecturas es información del autor y del administrador
    if usuario.rol != "administrador" and not datos["es_mio"]:
        datos["lecturas"] = None
    return ComunicadoSalida.model_validate(datos)


async def _comunicado_visible(sesion: AsyncSession, usuario: UsuarioActual, id_comunicado: int):
    """El comunicado, si el usuario puede verlo (si no existe o no le corresponde: 404)."""
    filas = await repo.comunicados_cu27(sesion, usuario.rol, usuario.ci, id_comunicado)
    if not filas:
        raise NoEncontrado("No existe ese comunicado o no está dirigido a usted.")
    return filas[0]


# ------------------------------------------------------------
# 1. BANDEJA: los comunicados que ve el usuario
# ------------------------------------------------------------

async def bandeja(sesion: AsyncSession, usuario: UsuarioActual, tipo: str | None = None) -> BandejaSalida:
    filas = await repo.comunicados_cu27(sesion, usuario.rol, usuario.ci)
    if tipo:
        filas = [f for f in filas if f.tipo_comunicado == tipo]
    return BandejaSalida(
        comunicados=[_salida(usuario, f) for f in filas],
        no_leidos=sum(1 for f in filas if f.es_destinatario and f.leido_en is None),
    )


async def detalle(sesion: AsyncSession, usuario: UsuarioActual, id_comunicado: int) -> ComunicadoSalida:
    return _salida(usuario, await _comunicado_visible(sesion, usuario, id_comunicado))


# ------------------------------------------------------------
# 2. PUBLICAR
# ------------------------------------------------------------

async def destinos(sesion: AsyncSession, usuario: UsuarioActual) -> DestinosSalida:
    """Cursos y estudiantes a los que el usuario puede publicar en la gestión abierta."""
    gestion = await gestion_abierta(sesion)
    if gestion is None:
        return DestinosSalida(gestion=None, puede_todos=False, cursos=[], estudiantes=[])
    profesor = usuario.ci if usuario.rol == "profesor" else None
    cursos = await repo.cursos_destino_cu27(sesion, gestion.id_gestion, profesor)
    estudiantes = await repo.estudiantes_destino_cu27(sesion, gestion.id_gestion, profesor)
    return DestinosSalida(
        gestion=gestion.anio,
        puede_todos=usuario.rol == "administrador",
        cursos=[CursoDestinoSalida.model_validate(f._asdict()) for f in cursos],
        estudiantes=[EstudianteDestinoSalida.model_validate(f._asdict()) for f in estudiantes],
    )


async def publicar(sesion: AsyncSession, usuario: UsuarioActual, datos: ComunicadoCrear) -> ComunicadoSalida:
    gestion = await gestion_abierta(sesion)
    if gestion is None:
        raise ErrorNegocio("No hay una gestión abierta: no se pueden publicar comunicados.")
    await politicas.validar_destino(sesion, usuario, datos, gestion.id_gestion)
    if datos.fecha_citacion is not None and datos.fecha_citacion <= datetime.now(timezone.utc):
        raise ErrorNegocio("La fecha de la citación debe ser posterior a la fecha actual.")

    comunicado = Comunicado(
        titulo=datos.titulo, contenido=datos.contenido, tipo_comunicado=datos.tipo_comunicado,
        alcance=datos.alcance, fecha_citacion=datos.fecha_citacion, id_gestion_comunicado=gestion.id_gestion,
        id_curso_comunicado=datos.id_curso, ci_estudiante_comunicado=datos.ci_estudiante, ci_autor=usuario.ci,
    )
    sesion.add(comunicado)
    await sesion.flush()
    return await detalle(sesion, usuario, comunicado.id_comunicado)


# ------------------------------------------------------------
# 3. REGISTRO DE LECTURA
# ------------------------------------------------------------

async def marcar_leido(sesion: AsyncSession, usuario: UsuarioActual, id_comunicado: int) -> ComunicadoSalida:
    comunicado = await _comunicado_visible(sesion, usuario, id_comunicado)
    if not comunicado.es_destinatario:
        raise ErrorNegocio("Solo los destinatarios del comunicado lo marcan como leído.")
    await repo.marcar_leido_cu27(sesion, id_comunicado, usuario.ci)
    return await detalle(sesion, usuario, id_comunicado)


async def lecturas(sesion: AsyncSession, usuario: UsuarioActual, id_comunicado: int) -> LecturasSalida:
    """Quién lo leyó (y cuándo) y quién todavía no: solo para el autor o el administrador."""
    comunicado = await _comunicado_visible(sesion, usuario, id_comunicado)
    politicas.puede_ver_lecturas_o_eliminar(usuario, comunicado)
    filas = await repo.destinatarios_cu27(sesion, id_comunicado)
    lectores = [LectorSalida.model_validate(f._asdict()) for f in filas]
    return LecturasSalida(
        id_comunicado=id_comunicado, titulo=comunicado.titulo, total_destinatarios=len(lectores),
        total_leidos=sum(1 for x in lectores if x.leido_en is not None), destinatarios=lectores,
    )


# ------------------------------------------------------------
# 4. ELIMINAR
# ------------------------------------------------------------

async def eliminar(sesion: AsyncSession, usuario: UsuarioActual, id_comunicado: int) -> Mensaje:
    """El autor o el administrador lo eliminan (sus lecturas se borran en cascada)."""
    fila = await _comunicado_visible(sesion, usuario, id_comunicado)
    politicas.puede_ver_lecturas_o_eliminar(usuario, fila)
    await sesion.delete(await sesion.get(Comunicado, id_comunicado))
    await sesion.flush()
    return Mensaje(mensaje=f"Se eliminó el comunicado «{fila.titulo}».")

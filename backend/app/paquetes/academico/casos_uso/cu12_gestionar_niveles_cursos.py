"""
CU12 - Gestionar niveles educativos y cursos
Paquete: academico

Actores ........: Admin. académico
Rol del sistema : administrador
Tablas .........: nivel_educativo, grado, curso
Usa de la BD ...: Vista v_curso (nombre legible del curso)

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Nombre de nivel único; nombre y orden del grado únicos dentro de su nivel.
    - Paralelo único por grado (se guarda en mayúsculas) y cupo mayor a 0 (lo asegura la BD).
    - El cupo no puede quedar por debajo de los inscritos activos en la gestión abierta.
    - No eliminar lo que está en uso: mostrar mensaje claro.
        - Nivel con grados o aranceles.
        - Grado con paralelos o con plan de estudios (materia_grado se borraría en cascada).
        - Paralelo con inscripciones, asignaciones de profesores o comunicados.

Precondición:
    Sesión iniciada como administrador.

Postcondición:
    El catálogo de niveles, grados y cursos (paralelos y cupos) queda actualizado.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.errores import Conflicto, ErrorNegocio, NoEncontrado
from app.paquetes.academico import politicas
from app.paquetes.academico import repository as repo
from app.paquetes.academico.models import Curso, Grado, NivelEducativo
from app.paquetes.academico.schemas import (
    CursoActualizar, CursoCrear, CursoEstructuraSalida, CursoSalida, EstructuraSalida, GradoActualizar,
    GradoCrear, GradoEstructuraSalida, GradoSalida, NivelEducativoSalida, NivelEntrada, NivelEstructuraSalida,
)


def _en_uso(que: str, partes: list[tuple[int, str]]) -> None:
    """Conflicto con el detalle de lo que depende del registro, si algo depende."""
    usos = [f"{n} {texto}" for n, texto in partes if n]
    if usos:
        raise Conflicto(f"No se puede eliminar {que} porque tiene {' y '.join(usos)}.")


# ------------------------------------------------------------
# 1. CONSULTAR LA ESTRUCTURA COMPLETA
# ------------------------------------------------------------

async def estructura(sesion: AsyncSession) -> EstructuraSalida:
    gestion = await politicas.gestion_abierta(sesion)
    cursos = defaultdict(list)
    for c in await repo.cursos_estructura_cu12(sesion, gestion.id_gestion if gestion else None):
        cursos[c.id_grado].append(
            CursoEstructuraSalida(id_curso=c.id_curso, paralelo=c.paralelo, cupo_maximo=c.cupo_maximo, inscritos=c.inscritos)
        )
    grados = defaultdict(list)
    for g in await repo.grados_estructura_cu12(sesion):
        grados[g.id_nivel].append(
            GradoEstructuraSalida(id_grado=g.id_grado, nombre_grado=g.nombre_grado, orden_grado=g.orden_grado,
                                  materias=g.materias, cursos=cursos[g.id_grado])
        )
    return EstructuraSalida(
        gestion=gestion.anio if gestion else None,
        niveles=[
            NivelEstructuraSalida(id_nivel=n.id_nivel, nombre_nivel=n.nombre_nivel, grados=grados[n.id_nivel])
            for n in await repo.listar_niveles(sesion)
        ],
    )


# ------------------------------------------------------------
# 2. NIVELES EDUCATIVOS
# ------------------------------------------------------------

async def _nivel(sesion: AsyncSession, id_nivel: int) -> NivelEducativo:
    nivel = await sesion.get(NivelEducativo, id_nivel)
    if nivel is None:
        raise NoEncontrado("No existe ese nivel educativo.")
    return nivel


async def registrar_nivel(sesion: AsyncSession, datos: NivelEntrada) -> NivelEducativoSalida:
    if await repo.buscar_nivel_cu12(sesion, datos.nombre_nivel):
        raise Conflicto(f"Ya existe el nivel {datos.nombre_nivel}.")
    nivel = NivelEducativo(nombre_nivel=datos.nombre_nivel)
    sesion.add(nivel)
    await sesion.flush()
    return NivelEducativoSalida.model_validate(nivel)


async def actualizar_nivel(sesion: AsyncSession, id_nivel: int, datos: NivelEntrada) -> NivelEducativoSalida:
    nivel = await _nivel(sesion, id_nivel)
    if await repo.buscar_nivel_cu12(sesion, datos.nombre_nivel, id_excluir=id_nivel):
        raise Conflicto(f"Ya existe otro nivel llamado {datos.nombre_nivel}.")
    nivel.nombre_nivel = datos.nombre_nivel
    await sesion.flush()
    return NivelEducativoSalida.model_validate(nivel)


async def eliminar_nivel(sesion: AsyncSession, id_nivel: int) -> None:
    nivel = await _nivel(sesion, id_nivel)
    uso = await repo.uso_nivel_cu12(sesion, id_nivel)
    _en_uso(f"el nivel {nivel.nombre_nivel}", [(uso.grados, "grado(s)"), (uso.aranceles, "arancel(es) registrados")])
    await sesion.delete(nivel)
    await sesion.flush()


# ------------------------------------------------------------
# 3. GRADOS
# ------------------------------------------------------------

async def _grado(sesion: AsyncSession, id_grado: int) -> Grado:
    grado = await sesion.get(Grado, id_grado)
    if grado is None:
        raise NoEncontrado("No existe ese grado.")
    return grado


async def _validar_grado_unico(sesion: AsyncSession, id_nivel: int, nombre: str | None, orden: int | None,
                               id_excluir: int | None = None) -> None:
    if nombre is not None and await repo.buscar_grado_cu12(sesion, id_nivel, nombre=nombre, id_excluir=id_excluir):
        raise Conflicto(f"El nivel ya tiene un grado llamado {nombre}.")
    if orden is not None:
        otro = await repo.buscar_grado_cu12(sesion, id_nivel, orden=orden, id_excluir=id_excluir)
        if otro:
            raise Conflicto(f"El orden {orden} ya lo usa el grado {otro.nombre_grado} en este nivel.")


async def registrar_grado(sesion: AsyncSession, datos: GradoCrear) -> GradoSalida:
    await _nivel(sesion, datos.id_nivel)
    await _validar_grado_unico(sesion, datos.id_nivel, datos.nombre_grado, datos.orden_grado)
    grado = Grado(nombre_grado=datos.nombre_grado, orden_grado=datos.orden_grado,
                  id_nivel_educativo_grado=datos.id_nivel)
    sesion.add(grado)
    await sesion.flush()
    return GradoSalida.model_validate(grado)


async def actualizar_grado(sesion: AsyncSession, id_grado: int, datos: GradoActualizar) -> GradoSalida:
    grado = await _grado(sesion, id_grado)
    await _validar_grado_unico(sesion, grado.id_nivel_educativo_grado, datos.nombre_grado, datos.orden_grado,
                               id_excluir=id_grado)
    for campo, valor in datos.model_dump(exclude_none=True).items():
        setattr(grado, campo, valor)
    await sesion.flush()
    return GradoSalida.model_validate(grado)


async def eliminar_grado(sesion: AsyncSession, id_grado: int) -> None:
    grado = await _grado(sesion, id_grado)
    uso = await repo.uso_grado_cu12(sesion, id_grado)
    _en_uso(f"el grado {grado.nombre_grado}",
            [(uso.cursos, "paralelo(s)"), (uso.materias, "materia(s) en su plan de estudios")])
    await sesion.delete(grado)
    await sesion.flush()


# ------------------------------------------------------------
# 4. CURSOS (PARALELOS Y CUPOS)
# ------------------------------------------------------------

async def _curso(sesion: AsyncSession, id_curso: int) -> Curso:
    curso = await sesion.get(Curso, id_curso)
    if curso is None:
        raise NoEncontrado("No existe ese curso.")
    return curso


async def registrar_curso(sesion: AsyncSession, datos: CursoCrear) -> CursoSalida:
    grado = await _grado(sesion, datos.id_grado)
    if await repo.buscar_curso_cu12(sesion, datos.id_grado, datos.paralelo):
        raise Conflicto(f"El grado {grado.nombre_grado} ya tiene el paralelo {datos.paralelo}.")
    curso = Curso(paralelo=datos.paralelo, cupo_maximo=datos.cupo_maximo, id_grado_curso=datos.id_grado)
    sesion.add(curso)
    await sesion.flush()
    return CursoSalida.model_validate(curso)


async def actualizar_curso(sesion: AsyncSession, id_curso: int, datos: CursoActualizar) -> CursoSalida:
    curso = await _curso(sesion, id_curso)
    if datos.paralelo is not None and await repo.buscar_curso_cu12(
        sesion, curso.id_grado_curso, datos.paralelo, id_excluir=id_curso
    ):
        raise Conflicto(f"El grado ya tiene el paralelo {datos.paralelo}.")
    if datos.cupo_maximo is not None:
        gestion = await politicas.gestion_abierta(sesion)
        if gestion:
            inscritos = await repo.inscritos_activos_cu12(sesion, id_curso, gestion.id_gestion)
            if datos.cupo_maximo < inscritos:
                raise ErrorNegocio(
                    f"El curso tiene {inscritos} inscritos en la gestión {gestion.anio}: "
                    f"el cupo no puede ser menor a {inscritos}."
                )
    for campo, valor in datos.model_dump(exclude_none=True).items():
        setattr(curso, campo, valor)
    await sesion.flush()
    return CursoSalida.model_validate(curso)


async def eliminar_curso(sesion: AsyncSession, id_curso: int) -> None:
    curso = await _curso(sesion, id_curso)
    uso = await repo.uso_curso_cu12(sesion, id_curso)
    _en_uso(f"el paralelo {curso.paralelo}", [
        (uso.inscripciones, "inscripción(es)"),
        (uso.asignaciones, "profesor(es) asignados"),
        (uso.comunicados, "comunicado(s)"),
    ])
    await sesion.delete(curso)
    await sesion.flush()

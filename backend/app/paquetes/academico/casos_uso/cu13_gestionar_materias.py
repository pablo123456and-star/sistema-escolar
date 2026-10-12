"""
CU13 - Gestionar materias y asignarlas a cursos
Paquete: academico

Actores ........: Admin. académico
Rol del sistema : administrador
Tablas .........: materia, materia_grado
Usa de la BD ...: —

Reglas de negocio que implementa este caso de uso (backend):
    - Solo administrador.
    - Nombre de materia único (lo asegura la BD).
    - Plan de estudios: agregar o quitar una materia de un grado (materia_grado).

Precondición:
    Sesión iniciada como administrador. El grado existe.

Postcondición:
    La materia queda registrada y el plan de estudios del grado actualizado.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: IMPLEMENTADO.
"""
# ============================================================
# CU13 - GESTIONAR MATERIAS Y PLAN DE ESTUDIOS
# ============================================================

from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.errores import (
    Conflicto,
    NoEncontrado,
)

from app.nucleo.esquemas import Pagina

from app.paquetes.academico import repository as repo

from app.paquetes.academico.models import (
    Materia,
    MateriaGrado,
    Grado,
)

from app.paquetes.academico.schemas import (
    MateriaCrear,
    MateriaActualizar,
    MateriaSalida,
    NivelEducativoSalida,
    GradoSalida,
    OpcionesPlanSalida,
    MateriaPlanEntrada,
    PlanEstudiosSalida,
)


# ------------------------------------------------------------
# 1. LISTAR Y BUSCAR MATERIAS
# ------------------------------------------------------------

async def listar(
    sesion: AsyncSession,
    q: str | None = None,
    pagina: int = 1,
    tamano: int = 10,
) -> Pagina[MateriaSalida]:

    materias, total = await repo.listar_materias(
        sesion,
        q=q,
        pagina=pagina,
        tamano=tamano,
    )

    return Pagina[MateriaSalida](
        items=[
            MateriaSalida.model_validate(materia)
            for materia in materias
        ],
        total=total,
        pagina=pagina,
        tamano=tamano,
    )


# ------------------------------------------------------------
# 2. OBTENER UNA MATERIA
# ------------------------------------------------------------

async def obtener(
    sesion: AsyncSession,
    id_materia: int,
) -> MateriaSalida:

    materia = await repo.obtener_materia(
        sesion,
        id_materia,
    )

    if materia is None:
        raise NoEncontrado(
            "No existe una materia con ese identificador."
        )

    return MateriaSalida.model_validate(materia)


# ------------------------------------------------------------
# 3. REGISTRAR MATERIA
# ------------------------------------------------------------

async def registrar(
    sesion: AsyncSession,
    datos: MateriaCrear,
) -> MateriaSalida:

    existente = await repo.buscar_materia_por_nombre(
        sesion,
        datos.nombre_materia,
    )

    if existente is not None:
        raise Conflicto(
            "Ya existe una materia registrada con ese nombre."
        )

    materia = Materia(
        nombre_materia=datos.nombre_materia,
        carga_horaria=datos.carga_horaria,
    )

    sesion.add(materia)

    await sesion.flush()

    return MateriaSalida.model_validate(materia)


# ------------------------------------------------------------
# 4. MODIFICAR MATERIA
# ------------------------------------------------------------

async def actualizar(
    sesion: AsyncSession,
    id_materia: int,
    datos: MateriaActualizar,
) -> MateriaSalida:

    materia = await repo.obtener_materia(
        sesion,
        id_materia,
    )

    if materia is None:
        raise NoEncontrado(
            "La materia que deseas modificar no existe."
        )

    cambios = datos.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    if "nombre_materia" in cambios:

        existente = await repo.buscar_materia_por_nombre(
            sesion,
            cambios["nombre_materia"],
            id_excluir=id_materia,
        )

        if existente is not None:
            raise Conflicto(
                "Ya existe otra materia con ese nombre."
            )

    for campo, valor in cambios.items():
        setattr(materia, campo, valor)

    await sesion.flush()

    return MateriaSalida.model_validate(materia)


# ------------------------------------------------------------
# 5. ELIMINAR MATERIA
# ------------------------------------------------------------

async def eliminar(
    sesion: AsyncSession,
    id_materia: int,
) -> None:

    materia = await repo.obtener_materia(
        sesion,
        id_materia,
    )

    if materia is None:
        raise NoEncontrado(
            "La materia que deseas eliminar no existe."
        )

    tiene_plan = await repo.materia_tiene_plan(
        sesion,
        id_materia,
    )

    if tiene_plan:
        raise Conflicto(
            "No se puede eliminar la materia porque "
            "pertenece a un plan de estudios."
        )

    tiene_asignaciones = (
        await repo.materia_tiene_asignaciones(
            sesion,
            id_materia,
        )
    )

    if tiene_asignaciones:
        raise Conflicto(
            "No se puede eliminar la materia porque "
            "tiene profesores asignados."
        )

    await sesion.delete(materia)

    await sesion.flush()


# ------------------------------------------------------------
# 6. CONSULTAR NIVELES Y GRADOS
# ------------------------------------------------------------

async def opciones(
    sesion: AsyncSession,
) -> OpcionesPlanSalida:

    niveles = await repo.listar_niveles(sesion)

    grados = await repo.listar_grados(sesion)

    return OpcionesPlanSalida(
        niveles=[
            NivelEducativoSalida.model_validate(nivel)
            for nivel in niveles
        ],
        grados=[
            GradoSalida.model_validate(grado)
            for grado in grados
        ],
    )


# ------------------------------------------------------------
# 7. CONSULTAR PLAN DE ESTUDIOS
# ------------------------------------------------------------

async def consultar_plan(
    sesion: AsyncSession,
    id_grado: int,
) -> PlanEstudiosSalida:

    grado = await sesion.get(Grado, id_grado)

    if grado is None:
        raise NoEncontrado(
            "El grado seleccionado no existe."
        )

    materias_plan = await repo.materias_del_grado(
        sesion,
        id_grado,
    )

    disponibles = await repo.materias_disponibles(
        sesion,
        id_grado,
    )

    return PlanEstudiosSalida(
        id_grado=grado.id_grado,
        nombre_grado=grado.nombre_grado,
        materias_plan=[
            MateriaSalida.model_validate(materia)
            for materia in materias_plan
        ],
        materias_disponibles=[
            MateriaSalida.model_validate(materia)
            for materia in disponibles
        ],
    )


# ------------------------------------------------------------
# 8. AGREGAR MATERIA AL PLAN DE ESTUDIOS
# ------------------------------------------------------------

async def agregar_al_plan(
    sesion: AsyncSession,
    id_grado: int,
    datos: MateriaPlanEntrada,
) -> PlanEstudiosSalida:

    grado = await sesion.get(Grado, id_grado)

    if grado is None:
        raise NoEncontrado(
            "El grado seleccionado no existe."
        )

    materia = await repo.obtener_materia(
        sesion,
        datos.id_materia,
    )

    if materia is None:
        raise NoEncontrado(
            "La materia seleccionada no existe."
        )

    ya_existe = await repo.materia_en_plan(
        sesion,
        id_grado,
        datos.id_materia,
    )

    if ya_existe:
        raise Conflicto(
            "La materia ya pertenece al plan de estudios "
            "de este grado."
        )

    relacion = MateriaGrado(
        id_grado_mg=id_grado,
        id_materia_mg=datos.id_materia,
    )

    sesion.add(relacion)

    await sesion.flush()

    return await consultar_plan(sesion, id_grado)


# ------------------------------------------------------------
# 9. QUITAR MATERIA DEL PLAN DE ESTUDIOS
# ------------------------------------------------------------

async def quitar_del_plan(
    sesion: AsyncSession,
    id_grado: int,
    id_materia: int,
) -> PlanEstudiosSalida:

    grado = await sesion.get(Grado, id_grado)

    if grado is None:
        raise NoEncontrado(
            "El grado seleccionado no existe."
        )

    relacion = await sesion.get(
        MateriaGrado,
        (id_grado, id_materia),
    )

    if relacion is None:
        raise NoEncontrado(
            "La materia no pertenece al plan de estudios "
            "de este grado."
        )

    tiene_asignacion = (
        await repo.tiene_asignacion_en_gestion_abierta(
            sesion,
            id_grado,
            id_materia,
        )
    )

    if tiene_asignacion:
        raise Conflicto(
            "No se puede quitar la materia del plan "
            "porque tiene profesores asignados "
            "en la gestión abierta."
        )

    await sesion.delete(relacion)

    await sesion.flush()

    return await consultar_plan(sesion, id_grado)
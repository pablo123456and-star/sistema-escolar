"""
CU09 - Consultar estudiantes/tutores relacionados
Paquete: personas

Actores ........: Tutor, Administrativo
Rol del sistema : administrador, tutor, estudiante, profesor
Tablas .........: tutor_estudiante, persona, estudiante, tutor
Usa de la BD ...: —

Reglas de negocio que implementa este caso de uso (backend):
    - Administrador: los tutores de cualquier estudiante o los estudiantes de cualquier tutor.
    - Tutor: sus estudiantes (su propio CI) o los tutores de uno de sus hijos.
    - Estudiante: solo sus propios tutores.
    - Profesor: los tutores de los estudiantes de sus clases en la gestión abierta (misma regla que el CU07).
    - El CI debe ser del tipo consultado (estudiante o tutor); si no, se avisa qué es.
    - A quien no le corresponde se le responde 403, exista o no el CI (no se revela si existe).
    - Solo lectura.

Precondición:
    Sesión iniciada.

Postcondición:
    Se muestra la lista de estudiantes del tutor (o de tutores del estudiante). No se modifica nada.

Flujo: router.py -> este caso de uso -> repository.py -> BD.
Estado: IMPLEMENTADO.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import ErrorNegocio, NoEncontrado, SinPermiso
from app.paquetes.academico import politicas as academico
from app.paquetes.personas import repository as repo
from app.paquetes.personas.models import Estudiante, Persona, Tutor


async def _puede_ver(sesion: AsyncSession, usuario: UsuarioActual, ci: str) -> bool:
    if usuario.rol == "administrador":
        return True
    if usuario.rol in ("estudiante", "tutor") and usuario.ci == ci:
        return True
    if usuario.rol in ("tutor", "profesor"):
        # tutor: uno de sus hijos; profesor: un estudiante de sus clases en la gestión abierta
        gestion = await academico.gestion_abierta(sesion)
        return await repo.estudiante_visible_cu07(
            sesion, usuario.rol, usuario.ci, gestion.id_gestion if gestion else None, ci
        )
    return False


async def consultar(sesion: AsyncSession, usuario: UsuarioActual, ci: str, tipo: str) -> dict:
    if not await _puede_ver(sesion, usuario, ci):
        raise SinPermiso("No tiene permiso para ver los relacionados de esta persona.")
    persona = await sesion.get(Persona, ci)
    if persona is None:
        raise NoEncontrado("No existe una persona con ese CI.")
    nombre = f"{persona.nombre_persona} {persona.apellidos}"

    es_estudiante = await sesion.get(Estudiante, ci) is not None
    es_tutor = await sesion.get(Tutor, ci) is not None
    if tipo == "estudiante" and not es_estudiante:
        raise ErrorNegocio(
            f"{nombre} no está registrado como estudiante"
            + (": es tutor. Consulte «Los estudiantes de este tutor»." if es_tutor else "."),
            codigo="tipo_incorrecto",
        )
    if tipo == "tutor" and not es_tutor:
        raise ErrorNegocio(
            f"{nombre} no está registrado como tutor"
            + (": es estudiante. Consulte «Los tutores de este estudiante»." if es_estudiante else "."),
            codigo="tipo_incorrecto",
        )

    if tipo == "estudiante":
        relacionados = [
            {"ci": v["ci_tutor"], "nombre_completo": v["nombre_tutor"], "telefono": v["telefono_tutor"],
             "curso": None, "estado": None, **_vinculo(v)}
            for v in await repo.vinculos(sesion, ci_estudiante=ci)
        ]
    else:
        relacionados = [
            {"ci": v["ci_estudiante"], "nombre_completo": v["nombre_estudiante"], "telefono": None,
             "curso": v["curso_estudiante"], "estado": v["estado_estudiante"], **_vinculo(v)}
            for v in await repo.vinculos(sesion, ci_tutor=ci)
        ]
    return {"ci": ci, "nombre_completo": nombre, "tipo": tipo, "relacionados": relacionados}


def _vinculo(v: dict) -> dict:
    return {
        "parentesco": v["parentesco"],
        "es_principal": v["es_principal"],
        "es_responsable_pago": v["es_responsable_pago"],
        "autorizado_recoger": v["autorizado_recoger"],
    }

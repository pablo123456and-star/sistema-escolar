"""
backend/app/paquetes/personas/casos_uso/cu09_consultar_relacionados.py
CU09 - Consultar estudiantes/tutores relacionados
Paquete: personas
Estado: IMPLEMENTADO.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.nucleo.errores import NoEncontrado, SinPermiso
from app.paquetes.personas import repository as repo
from app.paquetes.personas.models import Persona


async def consultar(sesion: AsyncSession, usuario, ci: str, tipo: str):
    # 1. Verificar que la persona buscada existe
    persona = await sesion.get(Persona, str(ci))
    if persona is None:
        raise NoEncontrado("No existe una persona con ese CI.")

    rol = usuario.rol
    ci_usuario = str(usuario.ci)
    ci_buscado = str(ci)

    if rol == "administrador":
        pass
        
    elif rol == "estudiante":
        # El estudiante solo se puede ver a sí mismo
        if ci_usuario != ci_buscado:
            raise SinPermiso("No tiene permiso para ver esta información.")
        
    elif rol == "tutor":
        if ci_usuario != ci_buscado:
            # Verificamos que el ci buscado sea uno de sus estudiantes
            vinculos = await repo.vinculos(sesion, ci_tutor=ci_usuario)
            if not any(str(v["ci_estudiante"]) == ci_buscado for v in vinculos):
                raise SinPermiso("No tiene permiso para ver esta información.")
                
    elif rol == "profesor":
        # Buscamos la gestión que está abierta actualmente
        id_gestion = await sesion.scalar(text("SELECT id_gestion FROM gestion WHERE estado_gestion = 'abierta' LIMIT 1"))
        
        if not id_gestion:
            raise SinPermiso("No hay una gestión académica abierta para validar permisos.")

        # Ahora sí, le pasamos el id_gestion correcto a la función del CU07
        visible = await repo.estudiante_visible_cu07(sesion, rol, ci_usuario, id_gestion, ci_buscado)
        if not visible:
            raise SinPermiso("No tiene permiso para ver esta información.")
            
    else:
        raise SinPermiso("Rol no autorizado.")

    # 3. Consultar los datos
    filas = await repo.consultar_relacionados(sesion, ci_buscado, tipo)
    return [dict(fila) for fila in filas]
"""
backend/app/paquetes/personas/casos_uso/cu09_consultar_relacionados.py
CU09 - Consultar estudiantes/tutores relacionados
Paquete: personas

Actores ........: Tutor, Administrativo
Rol del sistema : tutor, administrador, estudiante, profesor
Tablas .........: tutor_estudiante, persona
Usa de la BD ...: —

Reglas de negocio que implementa este caso de uso (backend):
    - Administrador: todos. Tutor: sus estudiantes. Estudiante: sus tutores. Profesor: tutores de sus estudiantes.
    - Solo lectura.

Precondición:
    Sesión iniciada.

Postcondición:
    Se muestra la lista de estudiantes del tutor (o de tutores del estudiante). No se modifica nada.

Flujo: router.py -> este caso de uso -> politicas.py / repository.py -> BD.
Estado: PENDIENTE DE IMPLEMENTAR.
"""

"""
backend/app/paquetes/personas/casos_uso/cu09_consultar_relacionados.py
CU09 - Consultar estudiantes/tutores relacionados
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.errores import NoEncontrado
from app.paquetes.personas import repository as repo
from app.paquetes.personas.models import Persona

async def consultar(sesion: AsyncSession, ci: str, tipo: str):
    # 1. Verificar que la persona existe en la base de datos
    persona = await sesion.get(Persona, ci)
    if persona is None:
        raise NoEncontrado("No existe una persona con ese CI.")

    # 2. Obtener los relacionados usando el repositorio que acabas de crear
    filas = await repo.consultar_relacionados(sesion, ci, tipo)
    
    # 3. Retornar los datos (FastAPI lo convierte a JSON automáticamente)
    return [dict(fila) for fila in filas]

"""
Reporte dinámico (consigna del ciclo 3: «Reportes: estático y dinámico. Generar a 2 formatos»)
Paquete: reportes

Actores ........: Director, Secretaría
Rol del sistema : administrador
Tablas .........: inscripcion, persona, estudiante, pago_mensualidad, asistencia, calificacion (solo lectura), bitacora
Usa de la BD ...: Vistas v_estado_pagos, v_nota_final y v_curso; fn_registrar_bitacora

Reglas de negocio que implementa (backend):
    - Solo administrador.
    - El usuario elige la fuente (estudiantes e inscripciones, pagos, asistencia o calificaciones),
      los filtros, las columnas (1 a 20) y el orden.
    - Fuentes, columnas y filtros salen de una lista fija (repository.FUENTES): una clave que no
      está en la lista se rechaza y los valores van como parámetros (nunca dentro del SQL).
    - Cada valor de filtro se valida según su tipo (id numérico, fecha, número u opción de la lista).
    - Vista previa: hasta 200 filas; PDF y Excel: hasta 5000 (se avisa si hay más).
    - Cada descarga queda en la bitácora.

Precondición:
    Sesión iniciada como administrador.

Postcondición:
    Se entrega el reporte; no se modifica ningún dato (solo se anota la descarga en la bitácora).

Flujo: router.py -> este caso de uso -> repository.py -> BD; nucleo/exportar.py arma el PDF y el Excel.
Estado: IMPLEMENTADO.
"""
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import ErrorNegocio
from app.nucleo.exportar import Columna, Tabla
from app.paquetes.reportes import repository as repo
from app.paquetes.reportes.schemas import (
    ColumnaFuente,
    FiltroFuente,
    FuenteSalida,
    OpcionFiltro,
    ReporteDinamicoEntrada,
)

LIMITE_VISTA_PREVIA = 200
LIMITE_ARCHIVO = 5000
_IDS = ("gestion", "nivel", "curso", "periodo", "materia")


def fuentes() -> list[FuenteSalida]:
    return [
        FuenteSalida(
            clave=clave, nombre=f.nombre, descripcion=f.descripcion,
            columnas=[ColumnaFuente(clave=k, titulo=c.titulo, tipo=c.tipo, por_defecto=c.por_defecto)
                      for k, c in f.columnas.items()],
            filtros=[FiltroFuente(clave=k, titulo=x.titulo, tipo=x.tipo,
                                  opciones=[OpcionFiltro(valor=v, etiqueta=e) for v, e in x.opciones])
                     for k, x in f.filtros.items()],
        )
        for clave, f in repo.FUENTES.items()
    ]


def _valor(filtro: repo.Filtro, valor):
    """Convierte y valida el valor de un filtro según su tipo."""
    try:
        if filtro.tipo in _IDS:
            return int(valor)
        if filtro.tipo == "fecha":
            return date.fromisoformat(str(valor))
        if filtro.tipo == "numero":
            return float(valor)
    except ValueError:
        raise ErrorNegocio(f"El valor de «{filtro.titulo}» no es válido.") from None
    valor = str(valor)
    if valor not in {v for v, _ in filtro.opciones}:
        raise ErrorNegocio(f"El valor de «{filtro.titulo}» no es una opción válida.")
    return valor


async def _texto_filtro(sesion: AsyncSession, filtro: repo.Filtro, valor) -> str:
    if filtro.tipo in _IDS:
        nombre = await repo.nombre_de(sesion, filtro.tipo, valor)
        if nombre is None:
            raise ErrorNegocio(f"No existe ese valor de «{filtro.titulo}».")
        return f"{filtro.titulo}: {nombre}"
    if filtro.tipo == "fecha":
        return f"{filtro.titulo}: {valor:%d/%m/%Y}"
    if filtro.tipo == "opcion":
        return f"{filtro.titulo}: {dict(filtro.opciones)[valor]}"
    return f"{filtro.titulo}: {valor:g}"


async def generar(sesion: AsyncSession, usuario: UsuarioActual, datos: ReporteDinamicoEntrada,
                  para_archivo: bool) -> tuple[Tabla, int]:
    """Arma la tabla del reporte personalizado y devuelve también el total de registros."""
    fuente = repo.FUENTES.get(datos.fuente)
    if fuente is None:
        raise ErrorNegocio("Fuente de datos no válida.")
    invalidas = [c for c in datos.columnas if c not in fuente.columnas]
    if invalidas:
        raise ErrorNegocio(f"Columnas no válidas para {fuente.nombre}: {', '.join(invalidas)}.")
    if datos.orden is not None and datos.orden not in fuente.columnas:
        raise ErrorNegocio("Columna de orden no válida.")

    filtros, textos = {}, []
    for clave, valor in datos.filtros.items():
        if clave not in fuente.filtros:
            raise ErrorNegocio(f"Filtro no válido para {fuente.nombre}: {clave}.")
        if valor is None or valor == "":
            continue
        filtros[clave] = _valor(fuente.filtros[clave], valor)
        textos.append(await _texto_filtro(sesion, fuente.filtros[clave], filtros[clave]))

    limite = LIMITE_ARCHIVO if para_archivo else LIMITE_VISTA_PREVIA
    filas, total = await repo.dinamico(sesion, datos.fuente, datos.columnas, filtros, datos.orden, datos.descendente,
                                       limite)
    if datos.orden:
        textos.append(f"Orden: {fuente.columnas[datos.orden].titulo} ({'descendente' if datos.descendente else 'ascendente'})")
    tabla = Tabla(f"Reporte personalizado: {fuente.nombre}",
                  [Columna(c, fuente.columnas[c].titulo, fuente.columnas[c].tipo) for c in datos.columnas],
                  [dict(f) for f in filas], textos or ["Sin filtros: todos los registros."])
    tabla.resumen = [f"Registros: {total}."]
    if total > len(filas):
        tabla.resumen = [f"Se muestran {len(filas)} de {total} registros; agregue filtros para acotar el reporte."]
    tabla.generado_por = await repo.nombre_usuario(sesion, usuario.ci) or usuario.nombre_usuario
    tabla.generado_en = await repo.ahora(sesion)
    return tabla, total

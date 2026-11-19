"""
CU28 - Consultar información por comando de voz (asistente)
Paquete: asistente

Actores ........: Administrador, Director, Secretaria, Docente, Padre/Tutor, Estudiante
Rol del sistema : administrador, profesor, tutor, estudiante (cualquier usuario con sesión)
Tablas .........: ninguna propia; lee la información a través de la API (solo GET)
Usa de la BD ...: fn_registrar_bitacora (cada consulta queda en la bitácora)
Servicio externo: Groq (voz a texto con Whisper y modelo de lenguaje con herramientas)

Reglas de negocio que implementa este caso de uso (backend):
    - Solo lectura: el asistente no registra, modifica ni elimina nada.
    - El modelo no lee la base de datos: usa la herramienta consultar_api, que solo acepta las rutas
      GET del catálogo (catalogo.py) y las llama con el token del usuario que pregunta. Por eso se
      aplican los mismos permisos que en las pantallas: un estudiante no ve las notas de otro, un
      docente solo ve a los estudiantes de sus clases y un tutor solo a sus hijos (si no le
      corresponde, la API responde 403 y el asistente lo explica).
    - A Groq solo se envía la pregunta y el resultado de las consultas necesarias para responder.
    - Como máximo 6 consultas por pregunta; la respuesta es breve para poder leerse en voz alta.
    - Cada pregunta queda registrada en la bitácora.

Precondición:
    Sesión iniciada y GROQ_API_KEY configurada en el servidor.

Postcondición:
    El usuario recibe la respuesta en texto (y el navegador la lee en voz alta). No se modifica nada.

Flujo: router.py -> este caso de uso -> nucleo/groq.py (Groq) y catalogo.py -> API (GET) -> BD.
Estado: IMPLEMENTADO.
"""
import json
import logging
import re
import unicodedata
from datetime import datetime
from urllib.parse import urlencode

from sqlalchemy.ext.asyncio import AsyncSession

from app.nucleo import groq
from app.nucleo.dependencias import UsuarioActual
from app.nucleo.errores import ErrorNegocio
from app.paquetes.asistente import catalogo
from app.paquetes.asistente import repository as repo
from app.paquetes.asistente.schemas import ConsultaEntrada, RespuestaAsistente

logger = logging.getLogger("app.asistente")

MAX_PASOS = 6
MAX_CARACTERES_RESULTADO = 12000     # el plan gratuito de Groq permite 8000 tokens por minuto
MAX_ELEMENTOS_LISTA = 60
MAX_AUDIO_BYTES = 5 * 1024 * 1024
MAX_EMPATADOS = 5
AVISO_RECORTE = ("Resultado incompleto: no afirmes máximos, mínimos ni totales; pide una consulta más concreta "
                 "(por materia, estudiante o trimestre).")

# Lo que Whisper suele "escuchar" en una grabación en silencio (normalizado: minúsculas, sin tildes ni signos).
ALUCINACIONES_WHISPER = {
    "gracias", "muchas gracias", "gracias por ver", "gracias por ver el video", "gracias por ver el video hasta el final",
    "gracias por su atencion", "gracias por mirar", "suscribete", "suscribete al canal", "no olvides suscribirte",
    "musica", "aplausos", "risas", "silencio", "hasta la proxima", "nos vemos", "adios", "chau", "bye", "you",
    "thank you", "thanks for watching", "amen",
}

HERRAMIENTAS = [{
    "type": "function",
    "function": {
        "name": "consultar_api",
        "description": "Consulta (solo lectura) una ruta GET del sistema escolar con los permisos del usuario que pregunta.",
        "parameters": {
            "type": "object",
            "properties": {
                "ruta": {"type": "string",
                         "description": "Ruta del catálogo con sus valores reemplazados, por ejemplo /horarios/consulta "
                                        "o /evaluacion/boletines/4500001"},
                "parametros": {"type": "object",
                               "description": "Parámetros de consulta, por ejemplo {\"id_curso\": 14}"},
            },
            "required": ["ruta"],
        },
    },
}]

SISTEMA = """Eres el asistente del sistema de información de la Unidad Educativa "Mariscal Sucre G".
Respondes preguntas sobre la información del sistema (horarios, notas, asistencia, boletines, pagos,
inventario, comunicados, estudiantes, docentes, inscripciones...) consultando la API con la herramienta
consultar_api.

Usuario que pregunta: {nombre} (rol: {rol}). Hoy es {hoy}.
{gestion}

Reglas:
- Usa SOLO los datos que devuelve consultar_api. Nunca inventes datos.
- La API aplica los permisos del usuario. Si responde 403 explica con amabilidad que no tiene permiso
  para ver esa información; si responde 404, que no existe. No busques otra forma de obtener ese dato.
- Para usar una ruta con identificadores (id_curso, id_periodo, CI...), obtenlos antes con las rutas de
  opciones o de búsqueda. Si el usuario dice "mi", "mis" o "mis hijos", usa las rutas del usuario conectado.
- Las rutas /mias y /mis-cuotas devuelven SOLO datos del usuario conectado (o de sus hijos): nunca los presentes
  como datos de otra persona. Si preguntan por otra persona, usa las rutas de esa persona (boletín, historial...).
- Para preguntas sobre un curso completo (quién falta más, quién tiene menos asistencia, mejor o peor promedio
  del curso) usa los reportes fijos de asistencia o rendimiento, no el historial de cada estudiante.
- Al hablar de notas, asistencia o boletines, di siempre a qué trimestre y gestión se refieren los datos. Si el
  usuario no indica el trimestre, usa el trimestre en curso y menciónalo (los id_periodo de la gestión
  abierta están arriba: no los consultes de nuevo).
- Si un resultado trae "resumen", usa esos valores (nota más alta, más baja, promedios, reprobados) y no los
  calcules tú. En el centralizador, "general_todas_las_materias" mezcla todas las materias del curso; si la
  pregunta es de una materia concreta, usa SOLO "por_materia" de esa materia. Al dar una nota, di siempre de
  qué materia es. Si trae "recortado": true, di que la información está incompleta y no afirmes máximos, mínimos
  ni totales. Las tablas vienen como "columnas" y "filas" (cada fila en el orden de las columnas).
- Solo puedes consultar; no registras ni modificas nada. Si te piden un cambio, indica en qué pantalla hacerlo.
- Si la pregunta no tiene que ver con el sistema escolar, responde que solo ayudas con información del sistema.
- Tu respuesta se leerá en voz alta: escribe en español, en texto corrido de 1 a 4 oraciones. Nada de
  listas, viñetas, guiones, numeraciones, tablas, negritas, markdown, JSON, rutas ni identificadores internos.
  Si hay varios datos, únelos en una oración ("Matemática 78, Lenguaje 85 y Física 70"). Usa los nombres de
  personas, cursos y materias.

Rutas disponibles (solo GET; lo que va después de "?" son parámetros de consulta; los marcados con * son
obligatorios y el resto opcionales):
{catalogo}"""


def _gestion(periodos: list[dict], ahora: datetime) -> str:
    """Gestión abierta y sus trimestres (con id_periodo), marcando el que está en curso."""
    if not periodos:
        return "No hay una gestión abierta."
    partes = []
    for p in periodos:
        en_curso = p["fecha_inicio_p"] <= ahora.date() <= p["fecha_final_p"]
        partes.append(f"{p['nombre_periodo']} (id_periodo {p['id_periodo']}, {p['estado_periodo']}"
                      f"{', en curso' if en_curso else ''})")
    return (f"Gestión abierta: {periodos[0]['anio']} (id_gestion {periodos[0]['id_gestion']}). "
            f"Trimestres: {'; '.join(partes)}.")


def _sistema(usuario: UsuarioActual, ahora: datetime, periodos: list[dict]) -> str:
    dia = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")[ahora.weekday()]
    return SISTEMA.format(nombre=usuario.nombre_usuario, rol=usuario.rol, hoy=f"{dia} {ahora:%d/%m/%Y}",
                          gestion=_gestion(periodos, ahora), catalogo=catalogo.descripcion(usuario.rol))


async def _consultar_api(ruta: str, parametros: dict | None, token: str, ip: str | None) -> dict:
    """Llama a una ruta GET de la propia API (en el mismo proceso) con el token del usuario."""
    ruta = "/" + str(ruta or "").strip().lstrip("/").split("?")[0]
    if not catalogo.ruta_permitida(ruta):
        return {"estado": 400, "datos": "Ruta no permitida: use solo las rutas GET del catálogo."}
    params = {k: v for k, v in (parametros or {}).items()
              if isinstance(k, str) and isinstance(v, (str, int, float, bool)) and v != ""}
    if ruta.startswith("/reportes/estaticos/"):
        params["formato"] = "json"
    from app.main import PREFIJO_API, app   # import tardío: main importa este paquete

    cabeceras = [(b"authorization", f"Bearer {token}".encode()), (b"accept", b"application/json"),
                 (b"host", b"asistente.interno")]
    if ip:
        cabeceras.append((b"x-forwarded-for", ip.encode()))
    scope = {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "GET", "scheme": "http",
        "path": PREFIJO_API + ruta, "raw_path": (PREFIJO_API + ruta).encode(), "root_path": "",
        "query_string": urlencode(params).encode(), "headers": cabeceras,
        "client": ("127.0.0.1", 0), "server": ("asistente.interno", 80),
    }
    estado, cuerpo = {}, []

    async def recibir():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def enviar(mensaje):
        if mensaje["type"] == "http.response.start":
            estado["codigo"] = mensaje["status"]
        elif mensaje["type"] == "http.response.body":
            cuerpo.append(mensaje.get("body", b""))

    await app(scope, recibir, enviar)
    texto = b"".join(cuerpo).decode(errors="replace")
    try:
        datos = json.loads(texto)
    except ValueError:
        datos = texto
    if isinstance(datos, dict) and "detalle" in datos and estado.get("codigo", 500) >= 400:
        datos = datos["detalle"]
    codigo = estado.get("codigo", 500)
    if codigo == 200:
        datos = _preparar(ruta, datos)
    return {"estado": codigo, "datos": datos}


# --- Resúmenes calculados en el servidor ------------------------------------------------------------
# El modelo se equivoca al buscar máximos o promedios entre cientos de números: para las rutas con muchas
# notas, el backend reordena los datos como tabla y calcula el resumen. Para agregar otra ruta, basta
# con sumar (patrón, función) a PREPARADORES.

def _nombre(fila: dict) -> str:
    return f"{fila.get('apellidos') or ''} {fila.get('nombre_persona') or ''}".strip()


def _redondear(valor):
    return round(valor, 2) if isinstance(valor, float) else valor


def _extremo(valores: list[tuple], funcion, campos: tuple[str, ...]) -> dict | None:
    """Mayor o menor valor con quiénes lo tienen (si hay empate, hasta MAX_EMPATADOS)."""
    if not valores:
        return None
    objetivo = funcion(v[0] for v in valores)
    empatados = [v for v in valores if v[0] == objetivo]
    salida = {"valor": _redondear(objetivo),
              "quienes": [dict(zip(campos, v[1:])) for v in empatados[:MAX_EMPATADOS]]}
    if len(empatados) > MAX_EMPATADOS:
        salida["y_otros"] = len(empatados) - MAX_EMPATADOS
    return salida


def _promedio(valores: list[float]) -> float | None:
    return round(sum(valores) / len(valores), 2) if valores else None


def _preparar_centralizador(datos):
    if not isinstance(datos, dict) or not isinstance(datos.get("filas"), list):
        return datos
    minima = datos.get("nota_minima")
    materias = [m.get("materia") for m in datos.get("materias") or []]
    notas, promedios, filas = [], [], []
    reprobados_por_estudiante = 0
    for fila in datos["filas"]:
        estudiante = _nombre(fila)
        por_materia = {n.get("materia"): n.get("nota_final") for n in fila.get("notas") or []
                       if n.get("nota_final") is not None}
        notas += [(valor, estudiante, materia) for materia, valor in por_materia.items()]
        if minima is not None and any(v < minima for v in por_materia.values()):
            reprobados_por_estudiante += 1
        promedio = fila.get("promedio_estudiante")
        if promedio is not None:
            promedios.append((promedio, estudiante))
        filas.append([estudiante, *[_redondear(por_materia.get(m)) for m in materias], _redondear(promedio)])
    general = {
        "nota_mas_alta": _extremo(notas, max, ("estudiante", "materia")),
        "nota_mas_baja": _extremo(notas, min, ("estudiante", "materia")),
        "promedio_curso": _promedio([p for p, _ in promedios]),
        "mejor_promedio": _extremo(promedios, max, ("estudiante",)),
        "peor_promedio": _extremo(promedios, min, ("estudiante",)),
        "cantidad_estudiantes": len(datos["filas"]),
        "notas_reprobadas": sum(1 for v, _, _ in notas if minima is not None and v < minima),
        "estudiantes_con_alguna_materia_reprobada": reprobados_por_estudiante,
    }
    por_materia = {}
    for materia in materias:
        de_materia = [(v, e) for v, e, m in notas if m == materia]
        if de_materia:
            por_materia[materia] = {
                "nota_mas_alta": _extremo(de_materia, max, ("estudiante",)),
                "nota_mas_baja": _extremo(de_materia, min, ("estudiante",)),
                "promedio": _promedio([v for v, _ in de_materia]),
                "reprobados": sum(1 for v, _ in de_materia if minima is not None and v < minima),
            }
    resumen = {"general_todas_las_materias": general, "por_materia": por_materia}
    return {"resumen": resumen, "curso": datos.get("curso"), "periodo": datos.get("periodo"),
            "gestion": datos.get("anio"), "nota_minima": minima,
            "notas": {"columnas": ["estudiante", *materias, "promedio"], "filas": filas}}


def _preparar_planilla(datos):
    if not isinstance(datos, dict) or not isinstance(datos.get("estudiantes"), list):
        return datos
    minima = datos.get("nota_minima")
    dimensiones = [(str(d.get("id_dimension")), d.get("nombre_dimension")) for d in datos.get("dimensiones") or []]
    notas, filas = [], []
    for e in datos["estudiantes"]:
        estudiante, final = _nombre(e), e.get("nota_final")
        puntajes = {str(k): v for k, v in (e.get("puntajes") or {}).items()}
        if final is not None:
            notas.append((final, estudiante))
        filas.append([estudiante, *[_redondear(puntajes.get(i)) for i, _ in dimensiones], _redondear(final),
                      e.get("observacion")])
    clase, periodo = datos.get("clase") or {}, datos.get("periodo") or {}
    resumen = {
        "nota_mas_alta": _extremo(notas, max, ("estudiante",)),
        "nota_mas_baja": _extremo(notas, min, ("estudiante",)),
        "promedio": _promedio([v for v, _ in notas]),
        "cantidad_estudiantes": len(datos["estudiantes"]),
        "sin_nota": len(datos["estudiantes"]) - len(notas),
        "reprobados": sum(1 for v, _ in notas if minima is not None and v < minima),
    }
    return {"resumen": resumen, "materia": clase.get("materia"), "curso": clase.get("curso"),
            "profesor": clase.get("profesor"), "periodo": periodo.get("nombre_periodo"),
            "estado_periodo": periodo.get("estado_periodo"), "nota_minima": minima,
            "notas": {"columnas": ["estudiante", *[n for _, n in dimensiones], "nota_final", "observacion"],
                      "filas": filas}}


def _numero(valor) -> float | None:
    try:
        return None if valor is None else float(valor)
    except (TypeError, ValueError):
        return None


def _preparar_reporte_curso(campo: str, nombre_mas: str, nombre_menos: str):
    """Reportes fijos de un curso (asistencia, rendimiento): agrega quién tiene el valor más alto y más bajo."""
    def preparar(datos):
        if not isinstance(datos, dict) or not isinstance(datos.get("filas"), list):
            return datos
        valores = [(v, f.get("estudiante")) for f in datos["filas"] if (v := _numero(f.get(campo))) is not None]
        resumen = {nombre_mas: _extremo(valores, max, ("estudiante",)),
                   nombre_menos: _extremo(valores, min, ("estudiante",)),
                   "promedio_del_curso": _promedio([v for v, _ in valores]),
                   "cantidad_estudiantes": len(datos["filas"]), "sin_datos": len(datos["filas"]) - len(valores),
                   "texto": datos.get("resumen")}
        if campo == "porcentaje":
            resumen["menos_de_80_por_ciento"] = sum(1 for v, _ in valores if v < 80)
        claves = [c.get("clave") for c in datos.get("columnas") or [] if c.get("clave") != "ci"]
        return {"resumen": resumen, "reporte": datos.get("titulo"), "filtros": datos.get("filtros"),
                "tabla": {"columnas": claves, "filas": [[_redondear(f.get(c)) for c in claves] for f in datos["filas"]]}}
    return preparar


def _preparar_propios(de_quien: str):
    """Rutas del usuario conectado: se marca de quién son, para que el modelo no las atribuya a otra persona."""
    def preparar(datos):
        return {"pertenecen_a": de_quien,
                "aviso": "Estos datos NO son de ninguna otra persona por la que se haya preguntado.", "datos": datos}
    return preparar


PREPARADORES = [
    (re.compile(r"^/evaluacion/centralizador$"), _preparar_centralizador),
    (re.compile(r"^/evaluacion/calificaciones/planilla/[^/]+$"), _preparar_planilla),
    (re.compile(r"^/reportes/estaticos/asistencia$"),
     _preparar_reporte_curso("porcentaje", "mayor_asistencia", "menor_asistencia")),
    (re.compile(r"^/reportes/estaticos/rendimiento$"),
     _preparar_reporte_curso("promedio", "mejor_promedio", "peor_promedio")),
    (re.compile(r"^/evaluacion/calificaciones/mias$"), _preparar_propios("el usuario conectado (sus propias notas)")),
    (re.compile(r"^/administracion/mis-cuotas$"),
     _preparar_propios("el usuario conectado (sus propias cuotas o las de sus hijos)")),
]


def _preparar(ruta: str, datos):
    for patron, funcion in PREPARADORES:
        if patron.match(ruta):
            return funcion(datos)
    return datos


# --- Compactación (menos tokens para Groq) ------------------------------------------------------------

def _vacio(valor) -> bool:
    return valor is None or valor == "" or valor == [] or valor == {}


def _compactar(valor):
    """Quita campos vacíos, recorta listas largas y convierte listas de registros iguales en tabla."""
    if isinstance(valor, dict):
        return {k: _compactar(v) for k, v in valor.items() if not _vacio(v)}
    if isinstance(valor, list):
        recorte = valor[:MAX_ELEMENTOS_LISTA]
        sobran = len(valor) - len(recorte)
        if (len(recorte) >= 3 and all(isinstance(v, dict) for v in recorte)
                and all(v.keys() == recorte[0].keys() for v in recorte)):
            columnas = [k for k in recorte[0] if any(not _vacio(v[k]) for v in recorte)]
            tabla = {"columnas": columnas, "filas": [[_compactar(v[k]) for k in columnas] for v in recorte]}
            if sobran:
                tabla["omitidas"] = sobran
            return tabla
        salida = [_compactar(v) for v in recorte]
        if sobran:
            salida.append(f"... y {sobran} más")
        return salida
    if isinstance(valor, float):
        return round(valor, 2)
    return valor


def _contenido(resultado: dict) -> str:
    """Resultado para el modelo. Si no entra en el límite, se avisa que está incompleto (no se corta a ciegas)."""
    def a_json(valor):
        return json.dumps(valor, ensure_ascii=False, default=str, separators=(",", ":"))
    texto = a_json(_compactar(resultado))
    if len(texto) <= MAX_CARACTERES_RESULTADO:
        return texto
    return a_json({"estado": resultado.get("estado"), "recortado": True, "aviso": AVISO_RECORTE,
                   "datos": texto[:MAX_CARACTERES_RESULTADO - 400]})


# Espacios y guiones "no separables" que a veces manda el modelo: se cambian por los comunes.
ESPACIOS_RAROS = str.maketrans({"\u00a0": " ", "\u202f": " ", "\u2009": " ", "\u2011": "-", "\u2010": "-"})


def _texto_para_voz(texto: str) -> str:
    """Por si el modelo igual usa markdown: quita viñetas, numeraciones y asteriscos, y une las líneas."""
    lineas = []
    texto = texto.translate(ESPACIOS_RAROS).replace("**", "").replace("__", "")
    for linea in texto.splitlines():
        linea = re.sub(r"^\s*(?:[-*•#>]+\s*|\d+[.)]\s+)", "", linea).strip()
        if linea:
            lineas.append(linea if linea[-1] in ".:;,!?" else linea + ".")
    return " ".join(lineas)


def _mensaje_modelo(m: dict) -> dict:
    """Solo los campos que se vuelven a enviar al modelo."""
    salida = {"role": "assistant", "content": m.get("content") or ""}
    if m.get("tool_calls"):
        salida["tool_calls"] = m["tool_calls"]
    return salida


async def responder(sesion: AsyncSession, usuario: UsuarioActual, datos: ConsultaEntrada, token: str,
                    ip: str | None = None) -> RespuestaAsistente:
    pregunta = datos.pregunta.strip()
    if not groq.habilitado():
        raise groq.AsistenteNoDisponible("El asistente por voz no está configurado en el servidor.")
    await repo.registrar_consulta(sesion, pregunta)

    sistema = _sistema(usuario, await repo.ahora(sesion), await repo.gestion_abierta(sesion))
    mensajes = [{"role": "system", "content": sistema}]
    for turno in datos.historial[-6:]:
        mensajes += [{"role": "user", "content": turno.pregunta}, {"role": "assistant", "content": turno.respuesta}]
    mensajes.append({"role": "user", "content": pregunta})

    consultas: list[str] = []
    for _ in range(MAX_PASOS + 1):
        mensaje = await groq.chat(mensajes, HERRAMIENTAS)
        pedidos = mensaje.get("tool_calls") or []
        if not pedidos:
            respuesta = _texto_para_voz(mensaje.get("content") or "")
            return RespuestaAsistente(pregunta=pregunta, respuesta=respuesta or "No encontré una respuesta.",
                                      consultas=consultas)
        mensajes.append(_mensaje_modelo(mensaje))
        for pedido in pedidos:
            try:
                argumentos = json.loads(pedido["function"].get("arguments") or "{}")
            except ValueError:
                argumentos = {}
            if len(consultas) >= MAX_PASOS:
                resultado = {"estado": 429, "datos": "Se alcanzó el máximo de consultas: responda con lo obtenido."}
            else:
                resultado = await _consultar_api(argumentos.get("ruta", ""), argumentos.get("parametros"), token, ip)
                consultas.append(str(argumentos.get("ruta", "")))
            mensajes.append({"role": "tool", "tool_call_id": pedido["id"], "content": _contenido(resultado)})
    return RespuestaAsistente(pregunta=pregunta, consultas=consultas,
                              respuesta="No pude completar la consulta. Intente con una pregunta más concreta.")


def _es_silencio(texto: str) -> bool:
    """True si la transcripción está vacía o es una frase que Whisper inventa cuando no hay voz."""
    bajo = (texto or "").lower()
    if "amara.org" in bajo:
        return True
    sin_tildes = "".join(c for c in unicodedata.normalize("NFD", bajo) if unicodedata.category(c) != "Mn")
    limpio = " ".join(re.sub(r"[^\w\s]", " ", sin_tildes).split())
    return len(limpio) < 2 or "subtitulo" in limpio or limpio in ALUCINACIONES_WHISPER


async def responder_audio(sesion: AsyncSession, usuario: UsuarioActual, audio: bytes, tipo_audio: str, token: str,
                          ip: str | None = None, historial: list | None = None) -> RespuestaAsistente:
    if not audio:
        raise ErrorNegocio("No se recibió audio.")
    if len(audio) > MAX_AUDIO_BYTES:
        raise ErrorNegocio("La grabación es demasiado larga: haga una pregunta más corta.")
    texto = await groq.transcribir(audio, tipo_audio or "audio/webm")
    if _es_silencio(texto):
        raise ErrorNegocio("No se escuchó la pregunta. Revise el micrófono y hable más cerca.")
    return await responder(sesion, usuario, ConsultaEntrada(pregunta=texto[:500], historial=(historial or [])[-6:]),
                           token, ip)

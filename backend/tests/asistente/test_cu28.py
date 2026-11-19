"""Pruebas del CU28: consultar información por comando de voz (asistente).

Groq se simula: las pruebas no salen a internet ni gastan la cuota. El modelo simulado pide las
consultas que se le indiquen y se verifica qué le devolvió la API (con los permisos del usuario).

Datos de 08_datos_prueba: mquispe (4500001) es estudiante de 1ro A Sec.; rflores enseña en 1ro A Sec.
(4500001-4500006); 4500007 es de 6to A Pri. (erojas); marioq es tutor de 4500001 y 4500007.
"""
import base64
import json

import pytest
from sqlalchemy import text

from app.nucleo import bd, groq
from app.paquetes.asistente import catalogo
from app.paquetes.asistente.casos_uso import cu28_consultar_por_voz as cu28
from tests.conftest import iniciar

URL = "/asistente"


def _pedido(ruta: str, parametros: dict | None = None, id_: str = "c1") -> dict:
    argumentos = {"ruta": ruta, **({"parametros": parametros} if parametros else {})}
    return {"id": id_, "type": "function", "function": {"name": "consultar_api", "arguments": json.dumps(argumentos)}}


class GroqSimulado:
    """Devuelve en orden los mensajes indicados y guarda lo que la API respondió a cada consulta."""

    def __init__(self, *respuestas: dict):
        self.respuestas = list(respuestas)
        self.resultados: list[dict] = []
        self.sistema = ""
        self.mensajes: list[dict] = []

    async def chat(self, mensajes, herramientas):
        self.sistema = mensajes[0]["content"]
        self.mensajes = list(mensajes)
        self.resultados = [json.loads(m["content"]) for m in mensajes if m["role"] == "tool"]
        return self.respuestas.pop(0) if self.respuestas else {"role": "assistant", "content": "Listo."}


@pytest.fixture
def simular(monkeypatch):
    monkeypatch.setattr(groq, "habilitado", lambda: True)

    def _simular(*respuestas: dict) -> GroqSimulado:
        falso = GroqSimulado(*respuestas)
        monkeypatch.setattr(groq, "chat", falso.chat)
        return falso
    return _simular


async def _valor(consulta: str, **params):
    async with bd._fabrica() as sesion:
        return await sesion.scalar(text(consulta), params)


async def test_cu28_requiere_sesion(cliente):
    assert (await cliente.get(f"{URL}/estado")).status_code == 401
    assert (await cliente.post(f"{URL}/consulta", json={"pregunta": "Mis notas"})).status_code == 401
    assert (await cliente.post(f"{URL}/voz", content=b"x", headers={"content-type": "audio/webm"})).status_code == 401


async def test_cu28_sin_clave_no_disponible(cliente, monkeypatch):
    monkeypatch.setattr(groq, "habilitado", lambda: False)
    cabecera = await iniciar(cliente, "mquispe")
    r = await cliente.get(f"{URL}/estado", headers=cabecera)
    assert r.status_code == 200 and r.json() == {"habilitado": False}
    r = await cliente.post(f"{URL}/consulta", headers=cabecera, json={"pregunta": "Mis notas"})
    assert r.status_code == 503
    assert r.json()["codigo"] == "asistente_no_disponible"


async def test_cu28_estudiante_consulta_sus_notas(cliente, simular):
    falso = simular({"role": "assistant", "content": None, "tool_calls": [_pedido("/evaluacion/calificaciones/mias")]},
                    {"role": "assistant", "content": "- Matemática: 78\n- Lenguaje: 85"})
    cabecera = await iniciar(cliente, "mquispe")
    r = await cliente.post(f"{URL}/consulta", headers=cabecera, json={"pregunta": "¿Cuáles son mis notas?"})
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["consultas"] == ["/evaluacion/calificaciones/mias"]
    assert falso.resultados[0]["estado"] == 200
    assert cuerpo["respuesta"] == "Matemática: 78. Lenguaje: 85."          # sin viñetas, apto para voz
    assert "mquispe" in falso.sistema and "estudiante" in falso.sistema
    assert "Gestión abierta" in falso.sistema and "id_periodo" in falso.sistema


async def test_cu28_notas_propias_marcadas(cliente, simular):
    """/mias y /mis-cuotas llegan marcadas como del usuario conectado (el modelo no debe atribuirlas a otro)."""
    falso = simular({"role": "assistant", "content": None,
                     "tool_calls": [_pedido("/evaluacion/calificaciones/mias", id_="a"),
                                    _pedido("/administracion/mis-cuotas", id_="b")]})
    cabecera = await iniciar(cliente, "mquispe")
    r = await cliente.post(f"{URL}/consulta", headers=cabecera, json={"pregunta": "Notas de Mariana Ticona"})
    assert r.status_code == 200, r.text
    for resultado in falso.resultados:
        assert resultado["estado"] == 200
        assert resultado["datos"]["pertenecen_a"].startswith("el usuario conectado")
        assert "datos" in resultado["datos"]
    assert "nunca los presentes" in falso.sistema


async def test_cu28_estudiante_no_ve_notas_de_otro(cliente, simular):
    falso = simular({"role": "assistant", "content": None,
                     "tool_calls": [_pedido("/evaluacion/boletines/4500002", {"id_periodo": 1})]},
                    {"role": "assistant", "content": "No tienes permiso para ver esa información."})
    cabecera = await iniciar(cliente, "mquispe")
    r = await cliente.post(f"{URL}/consulta", headers=cabecera, json={"pregunta": "Notas de otro estudiante"})
    assert r.status_code == 200, r.text
    assert falso.resultados[0]["estado"] == 403


async def test_cu28_docente_solo_sus_estudiantes(cliente, simular):
    falso = simular({"role": "assistant", "content": None,
                     "tool_calls": [_pedido("/personas/seguimiento/estudiantes/4500001", id_="a"),
                                    _pedido("/personas/seguimiento/estudiantes/4500007", id_="b")]})
    cabecera = await iniciar(cliente, "rflores")
    r = await cliente.post(f"{URL}/consulta", headers=cabecera, json={"pregunta": "Seguimiento de dos estudiantes"})
    assert r.status_code == 200, r.text
    assert [x["estado"] for x in falso.resultados] == [200, 403]      # 4500007 no es de sus clases


async def test_cu28_solo_rutas_get_del_catalogo(cliente, simular):
    falso = simular({"role": "assistant", "content": None,
                     "tool_calls": [_pedido("/seguridad/sesion", id_="a"), _pedido("/../salud", id_="b")]})
    cabecera = await iniciar(cliente, "direccion")
    r = await cliente.post(f"{URL}/consulta", headers=cabecera, json={"pregunta": "Cambia mi contraseña"})
    assert r.status_code == 200, r.text
    assert [x["estado"] for x in falso.resultados] == [400, 400]
    assert not catalogo.ruta_permitida("/administracion/inventario/1/movimientos/../../x")
    assert catalogo.ruta_permitida("/administracion/inventario/1/movimientos")


async def test_cu28_catalogo_segun_rol():
    assert "/seguridad/bitacora" in catalogo.descripcion("administrador")
    admin = catalogo.descripcion("administrador")
    assert "/reportes/opciones" in admin and "clave: asistencia" in admin and "rendimiento" in admin
    for rol in ("profesor", "estudiante", "tutor"):
        texto = catalogo.descripcion(rol)
        assert "/seguridad/bitacora" not in texto and "/administracion/morosos" not in texto
        assert "/horarios/consulta" in texto


async def test_cu28_maximo_de_consultas(cliente, simular):
    siempre = {"role": "assistant", "content": None, "tool_calls": [_pedido("/seguridad/perfil")]}
    simular(*[siempre] * (cu28.MAX_PASOS + 1))
    cabecera = await iniciar(cliente, "mquispe")
    r = await cliente.post(f"{URL}/consulta", headers=cabecera, json={"pregunta": "Pregunta en bucle"})
    assert r.status_code == 200, r.text
    assert len(r.json()["consultas"]) == cu28.MAX_PASOS
    assert r.json()["respuesta"].startswith("No pude completar")


async def test_cu28_queda_en_bitacora(cliente, simular):
    simular({"role": "assistant", "content": "Hola."})
    antes = await _valor("SELECT count(*) FROM bitacora WHERE modulo = 'ASISTENTE'")
    cabecera = await iniciar(cliente, "marioq")
    r = await cliente.post(f"{URL}/consulta", headers=cabecera, json={"pregunta": "¿Mis hijos deben cuotas?"})
    assert r.status_code == 200, r.text
    assert await _valor("SELECT count(*) FROM bitacora WHERE modulo = 'ASISTENTE'") == antes + 1
    assert await _valor("SELECT accion FROM bitacora WHERE modulo = 'ASISTENTE' ORDER BY id_bitacora DESC LIMIT 1") \
        == "Consultó al asistente: «¿Mis hijos deben cuotas?»"


async def test_cu28_pregunta_por_voz(cliente, simular, monkeypatch):
    simular({"role": "assistant", "content": "Tienes dos clases el lunes."})
    recibido = {}

    async def transcribir(audio, tipo):
        recibido.update(audio=audio, tipo=tipo)
        return "¿Qué clases tengo el lunes?"
    monkeypatch.setattr(groq, "transcribir", transcribir)
    cabecera = await iniciar(cliente, "rflores")
    r = await cliente.post(f"{URL}/voz", content=b"audio-de-prueba",
                           headers={**cabecera, "content-type": "audio/webm;codecs=opus"})
    assert r.status_code == 200, r.text
    assert r.json()["pregunta"] == "¿Qué clases tengo el lunes?"
    assert recibido == {"audio": b"audio-de-prueba", "tipo": "audio/webm;codecs=opus"}
    r = await cliente.post(f"{URL}/voz", content=b"", headers={**cabecera, "content-type": "audio/webm"})
    assert r.status_code == 400


async def test_cu28_voz_con_historial(cliente, simular, monkeypatch):
    falso = simular({"role": "assistant", "content": "La más baja fue 44."},
                    {"role": "assistant", "content": "Sin historial."})

    async def transcribir(audio, tipo):
        return "¿Y cuál sería la nota más baja?"
    monkeypatch.setattr(groq, "transcribir", transcribir)
    cabecera = await iniciar(cliente, "direccion")
    turnos = [{"pregunta": "¿Nota más alta de Matemática en 1ro A?", "respuesta": "Fue 96, de Terrazas Ticona Claudia."}]
    historial = base64.b64encode(json.dumps(turnos, ensure_ascii=False).encode("utf-8")).decode()
    r = await cliente.post(f"{URL}/voz", content=b"audio", headers={**cabecera, "content-type": "audio/webm",
                                                                    "x-historial": historial})
    assert r.status_code == 200, r.text
    contenidos = [(m["role"], m["content"]) for m in falso.mensajes[1:]]
    assert contenidos == [("user", turnos[0]["pregunta"]), ("assistant", turnos[0]["respuesta"]),
                          ("user", "¿Y cuál sería la nota más baja?")]
    # Cabecera inválida: se responde igual, sin historial
    r = await cliente.post(f"{URL}/voz", content=b"audio", headers={**cabecera, "content-type": "audio/webm",
                                                                    "x-historial": "no-es-base64!!"})
    assert r.status_code == 200, r.text
    assert [m["role"] for m in falso.mensajes[1:]] == ["user"]


def test_cu28_texto_para_voz():
    assert cu28._texto_para_voz("**Notas:**\n1. Matemática 78\n2. Física 70") == "Notas: Matemática 78. Física 70."
    assert cu28._texto_para_voz("Tu promedio es 81.5 en total.") == "Tu promedio es 81.5 en total."
    assert cu28._texto_para_voz("1ro\u202fA Biología\u2011Geografía") == "1ro A Biología-Geografía."


def test_cu28_compactacion_tabular():
    registros = [{"nombre": "Ana", "nota": 80.456, "obs": None}, {"nombre": "Luis", "nota": 70.0, "obs": None},
                 {"nombre": "Eva", "nota": 90.0, "obs": ""}]
    assert cu28._compactar({"lista": registros, "vacio": [], "dos": registros[:2]}) == {
        "lista": {"columnas": ["nombre", "nota"], "filas": [["Ana", 80.46], ["Luis", 70.0], ["Eva", 90.0]]},
        "dos": [{"nombre": "Ana", "nota": 80.46}, {"nombre": "Luis", "nota": 70.0}],   # menos de 3: sin tabla
    }
    largo = cu28._compactar([{"i": i} for i in range(cu28.MAX_ELEMENTOS_LISTA + 5)])
    assert len(largo["filas"]) == cu28.MAX_ELEMENTOS_LISTA and largo["omitidas"] == 5


def test_cu28_aviso_de_recorte():
    grande = {"estado": 200, "datos": [{"texto": "x" * 400, "n": i, "m": i} for i in range(cu28.MAX_ELEMENTOS_LISTA)]}
    contenido = cu28._contenido(grande)
    assert len(contenido) <= cu28.MAX_CARACTERES_RESULTADO
    salida = json.loads(contenido)
    assert salida["recortado"] is True and salida["estado"] == 200 and "incompleto" in salida["aviso"]
    pequeno = json.loads(cu28._contenido({"estado": 200, "datos": {"a": 1}}))
    assert "recortado" not in pequeno


async def _centralizador_con_notas(cliente, cabecera) -> tuple[dict, dict]:
    """Primer (curso, trimestre) de la base de prueba cuyo centralizador tiene notas."""
    periodos = (await cliente.get("/evaluacion/boletines/opciones/periodos", headers=cabecera)).json()
    cursos = (await cliente.get("/evaluacion/boletines/opciones/cursos", headers=cabecera)).json()
    for periodo in periodos:
        for curso in cursos:
            params = {"id_curso": curso["id_curso"], "id_periodo": periodo["id_periodo"]}
            r = await cliente.get("/evaluacion/centralizador", headers=cabecera, params=params)
            if r.status_code == 200 and sum(len(f["notas"]) for f in r.json()["filas"]) >= 5:
                return params, r.json()
    pytest.skip("La base de prueba no tiene notas en ningún centralizador")


async def test_cu28_resumen_del_centralizador(cliente, admin, simular):
    params, crudo = await _centralizador_con_notas(cliente, admin)
    falso = simular({"role": "assistant", "content": None, "tool_calls": [_pedido("/evaluacion/centralizador", params)]})
    r = await cliente.post(f"{URL}/consulta", headers=admin, json={"pregunta": "Nota más alta y más baja del curso"})
    assert r.status_code == 200, r.text
    datos = falso.resultados[0]["datos"]
    notas = [(n["nota_final"], f"{f['apellidos']} {f['nombre_persona']}", n["materia"])
             for f in crudo["filas"] for n in f["notas"]]
    alta, baja = max(v for v, _, _ in notas), min(v for v, _, _ in notas)
    resumen = datos["resumen"]["general_todas_las_materias"]
    assert resumen["nota_mas_alta"]["valor"] == round(alta, 2)
    assert resumen["nota_mas_baja"]["valor"] == round(baja, 2)
    assert {"estudiante": next(e for v, e, m in notas if v == alta),
            "materia": next(m for v, e, m in notas if v == alta)} in resumen["nota_mas_alta"]["quienes"]
    assert resumen["cantidad_estudiantes"] == len(crudo["filas"])
    assert datos["curso"] == crudo["curso"] and datos["periodo"] == crudo["periodo"]
    assert datos["notas"]["columnas"][0] == "estudiante" and len(datos["notas"]["filas"]) == len(crudo["filas"])
    assert "recortado" not in falso.resultados[0]
    # Resumen de cada materia: no se mezclan las notas de otras materias
    por_materia = datos["resumen"]["por_materia"]
    for materia in {m for _, _, m in notas}:
        de_materia = [(v, e) for v, e, m in notas if m == materia]
        alta_m, baja_m = max(v for v, _ in de_materia), min(v for v, _ in de_materia)
        assert por_materia[materia]["nota_mas_alta"]["valor"] == round(alta_m, 2)
        assert por_materia[materia]["nota_mas_baja"]["valor"] == round(baja_m, 2)
        assert {"estudiante": next(e for v, e in de_materia if v == baja_m)} in \
            por_materia[materia]["nota_mas_baja"]["quienes"]


async def test_cu28_resumen_del_reporte_de_asistencia(cliente, admin, simular):
    """Quién tiene menos asistencia en un curso: el servidor calcula el mínimo y el máximo del reporte fijo."""
    opciones = (await cliente.get("/reportes/opciones", headers=admin)).json()
    for periodo in opciones["periodos"]:
        for curso in opciones["cursos"]:
            params = {"id_curso": curso["id_curso"], "id_periodo": periodo["id_periodo"]}
            crudo = (await cliente.get("/reportes/estaticos/asistencia", headers=admin, params=params)).json()
            porcentajes = [(f["porcentaje"], f["estudiante"]) for f in crudo.get("filas", [])
                           if f.get("porcentaje") is not None]
            if len(porcentajes) >= 3:
                break
        else:
            continue
        break
    else:
        pytest.skip("La base de prueba no tiene asistencia registrada")
    falso = simular({"role": "assistant", "content": None,
                     "tool_calls": [_pedido("/reportes/estaticos/asistencia", params)]})
    r = await cliente.post(f"{URL}/consulta", headers=admin, json={"pregunta": "¿Quién tiene menos asistencia?"})
    assert r.status_code == 200, r.text
    datos = falso.resultados[0]["datos"]
    menor = min(v for v, _ in porcentajes)
    assert datos["resumen"]["menor_asistencia"]["valor"] == round(menor, 2)
    assert {"estudiante": next(e for v, e in porcentajes if v == menor)} in datos["resumen"]["menor_asistencia"]["quienes"]
    assert datos["resumen"]["mayor_asistencia"]["valor"] == round(max(v for v, _ in porcentajes), 2)
    assert datos["resumen"]["cantidad_estudiantes"] == len(crudo["filas"])
    assert datos["tabla"]["columnas"][0] == "estudiante" and len(datos["tabla"]["filas"]) == len(crudo["filas"])


def test_cu28_resumen_del_reporte_de_rendimiento():
    preparar = cu28._preparar("/reportes/estaticos/rendimiento", {
        "titulo": "Rendimiento por curso", "filtros": ["Curso: 1ro A"], "resumen": ["Promedio del curso: 70."],
        "columnas": [{"clave": "ci"}, {"clave": "estudiante"}, {"clave": "promedio"}],
        "filas": [{"ci": "1", "estudiante": "Ana", "promedio": 81.5}, {"ci": "2", "estudiante": "Luis", "promedio": 55},
                  {"ci": "3", "estudiante": "Eva", "promedio": None}]})
    assert preparar["resumen"]["mejor_promedio"] == {"valor": 81.5, "quienes": [{"estudiante": "Ana"}]}
    assert preparar["resumen"]["peor_promedio"]["quienes"] == [{"estudiante": "Luis"}]
    assert preparar["resumen"]["sin_datos"] == 1
    assert preparar["tabla"]["columnas"] == ["estudiante", "promedio"]


async def test_cu28_resumen_de_la_planilla(cliente, profesor, simular):
    clases = (await cliente.get("/evaluacion/calificaciones/clases", headers=profesor)).json()
    for periodo in clases["periodos"]:
        for clase in clases["clases"]:
            ruta = f"/evaluacion/calificaciones/planilla/{clase['id_asignacion']}"
            crudo = (await cliente.get(ruta, headers=profesor, params={"id_periodo": periodo["id_periodo"]})).json()
            finales = [e["nota_final"] for e in crudo.get("estudiantes", []) if e["nota_final"] is not None]
            if len(finales) >= 3:
                break
        else:
            continue
        break
    else:
        pytest.skip("La base de prueba no tiene planillas con notas")
    falso = simular({"role": "assistant", "content": None,
                     "tool_calls": [_pedido(ruta, {"id_periodo": periodo["id_periodo"]})]})
    r = await cliente.post(f"{URL}/consulta", headers=profesor, json={"pregunta": "¿Quién tiene la nota más alta?"})
    assert r.status_code == 200, r.text
    datos = falso.resultados[0]["datos"]
    assert datos["resumen"]["nota_mas_alta"]["valor"] == round(max(finales), 2)
    assert datos["resumen"]["nota_mas_baja"]["valor"] == round(min(finales), 2)
    assert datos["materia"] == crudo["clase"]["materia"] and datos["periodo"] == crudo["periodo"]["nombre_periodo"]


async def test_cu28_silencio_de_whisper(cliente, simular, monkeypatch):
    simular({"role": "assistant", "content": "No debería llegar aquí."})
    cabecera = await iniciar(cliente, "mquispe")
    for alucinacion in ("¡Gracias!", "Subtítulos realizados por la comunidad de Amara.org", "Música", " . "):
        async def transcribir(audio, tipo, texto=alucinacion):
            return texto
        monkeypatch.setattr(groq, "transcribir", transcribir)
        r = await cliente.post(f"{URL}/voz", content=b"audio", headers={**cabecera, "content-type": "audio/webm"})
        assert r.status_code == 400, alucinacion
        assert "No se escuchó la pregunta" in r.json()["detalle"]
    assert not cu28._es_silencio("¿Qué clases tengo el lunes?")
    assert not cu28._es_silencio("Gracias, ¿y mis notas de Física?")

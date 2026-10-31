"""
DATASET DE DEMOSTRACIÓN - SISTEMA ESCOLAR "MARISCAL SUCRE G"

Completa una base que ya tiene los scripts 01 a 07 (y opcionalmente 08) con un colegio
de tamaño mediano: ~500 estudiantes en los 20 cursos, sus tutores, ~30 docentes,
asignaciones y horarios, la gestión 2025 cerrada (historial) y la gestión 2026 en curso
(asistencia, notas, boletines, becas, cuotas, pagos con morosos, seguimiento,
comunicados e inventario).

NO borra ni modifica lo que ya existe: lee la base y completa alrededor (cursos con
asignaciones o estudiantes cargados a mano, horarios existentes, usuarios, etc.).
Todos los datos son FICTICIOS (nombres inventados, correos @example.com).

Uso (desde la carpeta backend, con su entorno virtual activado):

    python ../basededato/dataset/cargar_dataset.py --url postgresql://postgres@localhost:1982/escuela_local --clave CONTRASEÑA

    --clave     contraseña de TODOS los usuarios nuevos del dataset (docentes, tutores y
                estudiantes de secundaria). En producción usar una que NO esté en el repositorio.
    --simular   hace todo y al final deshace los cambios (para probar sin guardar).
    --hasta     último día con asistencia (por defecto hoy, hora de Bolivia).
    --semilla   misma semilla = mismos datos (por defecto 2026).
    --corregir-aulas  si hay asignaciones cargadas a mano cuya aula ya no tiene espacio en el horario,
                las pasa al aula de su curso (u otra libre). Es lo ÚNICO que modifica de lo existente,
                y solo con esta opción; muestra qué cambió.

Se ejecuta en UNA transacción: si algo falla, la base queda exactamente como estaba.
Durante la carga se apaga la auditoría (si no, la bitácora tendría cientos de miles de
filas "INSERT" sin usuario); al final se vuelve a encender y queda una sola fila en la
bitácora que resume la carga.
"""
import argparse
import asyncio
import getpass
import json
import random
import sys
import unicodedata
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone

import asyncpg
import bcrypt

# ---------------------------------------------------------------------------
# Datos ficticios
# ---------------------------------------------------------------------------
NOMBRES_M = """Juan Carlos Luis Jose Miguel Jorge Fernando Diego Santiago Mateo Sebastian Daniel Alejandro
Gabriel Samuel David Adrian Nicolas Joaquin Bruno Rodrigo Marco Victor Ricardo Andres Pablo Hugo Ivan Franz
Wilson Edwin Ruben Alvaro Gonzalo Mauricio Ronald Freddy Elias Emiliano Thiago Leonardo Benjamin Matias Tomas
Isaac Josue Kevin Cristian Gael Dylan Ian Liam Alan Erick Rafael Oscar Mario Hector Raul""".split()
NOMBRES_F = """Maria Ana Carmen Rosa Lucia Sofia Valentina Camila Isabella Mariana Daniela Gabriela Andrea Paola
Fernanda Valeria Natalia Jimena Alejandra Patricia Silvia Elena Veronica Claudia Monica Lourdes Ximena Abigail
Antonella Luciana Renata Micaela Nicole Fabiola Wendy Roxana Marisol Cintia Noemi Judith Teresa Juana Gladys
Martha Carla Delia Victoria Emma Zoe Ariana Brenda Karen Rocio Miriam Sara Julia Paula Adriana""".split()
APELLIDOS = """Quispe Mamani Condori Choque Flores Gutierrez Rojas Vargas Fernandez Lopez Perez Gonzales Rodriguez
Torrez Limachi Apaza Ticona Huanca Chambi Copa Callisaya Poma Nina Laura Cruz Villca Aruquipa Alanoca Yujra Calle
Ramos Mendoza Salazar Justiniano Suarez Vaca Rivero Montano Aguilar Coca Ortiz Velasco Arce Siles Paz Soria Medina
Zeballos Guzman Herrera Castro Ayala Choquehuanca Tola Machaca Quisbert Huarachi Patzi Ali Sirpa Mollinedo Uruchi
Chuquimia Ticlla Gemio Blanco Escobar Morales Navarro Rios Salinas Terrazas Valdez Zambrana""".split()
ZONAS = """Villa Fatima|Miraflores|Sopocachi|Obrajes|Achumani|Calacoto|San Pedro|Villa Copacabana|Ciudad Satelite|
Villa Adela|Alto Obrajes|Irpavi|Pampahasi|Villa San Antonio|Tembladerani|Munaypata|Chasquipampa|Cota Cota|
Bajo Llojeta|Villa El Carmen""".replace("\n", "").split("|")
CALLES = ["calle 1", "calle 3", "calle 8", "calle 12", "calle 21", "av. Busch", "av. Arce", "av. 6 de Agosto",
          "av. Hernando Siles", "av. del Ejercito", "calle Murillo", "calle Sagarnaga", "pasaje Los Pinos"]
OCUPACIONES = ["Comerciante", "Chofer", "Enfermera", "Ingeniero", "Contadora", "Albanil", "Profesora", "Abogado",
               "Medico", "Costurera", "Mecanico", "Policia", "Secretaria", "Carpintero", "Ama de casa",
               "Administradora", "Agricultor", "Electricista", "Odontologa", "Arquitecto"]
BOLIVIA = timezone(timedelta(hours=-4))   # America/La_Paz (sin horario de verano)
EXPEDIDOS = ["LP"] * 14 + ["SC", "CB", "OR", "PT", "CH"]
MEDICAS = ["Asma leve: usa inhalador", "Alergia a la penicilina", "Usa lentes", "Rinitis alergica",
           "Intolerancia a la lactosa", "Epilepsia controlada con medicacion"]
MOTIVOS_BECA = ["Rendimiento academico", "Hermanos en la unidad educativa", "Situacion economica",
                "Hijo de docente", "Convenio institucional"]

FERIADOS = {date(2026, 1, 1), date(2026, 1, 22), date(2026, 2, 16), date(2026, 2, 17), date(2026, 4, 3),
            date(2026, 5, 1), date(2026, 6, 4), date(2026, 6, 22), date(2026, 8, 6), date(2026, 11, 2)}
VACACIONES_INVIERNO = (date(2026, 7, 6), date(2026, 7, 17))

DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes"]
# Inicial y Primaria: 3 bloques de 90 min (mañana). Secundaria: 4 bloques de 75 min,
# paralelo A en la mañana y B en la tarde.
BLOQUES_BASICO = [("08:00", "09:30"), ("09:45", "11:15"), ("11:30", "13:00")]
BLOQUES_SEC_MANANA = [("07:45", "09:00"), ("09:00", "10:15"), ("10:30", "11:45"), ("11:45", "13:00")]
BLOQUES_SEC_TARDE = [("13:45", "15:00"), ("15:00", "16:15"), ("16:30", "17:45"), ("17:45", "19:00")]

TITULOS = {
    "Matematica": "Lic. en Matematica", "Comunicacion y Lenguajes": "Lic. en Linguistica",
    "Lengua Extranjera": "Lic. en Idiomas", "Lengua Originaria": "Lic. en Linguistica Aymara",
    "Ciencias Sociales": "Lic. en Ciencias Sociales", "Educacion Fisica y Deportes": "Lic. en Educacion Fisica",
    "Educacion Musical": "Lic. en Musica", "Artes Plasticas y Visuales": "Lic. en Artes Plasticas",
    "Tecnica Tecnologica": "Ing. de Sistemas", "Ciencias Naturales": "Lic. en Biologia",
    "Biologia-Geografia": "Lic. en Biologia", "Fisica": "Lic. en Fisica", "Quimica": "Lic. en Quimica",
    "Cosmovisiones, Filosofia y Psicologia": "Lic. en Filosofia",
    "Valores, Espiritualidades y Religiones": "Lic. en Ciencias de la Religion",
}

# Estudiantes por curso (los que ya existen cuentan)
OBJETIVO = {"Inicial": 20, "Primaria": 26, "Secundaria": 24}
EDAD_INICIAL = {"Inicial": 3, "Primaria": 5, "Secundaria": 11}   # edad = base + orden del grado


def ascii_min(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if c.isalnum()).lower()


def hm(texto: str) -> time:
    h, m = texto.split(":")
    return time(int(h), int(m))


def minutos(t: time) -> int:
    return t.hour * 60 + t.minute


class Plan:
    """Todo lo que se va a insertar, armado en memoria antes de tocar la base."""

    def __init__(self, rng: random.Random):
        self.rng = rng
        self.personas = []          # tuplas para persona
        self.profesores = []
        self.tutores = []
        self.estudiantes = []
        self.tutor_estudiante = []
        self.usuarios = []          # (nombre_usuario, rol, ci)
        self.perfiles = []          # perfil de cada estudiante nuevo
        self.ins_2026 = []          # (ci, id_curso, fecha)
        self.ins_2025 = []          # (ci, clave_curso_2025, fecha)
        self.becas = []


async def main() -> None:
    p = argparse.ArgumentParser(description="Carga el dataset de demostración del sistema escolar.")
    p.add_argument("--url", required=True, help="postgresql://usuario:clave@host:puerto/base")
    p.add_argument("--clave", help="contraseña de los usuarios nuevos (si no se indica, se pide sin mostrarla)")
    p.add_argument("--hasta", type=date.fromisoformat, default=datetime.now(BOLIVIA).date())
    p.add_argument("--semilla", type=int, default=2026)
    p.add_argument("--simular", action="store_true")
    p.add_argument("--corregir-aulas", action="store_true",
                   help="pasa al aula de su curso las asignaciones existentes que no entran en el horario de su aula")
    args = p.parse_args()
    if args.clave is None:
        args.clave = getpass.getpass("Contraseña para los usuarios nuevos: ")
        if getpass.getpass("Repítala: ") != args.clave:
            sys.exit("Las contraseñas no coinciden.")
    if len(args.clave) < 8:
        sys.exit("La contraseña debe tener al menos 8 caracteres.")

    url = args.url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url, statement_cache_size=0)   # statement_cache_size=0: compatible con el pooler de Supabase
    try:
        await conn.execute("SET TIME ZONE 'America/La_Paz'")
        tr = conn.transaction()
        await tr.start()
        try:
            resumen = await cargar(conn, args)
        except BaseException:
            await tr.rollback()
            raise
        if args.simular:
            await tr.rollback()
            print("\nSIMULACIÓN: se deshicieron todos los cambios.")
        else:
            await tr.commit()
            print("\nDataset cargado y guardado.")
        for k, v in resumen.items():
            print(f"  {k:.<34} {v}")
    finally:
        await conn.close()


async def cargar(conn: asyncpg.Connection, args) -> dict:
    rng = random.Random(args.semilla)
    hasta = args.hasta
    log = lambda m: print(f"[{datetime.now():%H:%M:%S}] {m}", flush=True)

    # ------------------------------------------------------------------ estado actual
    g26 = await conn.fetchrow("SELECT * FROM gestion WHERE anio = 2026")
    if g26 is None or g26["estado_gestion"] != "abierta":
        sys.exit("Se necesita la gestión 2026 abierta (script 07).")
    if await conn.fetchval("SELECT 1 FROM gestion WHERE anio = 2025"):
        sys.exit("El dataset ya está cargado en esta base (existe la gestión 2025).")
    hasta = min(hasta, g26["fecha_final_g"])

    cursos = [dict(r) for r in await conn.fetch(
        "SELECT * FROM v_curso ORDER BY id_nivel, orden_grado, paralelo")]
    curso_por_id = {c["id_curso"]: c for c in cursos}
    clave_curso = {(c["nombre_nivel"], c["orden_grado"], c["paralelo"]): c for c in cursos}
    materias = {r["id_materia"]: r["nombre_materia"] for r in await conn.fetch("SELECT * FROM materia")}
    id_materia = {v: k for k, v in materias.items()}
    plan_grado = defaultdict(list)
    for r in await conn.fetch("SELECT * FROM materia_grado ORDER BY id_materia_mg"):
        plan_grado[r["id_grado_mg"]].append(r["id_materia_mg"])
    aulas = {r["numero"]: r["id_aula"] for r in await conn.fetch("SELECT * FROM aula")}
    asig_existentes = [dict(r) for r in await conn.fetch(
        "SELECT * FROM asignacion_profesor_clase WHERE id_gestion_asignacion = $1", g26["id_gestion"])]
    horario_existente = await conn.fetch(
        """SELECT h.*, a.ci_profesor_asignacion, a.id_aula_asignacion, a.id_curso_asignacion
             FROM horario h JOIN asignacion_profesor_clase a ON a.id_asignacion = h.id_asignacion_horario
            WHERE a.id_gestion_asignacion = $1""", g26["id_gestion"])
    inscritos = defaultdict(int)
    for r in await conn.fetch("""SELECT id_curso_inscripcion, count(*) n FROM inscripcion
                                  WHERE id_gestion_inscripcion = $1 AND estado_inscripcion = 'activa'
                                  GROUP BY 1""", g26["id_gestion"]):
        inscritos[r["id_curso_inscripcion"]] = r["n"]
    cis_usados = {r["ci"] for r in await conn.fetch("SELECT ci FROM persona")}
    usuarios_usados = {r["nombre_usuario"] for r in await conn.fetch("SELECT nombre_usuario FROM usuario")}
    administrativos = [r["ci_administrativo"] for r in await conn.fetch(
        "SELECT ci_administrativo FROM administrativo ORDER BY ci_administrativo")]
    if not administrativos:
        sys.exit("Se necesita al menos un administrativo para registrar los cobros.")
    cajeros = sorted(administrativos, key=lambda c: c != "1000002")   # secretaria primero si existe
    periodos26 = {r["nombre_periodo"]: dict(r) for r in await conn.fetch(
        "SELECT * FROM periodo WHERE id_gestion_periodo = $1", g26["id_gestion"])}
    roles = {r["nombre_rol"]: r["id_rol"] for r in await conn.fetch("SELECT * FROM rol")}

    # ------------------------------------------------------------------ generadores
    contador_ci = defaultdict(int)

    def nuevo_ci(base: int) -> str:
        while True:
            contador_ci[base] += 1
            ci = str(base + contador_ci[base])
            if ci not in cis_usados:
                cis_usados.add(ci)
                return ci

    def nuevo_usuario(nombre: str, apellidos: str) -> str:
        base = ascii_min(nombre[0] + apellidos.split()[0])
        candidato, n = base, 1
        while candidato in usuarios_usados:
            n += 1
            candidato = f"{base}{n}"
        usuarios_usados.add(candidato)
        return candidato

    correos_usados = set()

    def correo(nombre: str, apellidos: str) -> str:
        base = f"{ascii_min(nombre)}.{ascii_min(apellidos.split()[0])}"
        candidato, n = base, 1
        while candidato in correos_usados:
            n += 1
            candidato = f"{base}{n}"
        correos_usados.add(candidato)
        return f"{candidato}@example.com"

    def telefono() -> str:
        return f"{rng.choice('67')}{rng.randint(0, 9999999):07d}"

    def direccion() -> str:
        return f"Zona {rng.choice(ZONAS)}, {rng.choice(CALLES)} #{rng.randint(10, 2999)}"

    plan = Plan(rng)

    def persona(ci, nombre, apellidos, sexo, nacimiento=None, tel=None, email=None, expedido=None, dire=None):
        plan.personas.append((ci, expedido or rng.choice(EXPEDIDOS), nombre, apellidos, sexo, nacimiento,
                              dire, tel, email))

    # ------------------------------------------------------------------ docentes
    log("Planificando docentes y asignaciones...")
    es = lambda c, nivel: c["nombre_nivel"] == nivel

    def clave_docente(c: dict, materia: str) -> str:
        """Qué docente dicta esa materia en ese curso (misma clave = mismo docente)."""
        if es(c, "Inicial"):
            if materia == "Educacion Fisica y Deportes":
                return "ef_basico"
            if materia == "Educacion Musical":
                return "musica_basico"
            return f"maestra_{c['id_curso']}"
        if es(c, "Primaria"):
            if materia == "Educacion Fisica y Deportes":
                return "ef_basico"
            if materia == "Educacion Musical":
                return "musica_basico"
            if materia == "Lengua Extranjera":
                return "ingles_basico"
            return f"grado_{c['id_curso']}"
        if materia in ("Matematica", "Comunicacion y Lenguajes"):
            return f"{materia}_{c['paralelo']}"
        return f"sec_{materia}"

    docente_de = {}                               # clave -> ci
    for a in asig_existentes:                     # los docentes ya asignados conservan su rol
        k = clave_docente(curso_por_id[a["id_curso_asignacion"]], materias[a["id_materia_asignacion"]])
        docente_de.setdefault(k, a["ci_profesor_asignacion"])

    def crear_docente(materia: str, nivel: str) -> str:
        ci = nuevo_ci(2100000)
        sexo = rng.choice("MF")
        nombre = rng.choice(NOMBRES_M if sexo == "M" else NOMBRES_F)
        apellidos = f"{rng.choice(APELLIDOS)} {rng.choice(APELLIDOS)}"
        nac = date(rng.randint(1970, 1996), rng.randint(1, 12), rng.randint(1, 28))
        persona(ci, nombre, apellidos, sexo, nac, telefono(), correo(nombre, apellidos), dire=direccion())
        titulo = {"Inicial": "Prof. de Educacion Inicial", "Primaria": "Prof. de Educacion Primaria"}.get(nivel) \
            if nivel != "Secundaria" and materia not in ("Educacion Fisica y Deportes", "Educacion Musical",
                                                          "Lengua Extranjera") else TITULOS.get(materia)
        contrato = date(rng.randint(2008, 2025), 2, rng.randint(1, 5))
        plan.profesores.append((ci, titulo, contrato, 2026 - contrato.year + rng.randint(0, 6)))
        plan.usuarios.append((nuevo_usuario(nombre, apellidos), "profesor", ci))
        return ci

    # Asignaciones nuevas 2026 (las que ya existen se respetan)
    existe = {(a["id_curso_asignacion"], a["id_materia_asignacion"]) for a in asig_existentes}

    def aula_de(c: dict, materia: str) -> str:
        if materia == "Educacion Fisica y Deportes":
            return "CANCHA" if es(c, "Secundaria") else "PATIO"
        if es(c, "Inicial"):
            return f"I-0{c['orden_grado']}"
        if es(c, "Primaria"):
            return f"A-10{c['orden_grado']}"
        return f"B-20{c['orden_grado']}"

    asig_nuevas = []                              # dict: curso, materia, profesor, aula
    for c in cursos:
        for idm in plan_grado[c["id_grado"]]:
            if (c["id_curso"], idm) in existe:
                continue
            m = materias[idm]
            k = clave_docente(c, m)
            if k not in docente_de:
                docente_de[k] = crear_docente(m, c["nombre_nivel"])
            asig_nuevas.append({"curso": c["id_curso"], "materia": idm, "profesor": docente_de[k],
                                "aula": aula_de(c, m), "clave": k})
    if "PATIO" not in aulas:
        aulas["PATIO"] = None                     # se crea al insertar

    # ------------------------------------------------------------------ horario
    log("Armando horarios sin choques...")
    ocupado = {"curso": defaultdict(list), "prof": defaultdict(list), "aula": defaultdict(list)}

    def libre(tipo, clave, dia, ini, fin):
        return all(not (i < fin and ini < f) for (d, i, f) in ocupado[tipo][clave] if d == dia)

    def ocupar(curso, prof, aula, dia, ini, fin):
        ocupado["curso"][curso].append((dia, ini, fin))
        ocupado["prof"][prof].append((dia, ini, fin))
        if aula is not None:
            ocupado["aula"][aula].append((dia, ini, fin))

    bloques_de_asig = defaultdict(int)
    dias_de_asig = defaultdict(set)
    for h in horario_existente:
        ocupar(h["id_curso_asignacion"], h["ci_profesor_asignacion"], h["id_aula_asignacion"], h["dia"],
               minutos(h["hora_inicio_h"]), minutos(h["hora_final_f"]))
        bloques_de_asig[h["id_asignacion_horario"]] += 1
        dias_de_asig[h["id_asignacion_horario"]].add(h["dia"])

    def bloques_necesarios(c, m):
        if m == "Matematica":
            return 2
        if m == "Comunicacion y Lenguajes" and not (es(c, "Secundaria") and c["orden_grado"] >= 3):
            return 2
        if m == "Ciencias Naturales":
            return 2
        return 1

    def grilla(c):
        if not es(c, "Secundaria"):
            return BLOQUES_BASICO
        return BLOQUES_SEC_MANANA if c["paralelo"] == "A" else BLOQUES_SEC_TARDE

    nuevos_bloques = []                           # (ref asignacion, dia, ini, fin)

    def programar(ref, c, prof, aula_id, n, dias_usados):
        """Busca n bloques libres en días distintos; devuelve la lista o None (sin ocupar nada)."""
        elegidos, dias_ocup = [], set(dias_usados)
        candidatos = [(d, b) for d in DIAS for b in grilla(c)]
        rng.shuffle(candidatos)
        candidatos.sort(key=lambda x: x[0] in dias_ocup)    # primero días sin esa materia
        for d, (ini_t, fin_t) in candidatos:
            if len(elegidos) == n:
                break
            if d in dias_ocup:
                continue
            ini, fin = minutos(hm(ini_t)), minutos(hm(fin_t))
            if (libre("curso", c["id_curso"], d, ini, fin) and libre("prof", prof, d, ini, fin)
                    and (aula_id is None or libre("aula", aula_id, d, ini, fin))
                    and all(not (e[0] == d) for e in elegidos)):
                elegidos.append((d, ini, fin, ini_t, fin_t))
                dias_ocup.add(d)
        return elegidos if len(elegidos) == n else None

    # Primero las asignaciones de docentes compartidos (más restringidas)
    trabajo = []
    for a in asig_existentes:
        c = curso_por_id[a["id_curso_asignacion"]]
        if bloques_de_asig[a["id_asignacion"]] == 0:
            trabajo.append(("existente", a["id_asignacion"], c, a["ci_profesor_asignacion"],
                            a["id_aula_asignacion"], materias[a["id_materia_asignacion"]], None))
    for i, a in enumerate(asig_nuevas):
        c = curso_por_id[a["curso"]]
        trabajo.append(("nueva", i, c, a["profesor"], a["aula"], materias[a["materia"]], a["clave"]))
    carga_prof = defaultdict(int)
    for t in trabajo:
        carga_prof[t[3]] += 1
    # primero las asignaciones que ya existían (su docente y aula no se eligen), luego las más restringidas
    trabajo.sort(key=lambda t: (t[0] != "existente", -carga_prof[t[3]], -bloques_necesarios(t[2], t[5])))

    # Aulas comunes para cuando el aula del curso ya está llena (asignaciones cargadas a mano)
    aulas_comunes = sorted(n for n in aulas if n[:1] in "ABI" and "-" in n)
    CANCHAS = [x for x in ("PATIO", "CANCHA") if x in aulas]
    clave_aula = lambda numero: aulas.get(numero) if aulas.get(numero) is not None else numero  # PATIO aún sin id

    aulas_corregidas, sin_horario = [], []
    for origen, ref, c, prof, aula, m, k in trabajo:
        n = bloques_necesarios(c, m)
        aula_clave = clave_aula(aula) if isinstance(aula, str) else aula
        elegidos = programar(ref, c, prof, aula_clave, n, dias_de_asig[(origen, ref)])
        if elegidos is None and origen == "nueva":
            # 1) otra aula con el mismo docente; 2) otro docente (en su aula o en otra)
            alternativas = [x for x in (CANCHAS if m == "Educacion Fisica y Deportes" else aulas_comunes) if x != aula]
            rng.shuffle(alternativas)
            for alt in alternativas:
                elegidos = programar(ref, c, prof, clave_aula(alt), n, set())
                if elegidos:
                    aula, aula_clave = alt, clave_aula(alt)
                    break
            if elegidos is None:
                nuevo = crear_docente(m, c["nombre_nivel"])
                for alt in [aula] + alternativas:
                    elegidos = programar(ref, c, nuevo, clave_aula(alt), n, set())
                    if elegidos:
                        prof, aula, aula_clave = nuevo, alt, clave_aula(alt)
                        docente_de[k] = nuevo
                        break
            asig_nuevas[ref]["profesor"], asig_nuevas[ref]["aula"] = prof, aula
        if elegidos is None and origen == "existente" and args.corregir_aulas:
            # Asignación cargada a mano en un aula sin espacio: se pasa al aula del curso (u otra libre)
            propia = aula_de(c, m)
            otras = [x for x in (CANCHAS if m == "Educacion Fisica y Deportes" else aulas_comunes) if x != propia]
            for alt in [propia] + otras:
                elegidos = programar(ref, c, prof, clave_aula(alt), n, set())
                if elegidos:
                    aula_clave = clave_aula(alt)
                    aulas_corregidas.append((ref, alt, c["nombre_curso"], m))
                    break
        if elegidos is None:
            if origen == "existente":
                sin_horario.append(f"{m} en {c['nombre_curso']}")
                continue                           # asignación cargada a mano sin espacio: se deja sin horario
            sys.exit(f"No se pudo armar el horario de {m} en {c['nombre_curso']}.")
        for d, ini, fin, ini_t, fin_t in elegidos:
            ocupar(c["id_curso"], prof, aula_clave, d, ini, fin)
            nuevos_bloques.append((origen, ref, d, hm(ini_t), hm(fin_t)))

    # ------------------------------------------------------------------ familias y estudiantes
    log("Generando familias y estudiantes...")
    familias = []

    def nueva_familia():
        ap, am = rng.sample(APELLIDOS, 2)
        fam = {"ap": ap, "am": am, "hijos_cursos": set(), "tutores": [], "n": 0}
        tipo = rng.random()
        padre = madre = None
        if tipo < 0.97:
            if tipo < 0.65 or tipo >= 0.90:
                padre = (rng.choice(NOMBRES_M), f"{ap} {rng.choice(APELLIDOS)}", "M", "padre")
            if tipo < 0.90:
                madre = (rng.choice(NOMBRES_F), f"{am} {rng.choice(APELLIDOS)}", "F", "madre")
        else:
            abuela = rng.random() < 0.7
            fam_t = (rng.choice(NOMBRES_F if abuela else NOMBRES_M), f"{am} {rng.choice(APELLIDOS)}",
                     "F" if abuela else "M", "abuela" if abuela else "abuelo")
            madre = fam_t
        miembros = [t for t in (madre, padre) if t]
        principal = 0 if len(miembros) == 1 or rng.random() < 0.6 else 1
        for i, (nom, ape, sexo, parentesco) in enumerate(miembros):
            ci = nuevo_ci(3100000)
            nac = date(rng.randint(1968, 1995), rng.randint(1, 12), rng.randint(1, 28))
            persona(ci, nom, ape, sexo, nac, telefono(), correo(nom, ape), dire=direccion())
            plan.tutores.append((ci, rng.choice(OCUPACIONES)))
            plan.usuarios.append((nuevo_usuario(nom, ape), "tutor", ci))
            fam["tutores"].append({"ci": ci, "parentesco": parentesco, "principal": i == principal,
                                   "responsable": i == principal})
        familias.append(fam)
        return fam

    def perfil_estudiante():
        r = rng.random()
        hab = (rng.uniform(0.28, 0.46) if r < 0.05 else rng.uniform(0.5, 0.64) if r < 0.25
               else rng.uniform(0.65, 0.85) if r < 0.85 else rng.uniform(0.86, 0.97))
        r = rng.random()
        asis = ((rng.uniform(0.15, 0.22), 0.06, 0.02) if r < 0.03 else
                (rng.uniform(0.07, 0.11), 0.07, 0.02) if r < 0.15 else
                (rng.uniform(0.015, 0.035), rng.uniform(0.02, 0.06), 0.012))
        r = rng.random()
        pago, deuda = ("moroso", rng.choice([1, 1, 2, 2, 3])) if r < 0.10 else (("tardio", 0) if r < 0.16
                                                                                 else ("puntual", 0))
        return hab, asis, pago, deuda

    estudiantes_nuevos = []                        # dict con todo lo del estudiante
    for c in cursos:
        objetivo = min(OBJETIVO[c["nombre_nivel"]], c["cupo_maximo"])
        for _ in range(max(0, objetivo - inscritos[c["id_curso"]])):
            candidatas = [f for f in familias if f["n"] < 3 and c["id_grado"] not in f["hijos_cursos"]]
            fam = rng.choice(candidatas) if candidatas and rng.random() < 0.33 else nueva_familia()
            fam["hijos_cursos"].add(c["id_grado"])
            fam["n"] += 1
            sexo = rng.choice("MF")
            nombre = rng.choice(NOMBRES_M if sexo == "M" else NOMBRES_F)
            apellidos = f"{fam['ap']} {fam['am']}"
            edad = EDAD_INICIAL[c["nombre_nivel"]] + c["orden_grado"]
            nac = date(2026 - edad - 1, rng.randint(4, 12), rng.randint(1, 28))
            ci = nuevo_ci(4600000)
            persona(ci, nombre, apellidos, sexo, nac, dire=direccion())
            plan.estudiantes.append((ci, f"RUDE-{ci}", rng.choice(MEDICAS) if rng.random() < 0.05 else None))
            for t in fam["tutores"]:
                plan.tutor_estudiante.append((t["ci"], ci, t["parentesco"], t["principal"], t["responsable"]))
            if es(c, "Secundaria"):
                plan.usuarios.append((nuevo_usuario(nombre, apellidos), "estudiante", ci))
            hab, asis, pago, deuda = perfil_estudiante()
            est = {"ci": ci, "curso": c, "hab": hab, "asis": asis, "pago": pago, "deuda": deuda, "fam": fam,
                   "retiro": None}
            estudiantes_nuevos.append(est)
            plan.ins_2026.append((ci, c["id_curso"], date(2026, 1, rng.randint(12, 30))))

    # Algunos retiros durante 2026 (~1 %)
    for est in rng.sample(estudiantes_nuevos, max(1, len(estudiantes_nuevos) // 100)):
        est["retiro"] = (date(2026, rng.randint(5, 9), rng.randint(1, 28)),
                         rng.choice(["Cambio de domicilio", "Traslado a otra unidad educativa", "Viaje al exterior"]))

    # Becas 2026 (~8 %): hermanos, rendimiento, situación económica; pocas del 100 %
    for est in estudiantes_nuevos:
        r = rng.random()
        if est["fam"]["n"] >= 3 and r < 0.5:
            plan.becas.append((est["ci"], 25, MOTIVOS_BECA[1]))
        elif r < 0.07:
            pct = rng.choice([25, 25, 50, 50, 75]) if rng.random() > 0.08 else 100
            plan.becas.append((est["ci"], pct, rng.choice(MOTIVOS_BECA)))

    # Historial 2025: continuos (curso anterior), repitentes (mismo grado) y nuevos
    def curso_anterior(c):
        nivel, orden, par = c["nombre_nivel"], c["orden_grado"], c["paralelo"]
        if orden > 1:
            k = (nivel, orden - 1, par) if (nivel, orden - 1, par) in clave_curso else (nivel, orden - 1, "A")
            return clave_curso.get(k)
        anterior = {"Primaria": ("Inicial", 2), "Secundaria": ("Primaria", 6)}.get(nivel)
        return clave_curso.get((*anterior, "A")) if anterior else None

    ocupacion_2025 = defaultdict(int)
    for est in estudiantes_nuevos:
        c = est["curso"]
        r = rng.random()
        destino = None
        if r < 0.03 and not (es(c, "Inicial") and c["orden_grado"] == 1):
            destino, est["tipo"] = c, "repitente"
        elif r < 0.88:
            destino, est["tipo"] = curso_anterior(c), "continuo"
        if destino is None or ocupacion_2025[destino["id_curso"]] >= destino["cupo_maximo"] - 2:
            est["tipo"] = "nuevo"
            continue
        ocupacion_2025[destino["id_curso"]] += 1
        est["curso_2025"] = destino
        plan.ins_2025.append((est["ci"], destino["id_curso"], date(2025, 1, rng.randint(13, 31))))

    # ------------------------------------------------------------------ inserciones
    log(f"Insertando {len(plan.personas)} personas, {len(plan.usuarios)} usuarios...")
    tablas_auditadas = [(r["tgname"], r["tabla"]) for r in await conn.fetch(
        """SELECT t.tgname, c.relname AS tabla FROM pg_trigger t JOIN pg_class c ON c.oid = t.tgrelid
            WHERE NOT t.tgisinternal AND t.tgname LIKE 'trg_auditar_%'""")]
    for tg, tabla in tablas_auditadas:
        await conn.execute(f'ALTER TABLE {tabla} DISABLE TRIGGER {tg}')

    if aulas["PATIO"] is None:
        aulas["PATIO"] = await conn.fetchval(
            "INSERT INTO aula (numero, capacidad, tipo_aula) VALUES ('PATIO', 120, 'patio') RETURNING id_aula")

    await conn.copy_records_to_table("persona", records=plan.personas, columns=[
        "ci", "expedido", "nombre_persona", "apellidos", "sexo", "fecha_nacimiento", "direccion", "telefono", "email"])
    await conn.copy_records_to_table("profesor", records=plan.profesores, columns=[
        "ci_profesor", "titulo_academico", "fecha_contrato", "anios_experiencia"])
    await conn.copy_records_to_table("tutor", records=plan.tutores, columns=["ci_tutor", "ocupacion"])
    await conn.copy_records_to_table("estudiante", records=plan.estudiantes, columns=[
        "ci_estudiante", "rude", "observacion_medica"])
    await conn.copy_records_to_table("tutor_estudiante", records=plan.tutor_estudiante, columns=[
        "ci_tutor_tutorestudiante", "ci_estudiante_tutorestudiante", "parentesco", "es_principal",
        "es_responsable_pago"])
    hash_clave = bcrypt.hashpw(args.clave.encode(), bcrypt.gensalt(rounds=10)).decode()
    await conn.copy_records_to_table("usuario", records=[
        (u, hash_clave, roles[r], ci) for u, r, ci in plan.usuarios],
        columns=["nombre_usuario", "password_hash", "id_rol_usuario", "ci_persona"])

    # Asignaciones y horarios 2026
    log(f"Insertando {len(asig_nuevas)} asignaciones y {len(nuevos_bloques)} bloques de horario...")
    for a in asig_nuevas:
        a["id"] = await conn.fetchval(
            """INSERT INTO asignacion_profesor_clase (ci_profesor_asignacion, id_materia_asignacion,
                                                     id_curso_asignacion, id_aula_asignacion, id_gestion_asignacion)
               VALUES ($1, $2, $3, $4, $5) RETURNING id_asignacion""",
            a["profesor"], a["materia"], a["curso"], aulas[a["aula"]], g26["id_gestion"])
    for id_asig, numero, curso, materia in aulas_corregidas:
        await conn.execute("UPDATE asignacion_profesor_clase SET id_aula_asignacion = $1 WHERE id_asignacion = $2",
                           aulas[numero], id_asig)
        log(f"  aula corregida: {materia} en {curso} -> {numero}")
    for texto in sin_horario:
        log(f"  sin horario (asignacion existente sin espacio): {texto}")
    await conn.executemany(
        "INSERT INTO horario (id_asignacion_horario, dia, hora_inicio_h, hora_final_f) VALUES ($1, $2, $3, $4)",
        [((asig_nuevas[ref]["id"] if origen == "nueva" else ref), d, ini, fin)
         for origen, ref, d, ini, fin in nuevos_bloques])

    # ------------------------------------------------------------------ gestión 2025 (historial)
    log("Creando la gestión 2025 (historial)...")
    g25 = await conn.fetchval(
        """INSERT INTO gestion (anio, fecha_inicio_g, fecha_final_g, nota_minima_aprobacion, estado_gestion)
           VALUES (2025, '2025-02-03', '2025-12-05', 51, 'abierta') RETURNING id_gestion""")
    await conn.execute(
        """INSERT INTO periodo (nombre_periodo, tipo, fecha_inicio_p, fecha_final_p, id_gestion_periodo)
           VALUES ('1er Trimestre', 'trimestre', '2025-02-03', '2025-05-16', $1),
                  ('2do Trimestre', 'trimestre', '2025-05-19', '2025-08-29', $1),
                  ('3er Trimestre', 'trimestre', '2025-09-01', '2025-12-05', $1)""", g25)
    await conn.execute(
        """INSERT INTO dimension_evaluacion (nombre_dimension, puntaje_maximo, es_autoevaluacion, orden_dimension,
                                            id_gestion_dimension)
           SELECT nombre_dimension, puntaje_maximo, es_autoevaluacion, orden_dimension, $1
             FROM dimension_evaluacion WHERE id_gestion_dimension = $2""", g25, g26["id_gestion"])
    await conn.execute(
        """INSERT INTO arancel (monto_mensual, dia_vencimiento, id_gestion_arancel, id_nivel_arancel)
           SELECT round(monto_mensual * 0.92 / 10) * 10, dia_vencimiento, $1, id_nivel_arancel
             FROM arancel WHERE id_gestion_arancel = $2""", g25, g26["id_gestion"])
    # Asignaciones 2025 (mismo docente que en 2026 para esa materia y curso), sin horario
    asig26 = await conn.fetch("""SELECT * FROM asignacion_profesor_clase WHERE id_gestion_asignacion = $1""",
                              g26["id_gestion"])
    cursos_2025 = {est["curso_2025"]["id_curso"] for est in estudiantes_nuevos if "curso_2025" in est}
    await conn.executemany(
        """INSERT INTO asignacion_profesor_clase (ci_profesor_asignacion, id_materia_asignacion, id_curso_asignacion,
                                                 id_aula_asignacion, id_gestion_asignacion) VALUES ($1, $2, $3, $4, $5)""",
        [(a["ci_profesor_asignacion"], a["id_materia_asignacion"], a["id_curso_asignacion"],
          a["id_aula_asignacion"], g25) for a in asig26 if a["id_curso_asignacion"] in cursos_2025])

    # Inscripciones
    await conn.copy_records_to_table("inscripcion", records=[
        (ci, g25, curso, fecha) for ci, curso, fecha in plan.ins_2025],
        columns=["ci_estudiante_inscripcion", "id_gestion_inscripcion", "id_curso_inscripcion", "fecha_inscripcion"])
    await conn.copy_records_to_table("inscripcion", records=[
        (ci, g26["id_gestion"], curso, fecha) for ci, curso, fecha in plan.ins_2026],
        columns=["ci_estudiante_inscripcion", "id_gestion_inscripcion", "id_curso_inscripcion", "fecha_inscripcion"])
    await conn.copy_records_to_table("beca", records=[
        (pct, motivo, ci, g26["id_gestion"]) for ci, pct, motivo in plan.becas],
        columns=["porcentaje_descuento", "motivo_beca", "ci_estudiante_beca", "id_gestion_beca"])

    # Perfil de cada estudiante nuevo (lo usan las consultas masivas de abajo)
    await conn.execute("""CREATE TEMP TABLE tmp_perfil (
        ci VARCHAR(20) PRIMARY KEY, hab NUMERIC, hab25 NUMERIC, p_aus NUMERIC, p_tard NUMERIC, p_just NUMERIC,
        pago TEXT, deuda INT, retiro DATE, motivo_retiro TEXT) ON COMMIT DROP""")
    await conn.copy_records_to_table("tmp_perfil", records=[
        (e["ci"], e["hab"], (rng.uniform(0.26, 0.40) if e.get("tipo") == "repitente" else max(e["hab"], 0.63)),
         *e["asis"], e["pago"], e["deuda"], e["retiro"][0] if e["retiro"] else None,
         e["retiro"][1] if e["retiro"] else None) for e in estudiantes_nuevos])

    # ------------------------------------------------------------------ notas
    # Puntaje por dimensión = máximo * (habilidad del estudiante ± ruido determinista)
    sql_detalle = """
        INSERT INTO calificacion_detalle (id_calificacion_detalle, id_dimension_detalle, puntaje)
        SELECT c.id_calificacion, d.id_dimension,
               round(d.puntaje_maximo * least(0.99, greatest(0.05,
                     coalesce({hab}, 0.72)
                     + ((abs(hashtext(c.id_calificacion || '-' || d.id_dimension)) % 1000) / 1000.0 - 0.5) * 0.16
                     + CASE WHEN d.es_autoevaluacion THEN 0.08 ELSE 0 END)))
          FROM calificacion c
          JOIN periodo p ON p.id_periodo = c.id_periodo_calificacion
          JOIN dimension_evaluacion d ON d.id_gestion_dimension = p.id_gestion_periodo
          LEFT JOIN tmp_perfil pf ON pf.ci = c.ci_estudiante_calificacion
         WHERE p.id_gestion_periodo = $1 {filtro}
           AND NOT EXISTS (SELECT 1 FROM calificacion_detalle x
                            WHERE x.id_calificacion_detalle = c.id_calificacion AND x.id_dimension_detalle = d.id_dimension)"""
    sql_cabecera = """
        INSERT INTO calificacion (ci_estudiante_calificacion, id_materia_calificacion, id_periodo_calificacion,
                                  fecha_calificacion)
        SELECT i.ci_estudiante_inscripcion, a.id_materia_asignacion, p.id_periodo, p.fecha_final_p - 7
          FROM inscripcion i
          JOIN asignacion_profesor_clase a ON a.id_curso_asignacion = i.id_curso_inscripcion
                                          AND a.id_gestion_asignacion = i.id_gestion_inscripcion
          JOIN periodo p ON p.id_gestion_periodo = i.id_gestion_inscripcion
         WHERE i.id_gestion_inscripcion = $1 AND p.id_periodo = ANY($2::int[])
           AND (i.fecha_retiro IS NULL OR p.fecha_final_p < i.fecha_retiro)
        ON CONFLICT DO NOTHING"""

    log("Notas y boletines 2025...")
    p25 = [r["id_periodo"] for r in await conn.fetch(
        "SELECT id_periodo FROM periodo WHERE id_gestion_periodo = $1 ORDER BY fecha_inicio_p", g25)]
    await conn.execute(sql_cabecera, g25, p25)
    await conn.execute(sql_detalle.format(hab="pf.hab25", filtro=""), g25)
    for idp in p25:
        await conn.execute("CALL sp_emitir_boletines($1, NULL, NULL)", idp)

    # ------------------------------------------------------------------ cuotas y retiros 2026
    log("Cuotas 2025 y 2026...")
    for mes in range(2, 13):
        await conn.execute("CALL sp_generar_cuotas_mes($1, $2, NULL)", g25, mes)
    for mes in range(2, hasta.month + 1):
        primer_dia = date(2026, mes, 1)
        await conn.execute(
            """UPDATE inscripcion i SET estado_inscripcion = 'retirada', fecha_retiro = pf.retiro,
                                        motivo_retiro = pf.motivo_retiro
                 FROM tmp_perfil pf
                WHERE pf.ci = i.ci_estudiante_inscripcion AND i.id_gestion_inscripcion = $1
                  AND pf.retiro < $2 AND i.estado_inscripcion = 'activa'""", g26["id_gestion"], primer_dia)
        await conn.execute("CALL sp_generar_cuotas_mes($1, $2, NULL)", g26["id_gestion"], mes)
    await conn.execute(
        """UPDATE inscripcion i SET estado_inscripcion = 'retirada', fecha_retiro = pf.retiro, motivo_retiro = pf.motivo_retiro
             FROM tmp_perfil pf WHERE pf.ci = i.ci_estudiante_inscripcion AND i.id_gestion_inscripcion = $1
              AND pf.retiro <= $2 AND i.estado_inscripcion = 'activa'""", g26["id_gestion"], hasta)

    # Pagos: puntuales, tardíos y morosos (los morosos deben sus últimas cuotas vencidas).
    # Solo se cobran las cuotas creadas ahora; los recibos siguen la secuencia, en orden de fecha.
    log("Pagos con recibo...")
    await conn.execute(
        """WITH nuevas AS (
               SELECT pm.id_pago, pm.fecha_vencimiento, pm.id_gestion_pago, pm.ci_estudiante_pago,
                      coalesce(pf.pago, 'puntual') AS pago, coalesce(pf.deuda, 0) AS deuda,
                      abs(hashtext('pago' || pm.id_pago)) AS h,
                      row_number() OVER (PARTITION BY pm.ci_estudiante_pago, pm.id_gestion_pago
                                         ORDER BY pm.mes DESC) AS desde_el_final
                 FROM pago_mensualidad pm
                 LEFT JOIN tmp_perfil pf ON pf.ci = pm.ci_estudiante_pago
                WHERE pm.estado_pago = 'pendiente' AND pm.creado_en = now()
                  AND pm.fecha_vencimiento <= $1
           ),
           a_pagar AS (
               SELECT n.*,
                      CASE WHEN n.pago = 'tardio' AND n.id_gestion_pago = $2
                           THEN n.fecha_vencimiento + 3 + (n.h % 22)::int
                           ELSE n.fecha_vencimiento - (n.h % 9)::int END AS fecha
                 FROM nuevas n
                WHERE NOT (n.pago = 'moroso' AND n.id_gestion_pago = $2 AND n.desde_el_final <= n.deuda)
           ),
           validas AS (
               SELECT a.*, row_number() OVER (ORDER BY a.fecha, a.id_pago) AS orden
                 FROM a_pagar a WHERE a.fecha <= $1
           ),
           base AS (
               SELECT greatest(coalesce((SELECT max(numero_recibo) FROM pago_mensualidad), 0),
                               (SELECT last_value FROM seq_numero_recibo)) AS n
           )
        UPDATE pago_mensualidad pm SET
               estado_pago = 'pagado', fecha_pago = v.fecha, numero_recibo = base.n + v.orden,
               metodo_pago = (ARRAY['efectivo','efectivo','efectivo','efectivo','qr','qr','transferencia',
                                    'transferencia','tarjeta'])[1 + v.h % 9],
               ci_administrativo_pago = ($3::text[])[1 + (CASE WHEN v.h % 10 < 8 THEN 0
                                                          ELSE v.h % array_length($3::text[], 1) END)],
               ci_tutor_pago = (SELECT te.ci_tutor_tutorestudiante FROM tutor_estudiante te
                                 WHERE te.ci_estudiante_tutorestudiante = v.ci_estudiante_pago
                                 ORDER BY te.es_responsable_pago DESC, te.es_principal DESC LIMIT 1)
          FROM validas v, base
         WHERE pm.id_pago = v.id_pago""", hasta, g26["id_gestion"], cajeros)
    await conn.execute("""SELECT setval('seq_numero_recibo',
                                        greatest((SELECT max(numero_recibo) FROM pago_mensualidad),
                                                 (SELECT last_value FROM seq_numero_recibo)))""")

    # ------------------------------------------------------------------ cierre 2025
    log("Cerrando la gestión 2025 (promovidos y reprobados)...")
    await conn.execute("CALL sp_cerrar_gestion($1, NULL)", g25)

    # ------------------------------------------------------------------ asistencia 2026
    log("Asistencia 2026 (puede tardar un poco)...")
    no_clases = sorted(FERIADOS | {VACACIONES_INVIERNO[0] + timedelta(days=i)
                                  for i in range((VACACIONES_INVIERNO[1] - VACACIONES_INVIERNO[0]).days + 1)})
    await conn.execute(
        """INSERT INTO asistencia (id_asignacion_asistencia, ci_estudiante_asistencia, fecha_asistencia,
                                   estado_asistencia, observacion_asistencia)
           SELECT a.id_asignacion, i.ci_estudiante_inscripcion, d.dia,
                  CASE WHEN x.r < pf_aus THEN 'ausente'
                       WHEN x.r < pf_aus + pf_tard THEN 'tardanza'
                       WHEN x.r < pf_aus + pf_tard + pf_just THEN 'justificado'
                       ELSE 'presente' END,
                  CASE WHEN x.r >= pf_aus + pf_tard AND x.r < pf_aus + pf_tard + pf_just
                       THEN (ARRAY['Presento certificado medico', 'Permiso por tramite familiar',
                                   'Cita medica', 'Representacion del colegio en evento deportivo'])[1 + x.h % 4] END
             FROM asignacion_profesor_clase a
             JOIN (SELECT DISTINCT id_asignacion_horario, dia FROM horario) h ON h.id_asignacion_horario = a.id_asignacion
             JOIN inscripcion i ON i.id_curso_inscripcion = a.id_curso_asignacion
                               AND i.id_gestion_inscripcion = a.id_gestion_asignacion
             JOIN gestion g ON g.id_gestion = a.id_gestion_asignacion
             LEFT JOIN tmp_perfil pf ON pf.ci = i.ci_estudiante_inscripcion
             CROSS JOIN LATERAL (SELECT coalesce(pf.p_aus, 0.03) AS pf_aus, coalesce(pf.p_tard, 0.04) AS pf_tard,
                                        coalesce(pf.p_just, 0.01) AS pf_just) q
             CROSS JOIN LATERAL (SELECT s::date AS dia FROM generate_series(g.fecha_inicio_g, $2::date, '1 day') s) d
             CROSS JOIN LATERAL (SELECT abs(hashtext(i.ci_estudiante_inscripcion || a.id_asignacion || d.dia)) AS h) hh
             CROSS JOIN LATERAL (SELECT hh.h AS h, (hh.h % 10000) / 10000.0 AS r) x
            WHERE a.id_gestion_asignacion = $1
              AND extract(isodow FROM d.dia) = array_position(
                      ARRAY['lunes','martes','miercoles','jueves','viernes','sabado','domingo'], h.dia)
              AND d.dia <> ALL($3::date[])
              AND d.dia >= i.fecha_inscripcion
              AND (i.fecha_retiro IS NULL OR d.dia < i.fecha_retiro)
           ON CONFLICT DO NOTHING""", g26["id_gestion"], hasta, no_clases)

    # ------------------------------------------------------------------ notas 2026
    log("Notas y boletines 2026...")
    t1, t2, t3 = (periodos26[n]["id_periodo"] for n in ("1er Trimestre", "2do Trimestre", "3er Trimestre"))
    terminados = [periodos26[n]["id_periodo"] for n in ("1er Trimestre", "2do Trimestre")
                  if periodos26[n]["fecha_final_p"] < hasta]
    en_curso = [t3] if periodos26["3er Trimestre"]["fecha_inicio_p"] <= hasta else []
    await conn.execute(sql_cabecera, g26["id_gestion"], terminados + en_curso)
    await conn.execute(sql_detalle.format(hab="pf.hab", filtro="AND p.id_periodo = ANY($2::int[])"),
                       g26["id_gestion"], terminados)
    # 3er trimestre en curso: solo Ser y Saber registrados
    await conn.execute(sql_detalle.format(hab="pf.hab", filtro="AND p.id_periodo = ANY($2::int[]) AND d.orden_dimension <= 2"),
                       g26["id_gestion"], en_curso)
    await conn.execute("UPDATE periodo SET estado_periodo = 'cerrado' WHERE id_periodo = ANY($1::int[])", terminados)
    for idp in terminados:
        await conn.execute("CALL sp_emitir_boletines($1, NULL, NULL)", idp)

    # ------------------------------------------------------------------ seguimiento, comunicados, inventario
    log("Seguimiento, comunicados e inventario...")
    profesor_de_curso = defaultdict(list)
    for a in await conn.fetch("SELECT * FROM asignacion_profesor_clase WHERE id_gestion_asignacion = $1",
                              g26["id_gestion"]):
        profesor_de_curso[a["id_curso_asignacion"]].append(a["ci_profesor_asignacion"])
    fin_rango = min(hasta, date(2026, 10, 30))

    def fecha_2026(desde=date(2026, 2, 16)):
        return desde + timedelta(days=rng.randint(0, max(0, (fin_rango - desde).days)))

    seguimientos = []
    activos = [e for e in estudiantes_nuevos if not e["retiro"]]
    for e in rng.sample(activos, min(70, len(activos))):
        prof = rng.choice(profesor_de_curso[e["curso"]["id_curso"]])
        if e["hab"] < 0.47:
            seguimientos.append((e["ci"], "academico", None, "Bajo rendimiento en varias materias del trimestre",
                                 "Se cita al tutor para acordar un plan de refuerzo", fecha_2026(date(2026, 4, 1)), prof))
        elif e["hab"] > 0.9 and rng.random() < 0.6:
            seguimientos.append((e["ci"], "merito", None, rng.choice([
                "Primer lugar en la olimpiada de matematica del distrito", "Destacada participacion en la feria de ciencias",
                "Mejor promedio del curso en el trimestre"]), None, fecha_2026(), prof))
        elif rng.random() < 0.7:
            grav = rng.choice(["leve", "leve", "leve", "grave"])
            seguimientos.append((e["ci"], "conducta", grav, rng.choice([
                "Interrumpe la clase de forma reiterada", "Uso del celular durante la clase", "Llega tarde con frecuencia",
                "Pelea con un companero en el recreo", "No presenta tareas de forma reiterada"]),
                "Llamada de atencion" if grav == "leve" else "Citacion al tutor y compromiso firmado", fecha_2026(), prof))
        else:
            seguimientos.append((e["ci"], "salud", None, rng.choice([
                "Se siente mal durante la clase, se comunica al tutor", "Lesion leve en educacion fisica",
                "Presenta fiebre, el tutor lo recoge"]), "Se informa al tutor", fecha_2026(), prof))
    await conn.copy_records_to_table("seguimiento_estudiante", records=seguimientos, columns=[
        "ci_estudiante_seguimiento", "tipo_seguimiento", "gravedad", "descripcion_seguimiento", "accion_tomada",
        "fecha_seguimiento", "ci_registrado_por"])

    directora = cajeros[-1] if len(cajeros) > 1 else cajeros[0]
    comunicados = [
        ("Bienvenida a la gestion 2026", "Damos la bienvenida a estudiantes y familias. Las clases inician el lunes 2 de febrero.",
         "general", "todos", None, None, None, directora, datetime(2026, 1, 28, 9)),
        ("Feriado de Carnaval", "No habra clases el lunes 16 y martes 17 de febrero por Carnaval.",
         "general", "todos", None, None, None, directora, datetime(2026, 2, 12, 10)),
        ("Dia del Maestro", "El 6 de junio celebramos a nuestros docentes. Agradecemos el acto preparado por los cursos.",
         "general", "todos", None, None, None, directora, datetime(2026, 6, 3, 11)),
        ("Descanso pedagogico de invierno", "El descanso de invierno sera del 6 al 17 de julio. Las clases se reanudan el 20 de julio.",
         "general", "todos", None, None, None, directora, datetime(2026, 7, 1, 9)),
        ("Aniversario de la unidad educativa", "Invitamos a toda la comunidad al desfile y la kermes del aniversario.",
         "general", "todos", None, None, None, directora, datetime(2026, 9, 10, 8)),
    ]
    for c in rng.sample(cursos, 8):
        prof = rng.choice(profesor_de_curso[c["id_curso"]])
        comunicados.append(("Evaluacion del trimestre", f"Se recuerda a {c['nombre_curso']} que la evaluacion sera la proxima semana.",
                            "general", "curso", None, c["id_curso"], None, prof,
                            datetime.combine(fecha_2026(date(2026, 3, 1)), time(10))))
    for e in [x for x in activos if x["hab"] < 0.47][:6]:
        prof = rng.choice(profesor_de_curso[e["curso"]["id_curso"]])
        cita = datetime.combine(fecha_2026(date(2026, 5, 1)), time(rng.choice([9, 10, 11, 15])))
        comunicados.append(("Citacion al tutor", "Se solicita su presencia para conversar sobre el rendimiento del estudiante.",
                            "citacion", "estudiante", cita, None, e["ci"], prof, cita - timedelta(days=3)))
    zona = BOLIVIA
    ids_com = []
    for t in comunicados:
        ids_com.append(await conn.fetchval(
            """INSERT INTO comunicado (titulo, contenido, tipo_comunicado, alcance, fecha_citacion, id_gestion_comunicado,
                                       id_curso_comunicado, ci_estudiante_comunicado, ci_autor, fecha_publicacion)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) RETURNING id_comunicado""",
            t[0], t[1], t[2], t[3], t[4].replace(tzinfo=zona) if t[4] else None, g26["id_gestion"], t[5], t[6], t[7],
            t[8].replace(tzinfo=zona)))
    lecturas = set()
    tutores_cis = [t[0] for t in plan.tutores]
    for idc in ids_com[:5]:
        for ci in rng.sample(tutores_cis, min(len(tutores_cis), rng.randint(60, 180))):
            lecturas.add((idc, ci))
    await conn.copy_records_to_table("comunicado_lectura", records=list(lecturas),
                                     columns=["id_comunicado_lectura", "ci_persona_lectura"])

    articulos = [("Computadoras portatiles", 25), ("Microscopios", 12), ("Mesas de laboratorio", 8),
                 ("Instrumentos musicales (zampona y charango)", 30), ("Botiquin de primeros auxilios", 6),
                 ("Extintores", 10), ("Pizarras acrilicas", 20), ("Libros de biblioteca", 450),
                 ("Conos de entrenamiento", 40), ("Tizas y borradores (cajas)", 60)]
    existentes_inv = {r["nombre_inventario"] for r in await conn.fetch("SELECT nombre_inventario FROM inventario")}
    for nombre, cant in articulos:
        if nombre in existentes_inv:
            continue
        idi = await conn.fetchval("INSERT INTO inventario (nombre_inventario) VALUES ($1) RETURNING id_inventario", nombre)
        movs = [("entrada", cant, "Compra de la gestion", None, datetime(2026, 2, rng.randint(2, 20), 10))]
        for _ in range(rng.randint(1, 3)):
            movs.append(("salida", max(1, cant // rng.randint(5, 15)), "Entrega a docentes",
                         rng.choice(["Sala de profesores", "LAB-1", "COMP-1", "MUS-1", "CANCHA"]),
                         datetime.combine(fecha_2026(date(2026, 3, 1)), time(rng.randint(8, 12)))))
        for tipo, n, motivo, destino, cuando in sorted(movs, key=lambda m: m[4]):
            await conn.execute(
                """INSERT INTO movimiento_inventario (id_inventario_movimiento, tipo_accion_inventario, cantidad_movimiento,
                                                     motivo_movimiento, destino_movimiento, ci_administrativo_movimiento,
                                                     fecha_acceso_inventario)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                idi, tipo, n, motivo, destino, rng.choice(cajeros), cuando.replace(tzinfo=zona))

    # ------------------------------------------------------------------ fin
    for tg, tabla in tablas_auditadas:
        await conn.execute(f'ALTER TABLE {tabla} ENABLE TRIGGER {tg}')
    resumen = {
        "Estudiantes nuevos": len(estudiantes_nuevos),
        "  con historial 2025": len(plan.ins_2025),
        "  retirados en 2026": sum(1 for e in estudiantes_nuevos if e["retiro"]),
        "Tutores nuevos": len(plan.tutores),
        "Docentes nuevos": len(plan.profesores),
        "Usuarios nuevos": len(plan.usuarios),
        "Asignaciones 2026 nuevas": len(asig_nuevas),
        "Bloques de horario nuevos": len(nuevos_bloques),
        "Aulas corregidas": len(aulas_corregidas),
        "Asignaciones sin horario": len(sin_horario),
        "Asistencias (total en la base)": await conn.fetchval("SELECT count(*) FROM asistencia"),
        "Calificaciones (total)": await conn.fetchval("SELECT count(*) FROM calificacion"),
        "Cuotas (total)": await conn.fetchval("SELECT count(*) FROM pago_mensualidad"),
        "Cuotas atrasadas": await conn.fetchval("SELECT count(*) FROM v_estado_pagos WHERE estado_actual = 'atrasado'"),
        "Becas nuevas": len(plan.becas),
        "Resultado 2025": await conn.fetchval(
            """SELECT string_agg(resultado_final || ': ' || n, ', ') FROM (SELECT resultado_final, count(*) n
                 FROM inscripcion WHERE id_gestion_inscripcion = $1 GROUP BY 1) x""", g25),
        "Tamano de la base": await conn.fetchval("SELECT pg_size_pretty(pg_database_size(current_database()))"),
    }
    await conn.execute("SELECT fn_registrar_bitacora($1, 'ACADEMICO', 'OTRO', NULL, NULL, NULL, $2::jsonb)",
                       "Carga del dataset de demostracion (datos ficticios)",
                       json.dumps({k.strip(): str(v) for k, v in resumen.items()}))
    return resumen


if __name__ == "__main__":
    asyncio.run(main())

# Backend — API del Sistema Escolar (FastAPI)

API en Python que usa el frontend. **Aquí está la lógica de negocio del sistema**: login, permisos por rol, validaciones y altas/bajas/modificaciones. La base de datos (`basededato/sql/`) guarda los datos y sus relaciones, con unos pocos triggers y procedimientos.

> **Estado:** Ciclo 1 implementado — **seguridad** (CU01 iniciar sesión y recuperar contraseña, CU02 usuarios, CU03 roles y permisos, CU04 bitácora) y **personas** (CU06 estudiantes, CU08 tutores y vínculos). Los demás casos de uso siguen pendientes (su archivo explica las reglas que deben cumplir).

---

## 1. Requisitos obligatorios

Trabajamos 5 personas: **todos deben usar exactamente estas versiones**. Si una versión no coincide, aparecen errores que "en mi máquina sí funcionan".

| Herramienta | Versión obligatoria | Para qué |
|---|---|---|
| **Python** | **3.14.x** (probado con 3.14.3) | Lenguaje del backend |
| pip | 26.x (viene con Python 3.14) | Instalar dependencias |
| Git | cualquiera reciente | Control de versiones |
| **PostgreSQL** | **18.x** | Base de datos local para desarrollar ([descarga](https://www.postgresql.org/download/windows/)) |

Dependencias del proyecto (ya fijadas; **no se instalan a mano una por una**):

| Paquete | Versión |
|---|---|
| fastapi | 0.141.1 |
| uvicorn[standard] | 0.54.0 |
| pydantic | 2.13.5 |
| pydantic-settings | 2.15.0 |
| sqlalchemy[asyncio] | 2.1.1 |
| asyncpg | 0.31.0 |
| pyjwt[crypto] | 2.15.0 |
| bcrypt | 5.0.0 |
| pytest *(pruebas)* | 9.1.1 |
| pytest-asyncio *(pruebas)* | 1.4.0 |
| httpx2 *(pruebas)* | 2.13.1 |

Las versiones exactas de **todas** las dependencias, incluidas las internas, están en `requirements.lock`.

### Verifica tus versiones

```bash
python --version        # debe decir Python 3.14.x
python -m pip --version # debe decir pip 26.x ... (python 3.14)
git --version
psql --version          # debe decir psql (PostgreSQL) 18.x
```

Si `psql` "no se reconoce", está instalado pero no en el PATH: se encuentra en `C:\Program Files\PostgreSQL\18\bin\psql.exe`. También puedes usar pgAdmin.

En Windows, si `python --version` muestra otra versión, usa el lanzador `py`: `py -3.14 --version`.
Si no tienes Python 3.14, descárgalo de <https://www.python.org/downloads/> y marca **"Add python.exe to PATH"** al instalar.

---

## 2. Levantar el proyecto en local

Todos los comandos se ejecutan **dentro de la carpeta `backend/`**.

### Paso 1 — Crear el entorno virtual (solo la primera vez)

El entorno virtual (`.venv`) aísla las dependencias del proyecto de las de tu computadora.

**Windows (PowerShell):**
```powershell
cd backend
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (CMD / Símbolo del sistema):**
```bat
cd backend
py -3.14 -m venv .venv
.venv\Scripts\activate.bat
```

> En Windows las rutas usan `\`. Si escribes `.venv/Scripts/...` en CMD verás el error *"'.venv' no se reconoce como un comando"*.

**Linux / macOS:**
```bash
cd backend
python3.14 -m venv .venv
source .venv/bin/activate
```

Cuando está activado, la terminal muestra `(.venv)` al inicio de la línea. **Actívalo cada vez que abras una terminal nueva.**

### Paso 2 — Instalar las dependencias (versiones exactas)

```bash
python -m pip install -r requirements.lock
```

> Usa siempre `requirements.lock` (no `requirements.txt`): así todos tienen **las mismas versiones hasta la última dependencia interna**.

### Paso 3 — Crear la base de datos local (solo la primera vez)

Sigue la sección **"En tu PostgreSQL local"** de [basededato/sql/LEEME.md](../basededato/sql/LEEME.md): crear la base `escuela` y ejecutar los scripts `01` a `08` en orden. El `08` trae datos y usuarios de prueba para poder iniciar sesión.

### Paso 4 — Configurar las variables de entorno

```bash
# Windows
copy .env.example .env
# Linux / macOS
cp .env.example .env
```

Abre `.env` y completa los valores (ver sección 3).

### Paso 5 — Levantar la API

```bash
uvicorn app.main:app --reload
```

- API: <http://localhost:8000/api/v1/salud> → debe responder `{"estado":"ok"}`
- Documentación interactiva (Swagger): <http://localhost:8000/docs>

`--reload` reinicia el servidor solo cada vez que guardas un archivo. Para detenerlo: `Ctrl + C`.

Si falta `DATABASE_URL` o `JWT_SECRETO` en el `.env`, el servidor no arranca y dice qué variable falta.

### Paso 6 — Ejecutar las pruebas

```bash
pytest
```

Sin más configuración solo corre la prueba de humo (`/salud`). Las pruebas de los casos de uso
necesitan una base **de pruebas** creada con los scripts 01 a 08 (ver `basededato/sql/LEEME.md`).
Cada prueba corre en una transacción que se deshace al final: la base no cambia.

```powershell
# PowerShell (cambia usuario, contraseña, puerto y nombre de la base por los tuyos)
$env:TEST_DATABASE_URL = "postgresql+asyncpg://postgres:TU_CONTRASENA@localhost:5432/escuela_prueba"
pytest
```

```bash
# Linux / macOS
TEST_DATABASE_URL="postgresql+asyncpg://postgres:TU_CONTRASENA@localhost:5432/escuela_prueba" pytest
```

### Usuarios de prueba

`08_datos_prueba.sql` crea 6 usuarios (todos con la misma contraseña, indicada al final de ese archivo):
`direccion` y `secretaria` (administrador), `rflores` y `erojas` (docente), `mquispe` (estudiante) y `marioq` (tutor).
También se puede iniciar sesión con el correo de la persona (por ejemplo, el de `direccion`).

---

## 3. Variables de entorno (`.env`)

| Variable | Dónde se obtiene | Ejemplo |
|---|---|---|
| `DATABASE_URL` | Tu PostgreSQL local: usuario, contraseña, puerto y base `escuela` | `postgresql+asyncpg://postgres:CLAVE@localhost:5432/escuela` |
| `JWT_SECRETO` | Clave para firmar los tokens de sesión. Generarla con `python -c "import secrets; print(secrets.token_urlsafe(48))"` | `kX3v…` (48+ caracteres) |
| `JWT_MINUTOS` | Duración de la sesión en minutos | `480` |
| `CORS_ORIGINS` | URL del frontend en local | `http://localhost:5173` |

Si el grupo usa **Supabase como hosting** de la base, `DATABASE_URL` sale de Supabase → **Connect** → *Transaction pooler* (puerto 6543), cambiando `postgresql://` por `postgresql+asyncpg://`.

**Seguridad:**
- El archivo `.env` **nunca** se sube a Git (ya está en `.gitignore`).
- Contraseñas y `JWT_SECRETO` se comparten por un canal privado, **no** por el repositorio.

---

## 4. Estructura del proyecto

El sistema se organiza en **6 paquetes**. Cada paquete tiene sus archivos compartidos afuera y **un archivo por caso de uso** dentro de `casos_uso/`.

```
backend/
├── app/
│   ├── main.py                  ← crea la API y registra los 6 paquetes
│   ├── nucleo/                  ← compartido por TODOS los paquetes
│   │   ├── config.py            ← lee el .env
│   │   ├── bd.py                ← conexión a PostgreSQL (sesión por petición, hora de Bolivia)
│   │   ├── seguridad.py         ← contraseñas bcrypt y token JWT propio
│   │   ├── dependencias.py      ← usuario_actual, requiere_rol(...)
│   │   └── errores.py           ← errores de negocio y de la BD → respuestas HTTP
│   └── paquetes/
│       └── personas/            ← ejemplo de un paquete
│           ├── models.py        ← tablas (SQLAlchemy ORM)               (compartido)
│           ├── schemas.py       ← datos de entrada y salida (Pydantic)  (compartido)
│           ├── repository.py    ← consultas y escrituras a la BD        (compartido)
│           ├── politicas.py     ← reglas de negocio comunes             (compartido)
│           ├── router.py        ← los endpoints /api/v1/personas/...
│           └── casos_uso/
│               ├── cu05_registrar_actualizar_persona.py
│               ├── cu06_gestionar_estudiante.py
│               └── ...
└── tests/                       ← una carpeta de pruebas por paquete
```

| Paquete | Casos de uso |
|---|---|
| `seguridad` | CU01–CU04: sesión, usuarios, roles, bitácora |
| `personas` | CU05–CU11: personas, estudiantes, tutores, docentes, administrativos |
| `academico` | CU12–CU17: niveles, cursos, materias, asignaciones, gestión, inscripciones |
| `horarios` | CU18–CU20: aulas y horarios |
| `evaluacion` | CU21–CU24: asistencia, calificaciones, boletines |
| `administracion` | CU25–CU27: pagos, inventario, comunicados |

**Flujo de una petición:** `router.py` → `casos_uso/cuXX_*.py` → `politicas.py` / `repository.py` → base de datos.

**Reglas al implementar un caso de uso:**
- Cada archivo de `casos_uso/` ya tiene en su encabezado:
  - actores y rol;
  - tablas que usa;
  - **las reglas de negocio que debe programar**;
  - los objetos de la BD que aprovecha (trigger, procedimiento o vista);
  - precondición y postcondición.

  Implementa respetando eso.
- **La lógica va aquí, no en la base.** Valida en `politicas.py` o en el caso de uso antes de escribir. La BD solo garantiza la integridad de los datos (`CHECK`, `UNIQUE`, FK) y ejecuta sus triggers: auditoría, choques de horario y stock.
- Todo acceso a la BD pasa por `repository.py` (SQLAlchemy). Los 3 procedimientos (`sp_generar_cuotas_mes`, `sp_emitir_boletines`, `sp_cerrar_gestion`) se ejecutan con `CALL`.
- Cada petición informa a la BD quién hace el cambio (`app.id_usuario`, `app.ip`) para que la bitácora lo registre. Eso lo hace `nucleo/bd.py`.
- Rutas en español: `/api/v1/<paquete>/<recurso>`.

---

## 5. Reglas del equipo sobre dependencias

1. **No actualices ninguna versión por tu cuenta.** Cualquier cambio se acuerda con el grupo.
2. Para **agregar** una dependencia nueva (acordada):
   ```bash
   python -m pip install nombre==X.Y.Z             # siempre con versión exacta
   ```
   - Agrégala con `==X.Y.Z` en `requirements.txt` (o en `requirements-dev.txt` si es solo para pruebas).
   - Regenera el lock y vuelve a poner el encabezado del archivo:
     - Linux/macOS/Git Bash/CMD: `python -m pip freeze > requirements.lock`
     - PowerShell: `cmd /c "python -m pip freeze > requirements.lock"`. En PowerShell el `>` guarda en UTF-16 y rompe el archivo para el resto.
   - Sube los tres archivos en el mismo commit y avisa al grupo.
3. Cuando alguien cambie el lock, los demás ejecutan de nuevo `python -m pip install -r requirements.lock`.

---

## 6. Problemas comunes

| Problema | Solución |
|---|---|
| `'python' no se reconoce` o sale otra versión | Usa `py -3.14` en Windows; reinstala Python 3.14 marcando "Add to PATH" |
| PowerShell: *"la ejecución de scripts está deshabilitada"* al activar `.venv` | Ejecuta una vez: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `ModuleNotFoundError: No module named 'fastapi'` | No activaste el `.venv`. Actívalo (paso 1) y vuelve a intentar |
| CMD: *"'.venv' no se reconoce como un comando interno o externo"* | En CMD usa `\`: `.venv\Scripts\activate.bat` |
| `[Errno 10048]` / *address already in use* | El puerto 8000 está ocupado: `uvicorn app.main:app --reload --port 8001` |
| Error al conectar a la base de datos | Revisa `DATABASE_URL` en `.env`: prefijo `postgresql+asyncpg://`, puerto (5432 por defecto), contraseña y que la base `escuela` exista |
| `relation "persona" does not exist` | Falta ejecutar los scripts de `basededato/sql/` en tu base local (paso 3) |

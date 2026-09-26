# Frontend — Sistema Escolar (React)

Aplicación web en React + TypeScript que usan administrativos, docentes, estudiantes y tutores. **Solo habla con el backend FastAPI**: el inicio de sesión y todos los datos pasan por la API; nunca se conecta a la base de datos.

> **Estado:** estructura base. La página de inicio muestra los 6 paquetes y cada uno de los 27 casos de uso abre una pantalla "pendiente de implementar".

---

## 1. Requisitos obligatorios

Trabajamos 5 personas: **todos deben usar exactamente estas versiones**. El proyecto está configurado para que **npm se niegue a instalar** con otra versión de Node (`engine-strict`).

| Herramienta | Versión obligatoria | Para qué |
|---|---|---|
| **Node.js** | **24.21.0** (LTS "Krypton"; se acepta 24.x ≥ 24.21.0) | Ejecutar Vite y las herramientas |
| npm | 11.x (viene con Node 24) | Instalar dependencias |
| Git | cualquiera reciente | Control de versiones |

Dependencias principales (ya fijadas con versión **exacta** en `package.json` y `package-lock.json`):

| Paquete | Versión | Para qué |
|---|---|---|
| react / react-dom | 19.3.0 | Librería de interfaz |
| vite | 8.3.1 | Servidor de desarrollo y compilación |
| typescript | 6.0.3 | Tipado |
| react-router | 8.4.0 | Rutas / páginas |
| @tanstack/react-query | 5.104.0 | Pedir y guardar en caché los datos del backend |
| tailwindcss / @tailwindcss/vite | 4.3.3 | Estilos |
| shadcn (componentes UI) | 4.21.0 | Botones, formularios, tablas… (`src/componentes/ui`) |
| react-hook-form | 7.89.0 | Formularios |
| zod / @hookform/resolvers | 4.6.5 / 5.9.1 | Validación de formularios |
| oxlint | 1.85.0 | Revisión de código (lint) |

### Verifica tus versiones

```bash
node --version   # debe decir v24.21.0 (o 24.x mayor)
npm --version    # debe decir 11.x
```

### Instalar la versión correcta de Node

Se recomienda un gestor de versiones: el archivo `.nvmrc` ya indica `24.21.0`.

- **Windows:** instala [nvm-windows](https://github.com/coreybutler/nvm-windows/releases) y ejecuta:
  ```powershell
  nvm install 24.21.0
  nvm use 24.21.0
  ```
- **Linux / macOS:** instala [nvm](https://github.com/nvm-sh/nvm) y, dentro de `frontend/`, ejecuta:
  ```bash
  nvm install   # lee .nvmrc
  nvm use
  ```
- Otra opción: el instalador de Node 24 LTS desde <https://nodejs.org/>.

---

## 2. Levantar el proyecto en local

Todos los comandos se ejecutan **dentro de la carpeta `frontend/`**.

### Paso 1 — Instalar las dependencias (versiones exactas)

```bash
cd frontend
npm ci
```

> Usa **`npm ci`**, no `npm install`. `npm ci` instala exactamente lo que dice `package-lock.json` y no lo modifica, así todos tienen las mismas versiones.

### Paso 2 — Configurar las variables de entorno

```bash
# Windows
copy .env.example .env
# Linux / macOS
cp .env.example .env
```

Completa los valores (ver sección 3).

### Paso 3 — Levantar el servidor de desarrollo

```bash
npm run dev
```

Abre <http://localhost:5173>. Los cambios se ven al guardar, sin recargar. Para detenerlo: `Ctrl + C`.

> Para que las pantallas traigan datos, el **backend** también debe estar levantado (ver `backend/README.md`).

### Otros comandos

| Comando | Qué hace |
|---|---|
| `npm run build` | Compila para producción en `dist/`. Revisa también los tipos de TypeScript |
| `npm run preview` | Sirve localmente lo compilado en `dist/` |
| `npm run lint` | Revisa el código con oxlint |

**Antes de subir cambios**, ejecuta `npm run build` y `npm run lint`: los dos deben terminar sin errores.

---

## 3. Variables de entorno (`.env`)

| Variable | Dónde se obtiene | Ejemplo |
|---|---|---|
| `VITE_API_URL` | URL del backend (en local, `uvicorn` en el puerto 8000) | `http://localhost:8000/api/v1` |

**Seguridad:**
- Todo lo que empieza con `VITE_` **queda visible en el navegador**. Nunca pongas contraseñas ni claves secretas en el `.env` del frontend.
- El token de sesión lo entrega el backend al iniciar sesión (CU01) y se envía en cada petición.
- El `.env` no se sube a Git (ya está en `.gitignore`).

---

## 4. Estructura del proyecto

Tiene la misma forma que el backend: **6 paquetes**, con lo compartido afuera y **un archivo por caso de uso** en `casos_uso/`.

```
frontend/src/
├── main.tsx / App.tsx           ← arranque y rutas principales
├── index.css                    ← Tailwind + tema de shadcn
├── nucleo/                      ← compartido por TODOS los paquetes
│   ├── api.ts                   ← llamadas al backend con el token (login incluido)
│   ├── auth/                    ← sesión y rutas protegidas por rol
│   ├── layout/                  ← estructura de pantalla y menú
│   ├── rutas.tsx                ← junta las rutas de los 6 paquetes
│   └── mapaCasosUso.ts          ← lista de paquetes y casos de uso
├── componentes/
│   ├── ui/                      ← componentes de shadcn (no se editan a mano)
│   └── CasoUsoPendiente.tsx
├── lib/utils.ts                 ← función cn() para combinar clases
└── paquetes/
    └── personas/                ← ejemplo de un paquete
        ├── api.ts               ← llamadas al backend del paquete   (compartido)
        ├── schemas.ts           ← tipos y validaciones Zod          (compartido)
        ├── componentes/         ← piezas reutilizadas por sus CU    (compartido)
        ├── rutas.tsx            ← una ruta por caso de uso: /personas/cu06 …
        └── casos_uso/
            ├── CU05RegistrarActualizarPersona.tsx
            ├── CU06GestionarEstudiante.tsx
            └── ...
```

| Paquete | Casos de uso |
|---|---|
| `seguridad` | CU01–CU04 |
| `personas` | CU05–CU11 |
| `academico` | CU12–CU17 |
| `horarios` | CU18–CU20 |
| `evaluacion` | CU21–CU24 |
| `administracion` | CU25–CU27 |

- Cada archivo de `casos_uso/` tiene en su encabezado los actores, el rol, la **precondición**, la **postcondición** y la ruta del archivo del backend donde están sus reglas de negocio.
- Las reglas de negocio las aplica el backend. El frontend puede validar formularios para dar una mejor experiencia (Zod), pero **nunca es la única validación**.
- Importa con el alias `@/` (apunta a `src/`). Por ejemplo: `import { Button } from '@/componentes/ui/button'`.

### Agregar un componente de shadcn/ui

Usa siempre la misma versión del CLI:

```bash
npx shadcn@4.21.0 add input
```

Se crea en `src/componentes/ui/`.

---

## 5. Reglas del equipo sobre dependencias

1. **No actualices ninguna versión por tu cuenta.** Cualquier cambio se acuerda con el grupo.
2. Para **agregar** una dependencia acordada:
   ```bash
   npm install nombre@X.Y.Z          # queda exacta gracias a .npmrc (save-exact)
   ```
   Sube `package.json` y `package-lock.json` en el mismo commit y avisa al grupo.
3. Cuando alguien cambie el `package-lock.json`, los demás ejecutan `npm ci`.
4. **No borres ni regeneres** `package-lock.json` sin acordarlo.

---

## 6. Problemas comunes

| Problema | Solución |
|---|---|
| `npm ERR! code EBADENGINE` / *Unsupported engine* | Tu Node no es 24.x ≥ 24.21.0. Cambia con `nvm use 24.21.0` |
| `npm ci` dice que el lock no coincide con `package.json` | Alguien editó `package.json` sin actualizar el lock. Pide el `package-lock.json` correcto (no lo regeneres) |
| `Port 5173 is in use` | Otro `npm run dev` está abierto. Ciérralo o usa `npm run dev -- --port 5174` |
| La pantalla no trae datos | Revisa que el backend esté levantado y que `VITE_API_URL` en `.env` sea correcta. Reinicia `npm run dev` después de cambiar el `.env` |
| Error de tipos al hacer `npm run build` | TypeScript encontró un error. Léelo, corrígelo y vuelve a compilar; no se sube código que no compila |

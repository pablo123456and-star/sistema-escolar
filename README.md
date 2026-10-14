# Sistema de Información — Unidad Educativa "Mariscal Sucre G"

Sistema web para gestionar los procesos académicos y administrativos del colegio: personas, inscripciones, horarios, asistencia, calificaciones, boletines, pagos, inventario y comunicados.

Grupo #2 — Sistemas de Información I.

## Carpetas

| Carpeta | Contenido | Guía |
|---|---|---|
| `basededato/sql/` | Base de datos PostgreSQL: tablas y relaciones, 5 triggers, 3 procedimientos, 4 vistas y datos de prueba | [LEEME.md](basededato/sql/LEEME.md) |
| `backend/` | API en Python + FastAPI: **toda la lógica de negocio**, login y permisos | [README.md](backend/README.md) |
| `frontend/` | Aplicación web en React + TypeScript | [README.md](frontend/README.md) |
| `doc/` | Documento del proyecto | — |

## Arquitectura

```
Navegador (React) ──login y datos──► API (FastAPI) ──SQL──► PostgreSQL
                   ◄──token JWT────   lógica de negocio      datos + relaciones
                                      permisos por rol       triggers: auditoría, horarios, stock
                                      validaciones           procedimientos: cuotas, boletines, cierre
```

- **Frontend:** pantallas. Solo habla con el backend.
- **Backend:** reglas de negocio, login (bcrypt + JWT) y permisos. Es el único que accede a la base.
- **Base de datos:** guarda los datos y sus relaciones, con unos pocos triggers y procedimientos. Corre en PostgreSQL local para desarrollar; Supabase o Railway sirven como hosting.

## Versiones obligatorias (todo el equipo)

| Herramienta | Versión |
|---|---|
| Python | 3.14.x |
| Node.js | 24.21.0 (24.x LTS) |
| npm | 11.x (viene con Node 24) |
| PostgreSQL | 18.x en local (el hosting puede ser 15+) |

Las versiones exactas de cada librería están fijadas en `backend/requirements.lock` y `frontend/package-lock.json`. **No se cambian sin acordarlo con el grupo.**

## Paquetes y casos de uso

El backend y el frontend se organizan igual: **6 paquetes**, cada uno con sus archivos compartidos y un archivo por caso de uso en `casos_uso/`.

**Implementado (Ciclo 1):** CU01, CU02, CU03, CU04 (seguridad), CU06 y CU08 (personas). El resto está pendiente.

| Paquete | Casos de uso |
|---|---|
| `seguridad` | CU01 Iniciar sesión · CU02 Gestionar usuarios · CU03 Gestionar roles y permisos · CU04 Consultar bitácora |
| `personas` | CU05 Datos de persona · CU06 Gestionar estudiante · CU07 Antecedentes médicos y seguimiento · CU08 Registrar y asociar tutor · CU09 Consultar relacionados · CU10 Registrar docente · CU11 Registrar administrativo |
| `academico` | CU12 Niveles y cursos · CU13 Materias · CU14 Asignar profesor · CU15 Gestión académica · CU16 Inscribir estudiante · CU17 Historial de inscripciones |
| `horarios` | CU18 Gestionar aulas · CU19 Generar horario · CU20 Consultar horarios |
| `evaluacion` | CU21 Registrar asistencia · CU22 Historial de asistencia · CU23 Registrar calificaciones · CU24 Boletín y libreta |
| `administracion` | CU25 Pago de mensualidad · CU26 Gestionar inventario · CU27 Comunicados y citaciones |

## Orden para levantar todo en local

1. **Base de datos:** sigue `basededato/sql/LEEME.md`. Se crea una vez en tu PostgreSQL local, con datos y usuarios de prueba.
2. **Backend:** sigue `backend/README.md` → queda en <http://localhost:8000/docs>.
3. **Frontend:** sigue `frontend/README.md` → queda en <http://localhost:5173>.

## Integrantes — Grupo #2

**Docente:** Ing. Garzón Cuellar Angélica · **Materia:** Sistemas de Información I - SA

| N.º | Apellidos y nombres |
|---|---|
| 1 | Ayala Ayala Edison |
| 2 | Carrillo Callisaya Ronald |
| 3 | Cervante Dueñas Juan Clider |
| 4 | Cusi Mamani Benjamin |
| 5 | Loza Flores Jhonatan |
| 6 | Saldaña Zurita Pablo Andres |

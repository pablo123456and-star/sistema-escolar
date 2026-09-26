# Base de datos — Sistema Escolar (PostgreSQL)

La base guarda **los datos y sus relaciones**. **La lógica de negocio está en el backend** (FastAPI): validaciones, permisos por rol, altas, bajas y modificaciones.

Funciona igual en un **PostgreSQL local** (para desarrollar) y en **Supabase o Railway** (como hosting).

## Qué hay en la base

| Tipo | Cantidad | Detalle |
|---|---|---|
| Tablas | 34 | Con llaves primarias y foráneas, `CHECK`, `UNIQUE` e índices (`01_esquema.sql`) |
| Funciones de trigger | 5 | Ver tabla abajo (`02_funciones.sql`) |
| Función auxiliar | 1 | `fn_registrar_bitacora`: escribe una fila en la bitácora |
| Triggers | 24 | Enganchan las 5 funciones a las tablas (`03_triggers.sql`) |
| Procedimientos | 3 | `CREATE PROCEDURE`, se ejecutan con `CALL` (`04_procedimientos.sql`) |
| Vistas | 4 | `v_curso`, `v_nota_final`, `v_estado_pagos`, `v_horario` (`05_vistas.sql`) |

**Funciones de trigger:**

| Función | Para qué | Tablas |
|---|---|---|
| `fn_tg_actualizado_en` | Actualiza la fecha de modificación | persona, usuario, inscripcion, calificacion, pago_mensualidad, inventario |
| `fn_tg_auditar` | Registra en la bitácora qué cambió, quién e IP | 15 tablas sensibles (usuarios, personas, estudiantes, notas, asistencia, pagos, becas, aranceles, boletines, inventario…) |
| `fn_tg_bitacora_inmutable` | La bitácora no se puede editar ni borrar | bitacora |
| `fn_tg_validar_horario` | Impide que un profesor, un aula o un curso tengan dos clases a la misma hora en la misma gestión | horario |
| `fn_tg_aplicar_movimiento` | Cada entrada o salida actualiza el stock y no deja sacar más de lo que hay | movimiento_inventario |

**Procedimientos:**

| Procedimiento | Qué hace | Lo usa |
|---|---|---|
| `sp_generar_cuotas_mes(gestion, mes, INOUT creadas)` | Cuotas del mes según el arancel del nivel y la beca | CU25 |
| `sp_emitir_boletines(periodo, curso, INOUT emitidos)` | Boletines de un periodo (todos o de un curso) | CU23 / CU24 |
| `sp_cerrar_gestion(gestion, INOUT resultado)` | Promovido/reprobado de cada estudiante y cierre del año | CU15 |

### ¿Quién hizo cada cambio? (auditoría)

La bitácora guarda el usuario y la IP que el **backend** le indica al empezar cada transacción:

```sql
SELECT set_config('app.id_usuario', '5', true),
       set_config('app.ip', '181.115.1.2', true);
```

Si se escribe desde el SQL Editor o desde un script, el usuario queda vacío (`NULL`).

### Seguridad: solo el backend entra

`06_seguridad.sql`:
- Activa RLS en todas las tablas **sin crear políticas**.
- Quita todos los permisos a `PUBLIC`, y también a `anon`/`authenticated` si existen (en Supabase).

Resultado: nadie puede leer ni escribir por la API REST de Supabase, aunque tenga la clave pública. El backend se conecta con el usuario dueño de las tablas (`postgres`), al que RLS no le aplica.

---

## Dónde quedó cada regla de negocio

Antes estas reglas eran triggers o procedimientos. Ahora cada una va en el `politicas.py` o en el caso de uso del paquete correspondiente del backend. El encabezado de cada `casos_uso/cuXX_*.py` las lista.

| Regla | Caso de uso (paquete) |
|---|---|
| Solo el rol correcto puede ver o modificar cada dato | Todos (`nucleo/dependencias.py` + `politicas.py`) |
| Login: contraseña bcrypt, usuario activo, token JWT | CU01 (seguridad) |
| El rol coincide con la persona (profesor ↔ tabla profesor…) | CU02 (seguridad) |
| Registrar persona + estudiante + tutor + inscripción juntos | CU06 (personas) |
| Un solo tutor principal (la BD lo impide; el backend desmarca al anterior) | CU08 (personas) |
| La materia está en el plan del grado; aula disponible; profesor activo | CU14 (academico) |
| El periodo está dentro de su gestión y no se solapa | CU15 (academico) |
| Gestión abierta, persona activa, cupo del curso, sin deudas previas | CU16 (academico) |
| Asistencia: fecha no futura y dentro de la gestión; estudiante del curso | CU21 (evaluacion) |
| Nota: estudiante inscrito con esa materia, periodo abierto, puntaje ≤ máximo | CU23 (evaluacion) |
| Pago: cajero administrativo, recibo correlativo, fecha no futura, no cobrar dos veces | CU25 (administracion) |
| Los movimientos de inventario no se editan (se corrigen con otro movimiento) | CU26 (administracion) |
| Quién publica comunicados a quién | CU27 (administracion) |

---

## Instalar la base

Los scripts se ejecutan **en este orden**:

| Orden | Archivo |
|---|---|
| 1 | `01_esquema.sql` |
| 2 | `02_funciones.sql` |
| 3 | `03_triggers.sql` |
| 4 | `04_procedimientos.sql` |
| 5 | `05_vistas.sql` |
| 6 | `06_seguridad.sql` |
| 7 | `07_datos_iniciales.sql` |
| 8 | `08_datos_prueba.sql` (opcional, solo para desarrollo) |

### En tu PostgreSQL local (para desarrollar)

1. Crea la base (desde pgAdmin, o con `psql`):
   ```bash
   psql -U postgres -c "CREATE DATABASE escuela"
   ```
2. Ejecuta los 8 scripts en orden. En pgAdmin: *Query Tool* → abrir archivo → ▶. O con `psql`:
   ```bash
   psql -U postgres -d escuela -v ON_ERROR_STOP=1 -f 01_esquema.sql
   ```
   Repite el comando con cada archivo, en el orden de la tabla.
3. En `backend/.env` pon `DATABASE_URL=postgresql+asyncpg://postgres:TU_CONTRASEÑA@localhost:5432/escuela`.

### En Supabase (hosting)

1. **SQL Editor → New query**: pega cada script y pulsa **Run**, en el orden de la tabla. Si aparece el aviso de RLS, elige **Run and enable RLS**.
2. Ejecuta una vez, para que las fechas usen la hora de Bolivia:
   ```sql
   ALTER DATABASE postgres SET timezone TO 'America/La_Paz';
   ```
3. En el backend, `DATABASE_URL` sale de **Connect → Transaction pooler**: cambia `postgresql://` por `postgresql+asyncpg://`.

### Usuarios de prueba

`08_datos_prueba.sql` crea 6 usuarios, uno por cada rol, para poder iniciar sesión mientras desarrollan. Los nombres y la contraseña están al final de ese archivo. **No se cargan en producción.**

---

## Pruebas automáticas

`pruebas/10_pruebas.sql` tiene 85 comprobaciones. Revisa:
- Restricciones de datos: roles fijos, pagos, inscripciones, CI en cascada…
- Los 5 triggers y los 3 procedimientos.
- Las vistas.
- Que la API no pueda leer ni escribir nada.

1. Crea `%APPDATA%\postgresql\pgpass.conf` con tu contraseña de PostgreSQL:
   ```
   localhost:5432:*:postgres:TU_CONTRASEÑA
   ```
2. En PowerShell, desde `pruebas/`:
   ```powershell
   .\ejecutar_pruebas.ps1            # usa -Puerto 1982 si tu PostgreSQL no está en el 5432
   ```
   Crea la base `escuela_prueba`, ejecuta 01–08 y las pruebas. Al final debe decir **TODAS LAS PRUEBAS PASARON**.

`99_reiniciar.sql` borra todo lo del proyecto para empezar de cero.

# Dataset de demostración

`cargar_dataset.py` completa la base con un colegio de tamaño mediano para probar y presentar el sistema
con datos realistas. **Todos los datos son ficticios**: nombres inventados y correos `@example.com`.

## Qué agrega

| Dato | Cantidad aproximada |
|---|---|
| Estudiantes | ~470 nuevos (los 20 cursos llenos: 20 en Inicial, 26 en Primaria y 24 en Secundaria) |
| Tutores / docentes | ~530 tutores (familias con hermanos) / ~20 docentes nuevos |
| Usuarios | ~850: todos los docentes y tutores, y los estudiantes de Secundaria |
| Asignaciones y horarios | Todas las materias del plan de estudios, sin choques de docente, aula ni curso |
| Asistencia 2026 | ~230.000 registros, desde el inicio de la gestión hasta hoy (sin feriados ni vacaciones de invierno) |
| Notas 2026 | 1.º y 2.º trimestre completos y cerrados, con boletines; 3.º en curso (Ser y Saber) |
| Gestión 2025 | Cerrada: inscripciones, notas, boletines, pagos y resultado final (promovido / reprobado) |
| Pagos | Cuotas de 2025 y 2026, becas (~8 %), pagos con recibo y ~10 % de morosos |
| Otros | Seguimiento de estudiantes, comunicados, citaciones e inventario |

La base queda en unos 60 MB. Todas las pantallas responden igual de rápido.

## Qué NO hace

- **No borra ni modifica lo que ya existe**: lee la base y completa alrededor. Respeta los estudiantes,
  asignaciones, horarios y usuarios que ya estén cargados.
- No cambia las contraseñas de los usuarios existentes.
- Si algo falla, no queda nada a medias: todo va en una sola transacción.
- No se puede cargar dos veces: si la base ya tiene la gestión 2025, se detiene.

## Cómo cargarlo en tu base local

Requisitos: la base con los scripts 01 a 07 (o 01 a 09) y el entorno virtual del backend.

```powershell
cd backend
.venv\Scripts\activate
python ..\basededato\dataset\cargar_dataset.py --url postgresql://postgres:TU_CLAVE@localhost:5432/escuela_local --clave CONTRASEÑA
```

- `--url`: tu base local (puerto y contraseña de **tu** PostgreSQL).
- `--clave`: contraseña de **todos** los usuarios nuevos. En local usen la misma de `08_datos_prueba.sql`.
- `--simular`: hace todo y al final lo deshace (para probar sin guardar).
- Tarda menos de 1 minuto.

**Nunca lo corran contra `escuela_prueba`**: esa base es solo para las pruebas automáticas.

## Para entrar al sistema con usuarios del dataset

El nombre de usuario es la inicial del nombre más el primer apellido (por ejemplo `jmamani`, `jmamani2`).
Para ver algunos:

```sql
SELECT u.nombre_usuario, r.nombre_rol, p.nombre_persona || ' ' || p.apellidos AS persona
  FROM usuario u JOIN rol r ON r.id_rol = u.id_rol_usuario JOIN persona p ON p.ci = u.ci_persona
 WHERE p.ci LIKE '21%' OR p.ci LIKE '31%' OR p.ci LIKE '46%'   -- docentes, tutores y estudiantes del dataset
 ORDER BY r.nombre_rol, u.nombre_usuario
 LIMIT 30;
```

## Asignaciones cargadas a mano

Si la base tiene asignaciones de profesor hechas a mano cuya aula ya no tiene espacio en el horario
(por ejemplo, todas las materias de un curso en un aula de otro curso), quedan sin horario y sin asistencia.
Con `--corregir-aulas` el cargador las pasa al aula de su curso (u otra libre). Es lo **único** que modifica
de lo existente, solo con esa opción, y muestra en pantalla cada cambio.

## Producción

En producción la contraseña **no** debe ser la del repositorio: cualquiera que lea GitHub podría entrar
como cualquier docente o tutor de la página publicada. La carga en producción la hace solo una persona
del grupo, con una contraseña que se comparte por privado.

Si no se pasa `--clave`, el cargador la pide sin mostrarla en pantalla. Mientras carga (1 a 2 minutos),
la página publicada puede quedar en espera.

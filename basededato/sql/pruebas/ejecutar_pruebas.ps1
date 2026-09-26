# =====================================================================
# Ejecuta todos los scripts en una base de PRUEBA de tu PostgreSQL local
# y luego las pruebas automaticas. No toca ninguna otra base de datos.
#
# Uso (PowerShell, desde esta carpeta):
#     .\ejecutar_pruebas.ps1                      # puerto 5432, usuario postgres
#     .\ejecutar_pruebas.ps1 -Puerto 1982         # si tu PostgreSQL usa otro puerto
#
# La contrasena se lee de %APPDATA%\postgresql\pgpass.conf (ver LEEME.md).
# Nota: crea en tu servidor local los roles anon y authenticated (los de la
# API de Supabase) para comprobar que 06_seguridad.sql los bloquea.
# =====================================================================
param(
    [int]    $Puerto    = 5432,
    [string] $Servidor  = 'localhost',
    [string] $Usuario   = 'postgres',
    [string] $BaseDatos = 'escuela_prueba'
)

# psql escribe los avisos (NOTICE) en stderr: no deben detener el script;
# los errores reales se detectan con $LASTEXITCODE.
$ErrorActionPreference = 'Continue'
$env:PGCLIENTENCODING = 'UTF8'

$psql = Get-ChildItem 'C:\Program Files\PostgreSQL\*\bin\psql.exe' -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
if (-not $psql) { $psql = 'psql' }

$carpeta = Split-Path -Parent $PSScriptRoot
$conexion = @('-X', '-w', '-h', $Servidor, '-p', $Puerto, '-U', $Usuario, '-v', 'ON_ERROR_STOP=1')

Write-Host "== Recreando la base de prueba '$BaseDatos' ==" -ForegroundColor Cyan
& $psql @conexion -d postgres -q -c "DROP DATABASE IF EXISTS $BaseDatos" -c "CREATE DATABASE $BaseDatos" 2>&1 | ForEach-Object { "$_" }
if ($LASTEXITCODE -ne 0) { throw 'No se pudo conectar a PostgreSQL (revisa puerto y pgpass.conf)' }

$scripts = @(
    'pruebas\00_roles_api.sql',
    '01_esquema.sql',
    '02_funciones.sql',
    '03_triggers.sql',
    '04_procedimientos.sql',
    '05_vistas.sql',
    '06_seguridad.sql',
    '07_datos_iniciales.sql',
    '08_datos_prueba.sql',
    'pruebas\10_pruebas.sql'
)

foreach ($s in $scripts) {
    Write-Host "== $s ==" -ForegroundColor Cyan
    & $psql @conexion -d $BaseDatos -q -f (Join-Path $carpeta $s) 2>&1 | ForEach-Object { "$_" }
    if ($LASTEXITCODE -ne 0) { throw "Fallo al ejecutar $s" }
}

Write-Host ''
Write-Host "Listo. La base '$BaseDatos' queda creada para que la revises." -ForegroundColor Green

-- =====================================================================
-- 06 - SEGURIDAD  -  SISTEMA ESCUELA MODELO
-- Requiere: 01 a 05
-- =====================================================================
-- Modelo: SOLO EL BACKEND accede a la base de datos.
--   * Los permisos por rol (quién ve o modifica qué) se programan en el
--     backend: nucleo/dependencias.py y politicas.py de cada paquete.
--   * La base se protege cerrando todo acceso que no sea el del backend.
--
-- Qué hace este script:
--   1. Activa Row Level Security en TODAS las tablas y NO crea políticas:
--      cualquier rol que no sea el dueño de las tablas no ve ninguna fila.
--      (En Supabase esto cierra la API REST pública aunque alguien tenga
--      la clave "anon".)
--   2. Quita todos los permisos a PUBLIC y, si existen (Supabase), a los
--      roles anon y authenticated.
--
-- El backend se conecta con el usuario dueño de las tablas (el que
-- ejecutó estos scripts, p. ej. "postgres"), al que RLS no le aplica.
-- =====================================================================

BEGIN;

-- 1. RLS en todas las tablas, sin políticas ------------------------------
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
    END LOOP;
END;
$$;

-- 2. Sin permisos para nadie más que el dueño -----------------------------
REVOKE ALL ON ALL TABLES    IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM PUBLIC;
REVOKE ALL ON ALL ROUTINES  IN SCHEMA public FROM PUBLIC;
ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE EXECUTE ON ROUTINES FROM PUBLIC;

-- Roles de la API de Supabase (en un PostgreSQL local no existen: se omite)
DO $$
DECLARE
    r TEXT;
BEGIN
    FOREACH r IN ARRAY ARRAY['anon', 'authenticated'] LOOP
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
            EXECUTE format('REVOKE ALL ON ALL TABLES    IN SCHEMA public FROM %I', r);
            EXECUTE format('REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM %I', r);
            EXECUTE format('REVOKE ALL ON ALL ROUTINES  IN SCHEMA public FROM %I', r);
            EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES    FROM %I', r);
            EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON SEQUENCES FROM %I', r);
            EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON ROUTINES  FROM %I', r);
        END IF;
    END LOOP;
END;
$$;

COMMIT;

-- Si más adelante el backend usa un usuario propio (recomendado en
-- producción) en lugar de "postgres":
--   CREATE ROLE escuela_backend LOGIN PASSWORD '...' BYPASSRLS;
--   GRANT USAGE ON SCHEMA public TO escuela_backend;
--   GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO escuela_backend;
--   GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO escuela_backend;
--   GRANT EXECUTE ON ALL ROUTINES IN SCHEMA public TO escuela_backend;

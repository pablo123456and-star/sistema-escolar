-- =====================================================================
-- SOLO PARA PRUEBAS LOCALES (no ejecutar en Supabase)
-- =====================================================================
-- Crea los roles de la API de Supabase (anon, authenticated) con los
-- permisos por defecto que Supabase les da sobre el esquema public.
-- Así las pruebas pueden comprobar que 06_seguridad.sql los bloquea.
-- =====================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        CREATE ROLE anon NOLOGIN NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        CREATE ROLE authenticated NOLOGIN NOINHERIT;
    END IF;
END;
$$;

GRANT USAGE ON SCHEMA public TO anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES    TO anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON ROUTINES  TO anon, authenticated;

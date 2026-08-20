-- Grants for Render app role (gis_info_render) on managed Supabase.
GRANT USAGE, CREATE ON SCHEMA public TO gis_info_render;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO gis_info_render;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO gis_info_render;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO gis_info_render;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO gis_info_render;

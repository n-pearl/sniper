-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create database user if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'sniper_user') THEN
        CREATE USER sniper_user WITH PASSWORD 'sniper_password';
    END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE sniper TO sniper_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sniper_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sniper_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO sniper_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO sniper_user; 
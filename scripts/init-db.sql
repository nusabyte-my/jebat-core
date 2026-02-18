-- JEBAT Database Initialization Script
-- Run automatically on first PostgreSQL startup

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create database schema (if not using ORM migrations)
-- Note: Tables will be created by SQLAlchemy ORM on first run
-- This script sets up extensions and initial configuration

-- Set timezone
SET timezone = 'UTC';

-- Create initial user (optional, for manual access)
-- DO NOT use in production without changing password
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'jebat') THEN
        CREATE ROLE jebat WITH LOGIN PASSWORD 'jebat_password';
    END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE jebat_db TO jebat;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'JEBAT database initialization complete!';
    RAISE NOTICE 'Extensions enabled: uuid-ossp, pgvector, pg_trgm';
END
$$;

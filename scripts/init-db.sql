-- KooCAD Database Initialization Script

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables (will be managed by Alembic migrations later)
-- This is just for initial setup

-- Version info
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE koocad TO koocad;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO koocad;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO koocad;

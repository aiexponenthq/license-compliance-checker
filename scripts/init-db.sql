-- License Compliance Checker - Database Initialization Script
-- This script initializes the PostgreSQL database schema

-- ============================================================================
-- Extensions
-- ============================================================================

-- UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Users Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Indexes for users table
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- ============================================================================
-- Scans Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS scans (
    id SERIAL PRIMARY KEY,
    scan_id UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    project VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    generated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_seconds REAL,
    violations INTEGER DEFAULT 0,
    warnings INTEGER DEFAULT 0,
    total_dependencies INTEGER DEFAULT 0,
    policy_name VARCHAR(255),
    scan_type VARCHAR(50),
    repository_url VARCHAR(1024),
    branch VARCHAR(255),
    commit_sha VARCHAR(255),
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for scans table
CREATE INDEX IF NOT EXISTS idx_scans_scan_id ON scans(scan_id);
CREATE INDEX IF NOT EXISTS idx_scans_project ON scans(project);
CREATE INDEX IF NOT EXISTS idx_scans_status ON scans(status);
CREATE INDEX IF NOT EXISTS idx_scans_generated_at ON scans(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_scans_user_id ON scans(user_id);
CREATE INDEX IF NOT EXISTS idx_scans_policy_name ON scans(policy_name);

-- ============================================================================
-- Policies Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS policies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    version VARCHAR(50) NOT NULL DEFAULT '1.0',
    content TEXT NOT NULL,
    format VARCHAR(20) NOT NULL DEFAULT 'yaml',
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for policies table
CREATE INDEX IF NOT EXISTS idx_policies_name ON policies(name);
CREATE INDEX IF NOT EXISTS idx_policies_is_active ON policies(is_active);
CREATE INDEX IF NOT EXISTS idx_policies_created_by ON policies(created_by);

-- ============================================================================
-- Dependencies Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS dependencies (
    id SERIAL PRIMARY KEY,
    scan_id INTEGER REFERENCES scans(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(100),
    ecosystem VARCHAR(50) NOT NULL,
    license VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'unknown',
    confidence REAL,
    source VARCHAR(100),
    package_url TEXT,
    repository_url TEXT,
    homepage_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for dependencies table
CREATE INDEX IF NOT EXISTS idx_dependencies_scan_id ON dependencies(scan_id);
CREATE INDEX IF NOT EXISTS idx_dependencies_name ON dependencies(name);
CREATE INDEX IF NOT EXISTS idx_dependencies_ecosystem ON dependencies(ecosystem);
CREATE INDEX IF NOT EXISTS idx_dependencies_license ON dependencies(license);
CREATE INDEX IF NOT EXISTS idx_dependencies_status ON dependencies(status);

-- ============================================================================
-- Violations Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS violations (
    id SERIAL PRIMARY KEY,
    scan_id INTEGER REFERENCES scans(id) ON DELETE CASCADE,
    dependency_id INTEGER REFERENCES dependencies(id) ON DELETE CASCADE,
    severity VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    rule VARCHAR(255),
    context VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for violations table
CREATE INDEX IF NOT EXISTS idx_violations_scan_id ON violations(scan_id);
CREATE INDEX IF NOT EXISTS idx_violations_dependency_id ON violations(dependency_id);
CREATE INDEX IF NOT EXISTS idx_violations_severity ON violations(severity);

-- ============================================================================
-- API Keys Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    key_id UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    scopes TEXT[],
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for api_keys table
CREATE INDEX IF NOT EXISTS idx_api_keys_key_id ON api_keys(key_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_is_active ON api_keys(is_active);

-- ============================================================================
-- Audit Log Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for audit_log table
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON audit_log(resource_type, resource_id);

-- ============================================================================
-- Functions and Triggers
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scans_updated_at BEFORE UPDATE ON scans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_policies_updated_at BEFORE UPDATE ON policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Views
-- ============================================================================

-- View for scan summary statistics
CREATE OR REPLACE VIEW scan_summary AS
SELECT
    s.id,
    s.scan_id,
    s.project,
    s.status,
    s.generated_at,
    s.duration_seconds,
    s.violations,
    s.warnings,
    s.total_dependencies,
    COUNT(DISTINCT d.id) AS dependency_count,
    COUNT(DISTINCT v.id) AS violation_count,
    u.username AS created_by
FROM scans s
LEFT JOIN dependencies d ON s.id = d.scan_id
LEFT JOIN violations v ON s.id = v.scan_id
LEFT JOIN users u ON s.user_id = u.id
GROUP BY s.id, s.scan_id, s.project, s.status, s.generated_at,
         s.duration_seconds, s.violations, s.warnings, s.total_dependencies,
         u.username;

-- View for license distribution
CREATE OR REPLACE VIEW license_distribution AS
SELECT
    d.license,
    COUNT(*) AS count,
    COUNT(DISTINCT d.scan_id) AS scan_count
FROM dependencies d
WHERE d.license IS NOT NULL
GROUP BY d.license
ORDER BY count DESC;

-- View for ecosystem statistics
CREATE OR REPLACE VIEW ecosystem_stats AS
SELECT
    d.ecosystem,
    COUNT(*) AS dependency_count,
    COUNT(DISTINCT d.scan_id) AS scan_count,
    COUNT(DISTINCT d.license) AS unique_licenses
FROM dependencies d
GROUP BY d.ecosystem
ORDER BY dependency_count DESC;

-- ============================================================================
-- Initial Data
-- ============================================================================

-- Insert default admin user (password: changeme)
-- NOTE: This should be changed immediately in production!
INSERT INTO users (username, email, hashed_password, role)
VALUES (
    'admin',
    'admin@example.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lW5W8c5lQ5jK',  -- bcrypt hash of 'changeme'
    'admin'
) ON CONFLICT (username) DO NOTHING;

-- ============================================================================
-- Permissions
-- ============================================================================

-- Grant permissions to lcc user (adjust as needed)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO lcc;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO lcc;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO lcc;

-- ============================================================================
-- Completion
-- ============================================================================

-- Log database initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialization completed successfully';
END $$;

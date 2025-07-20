-- Database initialization script for Medical Triage-BOTS
-- This script sets up the initial database structure and data

-- Create extensions if they don't exist
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create enum types
DO $$ BEGIN
    CREATE TYPE triage_status AS ENUM ('pending', 'in_progress', 'completed', 'escalated');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE severity_level AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE bot_type AS ENUM ('chief', 'vision', 'text', 'specialist');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create users table if it doesn't exist
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create triage_cases table if it doesn't exist
CREATE TABLE IF NOT EXISTS triage_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id VARCHAR(100),
    chief_complaint TEXT,
    symptoms TEXT[],
    vital_signs JSONB,
    medical_history TEXT,
    current_medications TEXT[],
    allergies TEXT[],
    status triage_status DEFAULT 'pending',
    severity severity_level,
    priority_score INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_to UUID REFERENCES users(id),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Create bot_interactions table if it doesn't exist
CREATE TABLE IF NOT EXISTS bot_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID REFERENCES triage_cases(id) ON DELETE CASCADE,
    bot_type bot_type NOT NULL,
    input_data JSONB,
    output_data JSONB,
    confidence_score DECIMAL(3,2),
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create medical_assessments table if it doesn't exist
CREATE TABLE IF NOT EXISTS medical_assessments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID REFERENCES triage_cases(id) ON DELETE CASCADE,
    assessment_type VARCHAR(50),
    findings TEXT,
    recommendations TEXT[],
    risk_factors TEXT[],
    differential_diagnosis TEXT[],
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

-- Create audit_logs table if it doesn't exist
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(50),
    record_id UUID,
    action VARCHAR(10),
    old_data JSONB,
    new_data JSONB,
    user_id UUID,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_triage_cases_status ON triage_cases(status);
CREATE INDEX IF NOT EXISTS idx_triage_cases_severity ON triage_cases(severity);
CREATE INDEX IF NOT EXISTS idx_triage_cases_created_at ON triage_cases(created_at);
CREATE INDEX IF NOT EXISTS idx_triage_cases_patient_id ON triage_cases(patient_id);
CREATE INDEX IF NOT EXISTS idx_bot_interactions_case_id ON bot_interactions(case_id);
CREATE INDEX IF NOT EXISTS idx_bot_interactions_bot_type ON bot_interactions(bot_type);
CREATE INDEX IF NOT EXISTS idx_medical_assessments_case_id ON medical_assessments(case_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_table_record ON audit_logs(table_name, record_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_triage_cases_updated_at ON triage_cases;
CREATE TRIGGER update_triage_cases_updated_at
    BEFORE UPDATE ON triage_cases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, password_hash, full_name, role)
VALUES (
    'admin',
    'admin@medical-triage.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6hsOmHmhgC',  -- admin123
    'System Administrator',
    'admin'
) ON CONFLICT (username) DO NOTHING;

-- Insert sample test data for development
INSERT INTO triage_cases (
    patient_id,
    chief_complaint,
    symptoms,
    vital_signs,
    medical_history,
    status,
    severity
) VALUES (
    'TEST001',
    'Chest pain and shortness of breath',
    ARRAY['chest pain', 'shortness of breath', 'sweating'],
    '{"heart_rate": 110, "blood_pressure": "140/90", "temperature": 98.6, "oxygen_saturation": 95}',
    'History of hypertension, no known allergies',
    'pending',
    'high'
) ON CONFLICT DO NOTHING;

-- Create database health check function
CREATE OR REPLACE FUNCTION health_check()
RETURNS TABLE(status TEXT, timestamp TIMESTAMP WITH TIME ZONE) AS $$
BEGIN
    RETURN QUERY SELECT 'healthy'::TEXT, CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO medical_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO medical_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO medical_user;

-- Log initialization completion
INSERT INTO audit_logs (table_name, action, new_data, timestamp)
VALUES ('system', 'INIT', '{"message": "Database initialized successfully"}', CURRENT_TIMESTAMP);

-- ==================== JEBAT AI System - Database Initialization Script ====================
-- Version: 1.0.0
-- This script initializes the JEBAT database with all tables, indexes, and initial data
--
-- Order of execution:
-- 1. Create database and extensions
-- 2. Create tables and indexes
-- 3. Set up TimescaleDB hypertables
-- 4. Create functions and triggers
-- 5. Insert initial data
-- 6. Set up monitoring and maintenance

-- ==================== Database Creation ====================
-- This script assumes PostgreSQL is already started with the database created
-- via environment variables in docker-compose.yml

-- ==================== Run Main Schema ====================
-- Import the main schema file
\i /schemas/01_main_schema.sql

-- ==================== Performance Indexes ====================

-- Memory System Indexes
CREATE INDEX idx_memory_m0_user_session ON memory_m0(user_id, session_id);
CREATE INDEX idx_memory_m0_heat_score ON memory_m0(heat_score DESC);
CREATE INDEX idx_memory_m0_expires_at ON memory_m0(expires_at);
CREATE INDEX idx_memory_m0_created_at ON memory_m0(created_at DESC);

CREATE INDEX idx_memory_m1_user_session ON memory_m1(user_id, session_id);
CREATE INDEX idx_memory_m1_heat_score ON memory_m1(heat_score DESC);
CREATE INDEX idx_memory_m1_expires_at ON memory_m1(expires_at);
CREATE INDEX idx_memory_m1_embedding ON memory_m1 USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_memory_m2_user ON memory_m2(user_id);
CREATE INDEX idx_memory_m2_heat_score ON memory_m2(heat_score DESC);
CREATE INDEX idx_memory_m2_expires_at ON memory_m2(expires_at);
CREATE INDEX idx_memory_m2_embedding ON memory_m2 USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_memory_m3_user ON memory_m3(user_id);
CREATE INDEX idx_memory_m3_heat_score ON memory_m3(heat_score DESC);
CREATE INDEX idx_memory_m3_expires_at ON memory_m3(expires_at);
CREATE INDEX idx_memory_m3_tags ON memory_m3 USING GIN(tags);
CREATE INDEX idx_memory_m3_embedding ON memory_m3 USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX idx_memory_m4_user ON memory_m4(user_id);
CREATE INDEX idx_memory_m4_tags ON memory_m4 USING GIN(tags);
CREATE INDEX idx_memory_m4_archived_at ON memory_m4(archived_at DESC);
CREATE INDEX idx_memory_m4_embedding ON memory_m4 USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);

-- Agent System Indexes
CREATE INDEX idx_agents_type ON agents(type);
CREATE INDEX idx_agents_state ON agents(state);
CREATE INDEX idx_agents_active ON agents(is_active) WHERE is_active = true;
CREATE INDEX idx_agents_name ON agents USING GIN(to_tsvector('english', name));

CREATE INDEX idx_agent_performance_agent ON agent_performance(agent_id);
CREATE INDEX idx_agent_performance_created_at ON agent_performance(created_at DESC);
CREATE INDEX idx_agent_performance_metric_type ON agent_performance(metric_type);

-- Tasks Indexes
CREATE INDEX idx_tasks_user ON tasks(user_id);
CREATE INDEX idx_tasks_agent ON tasks(agent_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_priority ON tasks(priority);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX idx_tasks_parent ON tasks(parent_task_id);
CREATE INDEX idx_tasks_type ON tasks(task_type);
CREATE INDEX idx_tasks_title ON tasks USING GIN(to_tsvector('english', title));

-- Decision Engine Indexes
CREATE INDEX idx_decision_rules_type ON decision_rules(rule_type);
CREATE INDEX idx_decision_rules_active ON decision_rules(is_active) WHERE is_active = true;
CREATE INDEX idx_decision_logs_task ON decision_logs(task_id);
CREATE INDEX idx_decision_logs_created_at ON decision_logs(created_at DESC);

-- Error Recovery Indexes
CREATE INDEX idx_error_tracking_task ON error_tracking(task_id);
CREATE INDEX idx_error_tracking_resolved ON error_tracking(is_resolved);
CREATE INDEX idx_error_tracking_created_at ON error_tracking(created_at DESC);
CREATE INDEX idx_error_tracking_severity ON error_tracking(severity);

CREATE INDEX idx_circuit_breakers_service ON circuit_breakers(service_name);
CREATE INDEX idx_circuit_breakers_state ON circuit_breakers(state);
CREATE INDEX idx_dead_letter_queue_task ON dead_letter_queue(task_id);
CREATE INDEX idx_dead_letter_queue_processed ON dead_letter_queue(is_processed);
CREATE INDEX idx_dead_letter_queue_retry_at ON dead_letter_queue(next_retry_at);

-- Cache Indexes
CREATE INDEX idx_cache_entries_key ON cache_entries(cache_key);
CREATE INDEX idx_cache_entries_tier ON cache_entries(cache_tier);
CREATE INDEX idx_cache_entries_heat ON cache_entries(heat_score DESC);
CREATE INDEX idx_cache_entries_expires ON cache_entries(expires_at);

CREATE INDEX idx_cache_metrics_tier ON cache_metrics(cache_tier);
CREATE INDEX idx_cache_metrics_type ON cache_metrics(metric_type);

-- WebSocket Indexes
CREATE INDEX idx_websocket_connections_user ON websocket_connections(user_id);
CREATE INDEX idx_websocket_connections_session ON websocket_connections(session_id);
CREATE INDEX idx_websocket_connections_state ON websocket_connections(connection_state);
CREATE INDEX idx_websocket_messages_connection ON websocket_messages(connection_id);
CREATE INDEX idx_websocket_messages_created_at ON websocket_messages(created_at DESC);

-- MCP Protocol Indexes
CREATE INDEX idx_mcp_operations_id ON mcp_operations(operation_id);
CREATE INDEX idx_mcp_operations_method ON mcp_operations(method);
CREATE INDEX idx_mcp_operations_status ON mcp_operations(status);
CREATE INDEX idx_mcp_operations_created_at ON mcp_operations(created_at DESC);

-- Model Forge Indexes
CREATE INDEX idx_models_provider ON models(provider);
CREATE INDEX idx_models_type ON models(model_type);
CREATE INDEX idx_models_active ON models(is_active) WHERE is_active = true;
CREATE INDEX idx_model_usage_model ON model_usage(model_id);
CREATE INDEX idx_model_usage_user ON model_usage(user_id);
CREATE INDEX idx_model_usage_created_at ON model_usage(created_at DESC);

-- Sentinel Security Indexes
CREATE INDEX idx_security_events_type ON security_events(event_type);
CREATE INDEX idx_security_events_severity ON security_events(severity);
CREATE INDEX idx_security_events_user ON security_events(user_id);
CREATE INDEX idx_security_events_resolved ON security_events(is_resolved);
CREATE INDEX idx_security_events_created_at ON security_events(created_at DESC);

CREATE INDEX idx_security_policies_type ON security_policies(policy_type);
CREATE INDEX idx_security_policies_active ON security_policies(is_active) WHERE is_active = true;

-- Audit Log Indexes
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- Skills Indexes
CREATE INDEX idx_skills_type ON skills(skill_type);
CREATE INDEX idx_skills_active ON skills(is_active) WHERE is_active = true;
CREATE INDEX idx_agent_skills_agent ON agent_skills(agent_id);
CREATE INDEX idx_agent_skills_skill ON agent_skills(skill_id);
CREATE INDEX idx_skill_executions_skill ON skill_executions(skill_id);
CREATE INDEX idx_skill_executions_agent ON skill_executions(agent_id);
CREATE INDEX idx_skill_executions_created_at ON skill_executions(created_at DESC);

-- ==================== TimescaleDB Hypertables ====================

-- Convert time-series tables to hypertables
SELECT create_hypertable('agent_performance', 'created_at', if_not_exists => TRUE);
SELECT create_hypertable('cache_metrics', 'created_at', if_not_exists => TRUE);
SELECT create_hypertable('model_usage', 'created_at', if_not_exists => TRUE);
SELECT create_hypertable('security_events', 'created_at', if_not_exists => TRUE);
SELECT create_hypertable('audit_logs', 'created_at', if_not_exists => TRUE);
SELECT create_hypertable('skill_executions', 'created_at', if_not_exists => TRUE);

-- Set up data retention policies (90 days)
SELECT add_retention_policy('agent_performance', INTERVAL '90 days', if_not_exists => TRUE);
SELECT add_retention_policy('cache_metrics', INTERVAL '90 days', if_not_exists => TRUE);
SELECT add_retention_policy('model_usage', INTERVAL '90 days', if_not_exists => TRUE);
SELECT add_retention_policy('security_events', INTERVAL '90 days', if_not_exists => TRUE);
SELECT add_retention_policy('audit_logs', INTERVAL '90 days', if_not_exists => TRUE);
SELECT add_retention_policy('skill_executions', INTERVAL '90 days', if_not_exists => TRUE);

-- Set up continuous aggregates for performance metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS agent_performance_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', created_at) AS bucket,
    agent_id,
    metric_type,
    AVG(metric_value) AS avg_value,
    MIN(metric_value) AS min_value,
    MAX(metric_value) AS max_value,
    COUNT(*) AS sample_count
FROM agent_performance
GROUP BY bucket, agent_id, metric_type;

-- Refresh policy for continuous aggregates
SELECT add_continuous_aggregate_policy('agent_performance_hourly',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- ==================== Functions and Triggers ====================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at BEFORE UPDATE ON agents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_decision_rules_updated_at BEFORE UPDATE ON decision_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_circuit_breakers_updated_at BEFORE UPDATE ON circuit_breakers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_models_updated_at BEFORE UPDATE ON models
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_security_policies_updated_at BEFORE UPDATE ON security_policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agent_skills_updated_at BEFORE UPDATE ON agent_skills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_skills_updated_at BEFORE UPDATE ON skills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update heat score and access count
CREATE OR REPLACE FUNCTION update_memory_access()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_accessed_at = NOW();
    NEW.access_count = COALESCE(OLD.access_count, 0) + 1;
    -- Increase heat score on access (decay over time handled by background job)
    NEW.heat_score = LEAST(100.0, COALESCE(OLD.heat_score, 50.0) + 10.0);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply heat score trigger to memory tables
CREATE TRIGGER update_m0_access ON memory_m0
    FOR EACH ROW WHEN (OLD.access_count IS NOT NULL)
    EXECUTE FUNCTION update_memory_access();

CREATE TRIGGER update_m1_access ON memory_m1
    FOR EACH ROW WHEN (OLD.access_count IS NOT NULL)
    EXECUTE FUNCTION update_memory_access();

CREATE TRIGGER update_m2_access ON memory_m2
    FOR EACH ROW WHEN (OLD.access_count IS NOT NULL)
    EXECUTE FUNCTION update_memory_access();

CREATE TRIGGER update_m3_access ON memory_m3
    FOR EACH ROW WHEN (OLD.access_count IS NOT NULL)
    EXECUTE FUNCTION update_memory_access();

CREATE TRIGGER update_m4_access ON memory_m4
    FOR EACH ROW WHEN (OLD.access_count IS NOT NULL)
    EXECUTE FUNCTION update_memory_access();

-- Function to increment circuit breaker failure count
CREATE OR REPLACE FUNCTION update_circuit_breaker_failure()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' AND NEW.severity IN ('ERROR', 'CRITICAL', 'FATAL') THEN
        UPDATE circuit_breakers
        SET
            failure_count = failure_count + 1,
            state = CASE
                WHEN failure_count + 1 >= failure_threshold THEN 'OPEN'
                ELSE state
            END,
            last_failure_time = NOW()
        WHERE service_name = 'agent_' || NEW.agent_id::text;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER track_circuit_breaker_failure ON error_tracking
    AFTER INSERT FOR EACH ROW
    EXECUTE FUNCTION update_circuit_breaker_failure();

-- Function to log audit events
CREATE OR REPLACE FUNCTION log_audit_event()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (user_id, session_id, action, resource_type, resource_id, new_values, metadata)
        VALUES (NEW.user_id, NEW.session_id, 'INSERT', TG_TABLE_NAME, NEW.id, to_jsonb(NEW), '{"operation": "INSERT"}'::jsonb);
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (user_id, session_id, action, resource_type, resource_id, old_values, new_values, metadata)
        VALUES (NEW.user_id, NEW.session_id, 'UPDATE', TG_TABLE_NAME, NEW.id, to_jsonb(OLD), to_jsonb(NEW), '{"operation": "UPDATE"}'::jsonb);
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (user_id, session_id, action, resource_type, resource_id, old_values, metadata)
        VALUES (OLD.user_id, OLD.session_id, 'DELETE', TG_TABLE_NAME, OLD.id, to_jsonb(OLD), '{"operation": "DELETE"}'::jsonb);
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply audit logging to critical tables
CREATE TRIGGER audit_users ON users
    AFTER INSERT OR UPDATE OR DELETE FOR EACH ROW
    EXECUTE FUNCTION log_audit_event();

CREATE TRIGGER audit_agents ON agents
    AFTER INSERT OR UPDATE OR DELETE FOR EACH ROW
    EXECUTE FUNCTION log_audit_event();

CREATE TRIGGER audit_users ON users
    AFTER INSERT OR UPDATE OR DELETE FOR EACH ROW
    EXECUTE FUNCTION log_audit_event();

-- ==================== Initial Data ====================

-- Insert default admin user
INSERT INTO users (id, username, email, password_hash, full_name, is_admin, is_active)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'admin',
    'admin@jebat.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWqg.1jgH6G', -- bcrypt hash for 'admin'
    'JEBAT Administrator',
    true,
    true
) ON CONFLICT (username) DO NOTHING;

-- Insert default system user for agent operations
INSERT INTO users (id, username, email, password_hash, full_name, is_admin, is_active)
VALUES (
    '00000000-0000-0000-0000-000000000002',
    'system',
    'system@jebat.local',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyWqg.1jgH6G',
    'JEBAT System',
    true,
    true
) ON CONFLICT (username) DO NOTHING;

-- Insert default agents
INSERT INTO agents (id, name, type, description, config, capabilities, state, is_active) VALUES
(
    '00000000-0000-0000-0000-000000000010',
    'Researcher Agent',
    'researcher',
    'Specialized in web research, information gathering, and data collection',
    '{"max_results": 10, "search_engines": ["google", "bing"], "timeout": 300}'::jsonb,
    '["web_search", "data_extraction", "content_analysis", "source_verification"]'::jsonb,
    'IDLE',
    true
),
(
    '00000000-0000-0000-0000-000000000011',
    'Analyst Agent',
    'analyst',
    'Specialized in data analysis, pattern recognition, and insights generation',
    '{"analysis_depth": "deep", "visualization": true, "timeout": 300}'::jsonb,
    '["statistical_analysis", "pattern_recognition", "trend_detection", "report_generation"]'::jsonb,
    'IDLE',
    true
),
(
    '00000000-0000-0000-0000-000000000012',
    'Executor Agent',
    'executor',
    'Specialized in task execution, automation, and action implementation',
    '{"auto_approve": false, "timeout": 300, "max_retries": 3}'::jsonb,
    '["task_execution", "automation", "file_operations", "api_calls"]'::jsonb,
    'IDLE',
    true
),
(
    '00000000-0000-0000-0000-000000000013',
    'Memory Agent',
    'memory',
    'Specialized in memory management, consolidation, and retrieval optimization',
    '{"consolidation_interval": 3600, "compression_enabled": true, "timeout": 300}'::jsonb,
    '["memory_storage", "memory_retrieval", "memory_consolidation", "embedding_generation"]'::jsonb,
    'IDLE',
    true
) ON CONFLICT DO NOTHING;

-- Insert default skills
INSERT INTO skills (id, skill_name, skill_type, description, parameters, capabilities) VALUES
(
    '00000000-0000-0000-0000-000000000100',
    'web_search',
    'search',
    'Performs web search using various search engines',
    '{"query": "string", "max_results": "integer", "engine": "string"}'::jsonb,
    '["google_search", "bing_search", "duckduckgo_search", "result_ranking"]'::jsonb
),
(
    '00000000-0000-0000-0000-000000000101',
    'data_analyze',
    'analyze',
    'Analyzes data and extracts insights',
    '{"data": "object", "analysis_type": "string", "depth": "string"}'::jsonb,
    '["statistical_analysis", "pattern_detection", "trend_analysis", "anomaly_detection"]'::jsonb
),
(
    '00000000-0000-0000-0000-000000000102',
    'task_execute',
    'execute',
    'Executes tasks and automation workflows',
    '{"task": "object", "parameters": "object", "dry_run": "boolean"}'::jsonb,
    '["file_operations", "api_calls", "system_commands", "workflow_execution"]'::jsonb
),
(
    '00000000-0000-0000-0000-000000000103',
    'memory_remember',
    'remember',
    'Stores information in the memory system',
    '{"content": "string", "layer": "string", "metadata": "object"}'::jsonb,
    '["memory_storage", "embedding_generation", "metadata_extraction", "heat_scoring"]'::jsonb
),
(
    '00000000-0000-0000-0000-000000000104',
    'memory_recall',
    'remember',
    'Retrieves information from the memory system',
    '{"query": "string", "layer": "string", "limit": "integer"}'::jsonb,
    '["vector_search", "keyword_search", "hybrid_search", "context_retrieval"]'::jsonb
) ON CONFLICT DO NOTHING;

-- Assign skills to agents
INSERT INTO agent_skills (agent_id, skill_id, proficiency_level, is_enabled) VALUES
-- Researcher Agent skills
('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000100', 90, true),
('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000103', 85, true),
('00000000-0000-0000-0000-000000000010', '00000000-0000-0000-0000-000000000104', 80, true),

-- Analyst Agent skills
('00000000-0000-0000-0000-000000000011', '00000000-0000-0000-0000-000000000101', 95, true),
('00000000-0000-0000-0000-000000000011', '00000000-0000-0000-0000-000000000104', 85, true),

-- Executor Agent skills
('00000000-0000-0000-0000-000000000012', '00000000-0000-0000-0000-000000000102', 90, true),
('00000000-0000-0000-0000-000000000012', '00000000-0000-0000-0000-000000000104', 75, true),

-- Memory Agent skills
('00000000-0000-0000-0000-000000000013', '00000000-0000-0000-0000-000000000103', 95, true),
('00000000-0000-0000-0000-000000000013', '00000000-0000-0000-0000-000000000104', 95, true)
ON CONFLICT DO NOTHING;

-- Insert default decision rules
INSERT INTO decision_rules (rule_name, rule_type, conditions, actions, priority, is_active) VALUES
(
    'high_priority_to_analyst',
    'agent_selection',
    '{"priority": "CRITICAL", "task_type": "analysis"}'::jsonb,
    '{"agent_type": "analyst", "max_concurrent": 3}'::jsonb,
    100,
    true
),
(
    'research_to_researcher',
    'agent_selection',
    '{"task_type": "research", "requires_web_access": true}'::jsonb,
    '{"agent_type": "researcher", "max_concurrent": 5}'::jsonb,
    90,
    true
),
(
    'memory_to_memory_agent',
    'agent_selection',
    '{"task_type": "memory", "operation": ["store", "retrieve"]}'::jsonb,
    '{"agent_type": "memory", "max_concurrent": 10}'::jsonb,
    80,
    true
),
(
    'execution_to_executor',
    'agent_selection',
    '{"task_type": "execution", "requires_automation": true}'::jsonb,
    '{"agent_type": "executor", "max_concurrent": 5}'::jsonb,
    70,
    true
),
(
    'hot_cache_strategy',
    'cache_strategy',
    '{"access_frequency": "high", "data_size_kb": "< 100"}'::jsonb,
    '{"cache_tier": "HOT", "ttl_seconds": 300}'::jsonb,
    100,
    true
),
(
    'warm_cache_strategy',
    'cache_strategy',
    '{"access_frequency": "medium", "data_size_kb": "< 1000"}'::jsonb,
    '{"cache_tier": "WARM", "ttl_seconds": 3600}'::jsonb,
    90,
    true
),
(
    'cold_cache_strategy',
    'cache_strategy',
    '{"access_frequency": "low", "data_size_kb": "> 1000"}'::jsonb,
    '{"cache_tier": "COLD", "ttl_seconds": 86400}'::jsonb,
    80,
    true
) ON CONFLICT DO NOTHING;

-- Insert default models (Model Forge)
INSERT INTO models (model_name, provider, model_type, max_tokens, supports_function_calling, supports_vision, cost_per_1k_tokens, is_active) VALUES
(
    'gpt-4-turbo',
    'openai',
    'chat',
    128000,
    true,
    true,
    0.01,
    true
),
(
    'gpt-3.5-turbo',
    'openai',
    'chat',
    4096,
    true,
    false,
    0.002,
    true
),
(
    'claude-3-opus',
    'anthropic',
    'chat',
    200000,
    true,
    true,
    0.015,
    true
),
(
    'text-embedding-ada-002',
    'openai',
    'embedding',
    8191,
    false,
    false,
    0.0001,
    true
),
(
    'llama2-7b',
    'ollama',
    'chat',
    4096,
    false,
    false,
    0.0,
    true
) ON CONFLICT DO NOTHING;

-- Insert default security policies (Sentinel)
INSERT INTO security_policies (policy_name, policy_type, rules, actions, priority, is_active) VALUES
(
    'rate_limiting_per_user',
    'rate_limiting',
    '{"max_requests_per_minute": 60, "max_requests_per_hour": 1000}'::jsonb,
    '{"action": "throttle", "block_duration_seconds": 300}'::jsonb,
    100,
    true
),
(
    'content_filtering_malicious',
    'content_filtering',
    '{"patterns": ["<script>", "javascript:", "eval("], "max_length": 10000}'::jsonb,
    '{"action": "block", "log_event": true}'::jsonb,
    100,
    true
),
(
    'access_control_admin',
    'access_control',
    '{"required_role": "admin", "restricted_resources": ["users", "agents", "security_policies"]}'::jsonb,
    '{"action": "deny", "redirect": "/unauthorized"}'::jsonb,
    100,
    true
),
(
    'data_retention_90_days',
    'data_retention',
    '{"retention_days": 90, "apply_to": ["logs", "metrics", "events"]}'::jsonb,
    '{"action": "archive", "delete_after": 180}'::jsonb,
    50,
    true
) ON CONFLICT DO NOTHING;

-- ==================== Database Configuration ====================

-- Set up connection pool sizes (these are hints, actual settings in connection string)
ALTER DATABASE jebat_db SET shared_preload_libraries = 'timescaledb, pg_stat_statements';

-- Enable query logging for debugging (comment out in production)
-- ALTER DATABASE jebat_db SET log_statement = 'all';

-- Set time zone
SET timezone = 'UTC';

-- ==================== Completion Message ====================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'JEBAT Database Initialization Complete!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Tables created: %', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public');
    RAISE NOTICE 'Indexes created: %', (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public');
    RAISE NOTICE 'Hypertables created: %', (SELECT COUNT(*) FROM timescaledb_information.hypertables);
    RAISE NOTICE 'Functions created: %', (SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema = 'public');
    RAISE NOTICE 'Triggers created: %', (SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = 'public');
    RAISE NOTICE 'Default users: %', (SELECT COUNT(*) FROM users);
    RAISE NOTICE 'Default agents: %', (SELECT COUNT(*) FROM agents);
    RAISE NOTICE 'Default skills: %', (SELECT COUNT(*) FROM skills);
    RAISE NOTICE 'Default decision rules: %', (SELECT COUNT(*) FROM decision_rules);
    RAISE NOTICE 'Default models: %', (SELECT COUNT(*) FROM models);
    RAISE NOTICE 'Default security policies: %', (SELECT COUNT(*) FROM security_policies);
    RAISE NOTICE '========================================';
END $$;

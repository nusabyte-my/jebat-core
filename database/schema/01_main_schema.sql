-- ==================== JEBAT AI System - Main Database Schema ====================
-- Version: 1.0.0
-- Database: PostgreSQL 15+ with TimescaleDB 2.12+ and pgvector extension
--
-- This schema supports all enhanced systems:
-- - Memory System (5-layer architecture: M0-M4)
-- - Agent System (configurations, performance, tasks)
-- - Decision Engine (routing, priorities)
-- - Error Recovery System (circuit breakers, DLQ)
-- - Smart Cache (HOT/WARM/COLD tiers)
-- - MCP Protocol Server (JSON-RPC operations)
-- - WebSocket Gateway (real-time notifications)
-- - Model Forge (query optimization, model management)

-- ==================== Extensions ====================
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- ==================== ENUM Types ====================

-- Memory layer types
CREATE TYPE memory_layer AS ENUM ('M0', 'M1', 'M2', 'M3', 'M4');

-- Agent states
CREATE TYPE agent_state AS ENUM ('IDLE', 'BUSY', 'ERROR', 'MAINTENANCE', 'TERMINATED');

-- Task priorities
CREATE TYPE task_priority AS ENUM ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'BACKGROUND');

-- Task statuses
CREATE TYPE task_status AS ENUM ('PENDING', 'QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'RETRYING');

-- Error severity levels
CREATE TYPE error_severity AS ENUM ('INFO', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL');

-- Cache tier types
CREATE TYPE cache_tier AS ENUM ('HOT', 'WARM', 'COLD');

-- Circuit breaker states
CREATE TYPE circuit_state AS ENUM ('CLOSED', 'OPEN', 'HALF_OPEN');

-- WebSocket connection states
CREATE TYPE connection_state AS ENUM ('CONNECTING', 'CONNECTED', 'DISCONNECTED', 'ERROR');

-- ==================== Core Tables ====================

-- Memory System Tables (5-layer architecture)

-- M0: Working Memory (Immediate access, very short retention)
CREATE TABLE memory_m0 (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    session_id UUID NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    heat_score FLOAT DEFAULT 100.0,
    access_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '5 minutes',

    CONSTRAINT fk_user_m0 FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- M1: Short-term Memory (Recent conversations, temporary context)
CREATE TABLE memory_m1 (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    session_id UUID NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    heat_score FLOAT DEFAULT 80.0,
    access_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '24 hours',

    CONSTRAINT fk_user_m1 FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- M2: Medium-term Memory (Learning patterns, preferences)
CREATE TABLE memory_m2 (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    heat_score FLOAT DEFAULT 60.0,
    access_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '7 days',
    compressed BYTEA,

    CONSTRAINT fk_user_m2 FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- M3: Long-term Memory (Permanent knowledge, experiences)
CREATE TABLE memory_m3 (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    heat_score FLOAT DEFAULT 40.0,
    access_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT NOW() + INTERVAL '90 days',
    compressed BYTEA,
    tags TEXT[] DEFAULT '{}',

    CONSTRAINT fk_user_m3 FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- M4: Permanent Memory (Archived, immutable records)
CREATE TABLE memory_m4 (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    heat_score FLOAT DEFAULT 20.0,
    access_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ DEFAULT '9999-12-31 23:59:59.999999+00',
    compressed BYTEA,
    tags TEXT[] DEFAULT '{}',
    archived_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_user_m4 FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    settings JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

-- Agent Configuration Tables
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100) NOT NULL, -- 'researcher', 'analyst', 'executor', 'memory', 'custom'
    description TEXT,
    config JSONB DEFAULT '{}',
    capabilities JSONB DEFAULT '[]',
    state agent_state DEFAULT 'IDLE',
    max_concurrent_tasks INTEGER DEFAULT 5,
    timeout_seconds INTEGER DEFAULT 300,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_heartbeat_at TIMESTAMPTZ
);

-- Agent Performance Metrics (Time-series data for TimescaleDB)
CREATE TABLE agent_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL,
    task_id UUID,
    metric_type VARCHAR(50) NOT NULL, -- 'execution_time', 'success_rate', 'error_count', 'memory_usage', 'cpu_usage'
    metric_value FLOAT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_agent_performance_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

-- Tasks Table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL,
    user_id UUID NOT NULL,
    session_id UUID,
    parent_task_id UUID,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    task_type VARCHAR(100) NOT NULL,
    input_data JSONB,
    output_data JSONB,
    priority task_priority DEFAULT 'MEDIUM',
    status task_status DEFAULT 'PENDING',
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 300,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_task_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    CONSTRAINT fk_task_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_task_parent FOREIGN KEY (parent_task_id) REFERENCES tasks(id) ON DELETE SET NULL
);

-- Decision Engine Tables
CREATE TABLE decision_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_name VARCHAR(255) UNIQUE NOT NULL,
    rule_type VARCHAR(50) NOT NULL, -- 'agent_selection', 'task_routing', 'priority_assignment', 'cache_strategy'
    conditions JSONB NOT NULL,
    actions JSONB NOT NULL,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE decision_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID,
    agent_id UUID,
    rule_id UUID,
    decision_type VARCHAR(50) NOT NULL,
    input_context JSONB,
    output_decision JSONB,
    reasoning TEXT,
    confidence_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_decision_log_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    CONSTRAINT fk_decision_log_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL,
    CONSTRAINT fk_decision_log_rule FOREIGN KEY (rule_id) REFERENCES decision_rules(id) ON DELETE SET NULL
);

-- Error Recovery System Tables
CREATE TABLE error_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID,
    agent_id UUID,
    error_type VARCHAR(255) NOT NULL,
    error_message TEXT NOT NULL,
    error_stack TEXT,
    severity error_severity DEFAULT 'ERROR',
    is_resolved BOOLEAN DEFAULT false,
    resolution_message TEXT,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_error_tracking_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    CONSTRAINT fk_error_tracking_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL
);

CREATE TABLE circuit_breakers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    service_name VARCHAR(255) NOT NULL,
    state circuit_state DEFAULT 'CLOSED',
    failure_count INTEGER DEFAULT 0,
    failure_threshold INTEGER DEFAULT 5,
    success_count INTEGER DEFAULT 0,
    success_threshold INTEGER DEFAULT 2,
    last_failure_time TIMESTAMPTZ,
    open_timeout_seconds INTEGER DEFAULT 60,
    half_open_max_calls INTEGER DEFAULT 3,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE dead_letter_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID,
    agent_id UUID,
    original_message JSONB NOT NULL,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    next_retry_at TIMESTAMPTZ,
    is_processed BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_dlq_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    CONSTRAINT fk_dlq_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE SET NULL
);

-- Smart Cache Tables
CREATE TABLE cache_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_key VARCHAR(500) UNIQUE NOT NULL,
    cache_value BYTEA NOT NULL,
    cache_tier cache_tier NOT NULL,
    heat_score FLOAT DEFAULT 100.0,
    access_count INTEGER DEFAULT 0,
    size_bytes INTEGER,
    ttl_seconds INTEGER,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_accessed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE cache_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cache_tier cache_tier NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- 'hits', 'misses', 'evictions', 'size'
    metric_value FLOAT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- WebSocket Gateway Tables
CREATE TABLE websocket_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    session_id UUID NOT NULL,
    connection_id VARCHAR(255) UNIQUE NOT NULL,
    connection_state connection_state DEFAULT 'CONNECTING',
    connected_at TIMESTAMPTZ DEFAULT NOW(),
    disconnected_at TIMESTAMPTZ,
    last_ping_at TIMESTAMPTZ DEFAULT NOW(),
    last_pong_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',

    CONSTRAINT fk_ws_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE websocket_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    connection_id UUID NOT NULL,
    message_type VARCHAR(50) NOT NULL, -- 'request', 'response', 'notification', 'error'
    payload JSONB NOT NULL,
    is_sent BOOLEAN DEFAULT false,
    is_received BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_ws_message_connection FOREIGN KEY (connection_id) REFERENCES websocket_connections(id) ON DELETE CASCADE
);

-- MCP Protocol Server Tables
CREATE TABLE mcp_operations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operation_id VARCHAR(255) UNIQUE NOT NULL,
    method VARCHAR(100) NOT NULL, -- JSON-RPC 2.0 method names
    params JSONB,
    result JSONB,
    error JSONB,
    execution_time_ms INTEGER,
    status VARCHAR(50) NOT NULL, -- 'pending', 'processing', 'completed', 'error'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Model Forge Tables
CREATE TABLE models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(255) UNIQUE NOT NULL,
    provider VARCHAR(100) NOT NULL, -- 'openai', 'anthropic', 'ollama', 'custom'
    model_type VARCHAR(50) NOT NULL, -- 'chat', 'completion', 'embedding', 'image'
    api_endpoint TEXT,
    max_tokens INTEGER,
    supports_function_calling BOOLEAN DEFAULT false,
    supports_vision BOOLEAN DEFAULT false,
    cost_per_1k_tokens FLOAT,
    average_latency_ms INTEGER,
    success_rate FLOAT DEFAULT 1.0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE model_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL,
    task_id UUID,
    user_id UUID NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost FLOAT,
    latency_ms INTEGER,
    is_cached BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_model_usage_model FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
    CONSTRAINT fk_model_usage_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    CONSTRAINT fk_model_usage_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Sentinel Security System Tables
CREATE TABLE security_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL, -- 'anomaly_detected', 'threat_blocked', 'policy_violation', 'unauthorized_access'
    severity VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high', 'critical'
    user_id UUID,
    session_id UUID,
    ip_address INET,
    user_agent TEXT,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    is_resolved BOOLEAN DEFAULT false,
    resolved_by UUID,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_security_event_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_security_event_resolver FOREIGN KEY (resolved_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE security_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    policy_name VARCHAR(255) UNIQUE NOT NULL,
    policy_type VARCHAR(50) NOT NULL, -- 'rate_limiting', 'content_filtering', 'access_control', 'data_retention'
    rules JSONB NOT NULL,
    actions JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Logs
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    session_id UUID,
    action VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Skills System Tables
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    skill_name VARCHAR(255) UNIQUE NOT NULL,
    skill_type VARCHAR(50) NOT NULL, -- 'search', 'analyze', 'execute', 'remember', 'custom'
    description TEXT,
    parameters JSONB DEFAULT '{}',
    capabilities JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE agent_skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL,
    skill_id UUID NOT NULL,
    proficiency_level INTEGER DEFAULT 50, -- 0-100
    is_enabled BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_agent_skill_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    CONSTRAINT fk_agent_skill_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
    UNIQUE(agent_id, skill_id)
);

CREATE TABLE skill_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    skill_id UUID NOT NULL,
    agent_id UUID NOT NULL,
    task_id UUID,
    user_id UUID,
    input_parameters JSONB,
    output_results JSONB,
    execution_time_ms INTEGER,
    status VARCHAR(50) NOT NULL, -- 'success', 'error', 'timeout'
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT fk_skill_execution_skill FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
    CONSTRAINT fk_skill_execution_agent FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE,
    CONSTRAINT fk_skill_execution_task FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL,
    CONSTRAINT fk_skill_execution_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

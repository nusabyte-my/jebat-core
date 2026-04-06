-- JEBAT Memory System Database Schema
-- TimescaleDB (PostgreSQL 16) with time-series extensions

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- ============================================================================
-- MEMORIES TABLE - Core storage for all memory layers
-- ============================================================================

CREATE TABLE IF NOT EXISTS memories (
    -- Primary identification
    memory_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,

    -- Memory layer and lifecycle
    layer VARCHAR(20) NOT NULL CHECK (layer IN ('m0_sensory', 'm1_episodic', 'm2_semantic', 'm3_conceptual', 'm4_procedural')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,

    -- Deletion (soft delete)
    deleted_at TIMESTAMPTZ,
    delete_reason TEXT,

    -- Ownership and context
    user_id VARCHAR(100) NOT NULL,
    session_id VARCHAR(100),
    agent_id VARCHAR(100),
    source VARCHAR(100),

    -- Metadata
    tags TEXT[] DEFAULT '{}',
    modality VARCHAR(20) DEFAULT 'text' CHECK (modality IN ('text', 'image', 'audio', 'video', 'code', 'structured')),
    importance VARCHAR(20) DEFAULT 'medium' CHECK (importance IN ('critical', 'high', 'medium', 'low', 'trivial')),
    context JSONB DEFAULT '{}',

    -- Pinning (prevents decay)
    pinned BOOLEAN DEFAULT FALSE,
    pin_reason TEXT,

    -- Vector embedding for semantic search
    embedding VECTOR(1536)
);

-- Create hypertable for time-series queries (for M0-M3)
SELECT create_hypertable('memories', 'created_at', if_not_exists => TRUE);

-- Indexes for efficient queries
CREATE INDEX idx_memories_user ON memories(user_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_memories_layer ON memories(layer) WHERE deleted_at IS NULL;
CREATE INDEX idx_memories_created ON memories(created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_memories_expires ON memories(expires_at) WHERE expires_at IS NOT NULL;
CREATE INDEX idx_memories_tags ON memories USING GIN(tags) WHERE deleted_at IS NULL;
CREATE INDEX idx_memories_pinned ON memories(pinned) WHERE pinned = TRUE;
CREATE INDEX idx_memories_embedding ON memories USING ivfflat(embedding vector_cosine_ops) WHERE embedding IS NOT NULL;

-- ============================================================================
-- MEMORY_HEAT TABLE - Heat score components and tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS memory_heat (
    memory_id UUID PRIMARY KEY REFERENCES memories(memory_id) ON DELETE CASCADE,

    -- Heat score components (weights: 30%, 25%, 25%, 15%, 5%)
    visit_frequency FLOAT DEFAULT 0,
    interaction_depth FLOAT DEFAULT 0,
    recency FLOAT DEFAULT 1,
    cross_reference_count FLOAT DEFAULT 0,
    explicit_rating FLOAT DEFAULT 0.5,

    -- Computed total heat score
    total_heat FLOAT GENERATED ALWAYS AS (
        0.30 * visit_frequency +
        0.25 * interaction_depth +
        0.25 * recency +
        0.15 * cross_reference_count +
        0.05 * explicit_rating
    ) STORED,

    -- Visit tracking
    visit_count INTEGER DEFAULT 0,
    last_visit TIMESTAMPTZ,
    first_visit TIMESTAMPTZ DEFAULT NOW(),

    -- Decay tracking
    last_recalculation TIMESTAMPTZ DEFAULT NOW()
);

-- Index for heat-based queries
CREATE INDEX idx_memory_heat_total ON memory_heat(total_heat DESC);

-- ============================================================================
-- MEMORY_LINKS TABLE - Semantic relationships between memories
-- ============================================================================

CREATE TABLE IF NOT EXISTS memory_links (
    link_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL REFERENCES memories(memory_id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES memories(memory_id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL CHECK (relationship_type IN (
        'related_to', 'derived_from', 'contradicts', 'supports', 'example_of',
        'contains', 'part_of', 'before', 'after', 'caused_by', 'enables'
    )),
    strength FLOAT DEFAULT 1.0 CHECK (strength >= 0 AND strength <= 1),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Prevent duplicate links
    UNIQUE(source_id, target_id, relationship_type)
);

-- Indexes for relationship queries
CREATE INDEX idx_memory_links_source ON memory_links(source_id);
CREATE INDEX idx_memory_links_target ON memory_links(target_id);
CREATE INDEX idx_memory_links_type ON memory_links(relationship_type);

-- ============================================================================
-- MEMORY_VISITS TABLE - Detailed visit tracking for heat calculation
-- ============================================================================

CREATE TABLE IF NOT EXISTS memory_visits (
    visit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    memory_id UUID NOT NULL REFERENCES memories(memory_id) ON DELETE CASCADE,
    user_id VARCHAR(100) NOT NULL,

    -- Interaction depth (0.0-1.0)
    interaction_depth FLOAT DEFAULT 0.5 CHECK (interaction_depth >= 0 AND interaction_depth <= 1),

    -- Context
    session_id VARCHAR(100),
    action VARCHAR(50) CHECK (action IN ('view', 'edit', 'delete', 'pin', 'link', 'export')),

    -- Timing
    visited_at TIMESTAMPTZ DEFAULT NOW(),
    duration_seconds FLOAT
);

-- Create hypertable for time-series visit data
SELECT create_hypertable('memory_visits', 'visited_at', if_not_exists => TRUE);

-- Indexes for visit tracking
CREATE INDEX idx_memory_visits_memory ON memory_visits(memory_id);
CREATE INDEX idx_memory_visits_user ON memory_visits(user_id);
CREATE INDEX idx_memory_visits_visited ON memory_visits(visited_at DESC);

-- ============================================================================
-- MEMORY_PROFILES TABLE - Aggregated user profiles from M3/M4 memories
-- ============================================================================

CREATE TABLE IF NOT EXISTS memory_profiles (
    profile_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) NOT NULL UNIQUE,

    -- Aggregated preferences
    preferences JSONB DEFAULT '{}',

    -- Observed patterns
    patterns JSONB DEFAULT '{}',

    -- Mental models (from M3)
    mental_models TEXT[] DEFAULT '{}',

    -- Workflows (from M4)
    workflows JSONB DEFAULT '{}',

    -- Relationships
    key_relationships JSONB DEFAULT '{}',

    -- Important dates
    important_dates JSONB DEFAULT '{}',

    -- Metadata
    source_memories TEXT[] DEFAULT '{}',
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- SESSIONS TABLE - Track agent sessions and conversations
-- ============================================================================

CREATE TABLE IF NOT EXISTS sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_key VARCHAR(100) NOT NULL UNIQUE,

    -- Session metadata
    user_id VARCHAR(100) NOT NULL,
    agent_type VARCHAR(50),
    channel VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'terminated')),

    -- Timing
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    last_activity TIMESTAMPTZ DEFAULT NOW(),

    -- Context
    context JSONB DEFAULT '{}',

    -- Memory count
    memory_count INTEGER DEFAULT 0
);

-- Indexes for session queries
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_key ON sessions(session_key);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_activity ON sessions(last_activity DESC);

-- ============================================================================
-- CONSOLIDATION_LOGS TABLE - Track memory consolidation operations
-- ============================================================================

CREATE TABLE IF NOT EXISTS consolidation_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) NOT NULL,

    -- Consolidation stats
    memories_processed INTEGER DEFAULT 0,
    promoted INTEGER DEFAULT 0,
    demoted INTEGER DEFAULT 0,
    deleted INTEGER DEFAULT 0,
    heat_updated INTEGER DEFAULT 0,

    -- Breakdown by layer
    promotions_by_layer JSONB DEFAULT '{}',
    demotions_by_layer JSONB DEFAULT '{}',

    -- Performance
    duration_seconds FLOAT,
    error_count INTEGER DEFAULT 0,
    errors JSONB DEFAULT '{}',

    -- Timing
    consolidated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Details (stored separately if verbose)
    details JSONB DEFAULT '{}'
);

-- Create hypertable for consolidation tracking
SELECT create_hypertable('consolidation_logs', 'consolidated_at', if_not_exists => TRUE);

-- ============================================================================
-- RETENTION POLICIES - Automatic cleanup of expired memories
-- ============================================================================

-- M0: Sensory - 30 seconds
SELECT add_retention_policy('memories', INTERVAL '30 seconds', 'layer = ''m0_sensory''', if_not_exists => TRUE);

-- M1: Episodic - 24 hours
SELECT add_retention_policy('memories', INTERVAL '24 hours', 'layer = ''m1_episodic''', if_not_exists => TRUE);

-- M2: Semantic - 30 days
SELECT add_retention_policy('memories', INTERVAL '30 days', 'layer = ''m2_semantic''', if_not_exists => TRUE);

-- M3 and M4: No automatic retention (permanent)

-- Memory visits - 90 days
SELECT add_retention_policy('memory_visits', INTERVAL '90 days', if_not_exists => TRUE);

-- Consolidation logs - 365 days
SELECT add_retention_policy('consolidation_logs', INTERVAL '365 days', if_not_exists => TRUE);

-- ============================================================================
-- TRIGGERS - Automatic updates and maintenance
-- ============================================================================

-- Update updated_at on memory modification
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_memories_updated_at BEFORE UPDATE ON memories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Update profile updated_at on modification
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON memory_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Update session last_activity on modification
CREATE TRIGGER update_sessions_activity BEFORE UPDATE ON sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- VIEWS - Common query patterns
-- ============================================================================

-- Active memories (not deleted, not expired)
CREATE OR REPLACE VIEW active_memories AS
SELECT
    m.*,
    h.total_heat,
    h.visit_count
FROM memories m
LEFT JOIN memory_heat h ON m.memory_id = h.memory_id
WHERE m.deleted_at IS NULL
  AND (m.expires_at IS NULL OR m.expires_at > NOW())
  AND NOT m.pinned;

-- High heat memories (for consolidation)
CREATE OR REPLACE VIEW high_heat_memories AS
SELECT
    m.*,
    h.total_heat
FROM memories m
JOIN memory_heat h ON m.memory_id = h.memory_id
WHERE m.deleted_at IS NULL
  AND (m.expires_at IS NULL OR m.expires_at > NOW())
  AND h.total_heat >= 0.8
ORDER BY h.total_heat DESC;

-- Low heat memories (for decay)
CREATE OR REPLACE VIEW low_heat_memories AS
SELECT
    m.*,
    h.total_heat
FROM memories m
JOIN memory_heat h ON m.memory_id = h.memory_id
WHERE m.deleted_at IS NULL
  AND m.expires_at IS NULL
  AND h.total_heat < 0.4
  AND m.layer IN ('m2_semantic', 'm3_conceptual')
ORDER BY h.total_heat ASC;

-- User profile aggregation
CREATE OR REPLACE VIEW user_memory_stats AS
SELECT
    m.user_id,
    m.layer,
    COUNT(*) as count,
    AVG(h.total_heat) as avg_heat,
    MAX(h.total_heat) as max_heat,
    MIN(h.total_heat) as min_heat
FROM memories m
LEFT JOIN memory_heat h ON m.memory_id = h.memory_id
WHERE m.deleted_at IS NULL
  AND (m.expires_at IS NULL OR m.expires_at > NOW())
GROUP BY m.user_id, m.layer;

-- ============================================================================
-- FUNCTIONS - Utility functions for memory operations
-- ============================================================================

-- Calculate heat score for a memory
CREATE OR REPLACE FUNCTION calculate_heat(memory_id UUID)
RETURNS FLOAT AS $$
DECLARE
    current_heat FLOAT;
BEGIN
    -- Recalculate heat based on visits
    UPDATE memory_heat
    SET
        visit_frequency = (SELECT COUNT(*) / 7.0 FROM memory_visits WHERE memory_id = memory_heat.memory_id AND visited_at > NOW() - INTERVAL '7 days'),
        recency = EXP(-EXTRACT(EPOCH FROM (NOW() - GREATEST(last_visit, created_at))) / 86400.0),
        last_recalculation = NOW()
    WHERE memory_heat.memory_id = calculate_heat.memory_id;

    -- Get the new total heat
    SELECT total_heat INTO current_heat
    FROM memory_heat
    WHERE memory_id = calculate_heat.memory_id;

    RETURN current_heat;
END;
$$ LANGUAGE plpgsql;

-- Record a memory visit
CREATE OR REPLACE FUNCTION visit_memory(mem_id UUID, visit_user_id VARCHAR, visit_depth FLOAT DEFAULT 0.5)
RETURNS VOID AS $$
BEGIN
    -- Record visit
    INSERT INTO memory_visits (memory_id, user_id, interaction_depth)
    VALUES (mem_id, visit_user_id, visit_depth);

    -- Update heat stats
    UPDATE memory_heat
    SET
        visit_count = visit_count + 1,
        last_visit = NOW(),
        interaction_depth = LEAST(1.0, (interaction_depth * visit_count + visit_depth) / (visit_count + 1))
    WHERE memory_id = mem_id;

    -- Recalculate heat
    PERFORM calculate_heat(mem_id);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- INITIAL DATA - Seed data for development
-- ============================================================================

-- No initial seed data - schema is production-ready

-- ============================================================================
-- GRANTS - Permission setup (adjust for your environment)
-- ============================================================================

-- Grant permissions to application user (adjust username)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO jebat_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO jebat_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO jebat_app;

-- ============================================================================
-- COMMENTS - Schema documentation
-- ============================================================================

COMMENT ON TABLE memories IS 'Core storage for all memory layers (M0-M4)';
COMMENT ON TABLE memory_heat IS 'Heat score components and tracking for memories';
COMMENT ON TABLE memory_links IS 'Semantic relationships between memories';
COMMENT ON TABLE memory_visits IS 'Detailed visit tracking for heat calculation';
COMMENT ON TABLE memory_profiles IS 'Aggregated user profiles from M3/M4 memories';
COMMENT ON TABLE sessions IS 'Track agent sessions and conversations';
COMMENT ON TABLE consolidation_logs IS 'Track memory consolidation operations';

COMMENT ON COLUMN memories.layer IS 'Memory layer: m0_sensory, m1_episodic, m2_semantic, m3_conceptual, m4_procedural';
COMMENT ON COLUMN memory_heat.total_heat IS 'Computed heat score (0-1), higher = more important';
COMMENT ON COLUMN memory_links.relationship_type IS 'Type of semantic relationship between memories';
COMMENT ON COLUMN memory_visits.interaction_depth IS 'Depth of interaction (0.0-1.0), affects heat score';

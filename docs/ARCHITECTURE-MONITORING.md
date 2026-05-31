# JEBAT Monitoring Dashboard — Architecture Document

**Status**: Planned (2026-04-23)
**Scope**: Real-time monitoring dashboard for system metrics, Ultra-Loop cycles, Ultra-Think sessions, memory statistics, and agent performance
**Related**: ROADMAP.md (Q2 2026, April Week 1-2), /api/v1/metrics endpoint, existing get_stats() methods

---

## 1. Brainstorm

### Problem
JEBAT lacks a centralized real-time monitoring dashboard to visualize system health, performance metrics, and operational insights. While individual components have get_stats() methods and there's a /api/v1/metrics endpoint, there's no unified visualization layer for operators and developers.

### Goals
- Create a real-time dashboard showing key system metrics
- Visualize Ultra-Loop cycle statistics and performance
- Display Ultra-Think session analytics and thinking patterns
- Monitor memory layer statistics (M0/M1/M2/M3 layers, heat scores, consolidation rates)
- Track agent performance and utilization metrics
- Display channel activity and messaging statistics
- Provide health checks and alerting capabilities
- Enable historical trend analysis

### Non-Goals
- Long-term data retention (handled by TimescaleDB)
- Advanced alerting rules (Phase 2 work)
- User authentication for dashboard (initial version)
- Export/reporting features (future enhancement)

## 2. Wireframing (System Flow)

```
[Data Sources] ----> [Metrics Collection] ----> [Storage/Backend] ----> [Dashboard API] ----> [Frontend Visualization]
      |                     |                     |                     |                     |
      |                     |                     |                     |                     |
      v                     v                     v                     v                     v
[Orchestrator]     [HTTP Endpoints]     [TimescaleDB]     [FastAPI /metrics]     [React Dashboard]
[Memory Manager]   [Ultra-Loop Metrics]  [Time-series]     [JSON Responses]     [Charts/Tables]
[Decision Engine]  [Ultra-Think Metrics]                     [WebSocket?]       [Real-time Updates]
[Channel Manager]  [Agent Performance]
[Cache System]     [Memory Statistics]
```

### Data Flow:
1. Each component exposes get_stats() method
2. Metrics collector polls or receives updates from components
3. Data stored in TimescaleDB for time-series analysis
4. FastAPI /metrics endpoint serves current and historical data
5. Frontend React app consumes API and displays visualizations
6. Optional: WebSocket for real-time updates

## 3. DB Creation

### TimescaleDB Schema (Extension of existing):

```sql
-- Extend existing TimescaleDB setup from ARCHITECTURE.md
CREATE TABLE IF NOT EXISTS system_metrics (
    time TIMESTAMPTZ NOT NULL,
    component TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value DOUBLE PRECISION,
    metric_labels JSONB,
    PRIMARY KEY (time, component, metric_name)
);

SELECT create_hypertable('system_metrics', 'time');

-- Indexes for performance
CREATE INDEX ON system_metrics (component);
CREATE INDEX ON system_metrics (metric_name);
CREATE INDEX ON system_metrics (time DESC);

-- Pre-computed aggregates for dashboard performance
CREATE MATERIALIZED VIEW system_metrics_1h AS
SELECT 
    time_bucket('1 hour', time) AS bucket,
    component,
    metric_name,
    AVG(metric_value) AS avg_value,
    MAX(metric_value) AS max_value,
    MIN(metric_value) AS min_value,
    COUNT(*) AS sample_count
FROM system_metrics
GROUP BY bucket, component, metric_name
WITH NO DATA;

SELECT refresh_continuous_aggregate('system_metrics_1h');
```

### Existing Tables to Leverage:
- ultra_loop_cycles (from database integration)
- ultra_think_sessions (from memory integration)
- agent_performance (from agent system)
- memory_layers (from memory system)

## 4. Workflow

### Data Collection Phase:
1. Metrics collector service runs periodically (every 5-15 seconds)
2. For each registered component:
   - Call get_stats() method
   - Extract key metrics and convert to time-series points
   - Store in TimescaleDB with component and metric labels
3. Special handling for:
   - Ultra-Loop: cycle counts, success rates, execution times
   - Ultra-Think: session counts, thinking duration, token usage
   - Memory: layer sizes, heat scores, consolidation rates
   - Agents: success rates, average execution time, utilization
   - Channels: message rates, error rates, active connections

### Storage Phase:
1. Time-series data written to TimescaleDB
2. Automatic retention policies applied
3. Continuous aggregates pre-computed for common time windows (1h, 6h, 24h)

### API Phase:
1. FastAPI /metrics endpoint accepts query parameters:
   - time_range (last 1h, 6h, 24h, 7d)
   - component filter (orchestrator, memory, agent, etc.)
   - metric_filter (specific metrics to return)
   - aggregation (raw, avg, min, max, percentile)
2. Returns JSON formatted for charting libraries
3. Optional WebSocket endpoint for real-time updates

### Visualization Phase:
1. Frontend loads dashboard on initial visit
2. Subscribes to WebSocket for real-time updates (if implemented)
3. Polls REST API for historical data and periodic updates
4. Renders charts using Recharts or Plotly:
   - Time series line charts for trends
   - Bar charts for comparisons
   - Gauges for current status (health, success rates)
   - Tables for detailed breakdowns
   - Heatmaps for memory layer activity

## 5. UI/UX

### Dashboard Layout:
```
+-------------------------------------------------------------------------------------+
| Header: JEBAT System Monitoring | [Time Range Selector] | [Auto Refresh Toggle] |
+---------------------+---------------------+---------------------+---------------------+
| System Health       | Ultra-Loop Status   | Ultra-Think Activity| Memory Usage        |
| (Overall Status)    | (Cycles/Hour)       | (Sessions/Hour)     | (Layer Distribution)|
+---------------------+---------------------+---------------------+---------------------+
| Agent Performance   | Channel Activity    | Error Rates         | Resource Utilization|
| (Success Rates)     | (Messages/Hour)     | (Errors/Minute)     | (CPU/Memory/Disk)   |
+---------------------+---------------------+---------------------+---------------------+
| Detailed Metrics Panel (expandable sections for each component)                     |
+-------------------------------------------------------------------------------------+
| Real-time Alerts & Notifications (if implemented)                                   |
+-------------------------------------------------------------------------------------+
```

### Charts Types:
- **Time Series**: System uptime, request rates, response times
- **Gauges**: Health status (0-100%), success rates (0-100%), memory utilization
- **Bar Charts**: Agent performance comparison, channel message counts
- **Pie Charts**: Memory layer distribution, error type breakdown
- **Tables**: Detailed metric listings, recent errors, top slow operations
- **Heatmaps**: Memory access patterns over time

### User Interactions:
- Time range selector (1h, 6h, 24h, 7d, custom)
- Auto-refresh toggle (5s, 15s, 30s, 1m, manual)
- Component filtering (show/hide specific metric groups)
- Drill-down from summary cards to detailed views
- Export current view as PNG/CSV (future)

## 6. Structural Worktree

**New Files to Create**:
- `jebat-core/jebat/monitoring/` - New monitoring subsystem
- `jebat-core/jebat/monitoring/collector.py` - Metrics collection service
- `jebat-core/jebat/monitoring/storage.py` - TimescaleDB interface
- `jebat-core/jebat/monitoring/api.py` - FastAPI endpoints for dashboard
- `jebat-core/jebat/monitoring/dashboard.py` - Frontend (if using Streamlit) or integrate with existing web UI plans
- `jebat-core/jebat/monitoring/__init__.py` - Package exports
- `jebat-core/jebat/monitoring/models.py` - Pydantic/SQLModel definitions
- `jebat-core/jebat/monitoring/config.py` - Monitoring-specific configuration

**Existing Files to Modify**:
- `jebat-core/jebat/services/api/jebat_api.py` - Enhance /api/v1/metrics endpoint
- `jebat-core/jebat/core/agents/orchestrator.py` - Ensure get_stats() includes monitoring-relevant metrics
- `jebat-core/jebat/core/memory/manager.py` - Enhance get_stats() for memory layer details
- `jebat-core/jebat/features/ultra_loop/ultra_loop.py` - Enhance get_metrics() for cycle details
- `jebat-core/jebat/features/ultra_think/ultra_think.py` - Enhance get_metrics() for session details
- `jebat-core/jebat/integrations/channels/channel_manager.py` - Enhance get_stats() for channel details

**Configuration Files**:
- `jebat-core/jebat/config/monitoring.yaml` - Monitoring-specific settings
- Update `jebat-core/jebat/config/config.yaml` to include monitoring section

## 7. Checklist

- [ ] Create monitoring subsystem directory structure
- [ ] Implement metrics collector service
- [ ] Define TimescaleDB schema for system metrics
- [ ] Implement storage layer for time-series data
- [ ] Enhance existing get_stats() methods to include monitoring metrics
- [ ] Create FastAPI endpoints for dashboard data retrieval
- [ ] Build frontend dashboard with React (or Streamlit prototype)
- [ ] Implement time range filtering and component selection
- [ ] Add visualization charts for key metrics
- [ ] Implement real-time updates (WebSocket or polling)
- [ ] Add health status indicators and alerting placeholders
- [ ] Write comprehensive tests for monitoring components
- [ ] Update documentation (this file, ROADMAP.md, todo.md, lessons.md)
- [ ] Verify end-to-end functionality with test data
- [ ] Performance test metrics collection overhead
- [ ] Security review: ensure no sensitive data exposed in metrics

## 8. Security

### Threat Model:
- **Information Disclosure**: Metrics could reveal system internals or usage patterns
- **Denial of Service**: Metrics collection could impact system performance
- **Data Tampering**: False metrics could misleading operators
- **Unauthorized Access**: Dashboard could be accessed without proper controls

### Controls Implemented:
1. **Metric Sanitization**: Review all get_stats() outputs for sensitive data before collection
2. **Rate Limiting**: Limit metrics collection frequency to prevent overhead
3. **Data Validation**: Validate incoming metric values for plausibility
4. **Access Control**: Initial version assumes trusted environment; future versions add auth
5. **Secure Transmission**: Use HTTPS for API calls in production
6. **Minimal Privilege**: Database user has limited permissions (INSERT, SELECT on monitoring tables)

### Open Security Items:
- Add authentication requirement for /metrics endpoint
- Implement role-based access control for different metric views
- Add audit logging for metric access
- Encrypt sensitive metric labels if needed
- Implement secure WebSocket connections (wss://)

## 9. Orchestration & Handoff

The monitoring dashboard is designed as an **observable layer** that sits atop the existing JEBAT orchestration system:

- **Planning**: No additional planning required; monitoring observes existing orchestration
- **Execution**: Monitoring collector runs as a background service; does not interfere with task execution
- **Synthesis**: Metrics are aggregated and stored for later analysis; no impact on real-time task processing
- **API**: Extends existing /api/v1/metrics endpoint with enhanced detail and time-series capabilities
- **Testing**: Will add tests to test_monitoring.py; existing system tests should continue to pass

**Dependencies**:
- Existing get_stats() methods in all components (must be maintained and enhanced)
- TimescaleDB extension (already planned in ARCHITECTURE.md)
- FastAPI framework (already in use)
- TimescaleDB for time-series storage (new dependency for this phase)

**Backwards Compatibility**:
- All existing APIs remain unchanged
- Enhanced /api/v1/metrics endpoint is additive
- No changes to existing component interfaces
- Dashboard is optional; system functions identically without it

**Deliverable**: Complete real-time monitoring dashboard with:
- Functional metrics collection service
- Time-series storage in TimescaleDB
- Enhanced API endpoints with historical data
- React-based dashboard with multiple visualization types
- End-to-end testing and documentation
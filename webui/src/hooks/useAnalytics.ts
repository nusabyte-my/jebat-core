import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

// ==================== Types ====================

export interface TimeRange {
  start: string;
  end: string;
  period_type: 'auto' | 'hourly' | 'daily' | 'weekly' | 'monthly';
}

export interface EventCountResponse {
  bucket: string;
  tenant_id: string;
  category: string | null;
  event_name: string | null;
  event_count: number;
  unique_users: number;
  unique_sessions: number;
  avg_duration_ms: number | null;
  max_duration_ms: number | null;
}

export interface SessionMetricsResponse {
  bucket: string;
  tenant_id: string;
  session_count: number;
  unique_users: number;
  total_messages: number;
  total_tool_calls: number;
  total_api_calls: number;
  total_errors: number;
  avg_session_duration: number | null;
  avg_messages_per_session: number | null;
}

export interface SentimentDistribution {
  label: string;
  count: number;
  percentage: number;
}

export interface ConversationInsightSummary {
  tenant_id: string;
  period_start: string;
  period_end: string;
  total_conversations: number;
  avg_sentiment_score: number;
  sentiment_distribution: SentimentDistribution[];
  top_topics: Array<Record<string, unknown>>;
  avg_quality_score: number;
  avg_coherence_score: number;
  avg_helpfulness_score: number;
  avg_safety_score: number;
  total_tokens: number;
  avg_latency_ms: number;
}

export interface AgentPerformanceSummary {
  agent_id: string;
  agent_type: string;
  agent_name: string;
  total_executions: number;
  success_rate: number;
  error_rate: number;
  avg_duration_ms: number;
  p50_duration_ms: number;
  p95_duration_ms: number;
  p99_duration_ms: number;
  top_capabilities: Array<Record<string, unknown>>;
  top_errors: Array<Record<string, unknown>>;
}

export interface UsageStats {
  total_events: number;
  active_users: number;
  total_sessions: number;
  avg_session_duration: number;
  top_events: Array<{ event_name: string; count: number }>;
}

export interface SystemHealthMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  active_connections: number;
  request_latency_p50: number;
  request_latency_p95: number;
  error_rate: number;
}

// ==================== Query Keys ====================

export const analyticsKeys = {
  all: ['analytics'] as const,
  events: (timeRange: TimeRange) => [...analyticsKeys.all, 'events', timeRange] as const,
  sessions: (timeRange: TimeRange) => [...analyticsKeys.all, 'sessions', timeRange] as const,
  conversations: (timeRange: TimeRange) => [...analyticsKeys.all, 'conversations', timeRange] as const,
  agents: (timeRange: TimeRange) => [...analyticsKeys.all, 'agents', timeRange] as const,
  usage: (timeRange: TimeRange) => [...analyticsKeys.all, 'usage', timeRange] as const,
  health: () => [...analyticsKeys.all, 'health'] as const,
};

// ==================== API Functions ====================

async function fetchEventCounts(timeRange: TimeRange): Promise<EventCountResponse[]> {
  const params = new URLSearchParams({
    start: timeRange.start,
    end: timeRange.end,
    period_type: timeRange.period_type,
  });
  const response = await api.get<EventCountResponse[]>(
    `/api/v1/analytics/events/counts?${params}`
  );
  return response;
}

async function fetchSessionMetrics(timeRange: TimeRange): Promise<SessionMetricsResponse[]> {
  const params = new URLSearchParams({
    start: timeRange.start,
    end: timeRange.end,
    period_type: timeRange.period_type,
  });
  const response = await api.get<SessionMetricsResponse[]>(
    `/api/v1/analytics/sessions/metrics?${params}`
  );
  return response;
}

async function fetchConversationInsights(
  timeRange: TimeRange
): Promise<ConversationInsightSummary> {
  const params = new URLSearchParams({
    start: timeRange.start,
    end: timeRange.end,
  });
  const response = await api.get<ConversationInsightSummary>(
    `/api/v1/analytics/conversations/insights?${params}`
  );
  return response;
}

async function fetchAgentPerformance(
  timeRange: TimeRange
): Promise<AgentPerformanceSummary[]> {
  const params = new URLSearchParams({
    start: timeRange.start,
    end: timeRange.end,
  });
  const response = await api.get<AgentPerformanceSummary[]>(
    `/api/v1/analytics/agents/performance?${params}`
  );
  return response;
}

async function fetchUsageStats(timeRange: TimeRange): Promise<UsageStats> {
  const params = new URLSearchParams({
    start: timeRange.start,
    end: timeRange.end,
  });
  const response = await api.get<UsageStats>(
    `/api/v1/analytics/usage/stats?${params}`
  );
  return response;
}

async function fetchSystemHealth(): Promise<SystemHealthMetrics> {
  const response = await api.get<SystemHealthMetrics>('/api/v1/analytics/system/health');
  return response;
}

// ==================== Hooks ====================

export function useEventCounts(timeRange: TimeRange) {
  return useQuery({
    queryKey: analyticsKeys.events(timeRange),
    queryFn: () => fetchEventCounts(timeRange),
    staleTime: 30000,
    refetchInterval: 60000,
  });
}

export function useSessionMetrics(timeRange: TimeRange) {
  return useQuery({
    queryKey: analyticsKeys.sessions(timeRange),
    queryFn: () => fetchSessionMetrics(timeRange),
    staleTime: 30000,
    refetchInterval: 60000,
  });
}

export function useConversationInsights(timeRange: TimeRange) {
  return useQuery({
    queryKey: analyticsKeys.conversations(timeRange),
    queryFn: () => fetchConversationInsights(timeRange),
    staleTime: 60000,
    refetchInterval: 120000,
  });
}

export function useAgentPerformance(timeRange: TimeRange) {
  return useQuery({
    queryKey: analyticsKeys.agents(timeRange),
    queryFn: () => fetchAgentPerformance(timeRange),
    staleTime: 60000,
    refetchInterval: 120000,
  });
}

export function useUsageStats(timeRange: TimeRange) {
  return useQuery({
    queryKey: analyticsKeys.usage(timeRange),
    queryFn: () => fetchUsageStats(timeRange),
    staleTime: 30000,
    refetchInterval: 60000,
  });
}

export function useSystemHealth() {
  return useQuery({
    queryKey: analyticsKeys.health(),
    queryFn: fetchSystemHealth,
    staleTime: 10000,
    refetchInterval: 30000,
  });
}

// ==================== Utility ====================

export function getDefaultTimeRange(
  period: '1h' | '24h' | '7d' | '30d' = '24h'
): TimeRange {
  const end = new Date();
  const start = new Date();

  switch (period) {
    case '1h':
      start.setHours(start.getHours() - 1);
      break;
    case '24h':
      start.setHours(start.getHours() - 24);
      break;
    case '7d':
      start.setDate(start.getDate() - 7);
      break;
    case '30d':
      start.setDate(start.getDate() - 30);
      break;
  }

  return {
    start: start.toISOString(),
    end: end.toISOString(),
    period_type: 'auto',
  };
}
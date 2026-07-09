import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../../lib/api';

// ==================== Types ====================

export interface UsageOverview {
  period_start: string;
  period_end: string;
  total_api_calls: number;
  total_sessions: number;
  active_users: number;
  total_messages: number;
  total_swarm_executions: number;
  total_storage_mb: number;
  error_rate: number;
  avg_response_time_ms: number;
  top_endpoints: Array<{ endpoint: string; count: number }>;
  top_agents: Array<{ agent_id: string; agent_name: string; agent_type: string; executions: number; success_rate: number }>;
}

export interface EventCount {
  bucket: string;
  tenant_id: string;
  category?: string;
  event_name?: string;
  event_count: number;
  unique_users: number;
  unique_sessions: number;
  avg_duration_ms?: number;
  max_duration_ms?: number;
}

export interface SessionMetrics {
  bucket: string;
  tenant_id: string;
  session_count: number;
  unique_users: number;
  total_messages: number;
  total_tool_calls: number;
  total_api_calls: number;
  total_errors: number;
  avg_session_duration?: number;
  avg_messages_per_session?: number;
}

export interface ConversationInsights {
  period_start: string;
  period_end: string;
  total_conversations: number;
  avg_sentiment_score: number;
  sentiment_distribution: Array<{ label: string; count: number; percentage: number }>;
  top_topics: Array<{ topic: string; count: number }>;
  avg_quality_score: number;
  avg_coherence_score: number;
  avg_helpfulness_score: number;
  avg_safety_score: number;
  total_tokens: number;
  avg_latency_ms: number;
}

export interface AgentPerformance {
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
  top_capabilities: Array<{ capability: string; count: number }>;
  top_errors: Array<{ error: string; count: number }>;
}

export interface MemoryPattern {
  layer: string;
  total_memories: number;
  new_memories: number;
  avg_heat_score: number;
  total_size_mb: number;
  growth_rate: number;
  projected_size_30d_mb: number;
}

export interface Anomaly {
  id: string;
  metric_name: string;
  anomaly_type: string;
  severity: string;
  expected_value: number;
  actual_value: number;
  deviation_percent: number;
  detection_start: string;
  detection_end: string;
  is_resolved: boolean;
  model_name?: string;
}

export interface SentimentOverview {
  period_start: string;
  period_end: string;
  total_conversations: number;
  distribution: Array<{
    label: string;
    count: number;
    percentage: number;
    avg_score: number;
    avg_confidence: number;
  }>;
}

// ==================== API Functions ====================

const analyticsApi = {
  getOverview: (period: string) => 
    api.get<UsageOverview>(`/analytics/overview?period=${period}`),
  
  getEvents: (params: {
    start?: string;
    end?: string;
    category?: string;
    event_name?: string;
    period_type?: string;
    limit?: number;
    offset?: number;
  }) => 
    api.get<EventCount[]>('/analytics/events', { params }),
  
  getSessions: (params: {
    start?: string;
    end?: string;
    period_type?: string;
    limit?: number;
    offset?: number;
  }) => 
    api.get<SessionMetrics[]>('/analytics/sessions', { params }),
  
  getConversations: (params: {
    start?: string;
    end?: string;
  }) => 
    api.get<ConversationInsights>('/analytics/conversations', { params }),
  
  getAgents: (params: {
    start?: string;
    end?: string;
    agent_type?: string;
    limit?: number;
  }) => 
    api.get<AgentPerformance[]>('/analytics/agents', { params }),
  
  getMemory: (params: {
    start?: string;
    end?: string;
    layer?: string;
    period_type?: string;
  }) => 
    api.get<MemoryPattern[]>('/analytics/memory', { params }),
  
  getAnomalies: (params: {
    start?: string;
    end?: string;
    severity?: string;
    resolved?: boolean;
    limit?: number;
  }) => 
    api.get<Anomaly[]>('/analytics/anomalies', { params }),
  
  resolveAnomaly: (id: string, notes?: string) => 
    api.post(`/analytics/anomalies/${id}/resolve`, { notes }),
  
  getSentiment: (params: {
    start?: string;
    end?: string;
  }) => 
    api.get('/analytics/sentiment', { params }),
  
  getRealtimeStatus: () => 
    api.get('/analytics/realtime/status'),
};

// ==================== Hooks ====================

export function useAnalyticsOverview(period: string = '7d') {
  return useQuery({
    queryKey: ['analytics', 'overview', period],
    queryFn: () => analyticsApi.getOverview(period),
    staleTime: 60000, // 1 minute
    refetchInterval: 60000, // Auto-refresh every minute
  });
}

export function useEventCounts(params: {
  start?: string;
  end?: string;
  category?: string;
  event_name?: string;
  period_type?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ['analytics', 'events', params],
    queryFn: () => analyticsApi.getEvents(params),
    staleTime: 60000,
    refetchInterval: 60000,
  });
}

export function useSessionMetrics(params: {
  start?: string;
  end?: string;
  period_type?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: ['analytics', 'sessions', params],
    queryFn: () => analyticsApi.getSessions(params),
    staleTime: 60000,
    refetchInterval: 60000,
  });
}

export function useConversationInsights(params: {
  start?: string;
  end?: string;
}) {
  return useQuery({
    queryKey: ['analytics', 'conversations', params],
    queryFn: () => analyticsApi.getConversations(params),
    staleTime: 60000,
    refetchInterval: 60000,
  });
}

export function useAgentPerformance(params: {
  start?: string;
  end?: string;
  agent_type?: string;
  limit?: number;
}) {
  return useQuery({
    queryKey: ['analytics', 'agents', params],
    queryFn: () => analyticsApi.getAgents(params),
    staleTime: 60000,
    refetchInterval: 60000,
  });
}

export function useMemoryPatterns(params: {
  start?: string;
  end?: string;
  layer?: string;
  period_type?: string;
}) {
  return useQuery({
    queryKey: ['analytics', 'memory', params],
    queryFn: () => analyticsApi.getMemory(params),
    staleTime: 60000,
    refetchInterval: 60000,
  });
}

export function useAnomalies(params: {
  start?: string;
  end?: string;
  severity?: string;
  resolved?: boolean;
  limit?: number;
}) {
  return useQuery({
    queryKey: ['analytics', 'anomalies', params],
    queryFn: () => analyticsApi.getAnomalies(params),
    staleTime: 30000,
    refetchInterval: 30000,
  });
}

export function useResolveAnomaly() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, notes }: { id: string; notes?: string }) => 
      analyticsApi.resolveAnomaly(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analytics', 'anomalies'] });
    },
  });
}

export function useSentimentOverview(params: {
  start?: string;
  end?: string;
}) {
  return useQuery({
    queryKey: ['analytics', 'sentiment', params],
    queryFn: () => analyticsApi.getSentiment(params),
    staleTime: 60000,
    refetchInterval: 60000,
  });
}

export function useRealtimeStatus() {
  return useQuery({
    queryKey: ['analytics', 'realtime', 'status'],
    queryFn: () => analyticsApi.getRealtimeStatus(),
    staleTime: 30000,
  });
}

// ==================== WebSocket Hook ====================

export function useAnalyticsWebSocket(tenantId: string, token: string) {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const connect = useCallback(() => {
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/analytics/ws`;
    const websocket = new WebSocket(`${wsUrl}?token=${token}`);

    websocket.onopen = () => {
      setConnected(true);
      setError(null);
      console.log('Analytics WebSocket connected');
    };

    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setMessages(prev => [...prev.slice(-99), data]); // Keep last 100
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    websocket.onclose = () => {
      setConnected(false);
      // Reconnect after 5 seconds
      setTimeout(connect, 5000);
    };

    websocket.onerror = (err) => {
      setError('WebSocket error');
      console.error('WebSocket error:', err);
    };

    setWs(websocket);
  }, [token]);

  useEffect(() => {
    connect();
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [connect]);

  return { connected, messages, error };
}

// ==================== Utility Hooks ====================

export function useDateRange(preset: string = '7d') {
  const [startDate, setStartDate] = useState<Date | undefined>(() => {
    const end = new Date();
    const start = new Date();
    const days = parseInt(preset.replace('d', '')) || 7;
    start.setDate(start.getDate() - days);
    return start;
  });
  const [endDate, setEndDate] = useState<Date | undefined>(() => new Date());

  const setPreset = (newPreset: string) => {
    const end = new Date();
    const start = new Date();
    const days = parseInt(newPreset.replace('d', '')) || 7;
    start.setDate(start.getDate() - days);
    setStartDate(start);
    setEndDate(end);
  };

  return { startDate, endDate, setStartDate, setEndDate, setPreset };
}

export function usePeriod() {
  const [period, setPeriod] = useState('daily');
  return { period, setPeriod };
}

export function useCategoryFilter(categories: string[] = []) {
  const [category, setCategory] = useState('');
  return { category, setCategory, options: ['', ...categories] };
}
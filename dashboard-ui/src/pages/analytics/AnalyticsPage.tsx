'use client';

import { useState } from 'react';
import { Calendar, TrendingUp, TrendingDown, Users, MessageSquare, Bot, AlertTriangle, ExternalLink, RefreshCw } from 'lucide-react';
import { KPICard, CardGrid, MetricCard, FilterBar, Select, DateRangePicker } from '@/components/analytics/ui';
import { TimeSeriesChart, BarChart, PieChart } from '@/components/analytics/charts';
import { 
  useAnalyticsOverview, 
  useEventCounts, 
  useSessionMetrics, 
  useConversationInsights,
  useAgentPerformance,
  useMemoryPatterns,
  useAnomalies,
  useSentimentOverview,
  useResolveAnomaly,
  useDateRange,
  usePeriod,
} from '@/hooks/analytics/analytics';
import { cn } from '@/lib/utils';

export default function AnalyticsPage() {
  const { startDate, endDate, setPreset } = useDateRange('7d');
  const { period, setPeriod } = usePeriod();
  const [category, setCategory] = useState('');

  const { data: overview, isLoading: overviewLoading } = useAnalyticsOverview('7d');
  const { data: events, isLoading: eventsLoading } = useEventCounts({
    start: startDate?.toISOString(),
    end: endDate?.toISOString(),
    category: category || undefined,
    period_type: period,
  });
  const { data: sessions, isLoading: sessionsLoading } = useSessionMetrics({
    start: startDate?.toISOString(),
    end: endDate?.toISOString(),
    period_type: period,
  });
  const { data: conversations } = useConversationInsights({
    start: startDate?.toISOString(),
    end: endDate?.toISOString(),
  });
  const { data: agents } = useAgentPerformance({ limit: 10 });
  const { data: memory } = useMemoryPatterns({});
  const { data: anomalies, isLoading: anomaliesLoading } = useAnomalies({ limit: 20 });
  const { data: sentiment } = useSentimentOverview({});
  const resolveAnomaly = useResolveAnomaly();

  const handleResolveAnomaly = async (id: string) => {
    try {
      await resolveAnomaly.mutateAsync({ id });
    } catch (error) {
      console.error('Failed to resolve anomaly:', error);
    }
  };

  const eventsChartData = events?.map(e => ({
    timestamp: e.bucket,
    events: e.event_count,
    users: e.unique_users,
  })).reverse() || [];

  const sessionsChartData = sessions?.map(s => ({
    timestamp: s.bucket,
    sessions: s.session_count,
    users: s.unique_users,
    messages: s.total_messages,
  })).reverse() || [];

  const sentimentData = sentiment?.distribution?.map(d => ({
    name: d.label,
    value: d.count,
  })) || [];

  const memoryData = memory?.map(m => ({
    name: m.layer,
    memories: m.total_memories,
    size_mb: m.total_size_mb,
  })) || [];

  const agentExecutions = agents?.slice(0, 8).map(a => ({
    name: a.agent_name.length > 12 ? a.agent_name.slice(0, 12) + '...' : a.agent_name,
    executions: a.total_executions,
    success_rate: a.success_rate,
  })) || [];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics Dashboard</h1>
          <p className="text-muted-foreground mt-1">Monitor system performance, usage patterns, and anomalies</p>
        </div>
        <div className="flex items-center gap-2">
          <select value={period} onChange={(e) => setPeriod(e.target.value)} className="h-10 px-3 py-2 text-sm border border-input bg-background rounded-none focus:outline-none focus:ring-2 focus:ring-ring">
            <option value="hourly">Hourly</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
          <div className="flex items-center gap-1">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <select value="" onChange={(e) => setPreset(e.target.value)} className="h-10 px-3 py-2 text-sm border border-input bg-background rounded-none focus:outline-none focus:ring-2 focus:ring-ring text-muted-foreground">
              <option value="" disabled>Quick select</option>
              <option value="1d">Last 24h</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
            </select>
          </div>
        </div>
      </div>

      <CardGrid>
        <KPICard title="API Calls" value={overview?.total_api_calls || 0} trend={5.2} trendLabel="vs last period" icon={<TrendingUp className="h-6 w-6" />} />
        <KPICard title="Active Users" value={overview?.active_users || 0} trend={2.1} trendLabel="vs last period" icon={<Users className="h-6 w-6" />} />
        <KPICard title="Messages" value={overview?.total_messages || 0} trend={-1.3} trendLabel="vs last period" icon={<MessageSquare className="h-6 w-6" />} />
        <KPICard title="Error Rate" value={`${overview?.error_rate || 0}%`} trend={-0.5} trendLabel="vs last period" icon={<AlertTriangle className="h-6 w-6" />} />
      </CardGrid>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="bg-card border rounded-none p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Event Volume</h3>
            <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-none bg-cyan-500" /> Events</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-none bg-emerald-500" /> Users</span>
            </div>
          </div>
          <TimeSeriesChart data={eventsChartData} xKey="timestamp" yKeys={['events', 'users']} yLabels={{ events: 'Events', users: 'Unique Users' }} colors={['#06b6d4', '#10b981']} height={300} />
        </div>
        <div className="bg-card border rounded-none p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Sessions & Messages</h3>
            <div className="flex items-center gap-2 text-xs text-muted-foreground font-mono">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-none bg-cyan-500" /> Sessions</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-none bg-emerald-500" /> Messages</span>
            </div>
          </div>
          <TimeSeriesChart data={sessionsChartData} xKey="timestamp" yKeys={['sessions', 'messages']} yLabels={{ sessions: 'Sessions', messages: 'Messages' }} colors={['#06b6d4', '#10b981']} height={300} showArea />
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="bg-card border rounded-none p-5 lg:col-span-2">
          <h3 className="text-lg font-semibold mb-4">Sentiment Distribution</h3>
          <PieChart data={sentimentData} nameKey="name" valueKey="value" colors={['#10b981', '#52525b', '#ef4444', '#06b6d4']} height={300} />
        </div>
        <div className="bg-card border rounded-none p-5">
          <h3 className="text-lg font-semibold mb-4">Top Agents</h3>
          <BarChart data={agentExecutions} xKey="name" yKeys={['executions']} yLabels={{ executions: 'Executions' }} colors={['#06b6d4']} height={280} horizontal />
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="bg-card border rounded-none p-5">
          <h3 className="text-lg font-semibold mb-4">Memory Layer Distribution</h3>
          <BarChart data={memoryData} xKey="name" yKeys={['memories', 'size_mb']} yLabels={{ memories: 'Count', size_mb: 'Size (MB)' }} colors={['#06b6d4', '#10b981']} height={300} horizontal />
        </div>
        <div className="bg-card border rounded-none p-5">
          <h3 className="text-lg font-semibold mb-4">Agent Performance</h3>
          <div className="space-y-3">
            {agents?.slice(0, 5).map((agent) => (
              <div key={agent.agent_id} className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                <div className="flex items-center gap-3">
                  <Bot className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium truncate max-w-[150px]">{agent.agent_name}</p>
                    <p className="text-xs text-muted-foreground capitalize">{agent.agent_type}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-mono font-semibold">{agent.total_executions}</p>
                  <p className="text-xs text-green-500">{agent.success_rate.toFixed(1)}% success</p>
                </div>
              </div>
            ))}
            {agents && agents.length > 5 && (
              <button className="w-full text-sm text-primary hover:underline mt-2">View all {agents.length} agents</button>
            )}
          </div>
        </div>
      </div>

      <div className="bg-card border rounded-none p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Recent Anomalies</h3>
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">{anomaliesLoading ? 'Loading...' : `${anomalies?.length || 0} anomalies`}</span>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                <th className="pb-3 px-4">Metric</th>
                <th className="pb-3 px-4">Type</th>
                <th className="pb-3 px-4">Severity</th>
                <th className="pb-3 px-4">Deviation</th>
                <th className="pb-3 px-4">Detected</th>
                <th className="pb-3 px-4">Status</th>
                <th className="pb-3 px-4"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {(anomalies || []).map((anomaly) => (
                <tr key={anomaly.id} className="hover:bg-muted/50">
                  <td className="py-3 px-4 font-mono text-sm">{anomaly.metric_name}</td>
                  <td className="py-3 px-4"><span className="px-2 py-0.5 text-xs rounded-none bg-muted text-muted-foreground">{anomaly.anomaly_type}</span></td>
                  <td className="py-3 px-4"><span className={`px-2 py-0.5 text-xs rounded-none ${anomaly.severity === 'critical' ? 'bg-red-500/20 text-red-500' : anomaly.severity === 'high' ? 'bg-orange-500/20 text-orange-500' : anomaly.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-500' : 'bg-blue-500/20 text-blue-500'}`}>{anomaly.severity}</span></td>
                  <td className="py-3 px-4 font-mono text-sm">{anomaly.deviation_percent.toFixed(1)}%</td>
                  <td className="py-3 px-4 text-sm text-muted-foreground">{new Date(anomaly.detection_start).toLocaleString()}</td>
                  <td className="py-3 px-4"><span className={`px-2 py-0.5 text-xs rounded-none ${anomaly.is_resolved ? 'bg-green-500/20 text-green-500' : 'bg-yellow-500/20 text-yellow-500'}`}>{anomaly.is_resolved ? 'Resolved' : 'Active'}</span></td>
                  <td className="py-3 px-4 text-right">
                    {!anomaly.is_resolved && <button onClick={() => handleResolveAnomaly(anomaly.id)} disabled={resolveAnomaly.isPending} className="text-xs text-primary hover:underline">Resolve</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {(anomalies || []).length === 0 && !anomaliesLoading && (
            <div className="py-12 text-center text-muted-foreground">
              <AlertTriangle className="h-12 w-12 mx-auto mb-3 text-muted-foreground/30" />
              <p>No anomalies detected</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


'use client';
export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

import * as React from 'react';
import { format, parseISO } from 'date-fns';
import { BarChart3, LineChart, PieChart, TrendingUp, Activity, Users, Database, Bot } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import {
  MetricCard,
  LineChartComponent,
  BarChartComponent,
  PieChartComponent,
  AreaChartComponent,
} from '@/components/charts';
import {
  useEventCounts,
  useSessionMetrics,
  useConversationInsights,
  useAgentPerformance,
  useUsageStats,
  useSystemHealth,
  getDefaultTimeRange,
  type TimeRange,
  type EventCountResponse,
  type SessionMetricsResponse,
  type ConversationInsightSummary,
  type AgentPerformanceSummary,
  type UsageStats,
  type SystemHealthMetrics,
} from '@/hooks/useAnalytics';

const CHART_COLORS = [
  'hsl(var(--chart-1))',
  'hsl(var(--chart-2))',
  'hsl(var(--chart-3))',
  'hsl(var(--chart-4))',
  'hsl(var(--chart-5))',
  'hsl(var(--chart-6))',
];

const PERIOD_OPTIONS = [
  { value: '1h', label: 'Last Hour' },
  { value: '24h', label: 'Last 24 Hours' },
  { value: '7d', label: 'Last 7 Days' },
  { value: '30d', label: 'Last 30 Days' },
] as const;

function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}

function formatDuration(ms: number | null): string {
  if (!ms) return 'N/A';
  if (ms < 1000) return `${ms.toFixed(0)}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

function formatPercentage(value: number, decimals = 1): string {
  return `${value.toFixed(decimals)}%`;
}

export default function AnalyticsDashboard() {
  const [period, setPeriod] = React.useState<'1h' | '24h' | '7d' | '30d'>('24h');
  const timeRange = getDefaultTimeRange(period);

  // Fetch all analytics data
  const { data: eventCounts, isLoading: eventsLoading } = useEventCounts(timeRange);
  const { data: sessionMetrics, isLoading: sessionsLoading } = useSessionMetrics(timeRange);
  const { data: conversations, isLoading: conversationsLoading } = useConversationInsights(timeRange);
  const { data: agents, isLoading: agentsLoading } = useAgentPerformance(timeRange);
  const { data: usage, isLoading: usageLoading } = useUsageStats(timeRange);
  const { data: health, isLoading: healthLoading } = useSystemHealth();

  const isLoading = eventsLoading || sessionsLoading || conversationsLoading || agentsLoading || usageLoading || healthLoading;

  // Calculate aggregate metrics
  const totalEvents = eventCounts?.reduce((sum, e) => sum + e.event_count, 0) || 0;
  const totalSessions = sessionMetrics?.reduce((sum, s) => sum + s.session_count, 0) || 0;
  const avgSessionDuration = sessionMetrics?.length
    ? sessionMetrics.reduce((sum, s) => sum + (s.avg_session_duration || 0), 0) / sessionMetrics.length
    : 0;

  // System health metrics (with fallback mock data if API not available)
  const cpuUsage = health?.cpu_usage ?? 45;
  const memoryUsage = health?.memory_usage ?? 67;
  const diskUsage = health?.disk_usage ?? 32;
  const errorRate = health?.error_rate ?? 0.5;

  // Token/Latency width calculations for progress bars
  const tokensWidth = Math.min(((conversations?.total_tokens || 0) / 100000) * 100, 100);
  const latencyWidth = Math.min(((conversations?.avg_latency_ms || 0) / 5000) * 100, 100);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Real-time insights into usage, performance, and system health
          </p>
        </div>
        <Select value={period} onValueChange={setPeriod as (v: '1h' | '24h' | '7d' | '30d') => void}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Select period" />
          </SelectTrigger>
          <SelectContent>
            {PERIOD_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Key Metrics Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        <MetricCard
          title="Total Events"
          value={formatNumber(totalEvents)}
          icon={<Activity className="h-5 w-5" />}
        />
        <MetricCard
          title="Active Sessions"
          value={formatNumber(totalSessions)}
          icon={<Users className="h-5 w-5" />}
        />
        <MetricCard
          title="Avg Session Duration"
          value={formatDuration(avgSessionDuration)}
          icon={<LineChart className="h-5 w-5" />}
        />
        <MetricCard
          title="Conversations"
          value={formatNumber(conversations?.total_conversations || 0)}
          change={conversations?.avg_sentiment_score ? conversations.avg_sentiment_score * 100 - 50 : undefined}
          changeLabel="vs baseline"
          icon={<Bot className="h-5 w-5" />}
        />
        <MetricCard
          title="Agents Executed"
          value={formatNumber(agents?.reduce((sum, a) => sum + a.total_executions, 0) || 0)}
          icon={<Bot className="h-5 w-5" />}
        />
      </div>

      {/* System Health Row */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">CPU Usage</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="text-3xl font-bold">{formatPercentage(cpuUsage)}</div>
              <div className="flex-1 h-4 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary transition-all duration-500"
                  style={{ width: `${cpuUsage}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Memory Usage</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="text-3xl font-bold">{formatPercentage(memoryUsage)}</div>
              <div className="flex-1 h-4 bg-muted rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${
                    memoryUsage > 85 ? 'bg-red-500' : memoryUsage > 70 ? 'bg-yellow-500' : 'bg-primary'
                  }`}
                  style={{ width: `${memoryUsage}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Disk Usage</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="text-3xl font-bold">{formatPercentage(diskUsage)}</div>
              <div className="flex-1 h-4 bg-muted rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${
                    diskUsage > 90 ? 'bg-red-500' : diskUsage > 75 ? 'bg-yellow-500' : 'bg-primary'
                  }`}
                  style={{ width: `${diskUsage}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Error Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="text-3xl font-bold">{formatPercentage(errorRate, 2)}</div>
              <div className="flex-1 h-4 bg-muted rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${
                    errorRate > 5 ? 'bg-red-500' : errorRate > 1 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(errorRate * 20, 100)}%` }}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Tabs */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="usage">Usage Analytics</TabsTrigger>
          <TabsTrigger value="conversations">Conversations</TabsTrigger>
          <TabsTrigger value="system">System & Agents</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            {/* Event Counts Line Chart - Full Width */}
            <div className="md:col-span-4 lg:col-span-4">
              <LineChartComponent
                title="Events Over Time"
                subtitle={`Total: ${formatNumber(totalEvents)} events`}
                data={eventCounts?.map((e) => ({
                  time: format(parseISO(e.bucket), 'HH:mm'),
                  events: e.event_count,
                  users: e.unique_users,
                  sessions: e.unique_sessions,
                })) || []}
                lines={[
                  { dataKey: 'events', name: 'Events', color: CHART_COLORS[0] },
                  { dataKey: 'users', name: 'Unique Users', color: CHART_COLORS[1] },
                  { dataKey: 'sessions', name: 'Sessions', color: CHART_COLORS[2] },
                ]}
                height={300}
              />
            </div>

            {/* Session Metrics Line Chart - Half Width */}
            <div className="md:col-span-4 lg:col-span-3">
              <LineChartComponent
                title="Session Metrics"
                subtitle={`Avg Duration: ${formatDuration(avgSessionDuration)}`}
                data={sessionMetrics?.map((s) => ({
                  time: format(parseISO(s.bucket), 'HH:mm'),
                  sessions: s.session_count,
                  messages: s.total_messages,
                  toolCalls: s.total_tool_calls,
                  apiCalls: s.total_api_calls,
                })) || []}
                lines={[
                  { dataKey: 'sessions', name: 'Sessions', color: CHART_COLORS[0] },
                  { dataKey: 'messages', name: 'Messages', color: CHART_COLORS[1] },
                  { dataKey: 'toolCalls', name: 'Tool Calls', color: CHART_COLORS[2] },
                  { dataKey: 'apiCalls', name: 'API Calls', color: CHART_COLORS[3] },
                ]}
                height={300}
              />
            </div>

            {/* Sentiment Distribution Pie Chart */}
            <div className="md:col-span-4 lg:col-span-3">
              <PieChartComponent
                title="Sentiment Distribution"
                subtitle={
                  conversations
                    ? `${conversations.total_conversations} conversations • Avg: ${formatPercentage(conversations.avg_sentiment_score * 100)}`
                    : 'No data'
                }
                data={conversations?.sentiment_distribution.map((s) => ({
                  name: s.label,
                  value: s.count,
                })) || []}
                height={300}
              />
            </div>

            {/* Top Topics Bar Chart */}
            <div className="md:col-span-4 lg:col-span-4">
              <BarChartComponent
                title="Top Conversation Topics"
                subtitle="Most discussed topics"
                data={conversations?.top_topics.slice(0, 10).map((t, i) => ({
                  name: t.topic as string || `Topic ${i + 1}`,
                  count: t.count as number || 0,
                })) || []}
                bars={[{ dataKey: 'count', name: 'Mentions', color: CHART_COLORS[0] }]}
                xAxisKey="name"
                layout="horizontal"
                height={300}
              />
            </div>
          </div>
        </TabsContent>

        {/* Usage Analytics Tab */}
        <TabsContent value="usage" className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            <div className="md:col-span-4 lg:col-span-4">
              <AreaChartComponent
                title="Event Volume by Category"
                subtitle="Stacked area chart showing event categories over time"
                data={eventCounts?.map((e) => ({
                  time: format(parseISO(e.bucket), 'HH:mm'),
                  user_action: e.category === 'user_action' ? e.event_count : 0,
                  system_event: e.category === 'system_event' ? e.event_count : 0,
                  agent_execution: e.category === 'agent_execution' ? e.event_count : 0,
                  conversation: e.category === 'conversation' ? e.event_count : 0,
                  memory_operation: e.category === 'memory_operation' ? e.event_count : 0,
                  error: e.category === 'error' ? e.event_count : 0,
                })) || []}
                areas={[
                  { dataKey: 'user_action', name: 'User Actions', color: CHART_COLORS[0] },
                  { dataKey: 'system_event', name: 'System Events', color: CHART_COLORS[1] },
                  { dataKey: 'agent_execution', name: 'Agent Executions', color: CHART_COLORS[2] },
                  { dataKey: 'conversation', name: 'Conversations', color: CHART_COLORS[3] },
                  { dataKey: 'memory_operation', name: 'Memory Ops', color: CHART_COLORS[4] },
                  { dataKey: 'error', name: 'Errors', color: CHART_COLORS[5] },
                ]}
                stacked
                height={350}
              />
            </div>

            <div className="md:col-span-4 lg:col-span-3">
              <BarChartComponent
                title="Event Categories"
                subtitle="Total events by category"
                data={eventCounts?.reduce((acc: Record<string, number>, e) => {
                  const cat = e.category || 'unknown';
                  acc[cat] = (acc[cat] || 0) + e.event_count;
                  return acc;
                }, {}) && Object.entries(
                  eventCounts.reduce((acc: Record<string, number>, e) => {
                    const cat = e.category || 'unknown';
                    acc[cat] = (acc[cat] || 0) + e.event_count;
                    return acc;
                  }, {})
                ).map(([name, value]) => ({ name, value })) || []}
                bars={[{ dataKey: 'value', name: 'Count', color: CHART_COLORS[0] }]}
                xAxisKey="name"
                layout="horizontal"
                height={350}
              />
            </div>

            {/* Usage Stats Cards */}
            <div className="md:col-span-4 lg:col-span-7">
              <div className="grid gap-4 md:grid-cols-3">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Active Users
                    </CardTitle>
                    <Users className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">
                      {formatNumber(usage?.active_users || 0)}
                    </div>
                    <p className="text-xs text-muted-foreground">Unique users in period</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Total Sessions
                    </CardTitle>
                    <Activity className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">
                      {formatNumber(usage?.total_sessions || 0)}
                    </div>
                    <p className="text-xs text-muted-foreground">All sessions in period</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Avg Session Duration
                    </CardTitle>
                    <LineChart className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">
                      {formatDuration(usage?.avg_session_duration || 0)}
                    </div>
                    <p className="text-xs text-muted-foreground">Average per session</p>
                  </CardContent>
                </Card>
              </div>
            </div>

            {/* Top Events */}
            <div className="md:col-span-4 lg:col-span-7">
              <Card>
                <CardHeader>
                  <CardTitle>Top Events</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {usage?.top_events.slice(0, 10).map((event, i) => (
                      <div key={event.event_name} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-sm text-muted-foreground w-6 text-right">
                            {i + 1}.
                          </span>
                          <span className="font-mono text-sm">{event.event_name}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="w-32 h-3 bg-muted rounded-full overflow-hidden">
                            <div
                              className="h-full bg-primary transition-all duration-500"
                              style={{
                                width: `${((event.count / (usage.top_events[0]?.count || 1)) * 100).toFixed(0)}%`,
                              }}
                            />
                          </div>
                          <span className="text-sm font-medium w-16 text-right">
                            {formatNumber(event.count)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Conversations Tab */}
        <TabsContent value="conversations" className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Quality Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {conversations && [
                  { label: 'Quality Score', value: conversations.avg_quality_score },
                  { label: 'Coherence', value: conversations.avg_coherence_score },
                  { label: 'Helpfulness', value: conversations.avg_helpfulness_score },
                  { label: 'Safety', value: conversations.avg_safety_score },
                ].map((metric) => (
                  <div key={metric.label} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="h-2 w-20 bg-muted rounded-full overflow-hidden">
                        <div
                          className="h-full bg-primary transition-all duration-500"
                          style={{ width: `${metric.value * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium w-32">{metric.label}</span>
                    </div>
                    <span className="font-mono text-lg">{formatPercentage(metric.value * 100)}</span>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Token Usage</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-2 w-20 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary transition-all duration-500"
                        style={{ width: tokensWidth + "%" }}
                      />
                    </div>
                    <span className="text-sm font-medium w-32">Total Tokens</span>
                  </div>
                  <span className="font-mono text-lg">
                    {formatNumber(conversations?.total_tokens || 0)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-2 w-20 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-secondary transition-all duration-500"
                        style={{ width: latencyWidth + "%" }}
                      />
                    </div>
                    <span className="text-sm font-medium w-32">Avg Latency</span>
                  </div>
                  <span className="font-mono text-lg">
                    {formatDuration(conversations?.avg_latency_ms || 0)}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sentiment Timeline */}
          <PieChartComponent
            title="Sentiment Over Time"
            subtitle="Distribution of conversation sentiment"
            data={conversations?.sentiment_distribution.map((s) => ({
              name: s.label,
              value: s.count,
            })) || []}
            height={350}
          />
        </TabsContent>

        {/* System & Agents Tab */}
        <TabsContent value="system" className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Agent Performance Table */}
            <Card>
              <CardHeader>
                <CardTitle>Agent Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border">
                        <th className="text-left p-3 font-medium">Agent</th>
                        <th className="text-right p-3 font-medium">Executions</th>
                        <th className="text-right p-3 font-medium">Success Rate</th>
                        <th className="text-right p-3 font-medium">Avg Duration</th>
                        <th className="text-right p-3 font-medium">Error Rate</th>
                      </tr>
                    </thead>
                    <tbody>
                      {agents?.map((agent) => (
                        <tr key={agent.agent_id} className="border-b border-border/50">
                          <td className="p-3">
                            <div className="font-medium">{agent.agent_name}</div>
                            <div className="text-xs text-muted-foreground">{agent.agent_type}</div>
                          </td>
                          <td className="p-3 text-right font-mono">
                            {formatNumber(agent.total_executions)}
                          </td>
                          <td className="p-3 text-right">
                            <span
                              className={cn(
                                'font-mono',
                                agent.success_rate > 0.95 ? 'text-green-500' :
                                agent.success_rate > 0.8 ? 'text-yellow-500' : 'text-red-500'
                              )}
                            >
                              {formatPercentage(agent.success_rate * 100)}
                            </span>
                          </td>
                          <td className="p-3 text-right font-mono">
                            {formatDuration(agent.avg_duration_ms)}
                          </td>
                          <td className="p-3 text-right">
                            <span
                              className={cn(
                                'font-mono',
                                agent.error_rate < 0.01 ? 'text-green-500' :
                                agent.error_rate < 0.05 ? 'text-yellow-500' : 'text-red-500'
                              )}
                            >
                              {formatPercentage(agent.error_rate * 100, 2)}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            {/* Agent Success Rate Chart */}
            <BarChartComponent
              title="Agent Success Rates"
              subtitle="Success rate by agent"
              data={agents?.map((a) => ({
                name: a.agent_name,
                success_rate: a.success_rate * 100,
              })) || []}
              bars={[{ dataKey: 'success_rate', name: 'Success %', color: CHART_COLORS[0] }]}
              xAxisKey="name"
              layout="horizontal"
              height={400}
            />
          </div>

          {/* Agent Duration Chart */}
          <LineChartComponent
            title="Agent Execution Duration (p50, p95, p99)"
            subtitle="Latency percentiles by agent"
            data={agents?.map((a) => ({
              name: a.agent_name,
              p50: a.p50_duration_ms,
              p95: a.p95_duration_ms,
              p99: a.p99_duration_ms,
            })) || []}
            xAxisKey="name"
            lines={[
              { dataKey: 'p50', name: 'p50', color: CHART_COLORS[0] },
              { dataKey: 'p95', name: 'p95', color: CHART_COLORS[1] },
              { dataKey: 'p99', name: 'p99', color: CHART_COLORS[2] },
            ]}
            height={350}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
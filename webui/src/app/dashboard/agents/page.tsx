'use client';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Bot, Play, Pause, Settings, Activity, Zap, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/lib/auth-provider';

const agents = [
  {
    id: 'agent_1',
    name: 'Code Reviewer',
    type: 'specialist',
    status: 'idle',
    capabilities: ['code_analysis', 'security_review', 'best_practices'],
    description: 'Reviews code for quality, security, and maintainability',
  },
  {
    id: 'agent_2',
    name: 'Data Analyst',
    type: 'specialist',
    status: 'idle',
    capabilities: ['data_visualization', 'statistical_analysis', 'reporting'],
    description: 'Analyzes data and generates insights',
  },
  {
    id: 'agent_3',
    name: 'Security Scanner',
    type: 'specialist',
    status: 'idle',
    capabilities: ['vulnerability_scanning', 'penetration_testing', 'compliance'],
    description: 'Scans for security vulnerabilities and compliance issues',
  },
  {
    id: 'agent_4',
    name: 'Research Assistant',
    type: 'generalist',
    status: 'busy',
    capabilities: ['web_search', 'fact_checking', 'summarization'],
    description: 'Conducts research and synthesizes information',
  },
];

export default function AgentsPage() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Agents</h1>
          <p className="text-muted-foreground">Manage and monitor AI agents</p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" />
          Add Agent
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {agents.map((agent) => (
          <Card key={agent.id}>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <Bot className="h-5 w-5 text-primary" />
                  <CardTitle className="text-lg">{agent.name}</CardTitle>
                </div>
                <p className="text-sm text-muted-foreground mt-1">{agent.description}</p>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={cn(
                    'relative flex h-2 w-2 rounded-full',
                    agent.status === 'active' && 'bg-green-500',
                    agent.status === 'idle' && 'bg-gray-500',
                    agent.status === 'busy' && 'bg-yellow-500',
                    agent.status === 'error' && 'bg-red-500'
                  )}
                />
                <span className="text-xs capitalize">{agent.status}</span>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-1">
                {agent.capabilities.map((cap) => (
                  <span
                    key={cap}
                    className="text-xs px-2 py-0.5 bg-muted rounded"
                  >
                    {cap}
                  </span>
                ))}
              </div>
              <div className="flex gap-2">
                <Button
                  variant={agent.status === 'busy' ? 'secondary' : 'outline'}
                  size="sm"
                  className="flex-1"
                >
                  {agent.status === 'busy' ? (
                    <>
                      <Pause className="h-4 w-4 mr-2" />
                      Running
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      Execute
                    </>
                  )}
                </Button>
                <Button variant="ghost" size="sm">
                  <Settings className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
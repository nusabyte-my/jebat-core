import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Database, Search, Plus, Filter, Download } from 'lucide-react';
import { cn } from '../lib/utils';

export function MemoriesPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLayer, setSelectedLayer] = useState('all');

  const layers = ['all', 'M0_IMMEDIATE', 'M1_EPISODIC', 'M2_SEMANTIC', 'M3_PROCEDURAL', 'M4_STRATEGIC'];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Memories</h1>
          <p className="text-muted-foreground">Browse and manage stored memories</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" className="gap-2">
            <Download className="h-4 w-4" />
            Export
          </Button>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Add Memory
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Search Memories</CardTitle>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                placeholder="Search memories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 w-64 px-3 py-2 text-sm border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
            <select
              value={selectedLayer}
              onChange={(e) => setSelectedLayer(e.target.value)}
              className="px-3 py-2 text-sm border border-input bg-background rounded-lg"
            >
              {layers.map((layer) => (
                <option key={layer} value={layer}>
                  {layer === 'all' ? 'All Layers' : layer}
                </option>
              ))}
            </select>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { id: 'mem_001', content: 'User prefers dark mode with cyan accents', layer: 'M1_EPISODIC', user: 'user_123', heat: 0.92, date: '2026-06-15' },
              { id: 'mem_002', content: 'Project uses Vite with React 18', layer: 'M2_SEMANTIC', user: 'user_123', heat: 0.87, date: '2026-06-14' },
              { id: 'mem_003', content: 'API endpoint: /api/v1/chat', layer: 'M3_PROCEDURAL', user: 'user_456', heat: 0.75, date: '2026-06-13' },
            ].map((mem) => (
              <div key={mem.id} className="flex items-start gap-4 p-4 border rounded-lg hover:bg-muted/50 transition-colors">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-muted-foreground">{mem.layer}</span>
                    <span className="text-xs px-2 py-0.5 bg-muted rounded">{mem.heat * 100}%</span>
                  </div>
                  <p className="text-sm">{mem.content}</p>
                  <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                    <span>{mem.user}</span>
                    <span>{mem.date}</span>
                  </div>
                </div>
                <button className="text-muted-foreground hover:text-foreground">Edit</button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

import { useState } from 'react';
'use client';

import * as React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface ChartDataPoint {
  // optional time key
  [key: string]: string | number;
}

interface AreaChartComponentProps {
  data: ChartDataPoint[];
  areas: {
    dataKey: string;
    name: string;
    color?: string;
    fillOpacity?: number;
    strokeWidth?: number;
  }[];
  xAxisKey?: string;
  title?: string;
  subtitle?: string;
  className?: string;
  height?: number;
  showLegend?: boolean;
  showGrid?: boolean;
  stacked?: boolean;
  yAxisFormatter?: (value: number) => string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  tooltipFormatter?: (value: any, name: string) => [string, string];
}

export function AreaChartComponent({
  data,
  areas,
  xAxisKey = 'time',
  title,
  subtitle,
  className,
  height = 300,
  showLegend = true,
  showGrid = true,
  stacked = false,
  yAxisFormatter,
  tooltipFormatter,
}: AreaChartComponentProps) {
  if (!data.length) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64">
          <p className="text-muted-foreground">No data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      {(title || subtitle) && (
        <CardHeader>
          {title && <CardTitle>{title}</CardTitle>}
          {subtitle && <p className="text-sm text-muted-foreground">{subtitle}</p>}
        </CardHeader>
      )}
      <CardContent>
        <div className="w-full" style={{ height }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={data}
              margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
              stackOffset={stacked ? 'expand' : 'none'}
            >
              {showGrid && <CartesianGrid strokeDasharray="3 3" className="stroke-border/50" />}
              <XAxis
                dataKey={xAxisKey}
                tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
                axisLine={{ stroke: 'var(--border)' }}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
                axisLine={false}
                tickLine={false}
                tickFormatter={yAxisFormatter}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--card)',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                }}
                labelStyle={{ color: 'var(--foreground)', fontWeight: 600 }}
                formatter={tooltipFormatter as any}
              />
              {showLegend && (
                <Legend wrapperStyle={{ paddingTop: 20 }} />
              )}
              {areas.map((area, index) => (
                <Area
                  key={area.dataKey}
                  type="monotone"
                  dataKey={area.dataKey}
                  name={area.name}
                  stroke={area.color || `hsl(var(--chart-${index + 1}))`}
                  fill={area.color || `hsl(var(--chart-${index + 1}))`}
                  fillOpacity={area.fillOpacity ?? 0.3}
                  strokeWidth={area.strokeWidth ?? 1}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
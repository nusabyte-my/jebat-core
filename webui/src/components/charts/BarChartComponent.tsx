'use client';

import * as React from 'react';
import {
  BarChart,
  Bar,
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
  name: string;
  [key: string]: string | number;
}

interface BarChartComponentProps {
  data: ChartDataPoint[];
  bars: {
    dataKey: string;
    name: string;
    color?: string;
  }[];
  xAxisKey?: string;
  title?: string;
  subtitle?: string;
  className?: string;
  height?: number;
  showLegend?: boolean;
  showGrid?: boolean;
  layout?: 'vertical' | 'horizontal';
  yAxisFormatter?: (value: number) => string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  tooltipFormatter?: (value: any, name: string) => [string, string];
}

export function BarChartComponent({
  data,
  bars,
  xAxisKey = 'name',
  title,
  subtitle,
  className,
  height = 300,
  showLegend = true,
  showGrid = true,
  layout = 'vertical',
  yAxisFormatter,
  tooltipFormatter,
}: BarChartComponentProps) {
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
            <BarChart
              data={data}
              layout={layout}
              margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
            >
              {showGrid && (
                <CartesianGrid
                  strokeDasharray="3 3"
                  className="stroke-border/50"
                  vertical={layout === 'vertical'}
                  horizontal={layout === 'horizontal'}
                />
              )}
              <XAxis
                dataKey={xAxisKey}
                type="category"
                tick={{ fontSize: 12, fill: 'var(--muted-foreground)' }}
                axisLine={{ stroke: 'var(--border)' }}
                tickLine={false}
              />
              <YAxis
                type="number"
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
              {bars.map((bar, index) => (
                <Bar
                  key={bar.dataKey}
                  dataKey={bar.dataKey}
                  name={bar.name}
                  fill={bar.color || `hsl(var(--chart-${index + 1}))`}
                  radius={[4, 4, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
'use client';

import * as React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface PieDataPoint {
  name: string;
  value: number;
  [key: string]: string | number;
}

interface PieChartComponentProps {
  data: PieDataPoint[];
  title?: string;
  subtitle?: string;
  className?: string;
  height?: number;
  showLegend?: boolean;
  innerRadius?: number;
  outerRadius?: number;
  colors?: string[];
  nameKey?: string;
  valueKey?: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  tooltipFormatter?: (value: any, name: string) => [string, string];
}

const DEFAULT_COLORS = [
  'hsl(var(--chart-1))',
  'hsl(var(--chart-2))',
  'hsl(var(--chart-3))',
  'hsl(var(--chart-4))',
  'hsl(var(--chart-5))',
  'hsl(var(--chart-6))',
];

export function PieChartComponent({
  data,
  title,
  subtitle,
  className,
  height = 300,
  showLegend = true,
  innerRadius = 60,
  outerRadius = 100,
  colors = DEFAULT_COLORS,
  nameKey = 'name',
  valueKey = 'value',
  tooltipFormatter,
}: PieChartComponentProps) {
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

  const total = data.reduce((sum, item) => sum + (item[valueKey] as number), 0);

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
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={innerRadius}
                outerRadius={outerRadius}
                paddingAngle={2}
                dataKey={valueKey}
                nameKey={nameKey}
                label={({ name, percent }) =>
                  (percent ?? 0) > 0.05 ? `${name} ${((percent ?? 0) * 100).toFixed(0)}%` : ''
                }
                labelLine={false}
              >
                {data.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: 'var(--card)',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
                }}
                labelStyle={{ color: 'var(--foreground)', fontWeight: 600 }}
                formatter={tooltipFormatter as any ?? ((value: number) => [
                  `${((value / total) * 100).toFixed(1)}%`,
                  nameKey,
                ])}
              />
              {showLegend && (
                <Legend
                  wrapperStyle={{ paddingTop: 20 }}
                  formatter={(value) => value}
                />
              )}
            </PieChart>
          </ResponsiveContainer>
        </div>
        {total > 0 && showLegend && (
          <div className="flex flex-wrap justify-center gap-4 mt-4 text-sm">
            {data.map((item, index) => (
              <div
                key={item[nameKey] as string}
                className="flex items-center gap-2"
              >
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: colors[index % colors.length] }}
                />
                <span>
                  {item[nameKey]}: {((Number(item[valueKey]) / total) * 100).toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
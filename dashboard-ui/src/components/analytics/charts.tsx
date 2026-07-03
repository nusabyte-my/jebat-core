import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer, 
  AreaChart, 
  Area,
  BarChart as RechartsBarChart,
  Bar,
  XAxis as RechartsXAxis,
  YAxis as RechartsYAxis,
  Cell,
  PieChart as RechartsPieChart,
  Pie,
  Cell as PieCell,
  Tooltip as RechartsTooltip,
  Legend as RechartsLegend,
  ResponsiveContainer as RechartsResponsiveContainer,
} from 'recharts';
import { cn } from '../../lib/utils';

interface TimeSeriesChartProps {
  data: Array<{
    timestamp: string;
    value: number;
    [key: string]: any;
  }>;
  xKey?: string;
  yKeys: string[];
  yLabels?: Record<string, string>;
  colors?: string[];
  height?: number;
  showArea?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  className?: string;
}

export function TimeSeriesChart({
  data,
  xKey = 'timestamp',
  yKeys,
  yLabels,
  colors = ['#0ea5e9', '#22c55e', '#f59e0b', '#ef4444', '#a855f7'],
  height = 300,
  showArea = false,
  showLegend = true,
  showTooltip = true,
  className,
}: TimeSeriesChartProps) {
  const chartData = data.map((d) => ({
    ...d,
    [xKey]: new Date(d[xKey]).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  }));

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!showTooltip || !active || !payload) return null;
    return (
      <div className="bg-card border p-3 rounded-lg shadow-lg min-w-[180px]">
        <p className="font-mono text-xs text-muted-foreground mb-2">{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="flex items-center gap-2 text-sm" style={{ color: entry.color }}>
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
            <span>{yLabels?.[entry.name] || entry.name}:</span>
            <span className="font-medium">{typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}</span>
          </p>
        ))}
      </div>
    );
  };

  const ChartComponent = showArea ? AreaChart : LineChart;

  return (
    <div className={cn('w-full', className)}>
      <ResponsiveContainer width="100%" height={height}>
        <ChartComponent data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
          <XAxis
            dataKey={xKey}
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            axisLine={{ stroke: '#374151' }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: '#9ca3af', fontSize: 11 }}
            axisLine={{ stroke: '#374151' }}
            tickLine={false}
            tickFormatter={(value) => value >= 1000 ? `${(value/1000).toFixed(1)}k` : value}
          />
          {showTooltip && <Tooltip content={<CustomTooltip />} />}
          {showLegend && <Legend />}
          {yKeys.map((key, index) => (
            showArea ? (
              <Area
                key={key}
                type="monotone"
                dataKey={key}
                name={yLabels?.[key] || key}
                stroke={colors[index % colors.length]}
                fill={colors[index % colors.length]}
                fillOpacity={0.15}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6 }}
              />
            ) : (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                name={yLabels?.[key] || key}
                stroke={colors[index % colors.length]}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6, strokeWidth: 2 }}
              />
            )
          ))}
        </ChartComponent>
      </ResponsiveContainer>
    </div>
  );
}

interface BarChartProps {
  data: Array<{
    name: string;
    [key: string]: any;
  }>;
  xKey: string;
  yKeys: string[];
  yLabels?: Record<string, string>;
  colors?: string[];
  height?: number;
  horizontal?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  className?: string;
}

export function BarChart({
  data,
  xKey,
  yKeys,
  yLabels,
  colors = ['#0ea5e9', '#22c55e', '#f59e0b', '#ef4444', '#a855f7'],
  height = 300,
  horizontal = false,
  showLegend = true,
  showTooltip = true,
  className,
}: BarChartProps) {
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!showTooltip || !active || !payload) return null;
    return (
      <div className="bg-card border p-3 rounded-lg shadow-lg min-w-[180px]">
        <p className="font-mono text-xs text-muted-foreground mb-2">{label}</p>
        {payload.map((entry: any, index: number) => (
          <p key={index} className="flex items-center gap-2 text-sm" style={{ color: entry.color }}>
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
            <span>{yLabels?.[entry.name] || entry.name}:</span>
            <span className="font-medium">{typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}</span>
          </p>
        ))}
      </div>
    );
  };

  return (
    <div className={cn('w-full', className)}>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} layout={horizontal ? 'vertical' : 'horizontal'} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={!horizontal} />
          {horizontal ? (
            <>
              <XAxis
                type="number"
                tick={{ fill: '#9ca3af', fontSize: 11 }}
                axisLine={{ stroke: '#374151' }}
                tickLine={false}
                tickFormatter={(value) => value >= 1000 ? `${(value/1000).toFixed(1)}k` : value}
              />
              <YAxis
                type="category"
                dataKey={xKey}
                tick={{ fill: '#9ca3af', fontSize: 11 }}
                axisLine={{ stroke: '#374151' }}
                tickLine={false}
                width={120}
              />
            </>
          ) : (
            <>
              <XAxis
                dataKey={xKey}
                tick={{ fill: '#9ca3af', fontSize: 11 }}
                axisLine={{ stroke: '#374151' }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: '#9ca3af', fontSize: 11 }}
                axisLine={{ stroke: '#374151' }}
                tickLine={false}
                tickFormatter={(value) => value >= 1000 ? `${(value/1000).toFixed(1)}k` : value}
              />
            </>
          )}
          {showTooltip && <Tooltip 
            content={({ active, payload, label }: any) => {
              if (!active || !payload) return null;
              return (
                <div className="bg-card border p-3 rounded-lg shadow-lg min-w-[180px]">
                  <p className="font-mono text-xs text-muted-foreground mb-2">{label}</p>
                  {payload.map((entry: any, index: number) => (
                    <p key={index} className="flex items-center gap-2 text-sm" style={{ color: entry.color }}>
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
                      <span>{yLabels?.[entry.name] || entry.name}:</span>
                      <span className="font-medium">{typeof entry.value === 'number' ? entry.value.toLocaleString() : entry.value}</span>
                    </p>
                  ))}
                </div>
              );
            }} 
          />}
          {showLegend && <Legend />}
          {yKeys.map((key, index) => (
            <Bar
              key={key}
              dataKey={key}
              name={yLabels?.[key] || key}
              fill={colors[index % colors.length]}
              radius={[4, 4, 0, 0]}
            >
              {data.map((_, i) => (
                <Cell key={`cell-${i}-${index}`} fill={colors[index % colors.length]} />
              ))}
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

interface PieChartProps {
  data: Array<{
    name: string;
    value: number;
    [key: string]: any;
  }>;
  nameKey: string;
  valueKey: string;
  colors?: string[];
  height?: number;
  showLegend?: boolean;
  showTooltip?: boolean;
  innerRadius?: number;
  outerRadius?: number;
  className?: string;
}

export function PieChart({
  data,
  nameKey,
  valueKey,
  colors = ['#0ea5e9', '#22c55e', '#f59e0b', '#ef4444', '#a855f7', '#ec4899', '#06b6d4', '#84cc16'],
  height = 300,
  showLegend = true,
  showTooltip = true,
  innerRadius = 60,
  outerRadius = 100,
  className,
}: PieChartProps) {
  const total = data.reduce((sum, d) => sum + d[valueKey], 0);

  return (
    <div className={cn('w-full flex flex-col items-center', className)}>
      <ResponsiveContainer width="100%" height={height}>
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
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            labelLine={false}
          >
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export function KPICard({
  title,
  value,
  change,
  changeLabel,
  icon,
  trend,
  className,
}: {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  className?: string;
}) {
  const TrendIcon = trend === 'up' ? ArrowUp : trend === 'down' ? ArrowDown : Minus;
  const trendColor = trend === 'up' ? 'text-green-500' : trend === 'down' ? 'text-red-500' : 'text-muted-foreground';

  return (
    <div className={cn('bg-card border rounded-xl p-5 hover:bg-card/80 transition-colors', className)}>
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">
            {title}
          </p>
          <p className="text-2xl font-bold text-foreground truncate">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
          {change !== undefined && (
            <p className={cn('text-xs mt-1 flex items-center gap-1', trendColor)}>
              <TrendIcon className="w-3 h-3" />
              <span>{Math.abs(change).toFixed(1)}%</span>
              {changeLabel && <span className="text-muted-foreground">{changeLabel}</span>}
            </p>
          )}
        </div>
        {icon && (
          <div className="ml-4 flex-shrink-0 text-muted-foreground/50">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
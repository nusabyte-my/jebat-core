import { cn } from '../../lib/utils';
import { ArrowUp, ArrowDown, Minus, TrendingUp, TrendingDown, Users, MessageSquare, AlertTriangle } from 'lucide-react';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  options: SelectOption[];
  placeholder?: string;
  label?: string;
  error?: string;
}

export function Select({ options, placeholder, label, error, className, ...props }: SelectProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-foreground mb-1.5">
          {label}
        </label>
      )}
      <select
        className={cn(
          'flex h-10 w-full appearance-none rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background',
          'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
          'disabled:cursor-not-allowed disabled:opacity-50',
          error && 'border-destructive focus:ring-destructive',
          className
        )}
        {...props}
      >
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && <p className="mt-1.5 text-sm text-destructive">{error}</p>}
    </div>
  );
}

interface DateRangePickerProps {
  startDate: Date | undefined;
  endDate: Date | undefined;
  onChange: (dates: { startDate: Date | undefined; endDate: Date | undefined }) => void;
  presets?: Array<{ label: string; days: number }>;
  className?: string;
}

export function DateRangePicker({ startDate, endDate, onChange, presets, className }: DateRangePickerProps) {
  const defaultPresets = [
    { label: 'Last 24h', days: 1 },
    { label: 'Last 7d', days: 7 },
    { label: 'Last 30d', days: 30 },
    { label: 'Last 90d', days: 90 },
    { label: 'Last year', days: 365 },
  ];

  const handlePresetClick = (days: number) => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - days);
    onChange({ startDate: start, endDate: end });
  };

  return (
    <div className={cn('flex flex-wrap items-center gap-2', className)}>
      <div className="flex items-center gap-2">
        <label className="text-sm text-muted-foreground">From</label>
        <input
          type="date"
          value={startDate?.toISOString().split('T')[0] || ''}
          onChange={(e) => onChange({ startDate: e.target.value ? new Date(e.target.value) : undefined, endDate })}
          className="h-10 px-3 py-2 text-sm border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>
      <div className="flex items-center gap-2">
        <label className="text-sm text-muted-foreground">To</label>
        <input
          type="date"
          value={endDate?.toISOString().split('T')[0] || ''}
          onChange={(e) => onChange({ startDate, endDate: e.target.value ? new Date(e.target.value) : undefined })}
          className="h-10 px-3 py-2 text-sm border border-input bg-background rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
        />
      </div>
      <div className="flex flex-wrap gap-1">
        {presets?.map((preset) => (
          <button
            key={preset.label}
            type="button"
            onClick={() => handlePresetClick(preset.days)}
            className="px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg transition-colors"
          >
            {preset.label}
          </button>
        )) || defaultPresets.map((preset) => (
          <button
            key={preset.label}
            type="button"
            onClick={() => handlePresetClick(preset.days)}
            className="px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg transition-colors"
          >
            {preset.label}
          </button>
        ))}
      </div>
    </div>
  );
}

interface FilterBarProps {
  dateRange: { startDate: Date | undefined; endDate: Date | undefined };
  onDateRangeChange: (dates: { startDate: Date | undefined; endDate: Date | undefined }) => void;
  period?: string;
  onPeriodChange?: (period: string) => void;
  category?: string;
  onCategoryChange?: (category: string) => void;
  categories?: Array<{ value: string; label: string }>;
  className?: string;
}

export function FilterBar({ 
  dateRange, 
  onDateRangeChange, 
  period, 
  onPeriodChange, 
  category, 
  onCategoryChange, 
  categories,
  className 
}: FilterBarProps) {
  return (
    <div className={cn('flex flex-wrap items-end gap-4 p-4 bg-card border rounded-xl', className)}>
      <DateRangePicker 
        startDate={dateRange.startDate} 
        endDate={dateRange.endDate} 
        onChange={onDateRangeChange} 
      />
      
      {period && onPeriodChange && (
        <Select
          options={[
            { value: 'hourly', label: 'Hourly' },
            { value: 'daily', label: 'Daily' },
            { value: 'weekly', label: 'Weekly' },
            { value: 'monthly', label: 'Monthly' },
          ]}
          value={period}
          onChange={(e) => onPeriodChange(e.target.value)}
          label="Period"
          placeholder="Select period"
        />
      )}
      
      {category && onCategoryChange && categories && (
        <Select
          options={[{ value: '', label: 'All categories' }, ...categories]}
          value={category}
          onChange={(e) => onCategoryChange(e.target.value)}
          label="Category"
          placeholder="Select category"
        />
      )}
      
      <div className="flex-1" />
      
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <span>Auto-refresh</span>
        <label className="flex items-center gap-1.5 cursor-pointer">
          <input type="checkbox" className="h-4 w-4 rounded border-input" defaultChecked />
          <span>30s</span>
        </label>
      </div>
    </div>
  );
}

interface MetricCardProps {
  title: string;
  value: string | number;
  description?: string;
  trend?: number;
  trendLabel?: string;
  icon?: React.ReactNode;
  className?: string;
}

export function MetricCard({ title, value, description, trend, trendLabel, icon, className }: MetricCardProps) {
  const TrendIcon = trend !== undefined && trend > 0 ? ArrowUp : 
                    trend !== undefined && trend < 0 ? ArrowDown : 
                    Minus;
  
  const trendColor = trend !== undefined && trend > 0 ? 'text-green-500' : 
                     trend !== undefined && trend < 0 ? 'text-red-500' : 
                     'text-muted-foreground';

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
          {description && <p className="text-xs text-muted-foreground mt-1">{description}</p>}
          {trend !== undefined && (
            <p className={cn('text-xs mt-1 flex items-center gap-1', trendColor)}>
              <TrendIcon className="w-3 h-3" />
              <span>{Math.abs(trend).toFixed(1)}%</span>
              {trendLabel && <span className="text-muted-foreground">{trendLabel}</span>}
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

export function CardGrid({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={cn('grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4', className)}>
      {children}
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
  const TrendIcon = trend === 'up' ? TrendingUp : trend === 'down' ? TrendingDown : Minus;
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

export function LoadingSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn('animate-pulse bg-muted rounded-lg', className)} />
  );
}


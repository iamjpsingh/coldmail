/**
 * Stat Card Component
 * Displays statistics with optional trends and icons
 */
import * as React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { cn, formatNumber } from '@/lib/utils';

interface StatCardProps {
  /** Label describing the stat */
  label: string;
  /** The main value to display */
  value: number | string;
  /** Optional icon to display */
  icon?: React.ElementType;
  /** Optional description or secondary info */
  description?: string;
  /** Optional trend percentage (positive = up, negative = down) */
  trend?: number;
  /** Period for the trend (e.g., "vs last week") */
  trendPeriod?: string;
  /** Visual variant */
  variant?: 'default' | 'primary' | 'success' | 'warning' | 'destructive';
  /** Whether to format the value as a number */
  formatValue?: boolean;
  /** Additional class names */
  className?: string;
}

const variantStyles = {
  default: {
    icon: 'text-muted-foreground bg-muted',
    gradient: '',
  },
  primary: {
    icon: 'text-primary bg-primary/10',
    gradient: 'bg-gradient-to-br from-primary/5 via-transparent to-transparent',
  },
  success: {
    icon: 'text-green-600 bg-green-500/10',
    gradient: 'bg-gradient-to-br from-green-500/5 via-transparent to-transparent',
  },
  warning: {
    icon: 'text-amber-600 bg-amber-500/10',
    gradient: 'bg-gradient-to-br from-amber-500/5 via-transparent to-transparent',
  },
  destructive: {
    icon: 'text-red-600 bg-red-500/10',
    gradient: 'bg-gradient-to-br from-red-500/5 via-transparent to-transparent',
  },
};

export function StatCard({
  label,
  value,
  icon: Icon,
  description,
  trend,
  trendPeriod,
  variant = 'default',
  formatValue = true,
  className,
}: StatCardProps) {
  const styles = variantStyles[variant];

  const displayValue = formatValue && typeof value === 'number'
    ? formatNumber(value)
    : value;

  const TrendIcon = trend !== undefined
    ? trend > 0
      ? TrendingUp
      : trend < 0
        ? TrendingDown
        : Minus
    : null;

  const trendColor = trend !== undefined
    ? trend > 0
      ? 'text-green-600'
      : trend < 0
        ? 'text-red-600'
        : 'text-muted-foreground'
    : '';

  return (
    <Card className={cn('relative overflow-hidden', className)}>
      <div className={cn('absolute inset-0', styles.gradient)} />
      <CardContent className="relative pt-5 pb-4">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <p className="text-sm font-medium text-muted-foreground">{label}</p>
            <p className="text-3xl font-bold tracking-tight">{displayValue}</p>

            {(trend !== undefined || description) && (
              <div className="flex items-center gap-2 text-sm">
                {trend !== undefined && TrendIcon && (
                  <span className={cn('flex items-center gap-1 font-medium', trendColor)}>
                    <TrendIcon className="h-3.5 w-3.5" />
                    {Math.abs(trend)}%
                  </span>
                )}
                {trendPeriod && (
                  <span className="text-muted-foreground">{trendPeriod}</span>
                )}
                {description && !trend && (
                  <span className="text-muted-foreground">{description}</span>
                )}
              </div>
            )}
          </div>

          {Icon && (
            <div className={cn('rounded-xl p-2.5', styles.icon)}>
              <Icon className="h-5 w-5" />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

interface StatGridProps {
  children: React.ReactNode;
  columns?: 2 | 3 | 4 | 5;
  className?: string;
}

export function StatGrid({ children, columns = 4, className }: StatGridProps) {
  const gridCols = {
    2: 'md:grid-cols-2',
    3: 'md:grid-cols-3',
    4: 'md:grid-cols-2 lg:grid-cols-4',
    5: 'md:grid-cols-3 lg:grid-cols-5',
  };

  return (
    <div className={cn('grid grid-cols-1 gap-4', gridCols[columns], className)}>
      {children}
    </div>
  );
}

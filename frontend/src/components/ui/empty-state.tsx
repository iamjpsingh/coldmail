/**
 * Empty State Component
 * Displays a placeholder when there's no content
 */
import * as React from 'react';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  /** Icon to display (Lucide icon component) */
  icon: React.ElementType;
  /** Main title text */
  title: string;
  /** Description text */
  description: string;
  /** Action button or element */
  action?: React.ReactNode;
  /** Additional content */
  children?: React.ReactNode;
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Additional class names */
  className?: string;
}

const sizeStyles = {
  sm: {
    container: 'py-8',
    icon: 'h-10 w-10',
    iconBg: 'h-16 w-16',
    title: 'text-base',
    description: 'text-sm',
  },
  md: {
    container: 'py-12',
    icon: 'h-12 w-12',
    iconBg: 'h-20 w-20',
    title: 'text-lg',
    description: 'text-sm',
  },
  lg: {
    container: 'py-16',
    icon: 'h-16 w-16',
    iconBg: 'h-24 w-24',
    title: 'text-xl',
    description: 'text-base',
  },
};

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  children,
  size = 'md',
  className,
}: EmptyStateProps) {
  const styles = sizeStyles[size];

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-center',
        styles.container,
        className
      )}
    >
      {/* Icon with decorative background */}
      <div className="relative mb-6">
        <div
          className={cn(
            'absolute inset-0 rounded-full bg-gradient-to-br from-primary/10 to-accent/10 blur-xl',
            styles.iconBg
          )}
        />
        <div
          className={cn(
            'relative flex items-center justify-center rounded-2xl bg-muted/80 backdrop-blur-sm',
            styles.iconBg
          )}
        >
          <Icon className={cn('text-muted-foreground', styles.icon)} />
        </div>
      </div>

      {/* Text content */}
      <h3 className={cn('font-semibold text-foreground mb-2', styles.title)}>
        {title}
      </h3>
      <p
        className={cn(
          'text-muted-foreground max-w-sm mx-auto mb-6',
          styles.description
        )}
      >
        {description}
      </p>

      {/* Action button */}
      {action && <div className="flex items-center gap-3">{action}</div>}

      {/* Additional content */}
      {children && <div className="mt-6">{children}</div>}
    </div>
  );
}

interface EmptyStateCardProps extends EmptyStateProps {
  /** Whether to show a border */
  bordered?: boolean;
}

export function EmptyStateCard({
  bordered = true,
  className,
  ...props
}: EmptyStateCardProps) {
  return (
    <div
      className={cn(
        'rounded-xl bg-card',
        bordered && 'border',
        className
      )}
    >
      <EmptyState {...props} />
    </div>
  );
}

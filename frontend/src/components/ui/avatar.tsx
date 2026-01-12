/**
 * Avatar Component
 * Displays user avatars with fallback to initials
 */
import * as React from 'react';
import { cn, getInitials, stringToColor } from '@/lib/utils';

interface AvatarProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Image URL for the avatar */
  src?: string | null;
  /** Alt text for the image */
  alt?: string;
  /** Name to generate initials from */
  name?: string | null;
  /** Email to use as fallback for initials */
  email?: string;
  /** Size of the avatar */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  /** Whether to show a status indicator */
  status?: 'online' | 'offline' | 'busy' | 'away';
}

const sizeClasses = {
  xs: 'h-6 w-6 text-[10px]',
  sm: 'h-8 w-8 text-xs',
  md: 'h-10 w-10 text-sm',
  lg: 'h-12 w-12 text-base',
  xl: 'h-16 w-16 text-lg',
};

const statusSizeClasses = {
  xs: 'h-1.5 w-1.5 ring-1',
  sm: 'h-2 w-2 ring-1',
  md: 'h-2.5 w-2.5 ring-2',
  lg: 'h-3 w-3 ring-2',
  xl: 'h-4 w-4 ring-2',
};

const statusColors = {
  online: 'bg-green-500',
  offline: 'bg-gray-400',
  busy: 'bg-red-500',
  away: 'bg-yellow-500',
};

export function Avatar({
  src,
  alt,
  name,
  email,
  size = 'md',
  status,
  className,
  ...props
}: AvatarProps) {
  const [imageError, setImageError] = React.useState(false);
  const initials = getInitials(name, email);
  const colorClass = stringToColor(email || name || 'default');

  const showImage = src && !imageError;

  return (
    <div className={cn('relative inline-flex', className)} {...props}>
      <div
        className={cn(
          'relative flex shrink-0 items-center justify-center rounded-full font-semibold text-white overflow-hidden',
          sizeClasses[size],
          !showImage && colorClass
        )}
      >
        {showImage ? (
          <img
            src={src}
            alt={alt || name || 'Avatar'}
            className="h-full w-full object-cover"
            onError={() => setImageError(true)}
          />
        ) : (
          <span className="select-none">{initials}</span>
        )}
      </div>

      {status && (
        <span
          className={cn(
            'absolute bottom-0 right-0 rounded-full ring-background',
            statusSizeClasses[size],
            statusColors[status]
          )}
        />
      )}
    </div>
  );
}

interface AvatarGroupProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Maximum number of avatars to show before collapsing */
  max?: number;
  /** Size of the avatars */
  size?: 'xs' | 'sm' | 'md' | 'lg';
  children: React.ReactNode;
}

export function AvatarGroup({
  max = 3,
  size = 'md',
  children,
  className,
  ...props
}: AvatarGroupProps) {
  const avatars = React.Children.toArray(children);
  const visibleAvatars = avatars.slice(0, max);
  const remainingCount = avatars.length - max;

  return (
    <div
      className={cn('flex items-center -space-x-2', className)}
      {...props}
    >
      {visibleAvatars.map((avatar, index) => (
        <div
          key={index}
          className="relative ring-2 ring-background rounded-full"
        >
          {avatar}
        </div>
      ))}

      {remainingCount > 0 && (
        <div
          className={cn(
            'relative flex items-center justify-center rounded-full bg-muted text-muted-foreground font-medium ring-2 ring-background',
            sizeClasses[size]
          )}
        >
          +{remainingCount}
        </div>
      )}
    </div>
  );
}

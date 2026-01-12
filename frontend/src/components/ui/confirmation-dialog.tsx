/**
 * Confirmation Dialog Component
 * A reusable dialog for confirming destructive or important actions.
 */
import * as React from 'react';
import { AlertTriangle, Trash2, Info, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { cn } from '@/lib/utils';

type ConfirmationVariant = 'destructive' | 'warning' | 'info' | 'default';

interface ConfirmationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string | React.ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: ConfirmationVariant;
  onConfirm: () => void | Promise<void>;
  isLoading?: boolean;
  /** Additional content to display in the dialog body */
  children?: React.ReactNode;
}

const variantConfig: Record<
  ConfirmationVariant,
  {
    icon: React.ElementType;
    iconClass: string;
    bgClass: string;
    buttonVariant: 'destructive' | 'default' | 'outline';
  }
> = {
  destructive: {
    icon: Trash2,
    iconClass: 'text-destructive',
    bgClass: 'bg-destructive/10',
    buttonVariant: 'destructive',
  },
  warning: {
    icon: AlertTriangle,
    iconClass: 'text-warning',
    bgClass: 'bg-warning/10',
    buttonVariant: 'default',
  },
  info: {
    icon: Info,
    iconClass: 'text-info',
    bgClass: 'bg-info/10',
    buttonVariant: 'default',
  },
  default: {
    icon: AlertCircle,
    iconClass: 'text-primary',
    bgClass: 'bg-primary/10',
    buttonVariant: 'default',
  },
};

export function ConfirmationDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'default',
  onConfirm,
  isLoading = false,
  children,
}: ConfirmationDialogProps) {
  const [isPending, setIsPending] = React.useState(false);
  const config = variantConfig[variant];
  const Icon = config.icon;

  const handleConfirm = async () => {
    setIsPending(true);
    try {
      await onConfirm();
      onOpenChange(false);
    } catch (error) {
      // Let the parent handle errors
      console.error('Confirmation action failed:', error);
    } finally {
      setIsPending(false);
    }
  };

  const loading = isLoading || isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader className="flex-row items-start gap-4">
          <div
            className={cn(
              'flex h-12 w-12 shrink-0 items-center justify-center rounded-xl',
              config.bgClass
            )}
          >
            <Icon className={cn('h-6 w-6', config.iconClass)} />
          </div>
          <div className="flex-1">
            <DialogTitle className="text-lg">{title}</DialogTitle>
            <DialogDescription className="mt-1.5">
              {description}
            </DialogDescription>
          </div>
        </DialogHeader>

        {children && <div className="mt-4">{children}</div>}

        <DialogFooter className="mt-6 gap-2 sm:gap-0">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={loading}
          >
            {cancelLabel}
          </Button>
          <Button
            variant={config.buttonVariant}
            onClick={handleConfirm}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                Processing...
              </>
            ) : (
              confirmLabel
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Hook for managing confirmation dialog state
 */
export function useConfirmation() {
  const [state, setState] = React.useState<{
    open: boolean;
    title: string;
    description: string;
    variant: ConfirmationVariant;
    confirmLabel: string;
    onConfirm: () => void | Promise<void>;
  }>({
    open: false,
    title: '',
    description: '',
    variant: 'default',
    confirmLabel: 'Confirm',
    onConfirm: () => {},
  });

  const confirm = React.useCallback(
    (options: {
      title: string;
      description: string;
      variant?: ConfirmationVariant;
      confirmLabel?: string;
      onConfirm: () => void | Promise<void>;
    }) => {
      setState({
        open: true,
        title: options.title,
        description: options.description,
        variant: options.variant || 'default',
        confirmLabel: options.confirmLabel || 'Confirm',
        onConfirm: options.onConfirm,
      });
    },
    []
  );

  const close = React.useCallback(() => {
    setState((prev) => ({ ...prev, open: false }));
  }, []);

  const DialogComponent = React.useCallback(
    () => (
      <ConfirmationDialog
        open={state.open}
        onOpenChange={(open) => setState((prev) => ({ ...prev, open }))}
        title={state.title}
        description={state.description}
        variant={state.variant}
        confirmLabel={state.confirmLabel}
        onConfirm={state.onConfirm}
      />
    ),
    [state]
  );

  return {
    confirm,
    close,
    ConfirmationDialog: DialogComponent,
  };
}

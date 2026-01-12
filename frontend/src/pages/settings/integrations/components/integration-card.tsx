import {
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  MoreHorizontal,
  Play,
  Pause,
  Settings,
  Trash2,
  RefreshCw,
  Zap,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import type { Integration, IntegrationType } from '@/types/integrations';
import { formatDistanceToNow } from 'date-fns';

// Integration icons
const integrationIcons: Record<IntegrationType, React.ReactNode> = {
  slack: (
    <svg className="h-6 w-6" viewBox="0 0 24 24" fill="currentColor">
      <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z" />
    </svg>
  ),
  discord: (
    <svg className="h-6 w-6" viewBox="0 0 24 24" fill="currentColor">
      <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z" />
    </svg>
  ),
  hubspot: (
    <svg className="h-6 w-6" viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.164 7.93V5.084a2.198 2.198 0 001.267-1.984v-.066A2.197 2.197 0 0017.235.84h-.066a2.197 2.197 0 00-2.193 2.193v.066c0 .876.516 1.627 1.259 1.98v2.852a5.037 5.037 0 00-2.394 1.089l-6.108-4.755a2.593 2.593 0 00.094-.685A2.612 2.612 0 105.22 6.193c0 .631.226 1.21.6 1.663l-2.238 2.74a3.12 3.12 0 00-2.078-.79 3.124 3.124 0 00-3.124 3.124 3.124 3.124 0 003.124 3.124 3.12 3.12 0 002.078-.79l2.238 2.74a2.6 2.6 0 00-.6 1.663 2.612 2.612 0 102.607-2.613c-.24 0-.47.035-.692.097l-2.232-2.734a5.03 5.03 0 001.153-3.202 5.02 5.02 0 00-.457-2.093l5.99-4.663a5.037 5.037 0 002.395 1.09v7.087a3.13 3.13 0 00-2.08 2.943 3.136 3.136 0 006.27 0 3.13 3.13 0 00-2.08-2.947V7.93h-.041z" />
    </svg>
  ),
  salesforce: (
    <svg className="h-6 w-6" viewBox="0 0 24 24" fill="currentColor">
      <path d="M10.005 4.808c.86-1.049 2.17-1.716 3.633-1.716 1.724 0 3.235.937 4.048 2.332a5.023 5.023 0 011.565-.248c2.789 0 5.049 2.26 5.049 5.049 0 2.788-2.26 5.048-5.049 5.048-.357 0-.704-.037-1.039-.107-.66 1.461-2.129 2.479-3.838 2.479-1.163 0-2.211-.473-2.972-1.236-.762.763-1.81 1.236-2.973 1.236-2.293 0-4.152-1.858-4.152-4.151 0-.227.019-.45.054-.668a4.254 4.254 0 01-2.331-.417 4.247 4.247 0 01-.912-.657A4.261 4.261 0 010 9.466c0-2.359 1.912-4.271 4.271-4.271 1.109 0 2.119.423 2.878 1.117.855-.954 2.1-1.556 3.484-1.556.408 0 .804.052 1.184.151-.58.667-.959 1.509-1.027 2.435-.028.044-.054.089-.08.134-.316-.127-.661-.196-1.022-.196-1.46 0-2.643 1.183-2.643 2.643 0 .36.072.704.203 1.017-.046.027-.091.054-.135.082a3.86 3.86 0 00-.108-1.214z" />
    </svg>
  ),
  google_sheets: (
    <svg className="h-6 w-6" viewBox="0 0 24 24" fill="currentColor">
      <path d="M19.385 2H4.615A2.615 2.615 0 002 4.615v14.77A2.615 2.615 0 004.615 22h14.77A2.615 2.615 0 0022 19.385V4.615A2.615 2.615 0 0019.385 2zM9.5 18.5h-3v-3h3v3zm0-5h-3v-3h3v3zm0-5h-3v-3h3v3zm4.25 10h-3v-3h3v3zm0-5h-3v-3h3v3zm0-5h-3v-3h3v3zm4.25 10h-3v-3h3v3zm0-5h-3v-3h3v3zm0-5h-3v-3h3v3z" />
    </svg>
  ),
  zapier: <Zap className="h-6 w-6" />,
  n8n: (
    <svg className="h-6 w-6" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 3a9 9 0 110 18 9 9 0 010-18zm-2 4.5v9l7-4.5-7-4.5z" />
    </svg>
  ),
  custom_webhook: <Zap className="h-6 w-6" />,
};

const statusIcons = {
  connected: <CheckCircle className="h-4 w-4 text-green-500" />,
  disconnected: <XCircle className="h-4 w-4 text-gray-400" />,
  error: <AlertCircle className="h-4 w-4 text-red-500" />,
  pending: <Clock className="h-4 w-4 text-yellow-500" />,
};

const statusColors = {
  connected: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  disconnected: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
  error: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
};

interface IntegrationCardProps {
  integration: Integration;
  onTest: (id: string) => void;
  onSync: (id: string) => void;
  onSettings: (integration: Integration) => void;
  onToggleActive: (integration: Integration) => void;
  onDelete: (id: string) => void;
  isTestPending?: boolean;
  isSyncPending?: boolean;
}

export function IntegrationCard({
  integration,
  onTest,
  onSync,
  onSettings,
  onToggleActive,
  onDelete,
  isTestPending,
  isSyncPending,
}: IntegrationCardProps) {
  const canSync = ['hubspot', 'salesforce', 'google_sheets'].includes(
    integration.integration_type
  );

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-muted">
            {integrationIcons[integration.integration_type]}
          </div>
          <div>
            <CardTitle className="text-lg">{integration.name}</CardTitle>
            <CardDescription className="flex items-center gap-2 mt-1">
              <Badge variant="outline" className={statusColors[integration.status]}>
                {statusIcons[integration.status]}
                <span className="ml-1">{integration.status_display}</span>
              </Badge>
              {!integration.is_active && (
                <Badge variant="secondary">Paused</Badge>
              )}
            </CardDescription>
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onTest(integration.id)}>
              <Play className="mr-2 h-4 w-4" />
              Test Connection
            </DropdownMenuItem>
            {canSync && (
              <DropdownMenuItem onClick={() => onSync(integration.id)}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Sync Now
              </DropdownMenuItem>
            )}
            <DropdownMenuItem onClick={() => onSettings(integration)}>
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => onToggleActive(integration)}>
              {integration.is_active ? (
                <>
                  <Pause className="mr-2 h-4 w-4" />
                  Pause
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Resume
                </>
              )}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-destructive"
              onClick={() => onDelete(integration.id)}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </CardHeader>
      <CardContent>
        {integration.description && (
          <p className="text-sm text-muted-foreground mb-4">
            {integration.description}
          </p>
        )}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">Success Rate</span>
            <div className="flex items-center gap-2 mt-1">
              <div
                className={`w-2 h-2 rounded-full ${
                  integration.success_rate >= 95
                    ? 'bg-green-500'
                    : integration.success_rate >= 80
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                }`}
              />
              <span className="font-medium">
                {integration.success_rate.toFixed(1)}%
              </span>
            </div>
          </div>
          <div>
            <span className="text-muted-foreground">Total Syncs</span>
            <div className="font-medium mt-1">{integration.total_syncs}</div>
          </div>
          {integration.last_sync_at && (
            <div className="col-span-2">
              <span className="text-muted-foreground">Last Sync</span>
              <div className="font-medium mt-1">
                {formatDistanceToNow(new Date(integration.last_sync_at), {
                  addSuffix: true,
                })}
              </div>
            </div>
          )}
          {integration.last_error && (
            <div className="col-span-2">
              <span className="text-destructive text-xs">
                {integration.last_error}
              </span>
            </div>
          )}
        </div>
        <div className="flex gap-2 mt-4">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onTest(integration.id)}
            disabled={isTestPending}
          >
            {isTestPending ? (
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <Play className="mr-2 h-4 w-4" />
            )}
            Test
          </Button>
          {canSync && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onSync(integration.id)}
              disabled={isSyncPending}
            >
              {isSyncPending ? (
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" />
              )}
              Sync
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => onSettings(integration)}
          >
            <Settings className="mr-2 h-4 w-4" />
            Settings
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export { integrationIcons };

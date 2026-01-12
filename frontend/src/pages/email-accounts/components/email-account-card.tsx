import { useState } from 'react';
import { MoreVertical, Play, Pause, Trash2, TestTube, Settings, TrendingUp, Mail, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { useDeleteEmailAccount, useTestConnection, useStartWarmup, useStopWarmup } from '@/hooks/use-email-accounts';
import type { EmailAccount, EmailProvider } from '@/types/email-account';
import { TestEmailDialog } from './test-email-dialog';

interface EmailAccountCardProps {
  account: EmailAccount;
  onPause: (id: string) => Promise<void>;
  onResume: (id: string) => Promise<void>;
}

const providerLabels: Record<EmailProvider, string> = {
  smtp: 'SMTP',
  gmail: 'Gmail',
  outlook: 'Outlook',
  sendgrid: 'SendGrid',
  mailgun: 'Mailgun',
  aws_ses: 'AWS SES',
};

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-800',
  paused: 'bg-yellow-100 text-yellow-800',
  error: 'bg-red-100 text-red-800',
  disconnected: 'bg-gray-100 text-gray-800',
};

export function EmailAccountCard({ account, onPause, onResume }: EmailAccountCardProps) {
  const [isTestDialogOpen, setIsTestDialogOpen] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<{ testing: boolean; result?: string; success?: boolean }>({
    testing: false,
  });

  const deleteMutation = useDeleteEmailAccount();
  const testConnectionMutation = useTestConnection();
  const startWarmupMutation = useStartWarmup();
  const stopWarmupMutation = useStopWarmup();

  const handleTestConnection = async () => {
    setConnectionStatus({ testing: true });
    try {
      const result = await testConnectionMutation.mutateAsync({ id: account.id });
      setConnectionStatus({
        testing: false,
        success: result.success,
        result: result.success ? 'Connection successful' : 'Connection failed',
      });
    } catch (error) {
      setConnectionStatus({
        testing: false,
        success: false,
        result: 'Connection test failed',
      });
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this email account?')) {
      await deleteMutation.mutateAsync(account.id);
    }
  };

  const handleToggleWarmup = async () => {
    if (account.is_warming_up) {
      await stopWarmupMutation.mutateAsync(account.id);
    } else {
      await startWarmupMutation.mutateAsync({ id: account.id });
    }
  };

  return (
    <>
      <Card className="hover:shadow-md transition-shadow">
        <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
          <div className="space-y-1">
            <CardTitle className="text-lg font-semibold">{account.name}</CardTitle>
            <p className="text-sm text-muted-foreground">{account.email}</p>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={handleTestConnection}>
                <TestTube className="h-4 w-4 mr-2" />
                Test Connection
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setIsTestDialogOpen(true)}>
                <Mail className="h-4 w-4 mr-2" />
                Send Test Email
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleToggleWarmup}>
                <TrendingUp className="h-4 w-4 mr-2" />
                {account.is_warming_up ? 'Stop Warmup' : 'Start Warmup'}
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {account.status === 'active' ? (
                <DropdownMenuItem onClick={() => onPause(account.id)}>
                  <Pause className="h-4 w-4 mr-2" />
                  Pause
                </DropdownMenuItem>
              ) : (
                <DropdownMenuItem onClick={() => onResume(account.id)}>
                  <Play className="h-4 w-4 mr-2" />
                  Resume
                </DropdownMenuItem>
              )}
              <DropdownMenuItem>
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                onClick={handleDelete}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="flex items-center gap-2">
            <Badge variant="outline">{providerLabels[account.provider]}</Badge>
            <Badge className={statusColors[account.status]}>{account.status}</Badge>
            {account.is_oauth && <Badge variant="secondary">OAuth</Badge>}
            {account.is_warming_up && (
              <Badge className="bg-blue-100 text-blue-800">Warming Up</Badge>
            )}
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Sent Today</p>
              <p className="font-medium">
                {account.emails_sent_today} / {account.daily_limit}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Total Sent</p>
              <p className="font-medium">{account.total_emails_sent}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Reputation</p>
              <p className="font-medium">{account.reputation_score}%</p>
            </div>
            <div>
              <p className="text-muted-foreground">Bounce Rate</p>
              <p className="font-medium">{(account.bounce_rate * 100).toFixed(1)}%</p>
            </div>
          </div>

          {/* Connection test result */}
          {connectionStatus.result && (
            <div
              className={`flex items-center gap-2 text-sm ${
                connectionStatus.success ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {connectionStatus.success ? (
                <TestTube className="h-4 w-4" />
              ) : (
                <AlertCircle className="h-4 w-4" />
              )}
              {connectionStatus.result}
            </div>
          )}

          {/* Can send indicator */}
          <div className="flex items-center justify-between pt-2 border-t">
            <span className="text-sm text-muted-foreground">Available to send</span>
            <span
              className={`text-sm font-medium ${
                account.can_send ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {account.can_send ? `${account.remaining_today} remaining` : 'Limit reached'}
            </span>
          </div>
        </CardContent>
      </Card>

      <TestEmailDialog
        open={isTestDialogOpen}
        onOpenChange={setIsTestDialogOpen}
        accountId={account.id}
        accountEmail={account.email}
      />
    </>
  );
}

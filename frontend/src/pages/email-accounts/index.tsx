import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Plus, Mail, AlertCircle, CheckCircle2, Pause, Loader2, RefreshCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { StatCard, StatGrid } from '@/components/ui/stat-card';
import { EmptyStateCard } from '@/components/ui/empty-state';
import { useEmailAccounts, usePauseEmailAccount, useResumeEmailAccount } from '@/hooks/use-email-accounts';
import { EmailAccountCard } from './components/email-account-card';
import { AddEmailAccountDialog } from './components/add-email-account-dialog';
import type { EmailAccount } from '@/types/email-account';

export default function EmailAccountsPage() {
  const [searchParams] = useSearchParams();
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);

  const { data: accounts, isLoading, error, refetch, isRefetching } = useEmailAccounts();
  const pauseMutation = usePauseEmailAccount();
  const resumeMutation = useResumeEmailAccount();

  // Check for OAuth callback results
  const success = searchParams.get('success');
  const oauthEmail = searchParams.get('email');
  const oauthError = searchParams.get('error');

  const handlePause = async (id: string) => {
    await pauseMutation.mutateAsync(id);
  };

  const handleResume = async (id: string) => {
    await resumeMutation.mutateAsync(id);
  };

  const getStatusCounts = () => {
    if (!accounts) return { active: 0, paused: 0, error: 0, total: 0 };
    return {
      active: accounts.filter((a) => a.status === 'active').length,
      paused: accounts.filter((a) => a.status === 'paused').length,
      error: accounts.filter((a) => a.status === 'error').length,
      total: accounts.length,
    };
  };

  const counts = getStatusCounts();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Email Accounts</h1>
            <p className="text-muted-foreground">Manage your email accounts for sending campaigns</p>
          </div>
        </div>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Email Accounts</h1>
            <p className="text-muted-foreground">Manage your email accounts for sending campaigns</p>
          </div>
        </div>
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="rounded-full bg-destructive/10 p-4 mb-4">
              <AlertCircle className="h-8 w-8 text-destructive" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Unable to Load Email Accounts</h3>
            <p className="text-muted-foreground text-center max-w-md mb-6">
              We couldn't fetch your email accounts. Please check your connection and try again.
            </p>
            <Button onClick={() => refetch()} disabled={isRefetching}>
              {isRefetching ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <RefreshCcw className="h-4 w-4 mr-2" />
              )}
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* OAuth callback messages */}
      {success === 'true' && oauthEmail && (
        <Card className="border-green-500/50 bg-green-500/5">
          <CardContent className="py-4">
            <div className="flex items-center gap-2 text-green-700">
              <CheckCircle2 className="h-5 w-5" />
              <span>Successfully connected {oauthEmail}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {oauthError && (
        <Card className="border-destructive/50 bg-destructive/5">
          <CardContent className="py-4">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <span>OAuth error: {decodeURIComponent(oauthError)}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Email Accounts</h1>
          <p className="text-muted-foreground">
            Manage your email accounts for sending campaigns
          </p>
        </div>
        <Button onClick={() => setIsAddDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Add Account
        </Button>
      </div>

      {/* Stats Cards */}
      <StatGrid columns={4}>
        <StatCard
          label="Total Accounts"
          value={counts.total}
          icon={Mail}
          variant="primary"
        />
        <StatCard
          label="Active"
          value={counts.active}
          icon={CheckCircle2}
          variant="success"
        />
        <StatCard
          label="Paused"
          value={counts.paused}
          icon={Pause}
          variant="warning"
        />
        <StatCard
          label="Error"
          value={counts.error}
          icon={AlertCircle}
          variant="destructive"
        />
      </StatGrid>

      {/* Account List */}
      {accounts && accounts.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {accounts.map((account: EmailAccount) => (
            <EmailAccountCard
              key={account.id}
              account={account}
              onPause={handlePause}
              onResume={handleResume}
            />
          ))}
        </div>
      ) : (
        <EmptyStateCard
          icon={Mail}
          title="No email accounts yet"
          description="Add your first email account to start sending campaigns."
          action={
            <Button onClick={() => setIsAddDialogOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Add Account
            </Button>
          }
        />
      )}

      {/* Add Account Dialog */}
      <AddEmailAccountDialog
        open={isAddDialogOpen}
        onOpenChange={setIsAddDialogOpen}
      />
    </div>
  );
}

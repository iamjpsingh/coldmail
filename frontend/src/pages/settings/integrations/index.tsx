import { useState } from 'react';
import { Plus, Search, Plug, RefreshCw, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import {
  useIntegrations,
  useIntegrationTypes,
  useTestIntegration,
  useSyncIntegration,
  useActivateIntegration,
  useDeactivateIntegration,
  useDeleteIntegration,
  useCreateDiscordIntegration,
  useIntegrationSettings,
  useUpdateIntegrationSettings,
} from '@/hooks/use-integrations';
import type { Integration, DiscordIntegrationCreate } from '@/types/integrations';
import { IntegrationCard } from './components/integration-card';
import { AddIntegrationDialog } from './components/add-integration-dialog';
import { IntegrationSettingsDialog } from './components/integration-settings-dialog';

export default function IntegrationsPage() {
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [showSettingsDialog, setShowSettingsDialog] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  // Queries
  const { data: integrationsData, isLoading, error } = useIntegrations({
    search,
    status: statusFilter !== 'all' ? statusFilter : undefined,
    integration_type: typeFilter !== 'all' ? typeFilter : undefined,
  });
  const { data: integrationTypes } = useIntegrationTypes();
  const { data: integrationSettings } = useIntegrationSettings(selectedIntegration?.id || '');

  // Mutations
  const testMutation = useTestIntegration();
  const syncMutation = useSyncIntegration();
  const activateMutation = useActivateIntegration();
  const deactivateMutation = useDeactivateIntegration();
  const deleteMutation = useDeleteIntegration();
  const createDiscordMutation = useCreateDiscordIntegration();
  const updateSettingsMutation = useUpdateIntegrationSettings();

  const handleTest = async (id: string) => {
    try {
      const result = await testMutation.mutateAsync(id);
      if (result.success) {
        toast({
          title: 'Connection Successful',
          description: result.message,
        });
      } else {
        toast({
          title: 'Connection Failed',
          description: result.message,
          variant: 'destructive',
        });
      }
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to test connection.',
        variant: 'destructive',
      });
    }
  };

  const handleSync = async (id: string) => {
    try {
      const result = await syncMutation.mutateAsync(id);
      toast({
        title: 'Sync Complete',
        description: `Processed ${result.processed} records: ${result.created} created, ${result.updated} updated, ${result.failed} failed.`,
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to sync integration.',
        variant: 'destructive',
      });
    }
  };

  const handleToggleActive = async (integration: Integration) => {
    try {
      if (integration.is_active) {
        await deactivateMutation.mutateAsync(integration.id);
        toast({
          title: 'Integration Paused',
          description: `${integration.name} has been paused.`,
        });
      } else {
        await activateMutation.mutateAsync(integration.id);
        toast({
          title: 'Integration Activated',
          description: `${integration.name} has been activated.`,
        });
      }
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to update integration.',
        variant: 'destructive',
      });
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteMutation.mutateAsync(id);
      setDeleteConfirmId(null);
      toast({
        title: 'Integration Deleted',
        description: 'The integration has been permanently deleted.',
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to delete integration.',
        variant: 'destructive',
      });
    }
  };

  const handleSettings = (integration: Integration) => {
    setSelectedIntegration(integration);
    setShowSettingsDialog(true);
  };

  const handleCreateDiscord = async (data: DiscordIntegrationCreate) => {
    try {
      await createDiscordMutation.mutateAsync(data);
      toast({
        title: 'Integration Created',
        description: 'Discord integration has been created successfully.',
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to create Discord integration.',
        variant: 'destructive',
      });
      throw new Error('Failed to create');
    }
  };

  const handleSaveSettings = async (settings: Record<string, unknown>) => {
    if (!selectedIntegration) return;
    try {
      await updateSettingsMutation.mutateAsync({
        id: selectedIntegration.id,
        data: settings,
      });
      toast({
        title: 'Settings Saved',
        description: 'Integration settings have been updated.',
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to save settings.',
        variant: 'destructive',
      });
      throw new Error('Failed to save');
    }
  };

  const integrations: Integration[] = integrationsData?.results || [];
  const connectedCount = integrations.filter((i: Integration) => i.status === 'connected').length;
  const activeCount = integrations.filter((i: Integration) => i.is_active).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Integrations</h1>
          <p className="text-muted-foreground">
            Connect ColdMail with your favorite tools and services
          </p>
        </div>
        <Button onClick={() => setShowAddDialog(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Add Integration
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Integrations</CardDescription>
            <CardTitle className="text-3xl">{integrations.length}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Connected</CardDescription>
            <CardTitle className="text-3xl text-green-600">{connectedCount}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Active</CardDescription>
            <CardTitle className="text-3xl text-blue-600">{activeCount}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search integrations..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                <SelectItem value="connected">Connected</SelectItem>
                <SelectItem value="disconnected">Disconnected</SelectItem>
                <SelectItem value="error">Error</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
              </SelectContent>
            </Select>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {integrationTypes?.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Error State */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load integrations. Please try again.
          </AlertDescription>
        </Alert>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Integrations Grid */}
      {!isLoading && integrations.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Plug className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">No integrations yet</h3>
            <p className="text-muted-foreground text-center mb-4 max-w-md">
              Connect ColdMail with your favorite tools to automate your workflow,
              sync contacts, and receive notifications.
            </p>
            <Button onClick={() => setShowAddDialog(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Your First Integration
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {integrations.map((integration) => (
            <IntegrationCard
              key={integration.id}
              integration={integration}
              onTest={handleTest}
              onSync={handleSync}
              onSettings={handleSettings}
              onToggleActive={handleToggleActive}
              onDelete={setDeleteConfirmId}
              isTestPending={testMutation.isPending}
              isSyncPending={syncMutation.isPending}
            />
          ))}
        </div>
      )}

      {/* Add Integration Dialog */}
      <AddIntegrationDialog
        open={showAddDialog}
        onOpenChange={setShowAddDialog}
        integrationTypes={integrationTypes || []}
        onCreateDiscord={handleCreateDiscord}
        isCreating={createDiscordMutation.isPending}
      />

      {/* Settings Dialog */}
      <IntegrationSettingsDialog
        integration={selectedIntegration}
        settings={integrationSettings}
        open={showSettingsDialog}
        onOpenChange={setShowSettingsDialog}
        onSave={handleSaveSettings}
        isSaving={updateSettingsMutation.isPending}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteConfirmId !== null}
        onOpenChange={() => setDeleteConfirmId(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Integration</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this integration? This action cannot be
              undone and will stop all syncing and notifications.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirmId(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deleteConfirmId && handleDelete(deleteConfirmId)}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

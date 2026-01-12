import { useState } from 'react';
import {
  Webhook,
  Plus,
  Search,
  MoreHorizontal,
  Copy,
  Trash2,
  Play,
  Pause,
  RefreshCw,
  ExternalLink,
  CheckCircle,
  XCircle,
  AlertCircle,
  Eye,
  EyeOff,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardHeader,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Checkbox } from '@/components/ui/checkbox';
import { useToast } from '@/hooks/use-toast';
import {
  useWebhooks,
  useCreateWebhook,
  useDeleteWebhook,
  useUpdateWebhook,
  useTestWebhook,
  useActivateWebhook,
  useWebhookEventTypes,
  useWebhookSecret,
  useRegenerateWebhookSecret,
} from '@/hooks/use-webhooks';
import type {
  Webhook as WebhookType,
  WebhookCreate,
  WebhookEventType,
  WebhookEventTypeOption,
} from '@/types/webhooks';
import { formatDistanceToNow } from 'date-fns';

export default function WebhooksPage() {
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showSecretDialog, setShowSecretDialog] = useState(false);
  const [selectedWebhook, setSelectedWebhook] = useState<WebhookType | null>(null);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState<WebhookCreate>({
    name: '',
    description: '',
    url: '',
    events: [],
    verify_ssl: true,
    timeout_seconds: 30,
    max_retries: 5,
    retry_delay_seconds: 60,
  });

  const { data: webhooksData, isLoading } = useWebhooks({ search });
  const { data: eventTypes } = useWebhookEventTypes();
  const createMutation = useCreateWebhook();
  const deleteMutation = useDeleteWebhook();
  const updateMutation = useUpdateWebhook();
  const testMutation = useTestWebhook();
  const activateMutation = useActivateWebhook();

  const handleCreate = async () => {
    try {
      await createMutation.mutateAsync(formData);
      setShowCreateDialog(false);
      setFormData({
        name: '',
        description: '',
        url: '',
        events: [],
        verify_ssl: true,
        timeout_seconds: 30,
        max_retries: 5,
        retry_delay_seconds: 60,
      });
      toast({
        title: 'Webhook Created',
        description: 'Your webhook has been created successfully.',
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to create webhook.',
        variant: 'destructive',
      });
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteMutation.mutateAsync(id);
      setDeleteConfirmId(null);
      toast({
        title: 'Webhook Deleted',
        description: 'The webhook has been permanently deleted.',
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to delete webhook.',
        variant: 'destructive',
      });
    }
  };

  const handleToggleActive = async (webhook: WebhookType) => {
    try {
      if (webhook.is_active) {
        await updateMutation.mutateAsync({
          id: webhook.id,
          data: { is_active: false },
        });
        toast({
          title: 'Webhook Paused',
          description: 'The webhook has been paused.',
        });
      } else {
        await activateMutation.mutateAsync(webhook.id);
        toast({
          title: 'Webhook Activated',
          description: 'The webhook has been activated.',
        });
      }
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to update webhook.',
        variant: 'destructive',
      });
    }
  };

  const handleTest = async (id: string) => {
    try {
      const result = await testMutation.mutateAsync(id);
      if (result.success) {
        toast({
          title: 'Test Successful',
          description: `Webhook responded with status ${result.status_code}`,
        });
      } else {
        toast({
          title: 'Test Failed',
          description: result.error || 'Webhook delivery failed',
          variant: 'destructive',
        });
      }
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to test webhook.',
        variant: 'destructive',
      });
    }
  };

  const toggleEvent = (event: WebhookEventType) => {
    setFormData((prev) => ({
      ...prev,
      events: prev.events.includes(event)
        ? prev.events.filter((e) => e !== event)
        : [...prev.events, event],
    }));
  };

  const selectAllEvents = () => {
    if (eventTypes) {
      setFormData((prev) => ({
        ...prev,
        events: eventTypes.map((e: WebhookEventTypeOption) => e.value),
      }));
    }
  };

  const clearAllEvents = () => {
    setFormData((prev) => ({ ...prev, events: [] }));
  };

  // Group events by category
  const groupedEvents = eventTypes?.reduce(
    (acc: Record<string, WebhookEventTypeOption[]>, event: WebhookEventTypeOption) => {
      if (!acc[event.category]) {
        acc[event.category] = [];
      }
      acc[event.category].push(event);
      return acc;
    },
    {}
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Webhooks</h1>
          <p className="text-muted-foreground">
            Configure webhooks to receive real-time notifications
          </p>
        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create Webhook
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search webhooks..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>URL</TableHead>
                <TableHead>Events</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Success Rate</TableHead>
                <TableHead>Last Delivery</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : webhooksData?.results.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">
                    <div className="flex flex-col items-center gap-2">
                      <Webhook className="h-8 w-8 text-muted-foreground" />
                      <p className="text-muted-foreground">No webhooks yet</p>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowCreateDialog(true)}
                      >
                        Create your first webhook
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                webhooksData?.results.map((webhook: WebhookType) => (
                  <TableRow key={webhook.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{webhook.name}</div>
                        {webhook.description && (
                          <div className="text-sm text-muted-foreground">
                            {webhook.description}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2 max-w-[200px]">
                        <code className="text-sm truncate">{webhook.url}</code>
                        <a
                          href={webhook.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-muted-foreground hover:text-foreground"
                        >
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="secondary">
                        {webhook.events.includes('*' as WebhookEventType)
                          ? 'All events'
                          : `${webhook.events.length} events`}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      {webhook.is_active ? (
                        webhook.disabled_at ? (
                          <Badge variant="destructive">
                            <AlertCircle className="mr-1 h-3 w-3" />
                            Auto-disabled
                          </Badge>
                        ) : (
                          <Badge variant="default">
                            <CheckCircle className="mr-1 h-3 w-3" />
                            Active
                          </Badge>
                        )
                      ) : (
                        <Badge variant="secondary">
                          <Pause className="mr-1 h-3 w-3" />
                          Paused
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div
                          className={`w-2 h-2 rounded-full ${
                            webhook.success_rate >= 95
                              ? 'bg-green-500'
                              : webhook.success_rate >= 80
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                          }`}
                        />
                        {webhook.success_rate}%
                      </div>
                    </TableCell>
                    <TableCell>
                      {webhook.last_delivery_at ? (
                        <div className="flex items-center gap-1 text-sm">
                          {webhook.last_success_at === webhook.last_delivery_at ? (
                            <CheckCircle className="h-3 w-3 text-green-500" />
                          ) : (
                            <XCircle className="h-3 w-3 text-red-500" />
                          )}
                          {formatDistanceToNow(new Date(webhook.last_delivery_at), {
                            addSuffix: true,
                          })}
                        </div>
                      ) : (
                        <span className="text-muted-foreground text-sm">Never</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleTest(webhook.id)}>
                            <Play className="mr-2 h-4 w-4" />
                            Send Test
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => {
                              setSelectedWebhook(webhook);
                              setShowSecretDialog(true);
                            }}
                          >
                            <Eye className="mr-2 h-4 w-4" />
                            View Secret
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            onClick={() => handleToggleActive(webhook)}
                          >
                            {webhook.is_active ? (
                              <>
                                <Pause className="mr-2 h-4 w-4" />
                                Pause
                              </>
                            ) : (
                              <>
                                <Play className="mr-2 h-4 w-4" />
                                Activate
                              </>
                            )}
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            className="text-destructive"
                            onClick={() => setDeleteConfirmId(webhook.id)}
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Create Webhook Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create Webhook</DialogTitle>
            <DialogDescription>
              Configure a webhook to receive real-time event notifications.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="My Webhook"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                placeholder="Optional description"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="url">Endpoint URL</Label>
              <Input
                id="url"
                type="url"
                value={formData.url}
                onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                placeholder="https://example.com/webhook"
              />
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>Events</Label>
                <div className="space-x-2">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={selectAllEvents}
                  >
                    Select All
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={clearAllEvents}
                  >
                    Clear
                  </Button>
                </div>
              </div>
              <div className="border rounded-lg p-4 max-h-[300px] overflow-y-auto space-y-4">
                {groupedEvents &&
                  Object.entries(groupedEvents).map(([category, events]) => (
                    <div key={category}>
                      <h4 className="font-medium mb-2">{category}</h4>
                      <div className="grid grid-cols-2 gap-2">
                        {(events as WebhookEventTypeOption[]).map((event) => (
                          <label
                            key={event.value}
                            className="flex items-center space-x-2 text-sm"
                          >
                            <Checkbox
                              checked={formData.events.includes(event.value)}
                              onCheckedChange={() => toggleEvent(event.value)}
                            />
                            <span>{event.label}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Verify SSL</Label>
                <p className="text-xs text-muted-foreground">
                  Verify SSL certificates for HTTPS URLs
                </p>
              </div>
              <Switch
                checked={formData.verify_ssl}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, verify_ssl: checked })
                }
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="timeout">Timeout (seconds)</Label>
                <Input
                  id="timeout"
                  type="number"
                  value={formData.timeout_seconds}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      timeout_seconds: parseInt(e.target.value),
                    })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="max_retries">Max Retries</Label>
                <Input
                  id="max_retries"
                  type="number"
                  value={formData.max_retries}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      max_retries: parseInt(e.target.value),
                    })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="retry_delay">Retry Delay (seconds)</Label>
                <Input
                  id="retry_delay"
                  type="number"
                  value={formData.retry_delay_seconds}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      retry_delay_seconds: parseInt(e.target.value),
                    })
                  }
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={
                !formData.name ||
                !formData.url ||
                formData.events.length === 0 ||
                createMutation.isPending
              }
            >
              {createMutation.isPending ? 'Creating...' : 'Create Webhook'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Secret Dialog */}
      <WebhookSecretDialog
        webhook={selectedWebhook}
        open={showSecretDialog}
        onOpenChange={setShowSecretDialog}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteConfirmId !== null}
        onOpenChange={() => setDeleteConfirmId(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Webhook</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this webhook? This action cannot be
              undone.
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

function WebhookSecretDialog({
  webhook,
  open,
  onOpenChange,
}: {
  webhook: WebhookType | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { toast } = useToast();
  const [showSecret, setShowSecret] = useState(false);
  const { data: secretData } = useWebhookSecret(webhook?.id || '');
  const regenerateMutation = useRegenerateWebhookSecret();

  const handleRegenerate = async () => {
    if (!webhook) return;
    try {
      await regenerateMutation.mutateAsync(webhook.id);
      toast({
        title: 'Secret Regenerated',
        description: 'Your webhook signing secret has been regenerated.',
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to regenerate secret.',
        variant: 'destructive',
      });
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'Copied',
      description: 'Secret copied to clipboard.',
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Webhook Secret</DialogTitle>
          <DialogDescription>
            Use this secret to verify webhook signatures in your application.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="p-4 bg-muted rounded-lg">
            <p className="text-sm mb-2">
              Webhook payloads are signed with HMAC-SHA256. The signature is sent in
              the <code className="bg-background px-1 rounded">X-Webhook-Signature</code> header.
            </p>
          </div>
          <div className="space-y-2">
            <Label>Signing Secret</Label>
            <div className="flex gap-2">
              <div className="flex-1 relative">
                <Input
                  type={showSecret ? 'text' : 'password'}
                  value={secretData?.secret || ''}
                  readOnly
                  className="pr-10 font-mono text-sm"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  className="absolute right-2 top-1/2 -translate-y-1/2"
                  onClick={() => setShowSecret(!showSecret)}
                >
                  {showSecret ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
              </div>
              <Button
                variant="outline"
                onClick={() => secretData && copyToClipboard(secretData.secret)}
              >
                <Copy className="h-4 w-4" />
              </Button>
            </div>
          </div>
          <Button
            variant="outline"
            className="w-full"
            onClick={handleRegenerate}
            disabled={regenerateMutation.isPending}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            {regenerateMutation.isPending ? 'Regenerating...' : 'Regenerate Secret'}
          </Button>
          <p className="text-xs text-muted-foreground">
            Warning: Regenerating the secret will invalidate the current one. You'll
            need to update your webhook handler.
          </p>
        </div>
        <DialogFooter>
          <Button onClick={() => onOpenChange(false)}>Done</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

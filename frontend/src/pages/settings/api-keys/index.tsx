import { useState } from 'react';
import {
  Key,
  Plus,
  Search,
  MoreHorizontal,
  Copy,
  Trash2,
  Ban,
  CheckCircle,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import {
  useAPIKeys,
  useCreateAPIKey,
  useDeleteAPIKey,
  useRevokeAPIKey,
  useActivateAPIKey,
} from '@/hooks/use-webhooks';
import type { APIKey, APIKeyPermission, APIKeyCreateResponse } from '@/types/webhooks';
import { formatDistanceToNow } from 'date-fns';

export default function APIKeysPage() {
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showKeyDialog, setShowKeyDialog] = useState(false);
  const [newKey, setNewKey] = useState<APIKeyCreateResponse | null>(null);
  const [showKey, setShowKey] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    permission: 'read' as APIKeyPermission,
    allowed_ips: '',
    rate_limit_per_minute: 60,
    rate_limit_per_day: 10000,
  });

  const { data: apiKeysData, isLoading } = useAPIKeys({ search });
  const createMutation = useCreateAPIKey();
  const deleteMutation = useDeleteAPIKey();
  const revokeMutation = useRevokeAPIKey();
  const activateMutation = useActivateAPIKey();

  const handleCreate = async () => {
    try {
      const result = await createMutation.mutateAsync(formData);
      setNewKey(result);
      setShowCreateDialog(false);
      setShowKeyDialog(true);
      setFormData({
        name: '',
        description: '',
        permission: 'read',
        allowed_ips: '',
        rate_limit_per_minute: 60,
        rate_limit_per_day: 10000,
      });
      toast({
        title: 'API Key Created',
        description: 'Your new API key has been created successfully.',
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to create API key.',
        variant: 'destructive',
      });
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteMutation.mutateAsync(id);
      setDeleteConfirmId(null);
      toast({
        title: 'API Key Deleted',
        description: 'The API key has been permanently deleted.',
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to delete API key.',
        variant: 'destructive',
      });
    }
  };

  const handleRevoke = async (id: string) => {
    try {
      await revokeMutation.mutateAsync(id);
      toast({
        title: 'API Key Revoked',
        description: 'The API key has been revoked.',
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to revoke API key.',
        variant: 'destructive',
      });
    }
  };

  const handleActivate = async (id: string) => {
    try {
      await activateMutation.mutateAsync(id);
      toast({
        title: 'API Key Activated',
        description: 'The API key has been reactivated.',
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to activate API key.',
        variant: 'destructive',
      });
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: 'Copied',
      description: 'API key copied to clipboard.',
    });
  };

  const getPermissionBadge = (permission: APIKeyPermission) => {
    const variants: Record<APIKeyPermission, 'default' | 'secondary' | 'destructive'> = {
      read: 'secondary',
      write: 'default',
      admin: 'destructive',
    };
    return <Badge variant={variants[permission]}>{permission}</Badge>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">API Keys</h1>
          <p className="text-muted-foreground">
            Manage API keys for external access to your workspace
          </p>
        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create API Key
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search API keys..."
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
                <TableHead>Key Prefix</TableHead>
                <TableHead>Permission</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Used</TableHead>
                <TableHead>Total Requests</TableHead>
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
              ) : apiKeysData?.results.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">
                    <div className="flex flex-col items-center gap-2">
                      <Key className="h-8 w-8 text-muted-foreground" />
                      <p className="text-muted-foreground">No API keys yet</p>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowCreateDialog(true)}
                      >
                        Create your first API key
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                apiKeysData?.results.map((apiKey: APIKey) => (
                  <TableRow key={apiKey.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{apiKey.name}</div>
                        {apiKey.description && (
                          <div className="text-sm text-muted-foreground">
                            {apiKey.description}
                          </div>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <code className="text-sm bg-muted px-2 py-1 rounded">
                        {apiKey.key_prefix}...
                      </code>
                    </TableCell>
                    <TableCell>{getPermissionBadge(apiKey.permission)}</TableCell>
                    <TableCell>
                      {apiKey.is_active ? (
                        apiKey.is_expired ? (
                          <Badge variant="destructive">
                            <AlertCircle className="mr-1 h-3 w-3" />
                            Expired
                          </Badge>
                        ) : (
                          <Badge variant="default">
                            <CheckCircle className="mr-1 h-3 w-3" />
                            Active
                          </Badge>
                        )
                      ) : (
                        <Badge variant="secondary">
                          <Ban className="mr-1 h-3 w-3" />
                          Revoked
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {apiKey.last_used_at
                        ? formatDistanceToNow(new Date(apiKey.last_used_at), {
                            addSuffix: true,
                          })
                        : 'Never'}
                    </TableCell>
                    <TableCell>{apiKey.total_requests.toLocaleString()}</TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          {apiKey.is_active ? (
                            <DropdownMenuItem onClick={() => handleRevoke(apiKey.id)}>
                              <Ban className="mr-2 h-4 w-4" />
                              Revoke
                            </DropdownMenuItem>
                          ) : (
                            <DropdownMenuItem onClick={() => handleActivate(apiKey.id)}>
                              <CheckCircle className="mr-2 h-4 w-4" />
                              Activate
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            className="text-destructive"
                            onClick={() => setDeleteConfirmId(apiKey.id)}
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

      {/* Create API Key Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Create API Key</DialogTitle>
            <DialogDescription>
              Create a new API key for external access to your workspace.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="My API Key"
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
              <Label htmlFor="permission">Permission Level</Label>
              <Select
                value={formData.permission}
                onValueChange={(value: APIKeyPermission) =>
                  setFormData({ ...formData, permission: value })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="read">Read Only</SelectItem>
                  <SelectItem value="write">Read & Write</SelectItem>
                  <SelectItem value="admin">Full Access</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="allowed_ips">Allowed IPs (optional)</Label>
              <Input
                id="allowed_ips"
                value={formData.allowed_ips}
                onChange={(e) =>
                  setFormData({ ...formData, allowed_ips: e.target.value })
                }
                placeholder="192.168.1.1, 10.0.0.0/24"
              />
              <p className="text-xs text-muted-foreground">
                Comma-separated list of IPs. Leave empty to allow all.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="rate_per_minute">Rate Limit (per minute)</Label>
                <Input
                  id="rate_per_minute"
                  type="number"
                  value={formData.rate_limit_per_minute}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      rate_limit_per_minute: parseInt(e.target.value),
                    })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="rate_per_day">Rate Limit (per day)</Label>
                <Input
                  id="rate_per_day"
                  type="number"
                  value={formData.rate_limit_per_day}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      rate_limit_per_day: parseInt(e.target.value),
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
            <Button onClick={handleCreate} disabled={!formData.name || createMutation.isPending}>
              {createMutation.isPending ? 'Creating...' : 'Create API Key'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Show New Key Dialog */}
      <Dialog open={showKeyDialog} onOpenChange={setShowKeyDialog}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>API Key Created</DialogTitle>
            <DialogDescription>
              Make sure to copy your API key now. You won't be able to see it again!
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <div className="flex items-center gap-2 text-amber-800 mb-2">
                <AlertCircle className="h-4 w-4" />
                <span className="font-medium">Save your API key</span>
              </div>
              <p className="text-sm text-amber-700">
                This is the only time you'll see this key. Store it securely.
              </p>
            </div>
            <div className="space-y-2">
              <Label>API Key</Label>
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <Input
                    type={showKey ? 'text' : 'password'}
                    value={newKey?.raw_key || ''}
                    readOnly
                    className="pr-20 font-mono text-sm"
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    className="absolute right-2 top-1/2 -translate-y-1/2"
                    onClick={() => setShowKey(!showKey)}
                  >
                    {showKey ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                <Button
                  variant="outline"
                  onClick={() => newKey && copyToClipboard(newKey.raw_key)}
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={() => setShowKeyDialog(false)}>Done</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteConfirmId !== null}
        onOpenChange={() => setDeleteConfirmId(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete API Key</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this API key? This action cannot be
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

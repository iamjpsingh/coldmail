import { useState } from 'react';
import {
  GitBranch,
  Plus,
  Play,
  Pause,
  Archive,
  Copy,
  Trash2,
  MoreHorizontal,
  Users,
  Mail,
  MousePointerClick,
  MessageSquare,
  ChevronRight,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
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
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  useSequences,
  useCreateSequence,
  useDeleteSequence,
  useActivateSequence,
  usePauseSequence,
  useResumeSequence,
  useArchiveSequence,
  useDuplicateSequence,
} from '@/hooks/use-sequences';
import { useEmailAccounts } from '@/hooks/use-email-accounts';
import type { SequenceListItem, SequenceStatus, CreateSequenceRequest } from '@/types/sequences';

const statusColors: Record<SequenceStatus, string> = {
  draft: 'secondary',
  active: 'default',
  paused: 'outline',
  archived: 'secondary',
};

const statusLabels: Record<SequenceStatus, string> = {
  draft: 'Draft',
  active: 'Active',
  paused: 'Paused',
  archived: 'Archived',
};

function SequenceCard({
  sequence,
  onActivate,
  onPause,
  onResume,
  onArchive,
  onDuplicate,
  onDelete,
}: {
  sequence: SequenceListItem;
  onActivate: (id: string) => void;
  onPause: (id: string) => void;
  onResume: (id: string) => void;
  onArchive: (id: string) => void;
  onDuplicate: (id: string) => void;
  onDelete: (id: string) => void;
}) {
  const completionRate =
    sequence.total_enrolled > 0
      ? Math.round((sequence.completed_count / sequence.total_enrolled) * 100)
      : 0;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <GitBranch className="h-5 w-5 text-primary" />
          </div>
          <div>
            <CardTitle className="text-lg font-semibold">{sequence.name}</CardTitle>
            <p className="text-sm text-muted-foreground">
              {sequence.step_count} step{sequence.step_count !== 1 ? 's' : ''}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant={statusColors[sequence.status] as any}>
            {statusLabels[sequence.status]}
          </Badge>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {sequence.status === 'draft' && (
                <DropdownMenuItem onClick={() => onActivate(sequence.id)}>
                  <Play className="h-4 w-4 mr-2" />
                  Activate
                </DropdownMenuItem>
              )}
              {sequence.status === 'active' && (
                <DropdownMenuItem onClick={() => onPause(sequence.id)}>
                  <Pause className="h-4 w-4 mr-2" />
                  Pause
                </DropdownMenuItem>
              )}
              {sequence.status === 'paused' && (
                <DropdownMenuItem onClick={() => onResume(sequence.id)}>
                  <Play className="h-4 w-4 mr-2" />
                  Resume
                </DropdownMenuItem>
              )}
              <DropdownMenuItem onClick={() => onDuplicate(sequence.id)}>
                <Copy className="h-4 w-4 mr-2" />
                Duplicate
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {sequence.status !== 'archived' && (
                <DropdownMenuItem onClick={() => onArchive(sequence.id)}>
                  <Archive className="h-4 w-4 mr-2" />
                  Archive
                </DropdownMenuItem>
              )}
              <DropdownMenuItem
                onClick={() => onDelete(sequence.id)}
                className="text-destructive"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Stats Grid */}
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
              <Users className="h-4 w-4" />
            </div>
            <p className="text-xl font-bold">{sequence.active_enrolled}</p>
            <p className="text-xs text-muted-foreground">Active</p>
          </div>
          <div>
            <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
              <Mail className="h-4 w-4" />
            </div>
            <p className="text-xl font-bold">{sequence.open_rate}%</p>
            <p className="text-xs text-muted-foreground">Open Rate</p>
          </div>
          <div>
            <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
              <MousePointerClick className="h-4 w-4" />
            </div>
            <p className="text-xl font-bold">{sequence.click_rate}%</p>
            <p className="text-xs text-muted-foreground">Click Rate</p>
          </div>
          <div>
            <div className="flex items-center justify-center gap-1 text-muted-foreground mb-1">
              <MessageSquare className="h-4 w-4" />
            </div>
            <p className="text-xl font-bold">{sequence.reply_rate}%</p>
            <p className="text-xs text-muted-foreground">Reply Rate</p>
          </div>
        </div>

        {/* Completion Progress */}
        <div className="space-y-1">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Completion</span>
            <span>
              {sequence.completed_count} / {sequence.total_enrolled} ({completionRate}%)
            </span>
          </div>
          <Progress value={completionRate} />
        </div>

        {/* Description */}
        {sequence.description && (
          <p className="text-sm text-muted-foreground line-clamp-2">
            {sequence.description}
          </p>
        )}

        {/* View Details Button */}
        <Button variant="outline" className="w-full" size="sm">
          View Details
          <ChevronRight className="h-4 w-4 ml-2" />
        </Button>
      </CardContent>
    </Card>
  );
}

export default function SequencesPage() {
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newSequence, setNewSequence] = useState<CreateSequenceRequest>({
    name: '',
    description: '',
    stop_on_reply: true,
    stop_on_unsubscribe: true,
    stop_on_bounce: true,
    track_opens: true,
    track_clicks: true,
    include_unsubscribe_link: true,
  });

  const { data: sequences, isLoading } = useSequences();
  const { data: emailAccounts } = useEmailAccounts();
  const createSequence = useCreateSequence();
  const deleteSequence = useDeleteSequence();
  const activateSequence = useActivateSequence();
  const pauseSequence = usePauseSequence();
  const resumeSequence = useResumeSequence();
  const archiveSequence = useArchiveSequence();
  const duplicateSequence = useDuplicateSequence();

  const handleCreate = () => {
    createSequence.mutate(newSequence, {
      onSuccess: () => {
        setIsCreateOpen(false);
        setNewSequence({
          name: '',
          description: '',
          stop_on_reply: true,
          stop_on_unsubscribe: true,
          stop_on_bounce: true,
          track_opens: true,
          track_clicks: true,
          include_unsubscribe_link: true,
        });
      },
    });
  };

  const activeSequences = sequences?.filter((s) => s.status === 'active') ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Sequences</h1>
          <p className="text-muted-foreground">
            Automate your email follow-ups with multi-step sequences
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          Create Sequence
        </Button>
      </div>

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Sequences</p>
                <p className="text-2xl font-bold">{sequences?.length ?? 0}</p>
              </div>
              <GitBranch className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active</p>
                <p className="text-2xl font-bold text-green-600">
                  {activeSequences.length}
                </p>
              </div>
              <Play className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Enrolled</p>
                <p className="text-2xl font-bold">
                  {sequences?.reduce((sum, s) => sum + s.total_enrolled, 0) ?? 0}
                </p>
              </div>
              <Users className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Emails Sent</p>
                <p className="text-2xl font-bold">
                  {sequences?.reduce((sum, s) => sum + s.total_sent, 0) ?? 0}
                </p>
              </div>
              <Mail className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sequences Grid */}
      {isLoading ? (
        <div className="text-center py-8 text-muted-foreground">
          Loading sequences...
        </div>
      ) : sequences?.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <GitBranch className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No sequences yet</h3>
            <p className="text-muted-foreground mb-4">
              Create your first sequence to automate email follow-ups
            </p>
            <Button onClick={() => setIsCreateOpen(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Sequence
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {sequences?.map((sequence) => (
            <SequenceCard
              key={sequence.id}
              sequence={sequence}
              onActivate={(id) => activateSequence.mutate(id)}
              onPause={(id) => pauseSequence.mutate(id)}
              onResume={(id) => resumeSequence.mutate(id)}
              onArchive={(id) => archiveSequence.mutate(id)}
              onDuplicate={(id) => duplicateSequence.mutate(id)}
              onDelete={(id) => deleteSequence.mutate(id)}
            />
          ))}
        </div>
      )}

      {/* Create Sequence Dialog */}
      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Create New Sequence</DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label htmlFor="name">Sequence Name</Label>
              <Input
                id="name"
                value={newSequence.name}
                onChange={(e) =>
                  setNewSequence({ ...newSequence, name: e.target.value })
                }
                placeholder="e.g., Cold Outreach Follow-up"
              />
            </div>

            <div>
              <Label htmlFor="description">Description (optional)</Label>
              <Textarea
                id="description"
                value={newSequence.description}
                onChange={(e) =>
                  setNewSequence({ ...newSequence, description: e.target.value })
                }
                placeholder="Describe what this sequence does..."
                rows={2}
              />
            </div>

            <div>
              <Label htmlFor="email_account">Email Account</Label>
              <Select
                value={newSequence.email_account}
                onValueChange={(v) =>
                  setNewSequence({ ...newSequence, email_account: v })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select email account" />
                </SelectTrigger>
                <SelectContent>
                  {emailAccounts?.map((account) => (
                    <SelectItem key={account.id} value={account.id}>
                      {account.email}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-3">
              <Label>Stop Conditions</Label>
              <div className="flex items-center justify-between">
                <span className="text-sm">Stop on reply</span>
                <Switch
                  checked={newSequence.stop_on_reply}
                  onCheckedChange={(v) =>
                    setNewSequence({ ...newSequence, stop_on_reply: v })
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Stop on unsubscribe</span>
                <Switch
                  checked={newSequence.stop_on_unsubscribe}
                  onCheckedChange={(v) =>
                    setNewSequence({ ...newSequence, stop_on_unsubscribe: v })
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Stop on bounce</span>
                <Switch
                  checked={newSequence.stop_on_bounce}
                  onCheckedChange={(v) =>
                    setNewSequence({ ...newSequence, stop_on_bounce: v })
                  }
                />
              </div>
            </div>

            <div className="space-y-3">
              <Label>Tracking</Label>
              <div className="flex items-center justify-between">
                <span className="text-sm">Track opens</span>
                <Switch
                  checked={newSequence.track_opens}
                  onCheckedChange={(v) =>
                    setNewSequence({ ...newSequence, track_opens: v })
                  }
                />
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Track clicks</span>
                <Switch
                  checked={newSequence.track_clicks}
                  onCheckedChange={(v) =>
                    setNewSequence({ ...newSequence, track_clicks: v })
                  }
                />
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!newSequence.name || createSequence.isPending}
            >
              {createSequence.isPending ? 'Creating...' : 'Create Sequence'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

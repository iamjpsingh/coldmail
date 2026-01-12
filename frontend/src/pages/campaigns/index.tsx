import { useState } from 'react';
import {
  Plus,
  Search,
  Send,
  Clock,
  Pause,
  CheckCircle,
  XCircle,
  MoreHorizontal,
  Play,
  Copy,
  Trash2,
  Eye,
  BarChart3,
  RefreshCw,
  Mail,
  MousePointerClick,
  Reply,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { StatCard, StatGrid } from '@/components/ui/stat-card';
import { EmptyStateCard } from '@/components/ui/empty-state';
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog';
import { useToast } from '@/hooks/use-toast';
import {
  useCampaigns,
  useCampaignSummary,
  useDeleteCampaign,
  useStartCampaign,
  usePauseCampaign,
  useResumeCampaign,
  useCancelCampaign,
  useDuplicateCampaign,
} from '@/hooks/use-campaigns';
import { AddCampaignDialog } from './components/add-campaign-dialog';
import { CampaignDetailDialog } from './components/campaign-detail-dialog';
import { formatDateTime } from '@/lib/utils';
import type { CampaignListItem, CampaignStatus } from '@/types/campaign';

const statusConfig: Record<
  CampaignStatus,
  { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ElementType; color: string }
> = {
  draft: { label: 'Draft', variant: 'secondary', icon: Clock, color: 'text-slate-500' },
  scheduled: { label: 'Scheduled', variant: 'outline', icon: Clock, color: 'text-blue-500' },
  sending: { label: 'Sending', variant: 'default', icon: Send, color: 'text-primary' },
  paused: { label: 'Paused', variant: 'outline', icon: Pause, color: 'text-amber-500' },
  completed: { label: 'Completed', variant: 'secondary', icon: CheckCircle, color: 'text-green-500' },
  cancelled: { label: 'Cancelled', variant: 'destructive', icon: XCircle, color: 'text-red-500' },
};

export default function CampaignsPage() {
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [selectedCampaignId, setSelectedCampaignId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<CampaignListItem | null>(null);

  const { data: summary } = useCampaignSummary();
  const { data: campaigns, isLoading } = useCampaigns({
    status: statusFilter === 'all' ? undefined : statusFilter,
    search: search || undefined,
  });

  const deleteMutation = useDeleteCampaign();
  const startMutation = useStartCampaign();
  const pauseMutation = usePauseCampaign();
  const resumeMutation = useResumeCampaign();
  const cancelMutation = useCancelCampaign();
  const duplicateMutation = useDuplicateCampaign();

  const handleAction = async (action: string, campaign: CampaignListItem) => {
    try {
      switch (action) {
        case 'start':
          await startMutation.mutateAsync(campaign.id);
          toast({
            title: 'Campaign Started',
            description: `"${campaign.name}" is now sending.`,
          });
          break;
        case 'pause':
          await pauseMutation.mutateAsync(campaign.id);
          toast({
            title: 'Campaign Paused',
            description: `"${campaign.name}" has been paused.`,
          });
          break;
        case 'resume':
          await resumeMutation.mutateAsync(campaign.id);
          toast({
            title: 'Campaign Resumed',
            description: `"${campaign.name}" is now sending again.`,
          });
          break;
        case 'cancel':
          await cancelMutation.mutateAsync(campaign.id);
          toast({
            title: 'Campaign Cancelled',
            description: `"${campaign.name}" has been cancelled.`,
          });
          break;
        case 'duplicate':
          await duplicateMutation.mutateAsync({ id: campaign.id });
          toast({
            title: 'Campaign Duplicated',
            description: `A copy of "${campaign.name}" has been created.`,
          });
          break;
        case 'delete':
          setDeleteTarget(campaign);
          break;
      }
    } catch {
      toast({
        title: 'Action Failed',
        description: 'Something went wrong. Please try again.',
        variant: 'destructive',
      });
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteMutation.mutateAsync(deleteTarget.id);
      toast({
        title: 'Campaign Deleted',
        description: `"${deleteTarget.name}" has been deleted.`,
      });
      setDeleteTarget(null);
    } catch {
      toast({
        title: 'Delete Failed',
        description: 'Could not delete the campaign. Please try again.',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Campaigns</h1>
          <p className="text-muted-foreground mt-1">
            Create and manage your email campaigns
          </p>
        </div>
        <Button onClick={() => setShowAddDialog(true)} size="lg">
          <Plus className="h-4 w-4 mr-2" />
          Create Campaign
        </Button>
      </div>

      {/* Stats Cards */}
      <StatGrid columns={4}>
        <StatCard
          label="Total Campaigns"
          value={summary?.total || 0}
          icon={Send}
          description={`${summary?.sending || 0} sending, ${summary?.scheduled || 0} scheduled`}
          variant="primary"
        />
        <StatCard
          label="Emails Sent"
          value={summary?.total_emails_sent || 0}
          icon={Mail}
          description="Across all campaigns"
        />
        <StatCard
          label="Total Opens"
          value={summary?.total_opens || 0}
          icon={MousePointerClick}
          description="Unique email opens"
          variant="success"
        />
        <StatCard
          label="Total Replies"
          value={summary?.total_replies || 0}
          icon={Reply}
          description="Responses received"
          variant="primary"
        />
      </StatGrid>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search campaigns..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>

        <Tabs value={statusFilter} onValueChange={setStatusFilter}>
          <TabsList>
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="draft">Draft</TabsTrigger>
            <TabsTrigger value="scheduled">Scheduled</TabsTrigger>
            <TabsTrigger value="sending">Sending</TabsTrigger>
            <TabsTrigger value="completed">Completed</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Campaigns List */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : campaigns && campaigns.length > 0 ? (
        <div className="space-y-3">
          {campaigns.map((campaign) => (
            <CampaignCard
              key={campaign.id}
              campaign={campaign}
              onAction={handleAction}
              onView={() => setSelectedCampaignId(campaign.id)}
            />
          ))}
        </div>
      ) : (
        <EmptyStateCard
          icon={Send}
          title="No campaigns yet"
          description="Create your first email campaign to start reaching your contacts."
          action={
            <Button onClick={() => setShowAddDialog(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create Campaign
            </Button>
          }
        />
      )}

      {/* Dialogs */}
      <AddCampaignDialog open={showAddDialog} onOpenChange={setShowAddDialog} />

      {selectedCampaignId && (
        <CampaignDetailDialog
          campaignId={selectedCampaignId}
          open={!!selectedCampaignId}
          onOpenChange={(open) => !open && setSelectedCampaignId(null)}
        />
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmationDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
        title="Delete Campaign"
        description={`Are you sure you want to delete "${deleteTarget?.name}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={handleDelete}
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}

interface CampaignCardProps {
  campaign: CampaignListItem;
  onAction: (action: string, campaign: CampaignListItem) => void;
  onView: () => void;
}

function CampaignCard({ campaign, onAction, onView }: CampaignCardProps) {
  const config = statusConfig[campaign.status];
  const StatusIcon = config.icon;

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 flex-1">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-medium truncate">{campaign.name}</h3>
                <Badge variant={config.variant} className="shrink-0">
                  <StatusIcon className="h-3 w-3 mr-1" />
                  {config.label}
                </Badge>
                {campaign.is_ab_test && (
                  <Badge variant="outline" className="shrink-0">
                    A/B Test
                  </Badge>
                )}
              </div>
              <div className="text-sm text-muted-foreground">
                {campaign.email_account_email || 'No sender selected'}
              </div>
            </div>

            <div className="hidden md:flex items-center gap-6 text-sm">
              <div className="text-center">
                <div className="font-medium">{campaign.total_recipients}</div>
                <div className="text-muted-foreground text-xs">Recipients</div>
              </div>
              <div className="text-center">
                <div className="font-medium">{campaign.sent_count}</div>
                <div className="text-muted-foreground text-xs">Sent</div>
              </div>
              <div className="text-center">
                <div className="font-medium">{campaign.open_rate}%</div>
                <div className="text-muted-foreground text-xs">Open Rate</div>
              </div>
              <div className="text-center">
                <div className="font-medium">{campaign.click_rate}%</div>
                <div className="text-muted-foreground text-xs">Click Rate</div>
              </div>
            </div>

            {campaign.status === 'sending' && (
              <div className="hidden lg:block w-32">
                <div className="h-2 bg-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary transition-all"
                    style={{ width: `${campaign.progress_percentage}%` }}
                  />
                </div>
                <div className="text-xs text-muted-foreground text-center mt-1">
                  {campaign.progress_percentage}%
                </div>
              </div>
            )}

            <div className="hidden lg:block text-sm text-muted-foreground w-36 text-right">
              {campaign.status === 'scheduled' && campaign.scheduled_at
                ? `Scheduled: ${formatDateTime(campaign.scheduled_at)}`
                : campaign.status === 'completed' && campaign.completed_at
                  ? `Completed: ${formatDateTime(campaign.completed_at)}`
                  : campaign.status === 'sending' && campaign.started_at
                    ? `Started: ${formatDateTime(campaign.started_at)}`
                    : `Created: ${formatDateTime(campaign.created_at)}`}
            </div>
          </div>

          <div className="flex items-center gap-2 ml-4">
            <Button variant="ghost" size="icon" onClick={onView}>
              <Eye className="h-4 w-4" />
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={onView}>
                  <BarChart3 className="h-4 w-4 mr-2" />
                  View Details
                </DropdownMenuItem>

                {campaign.status === 'draft' && (
                  <DropdownMenuItem onClick={() => onAction('start', campaign)}>
                    <Play className="h-4 w-4 mr-2" />
                    Start Campaign
                  </DropdownMenuItem>
                )}

                {campaign.status === 'scheduled' && (
                  <DropdownMenuItem onClick={() => onAction('start', campaign)}>
                    <Play className="h-4 w-4 mr-2" />
                    Start Now
                  </DropdownMenuItem>
                )}

                {campaign.status === 'sending' && (
                  <DropdownMenuItem onClick={() => onAction('pause', campaign)}>
                    <Pause className="h-4 w-4 mr-2" />
                    Pause
                  </DropdownMenuItem>
                )}

                {campaign.status === 'paused' && (
                  <DropdownMenuItem onClick={() => onAction('resume', campaign)}>
                    <Play className="h-4 w-4 mr-2" />
                    Resume
                  </DropdownMenuItem>
                )}

                {['sending', 'paused', 'scheduled'].includes(campaign.status) && (
                  <DropdownMenuItem
                    onClick={() => onAction('cancel', campaign)}
                    className="text-destructive"
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    Cancel
                  </DropdownMenuItem>
                )}

                <DropdownMenuSeparator />

                <DropdownMenuItem onClick={() => onAction('duplicate', campaign)}>
                  <Copy className="h-4 w-4 mr-2" />
                  Duplicate
                </DropdownMenuItem>

                {campaign.status === 'draft' && (
                  <DropdownMenuItem
                    onClick={() => onAction('delete', campaign)}
                    className="text-destructive"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

import { RefreshCw, Mail, Users, MousePointer, Reply, AlertTriangle } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import {
  useCampaign,
  useCampaignStats,
  useCampaignRecipients,
  useCampaignLogs,
} from '@/hooks/use-campaigns';
import type { CampaignStatus, RecipientStatus } from '@/types/campaign';

interface CampaignDetailDialogProps {
  campaignId: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const statusConfig: Record<CampaignStatus, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
  draft: { label: 'Draft', variant: 'secondary' },
  scheduled: { label: 'Scheduled', variant: 'outline' },
  sending: { label: 'Sending', variant: 'default' },
  paused: { label: 'Paused', variant: 'outline' },
  completed: { label: 'Completed', variant: 'secondary' },
  cancelled: { label: 'Cancelled', variant: 'destructive' },
};

const recipientStatusColors: Record<RecipientStatus, string> = {
  pending: 'bg-gray-100 text-gray-800',
  queued: 'bg-blue-100 text-blue-800',
  sending: 'bg-yellow-100 text-yellow-800',
  sent: 'bg-green-100 text-green-800',
  delivered: 'bg-green-100 text-green-800',
  opened: 'bg-emerald-100 text-emerald-800',
  clicked: 'bg-teal-100 text-teal-800',
  replied: 'bg-cyan-100 text-cyan-800',
  bounced: 'bg-red-100 text-red-800',
  failed: 'bg-red-100 text-red-800',
  unsubscribed: 'bg-orange-100 text-orange-800',
  complained: 'bg-red-100 text-red-800',
  skipped: 'bg-gray-100 text-gray-800',
};

export function CampaignDetailDialog({
  campaignId,
  open,
  onOpenChange,
}: CampaignDetailDialogProps) {
  const { data: campaign, isLoading: campaignLoading } = useCampaign(campaignId);
  const { data: stats } = useCampaignStats(campaignId);
  const { data: recipients } = useCampaignRecipients(campaignId);
  const { data: logs } = useCampaignLogs(campaignId);

  if (campaignLoading || !campaign) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl">
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  const config = statusConfig[campaign.status];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <div>
              <DialogTitle className="flex items-center gap-2">
                {campaign.name}
                <Badge variant={config.variant}>{config.label}</Badge>
                {campaign.is_ab_test && (
                  <Badge variant="outline">A/B Test</Badge>
                )}
              </DialogTitle>
              <p className="text-sm text-muted-foreground mt-1">
                {campaign.email_account_email}
              </p>
            </div>
          </div>
        </DialogHeader>

        <Tabs defaultValue="overview" className="mt-4">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="recipients">Recipients</TabsTrigger>
            <TabsTrigger value="content">Content</TabsTrigger>
            <TabsTrigger value="activity">Activity</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-4">
            {/* Progress (for sending campaigns) */}
            {campaign.status === 'sending' && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Sending Progress</CardTitle>
                </CardHeader>
                <CardContent>
                  <Progress value={campaign.progress_percentage} className="h-3" />
                  <div className="flex justify-between text-sm text-muted-foreground mt-2">
                    <span>{campaign.sent_count} sent</span>
                    <span>{campaign.total_recipients} total</span>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-4">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Recipients</span>
                  </div>
                  <div className="text-2xl font-bold mt-1">
                    {stats?.total_recipients || campaign.total_recipients}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-4">
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Sent</span>
                  </div>
                  <div className="text-2xl font-bold mt-1">
                    {stats?.sent || campaign.sent_count}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-4">
                  <div className="flex items-center gap-2">
                    <MousePointer className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Open Rate</span>
                  </div>
                  <div className="text-2xl font-bold mt-1">
                    {stats?.open_rate || campaign.open_rate}%
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {stats?.unique_opens || campaign.unique_opens} unique opens
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-4">
                  <div className="flex items-center gap-2">
                    <Reply className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Click Rate</span>
                  </div>
                  <div className="text-2xl font-bold mt-1">
                    {stats?.click_rate || campaign.click_rate}%
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {stats?.unique_clicks || campaign.unique_clicks} unique clicks
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Additional Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm text-muted-foreground">Replied</div>
                  <div className="text-xl font-medium">
                    {stats?.replied || campaign.replied_count}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm text-muted-foreground">Bounced</div>
                  <div className="text-xl font-medium text-orange-600">
                    {stats?.bounced || campaign.bounced_count}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm text-muted-foreground">Unsubscribed</div>
                  <div className="text-xl font-medium text-orange-600">
                    {stats?.unsubscribed || campaign.unsubscribed_count}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-4">
                  <div className="text-sm text-muted-foreground">Failed</div>
                  <div className="text-xl font-medium text-red-600">
                    {stats?.failed || campaign.failed_count}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* A/B Test Results */}
            {campaign.is_ab_test && campaign.ab_variants.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">A/B Test Variants</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {campaign.ab_variants.map((variant) => (
                      <div
                        key={variant.id}
                        className={`p-4 rounded-lg border ${
                          variant.is_winner ? 'border-green-500 bg-green-50' : ''
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{variant.name}</span>
                            {variant.is_winner && (
                              <Badge variant="default">Winner</Badge>
                            )}
                            {variant.is_control && (
                              <Badge variant="outline">Control</Badge>
                            )}
                          </div>
                          <span className="text-sm text-muted-foreground">
                            {variant.sent_count} sent
                          </span>
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <span className="text-muted-foreground">Open Rate:</span>{' '}
                            <span className="font-medium">{variant.open_rate}%</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Click Rate:</span>{' '}
                            <span className="font-medium">{variant.click_rate}%</span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Replies:</span>{' '}
                            <span className="font-medium">{variant.replied_count}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Recipients Tab */}
          <TabsContent value="recipients">
            <Card>
              <CardContent className="pt-4">
                {recipients && recipients.length > 0 ? (
                  <div className="space-y-2">
                    {recipients.map((recipient) => (
                      <div
                        key={recipient.id}
                        className="flex items-center justify-between p-3 rounded-lg border"
                      >
                        <div>
                          <div className="font-medium">{recipient.contact_email}</div>
                          <div className="text-sm text-muted-foreground">
                            {recipient.contact_name}
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          {recipient.ab_variant_name && (
                            <span className="text-sm text-muted-foreground">
                              {recipient.ab_variant_name}
                            </span>
                          )}
                          <Badge
                            className={recipientStatusColors[recipient.status]}
                            variant="secondary"
                          >
                            {recipient.status}
                          </Badge>
                          {recipient.last_error && (
                            <AlertTriangle className="h-4 w-4 text-red-500" />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    No recipients yet
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Content Tab */}
          <TabsContent value="content">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Subject</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-medium">{campaign.subject}</p>
              </CardContent>
            </Card>

            <Card className="mt-4">
              <CardHeader>
                <CardTitle className="text-sm">Email Content</CardTitle>
              </CardHeader>
              <CardContent>
                <div
                  className="prose prose-sm max-w-none"
                  dangerouslySetInnerHTML={{ __html: campaign.content_html }}
                />
              </CardContent>
            </Card>
          </TabsContent>

          {/* Activity Tab */}
          <TabsContent value="activity">
            <Card>
              <CardContent className="pt-4">
                {logs && logs.length > 0 ? (
                  <div className="space-y-3">
                    {logs.map((log) => (
                      <div
                        key={log.id}
                        className="flex items-start gap-3 p-3 rounded-lg border"
                      >
                        <div className="flex-1">
                          <div className="font-medium">{log.message}</div>
                          <div className="text-sm text-muted-foreground">
                            {new Date(log.created_at).toLocaleString()}
                            {log.created_by_name && ` by ${log.created_by_name}`}
                          </div>
                        </div>
                        <Badge variant="outline">{log.log_type}</Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    No activity yet
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}

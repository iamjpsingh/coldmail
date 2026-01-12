import { useState } from 'react';
import {
  BarChart3,
  MousePointerClick,
  Mail,
  UserMinus,
  AlertTriangle,
  ShieldX,
  Bot,
  Monitor,
  Smartphone,
  Tablet,
  Globe,
  Chrome,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  useTrackingStats,
  useTrackingEvents,
  useDeviceBreakdown,
  useLocationBreakdown,
  useBrowserBreakdown,
  useBounceStats,
  useSuppressionStats,
} from '@/hooks/use-tracking';
import { useCampaigns } from '@/hooks/use-campaigns';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

function StatCard({
  title,
  value,
  subValue,
  icon: Icon,
}: {
  title: string;
  value: number;
  subValue?: string;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value.toLocaleString()}</div>
        {subValue && (
          <p className="text-xs text-muted-foreground">{subValue}</p>
        )}
      </CardContent>
    </Card>
  );
}

function DeviceIcon({ type }: { type: string }) {
  switch (type.toLowerCase()) {
    case 'mobile':
      return <Smartphone className="h-4 w-4" />;
    case 'tablet':
      return <Tablet className="h-4 w-4" />;
    default:
      return <Monitor className="h-4 w-4" />;
  }
}

export default function AnalyticsPage() {
  const [selectedCampaignId, setSelectedCampaignId] = useState<string | undefined>();

  const { data: campaigns } = useCampaigns();
  const { data: stats } = useTrackingStats(selectedCampaignId);
  const { data: events } = useTrackingEvents({
    campaign_id: selectedCampaignId,
    exclude_bots: true,
  });
  const { data: deviceBreakdown } = useDeviceBreakdown(selectedCampaignId);
  const { data: locationBreakdown } = useLocationBreakdown(selectedCampaignId);
  const { data: browserBreakdown } = useBrowserBreakdown(selectedCampaignId);
  const { data: bounceStats } = useBounceStats();
  const { data: suppressionStats } = useSuppressionStats();

  // Calculate rates
  const openRate = stats && stats.unique_opens > 0
    ? ((stats.unique_opens / (stats.unique_opens + stats.total_bounces)) * 100).toFixed(1)
    : '0.0';

  const clickRate = stats && stats.unique_clicks > 0 && stats.unique_opens > 0
    ? ((stats.unique_clicks / stats.unique_opens) * 100).toFixed(1)
    : '0.0';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics</h1>
          <p className="text-muted-foreground">
            Track email engagement and campaign performance
          </p>
        </div>

        {/* Campaign Filter */}
        <Select
          value={selectedCampaignId || 'all'}
          onValueChange={(value) =>
            setSelectedCampaignId(value === 'all' ? undefined : value)
          }
        >
          <SelectTrigger className="w-[250px]">
            <SelectValue placeholder="All Campaigns" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Campaigns</SelectItem>
            {campaigns?.map((campaign) => (
              <SelectItem key={campaign.id} value={campaign.id}>
                {campaign.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Unique Opens"
          value={stats?.unique_opens ?? 0}
          subValue={`${openRate}% open rate`}
          icon={Mail}
        />
        <StatCard
          title="Unique Clicks"
          value={stats?.unique_clicks ?? 0}
          subValue={`${clickRate}% click rate`}
          icon={MousePointerClick}
        />
        <StatCard
          title="Unsubscribes"
          value={stats?.total_unsubscribes ?? 0}
          icon={UserMinus}
        />
        <StatCard
          title="Bounces"
          value={stats?.total_bounces ?? 0}
          subValue={`${stats?.hard_bounces ?? 0} hard, ${stats?.soft_bounces ?? 0} soft`}
          icon={AlertTriangle}
        />
      </div>

      {/* Secondary Stats */}
      <div className="grid gap-4 md:grid-cols-3">
        <StatCard
          title="Bot Opens Filtered"
          value={stats?.bot_opens ?? 0}
          icon={Bot}
        />
        <StatCard
          title="Bot Clicks Filtered"
          value={stats?.bot_clicks ?? 0}
          icon={Bot}
        />
        <StatCard
          title="Suppressed Emails"
          value={stats?.suppressed_count ?? 0}
          icon={ShieldX}
        />
      </div>

      {/* Charts Row */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Device Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Monitor className="h-5 w-5" />
              Device Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {deviceBreakdown?.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                No data available
              </p>
            ) : (
              deviceBreakdown?.map((item) => (
                <div key={item.device_type} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <DeviceIcon type={item.device_type} />
                      <span className="capitalize">{item.device_type}</span>
                    </div>
                    <span className="text-muted-foreground">
                      {item.count} ({item.percentage}%)
                    </span>
                  </div>
                  <Progress value={item.percentage} className="h-2" />
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Browser Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Chrome className="h-5 w-5" />
              Browser Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {browserBreakdown?.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                No data available
              </p>
            ) : (
              browserBreakdown?.slice(0, 5).map((item) => (
                <div key={item.browser_name} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>{item.browser_name}</span>
                    <span className="text-muted-foreground">
                      {item.count} ({item.percentage}%)
                    </span>
                  </div>
                  <Progress value={item.percentage} className="h-2" />
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Location Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="h-5 w-5" />
              Top Locations
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {locationBreakdown?.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                No data available
              </p>
            ) : (
              locationBreakdown?.slice(0, 5).map((item) => (
                <div key={item.country_code} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>{item.country}</span>
                    <span className="text-muted-foreground">
                      {item.count} ({item.percentage}%)
                    </span>
                  </div>
                  <Progress value={item.percentage} className="h-2" />
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Events Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Recent Events
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead>Campaign</TableHead>
                <TableHead>Device</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Time</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {events?.slice(0, 10).map((event) => (
                <TableRow key={event.id}>
                  <TableCell>
                    <Badge
                      variant={
                        event.event_type === 'click'
                          ? 'default'
                          : event.event_type === 'open'
                          ? 'secondary'
                          : event.event_type === 'unsubscribe'
                          ? 'destructive'
                          : 'outline'
                      }
                    >
                      {event.event_type}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-medium">
                    {event.contact_email}
                  </TableCell>
                  <TableCell>{event.campaign_name}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <DeviceIcon type={event.device_type} />
                      <span className="text-sm text-muted-foreground">
                        {event.browser_name}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    {event.city && event.country
                      ? `${event.city}, ${event.country}`
                      : event.country || '-'}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {new Date(event.created_at).toLocaleString()}
                  </TableCell>
                </TableRow>
              ))}
              {events?.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                    No events recorded yet
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Deliverability Section */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Bounce Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Bounce Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span>Hard Bounces</span>
                <Badge variant="destructive">{bounceStats?.hard ?? 0}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>Soft Bounces</span>
                <Badge variant="secondary">{bounceStats?.soft ?? 0}</Badge>
              </div>
              {(bounceStats?.by_category?.length ?? 0) > 0 && (
                <div className="pt-4 border-t">
                  <p className="text-sm font-medium mb-2">By Category</p>
                  <div className="space-y-2">
                    {bounceStats?.by_category?.map((cat) => (
                      <div
                        key={cat.bounce_category}
                        className="flex items-center justify-between text-sm"
                      >
                        <span className="capitalize">
                          {cat.bounce_category.replace('_', ' ')}
                        </span>
                        <span className="text-muted-foreground">{cat.count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Suppression Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldX className="h-5 w-5" />
              Suppression List
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span>Total Suppressed</span>
                <Badge>{suppressionStats?.total ?? 0}</Badge>
              </div>
              {(suppressionStats?.by_reason?.length ?? 0) > 0 && (
                <div className="pt-4 border-t">
                  <p className="text-sm font-medium mb-2">By Reason</p>
                  <div className="space-y-2">
                    {suppressionStats?.by_reason?.map((reason) => (
                      <div
                        key={reason.reason}
                        className="flex items-center justify-between text-sm"
                      >
                        <span className="capitalize">
                          {reason.reason.replace('_', ' ')}
                        </span>
                        <span className="text-muted-foreground">{reason.count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

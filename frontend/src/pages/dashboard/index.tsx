import { useState } from 'react';
import {
  Users,
  Send,
  Mail,
  MousePointerClick,
  MessageSquare,
  TrendingUp,
  TrendingDown,
  Minus,
  Flame,
  Activity,
  BarChart3,
  Download,
  Calendar,
  ArrowUpRight,
  Loader2,
  Target,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { StatCard, StatGrid } from '@/components/ui/stat-card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  useDashboardStats,
  usePerformanceSummary,
  useActivityTimeline,
  useHotLeadsReport,
  useExportHotLeads,
} from '@/hooks/use-reports';
import { Link } from 'react-router-dom';

export default function DashboardPage() {
  const [periodDays, setPeriodDays] = useState(30);

  const { data: stats, isLoading: statsLoading } = useDashboardStats(periodDays);
  const { data: performance } = usePerformanceSummary(7);
  const { data: activity, isLoading: activityLoading } = useActivityTimeline({ limit: 10 });
  const { data: hotLeads, isLoading: leadsLoading } = useHotLeadsReport({ limit: 5 });
  const exportHotLeads = useExportHotLeads();

  const handleExportHotLeads = () => {
    exportHotLeads.mutate(70);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Track your email marketing performance at a glance
          </p>
        </div>

        {/* Period Selector */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Calendar className="h-4 w-4" />
            <span>Period:</span>
          </div>
          <Select
            value={periodDays.toString()}
            onValueChange={(value) => setPeriodDays(Number(value))}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Select period" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">Last 7 days</SelectItem>
              <SelectItem value="14">Last 14 days</SelectItem>
              <SelectItem value="30">Last 30 days</SelectItem>
              <SelectItem value="90">Last 90 days</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Main Stats Grid */}
      <StatGrid columns={4}>
        <StatCard
          label="Total Contacts"
          value={stats?.contacts.total ?? 0}
          icon={Users}
          description={`${stats?.contacts.new ?? 0} new this period`}
          variant="primary"
        />
        <StatCard
          label="Emails Sent"
          value={stats?.emails.sent ?? 0}
          icon={Send}
          trend={performance?.changes.emails_sent}
          trendPeriod="vs last period"
        />
        <StatCard
          label="Open Rate"
          value={`${stats?.rates.open_rate ?? 0}%`}
          formatValue={false}
          icon={Mail}
          trend={performance?.changes.open_rate}
          trendPeriod="vs last period"
          variant="success"
        />
        <StatCard
          label="Click Rate"
          value={`${stats?.rates.click_rate ?? 0}%`}
          formatValue={false}
          icon={MousePointerClick}
          trend={performance?.changes.click_rate}
          trendPeriod="vs last period"
        />
      </StatGrid>

      {/* Secondary Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 via-transparent to-transparent" />
          <CardContent className="relative pt-5 pb-4">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <p className="text-sm font-medium text-muted-foreground">Hot Leads</p>
                <p className="text-3xl font-bold tracking-tight">{stats?.contacts.hot_leads ?? 0}</p>
                <p className="text-sm text-muted-foreground">Ready to engage</p>
              </div>
              <div className="rounded-xl p-2.5 text-orange-600 bg-orange-500/10">
                <Flame className="h-5 w-5" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-transparent" />
          <CardContent className="relative pt-5 pb-4">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <p className="text-sm font-medium text-muted-foreground">Replies</p>
                <p className="text-3xl font-bold tracking-tight">{stats?.emails.replied ?? 0}</p>
                {performance?.changes.replies !== undefined && (
                  <div className="flex items-center gap-1 text-sm">
                    {performance.changes.replies > 0 ? (
                      <span className="flex items-center text-green-600">
                        <TrendingUp className="h-3.5 w-3.5 mr-1" />
                        +{performance.changes.replies}%
                      </span>
                    ) : performance.changes.replies < 0 ? (
                      <span className="flex items-center text-red-600">
                        <TrendingDown className="h-3.5 w-3.5 mr-1" />
                        {performance.changes.replies}%
                      </span>
                    ) : (
                      <span className="text-muted-foreground">No change</span>
                    )}
                  </div>
                )}
              </div>
              <div className="rounded-xl p-2.5 text-blue-600 bg-blue-500/10">
                <MessageSquare className="h-5 w-5" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-transparent to-transparent" />
          <CardContent className="relative pt-5 pb-4">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <p className="text-sm font-medium text-muted-foreground">Active Campaigns</p>
                <p className="text-3xl font-bold tracking-tight">{stats?.campaigns.active ?? 0}</p>
                <p className="text-sm text-muted-foreground">Currently running</p>
              </div>
              <div className="rounded-xl p-2.5 text-purple-600 bg-purple-500/10">
                <BarChart3 className="h-5 w-5" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-teal-500/5 via-transparent to-transparent" />
          <CardContent className="relative pt-5 pb-4">
            <div className="flex items-start justify-between">
              <div className="space-y-2">
                <p className="text-sm font-medium text-muted-foreground">Avg Lead Score</p>
                <p className="text-3xl font-bold tracking-tight">{stats?.contacts.avg_score ?? 0}</p>
                <p className="text-sm text-muted-foreground">Out of 100</p>
              </div>
              <div className="rounded-xl p-2.5 text-teal-600 bg-teal-500/10">
                <Target className="h-5 w-5" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Content Row */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Recent Activity */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-primary" />
                Recent Activity
              </CardTitle>
              <CardDescription>Latest engagement from your contacts</CardDescription>
            </div>
            <Button variant="ghost" size="sm" asChild>
              <Link to="/analytics">
                View All
                <ArrowUpRight className="h-4 w-4 ml-1" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent>
            {activityLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : activity && activity.length > 0 ? (
              <div className="space-y-3">
                {activity.slice(0, 6).map((event) => (
                  <div
                    key={event.id}
                    className="flex items-center justify-between py-2 border-b last:border-0"
                  >
                    <div className="flex items-center gap-3">
                      <Badge
                        variant={
                          event.type === 'click'
                            ? 'default'
                            : event.type === 'open'
                            ? 'secondary'
                            : event.type === 'reply'
                            ? 'default'
                            : 'outline'
                        }
                        className="w-14 justify-center text-xs"
                      >
                        {event.type}
                      </Badge>
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{event.contact_email}</p>
                        <p className="text-xs text-muted-foreground truncate">
                          {event.campaign_name}
                        </p>
                      </div>
                    </div>
                    <span className="text-xs text-muted-foreground whitespace-nowrap ml-2">
                      {new Date(event.created_at).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Activity className="h-10 w-10 text-muted-foreground/50 mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">No recent activity</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Activity will appear here when contacts engage
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Hot Leads */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Flame className="h-5 w-5 text-orange-500" />
                Hot Leads
              </CardTitle>
              <CardDescription>Contacts with highest engagement scores</CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportHotLeads}
              disabled={exportHotLeads.isPending}
            >
              {exportHotLeads.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Download className="h-4 w-4 mr-1" />
                  Export
                </>
              )}
            </Button>
          </CardHeader>
          <CardContent>
            {leadsLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : hotLeads?.leads && hotLeads.leads.length > 0 ? (
              <>
                <div className="space-y-3">
                  {hotLeads.leads.slice(0, 5).map((lead) => (
                    <div key={lead.id} className="flex items-center justify-between py-2 border-b last:border-0">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium truncate">
                          {lead.first_name} {lead.last_name}
                        </p>
                        <p className="text-xs text-muted-foreground truncate">{lead.email}</p>
                      </div>
                      <div className="flex items-center gap-3 ml-2">
                        <Badge variant="secondary" className="font-mono">
                          {lead.score}
                        </Badge>
                        {lead.score_trend === 'up' && (
                          <TrendingUp className="h-4 w-4 text-green-600" />
                        )}
                        {lead.score_trend === 'down' && (
                          <TrendingDown className="h-4 w-4 text-red-600" />
                        )}
                        {lead.score_trend === 'stable' && (
                          <Minus className="h-4 w-4 text-muted-foreground" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Distribution Summary */}
                <div className="mt-4 pt-4 border-t">
                  <p className="text-xs font-medium text-muted-foreground mb-3">Lead Distribution</p>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div className="rounded-lg bg-orange-500/10 py-2">
                      <p className="text-xl font-bold text-orange-600">{hotLeads.distribution.hot}</p>
                      <p className="text-xs text-muted-foreground">Hot</p>
                    </div>
                    <div className="rounded-lg bg-yellow-500/10 py-2">
                      <p className="text-xl font-bold text-yellow-600">{hotLeads.distribution.warm}</p>
                      <p className="text-xs text-muted-foreground">Warm</p>
                    </div>
                    <div className="rounded-lg bg-blue-500/10 py-2">
                      <p className="text-xl font-bold text-blue-600">{hotLeads.distribution.cold}</p>
                      <p className="text-xs text-muted-foreground">Cold</p>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center py-8">
                <Flame className="h-10 w-10 text-muted-foreground/50 mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">No hot leads yet</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Leads will appear as they engage with your campaigns
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Engagement Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Engagement Summary</CardTitle>
          <CardDescription>
            How your emails are performing across all campaigns
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Opened</span>
                <span className="font-medium">{stats?.emails.opened ?? 0}</span>
              </div>
              <Progress
                value={
                  stats?.emails.sent
                    ? ((stats.emails.opened / stats.emails.sent) * 100)
                    : 0
                }
                className="h-2"
              />
              <p className="text-xs text-muted-foreground">
                {stats?.emails.sent
                  ? ((stats.emails.opened / stats.emails.sent) * 100).toFixed(1)
                  : 0}% of sent emails
              </p>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Clicked</span>
                <span className="font-medium">{stats?.emails.clicked ?? 0}</span>
              </div>
              <Progress
                value={
                  stats?.emails.opened
                    ? ((stats.emails.clicked / stats.emails.opened) * 100)
                    : 0
                }
                className="h-2"
              />
              <p className="text-xs text-muted-foreground">
                {stats?.emails.opened
                  ? ((stats.emails.clicked / stats.emails.opened) * 100).toFixed(1)
                  : 0}% of opened emails
              </p>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Replied</span>
                <span className="font-medium">{stats?.emails.replied ?? 0}</span>
              </div>
              <Progress
                value={
                  stats?.emails.sent
                    ? ((stats.emails.replied / stats.emails.sent) * 100)
                    : 0
                }
                className="h-2"
              />
              <p className="text-xs text-muted-foreground">
                {stats?.emails.sent
                  ? ((stats.emails.replied / stats.emails.sent) * 100).toFixed(1)
                  : 0}% response rate
              </p>
            </div>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Bounced</span>
                <span className="font-medium">{stats?.emails.bounced ?? 0}</span>
              </div>
              <Progress
                value={
                  stats?.emails.sent
                    ? ((stats.emails.bounced / stats.emails.sent) * 100)
                    : 0
                }
                className="h-2 [&>div]:bg-red-500"
              />
              <p className="text-xs text-muted-foreground">
                {stats?.emails.sent
                  ? ((stats.emails.bounced / stats.emails.sent) * 100).toFixed(1)
                  : 0}% bounce rate
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common tasks to help you get started</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 md:grid-cols-4">
            <Button variant="outline" className="h-auto py-4 flex-col gap-2" asChild>
              <Link to="/campaigns">
                <Send className="h-5 w-5 text-primary" />
                <span>New Campaign</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col gap-2" asChild>
              <Link to="/contacts">
                <Users className="h-5 w-5 text-primary" />
                <span>Add Contacts</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col gap-2" asChild>
              <Link to="/templates">
                <Mail className="h-5 w-5 text-primary" />
                <span>Create Template</span>
              </Link>
            </Button>
            <Button variant="outline" className="h-auto py-4 flex-col gap-2" asChild>
              <Link to="/analytics">
                <BarChart3 className="h-5 w-5 text-primary" />
                <span>View Analytics</span>
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

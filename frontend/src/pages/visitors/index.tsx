import { useState } from 'react';
import {
  Users,
  UserCheck,
  UserX,
  Eye,
  Clock,
  Globe,
  Monitor,
  Smartphone,
  Tablet,
  Search,
  ChevronRight,
  Code,
  Copy,
  Check,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import {
  useWebsiteVisitors,
  useWebsiteTrackingStats,
  useWebsiteTrackingScript,
  useWebsiteTrackingSnippet,
  useUpdateWebsiteTrackingScript,
  useRegenerateTrackingScript,
  useTopPages,
} from '@/hooks/use-website-tracking';
import type { WebsiteVisitorListItem } from '@/types/tracking';

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  return `${hours}h ${mins}m`;
}

function formatTimeAgo(date: string): string {
  const now = new Date();
  const then = new Date(date);
  const diff = Math.floor((now.getTime() - then.getTime()) / 1000);

  if (diff < 60) return 'Just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return then.toLocaleDateString();
}

function getDeviceIcon(deviceType: string) {
  switch (deviceType?.toLowerCase()) {
    case 'mobile':
      return <Smartphone className="h-4 w-4" />;
    case 'tablet':
      return <Tablet className="h-4 w-4" />;
    default:
      return <Monitor className="h-4 w-4" />;
  }
}

function VisitorRow({ visitor }: { visitor: WebsiteVisitorListItem }) {
  return (
    <TableRow className="cursor-pointer hover:bg-muted/50">
      <TableCell>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
            {visitor.is_identified ? (
              <UserCheck className="h-4 w-4 text-primary" />
            ) : (
              <UserX className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
          <div>
            <div className="font-medium">
              {visitor.contact_name || visitor.contact_email || 'Anonymous Visitor'}
            </div>
            {visitor.company_name && (
              <div className="text-sm text-muted-foreground">{visitor.company_name}</div>
            )}
          </div>
        </div>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          {getDeviceIcon(visitor.device_type)}
          <span className="text-sm text-muted-foreground capitalize">
            {visitor.device_type || 'Unknown'}
          </span>
        </div>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-2">
          <Globe className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm">
            {visitor.city && visitor.country
              ? `${visitor.city}, ${visitor.country}`
              : visitor.country || 'Unknown'}
          </span>
        </div>
      </TableCell>
      <TableCell className="text-center">
        <Badge variant="secondary">{visitor.total_sessions}</Badge>
      </TableCell>
      <TableCell className="text-center">
        <Badge variant="outline">{visitor.total_page_views}</Badge>
      </TableCell>
      <TableCell className="text-center">
        <span className="text-sm">{formatDuration(visitor.total_time_on_site)}</span>
      </TableCell>
      <TableCell>
        <span className="text-sm text-muted-foreground">
          {formatTimeAgo(visitor.last_seen_at)}
        </span>
      </TableCell>
      <TableCell>
        <Button variant="ghost" size="icon">
          <ChevronRight className="h-4 w-4" />
        </Button>
      </TableCell>
    </TableRow>
  );
}

function SetupDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { data: script, isLoading: scriptLoading } = useWebsiteTrackingScript();
  useWebsiteTrackingSnippet(script?.id || '');
  const updateScript = useUpdateWebsiteTrackingScript();
  const regenerateScript = useRegenerateTrackingScript();
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (script?.embed_code) {
      await navigator.clipboard.writeText(script.embed_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleRegenerate = () => {
    if (script?.id) {
      regenerateScript.mutate(script.id);
    }
  };

  if (scriptLoading || !script) {
    return null;
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Website Tracking Setup</DialogTitle>
          <DialogDescription>
            Add the tracking script to your website to start tracking visitors
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="install" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="install">Install Script</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="install" className="space-y-4">
            <div className="space-y-2">
              <Label>Embed Code</Label>
              <div className="relative">
                <Textarea
                  value={script.embed_code}
                  readOnly
                  className="font-mono text-sm h-20"
                />
                <Button
                  size="sm"
                  variant="outline"
                  className="absolute top-2 right-2"
                  onClick={handleCopy}
                >
                  {copied ? (
                    <>
                      <Check className="h-4 w-4 mr-1" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4 mr-1" />
                      Copy
                    </>
                  )}
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">
                Add this code to the <code>&lt;head&gt;</code> section of your website.
              </p>
            </div>

            <div className="space-y-2">
              <Label>Script URL</Label>
              <div className="flex items-center gap-2">
                <Input value={script.snippet_url} readOnly className="font-mono text-sm" />
                <Button
                  size="icon"
                  variant="outline"
                  onClick={() => window.open(script.snippet_url, '_blank')}
                >
                  <ExternalLink className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="pt-4 border-t">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Script ID</Label>
                  <p className="text-sm text-muted-foreground font-mono">
                    {script.script_id}
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRegenerate}
                  disabled={regenerateScript.isPending}
                >
                  <RefreshCw
                    className={`h-4 w-4 mr-2 ${regenerateScript.isPending ? 'animate-spin' : ''}`}
                  />
                  Regenerate
                </Button>
              </div>
              <p className="text-sm text-muted-foreground mt-1">
                Regenerating will invalidate the current tracking script.
              </p>
            </div>
          </TabsContent>

          <TabsContent value="settings" className="space-y-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Enable Tracking</Label>
                  <p className="text-sm text-muted-foreground">
                    Turn tracking on or off
                  </p>
                </div>
                <Switch
                  checked={script.is_enabled}
                  onCheckedChange={(v) =>
                    updateScript.mutate({
                      id: script.id,
                      data: { is_enabled: v },
                    })
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Track Page Views</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically track page views
                  </p>
                </div>
                <Switch
                  checked={script.track_page_views}
                  onCheckedChange={(v) =>
                    updateScript.mutate({
                      id: script.id,
                      data: { track_page_views: v },
                    })
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Track Clicks</Label>
                  <p className="text-sm text-muted-foreground">
                    Track button and link clicks
                  </p>
                </div>
                <Switch
                  checked={script.track_clicks}
                  onCheckedChange={(v) =>
                    updateScript.mutate({
                      id: script.id,
                      data: { track_clicks: v },
                    })
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Track Forms</Label>
                  <p className="text-sm text-muted-foreground">
                    Track form submissions and identify visitors
                  </p>
                </div>
                <Switch
                  checked={script.track_forms}
                  onCheckedChange={(v) =>
                    updateScript.mutate({
                      id: script.id,
                      data: { track_forms: v },
                    })
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Track Scroll Depth</Label>
                  <p className="text-sm text-muted-foreground">
                    Track how far users scroll on pages
                  </p>
                </div>
                <Switch
                  checked={script.track_scroll_depth}
                  onCheckedChange={(v) =>
                    updateScript.mutate({
                      id: script.id,
                      data: { track_scroll_depth: v },
                    })
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Award Score on Visit</Label>
                  <p className="text-sm text-muted-foreground">
                    Award points to identified contacts for website visits
                  </p>
                </div>
                <Switch
                  checked={script.award_score_on_visit}
                  onCheckedChange={(v) =>
                    updateScript.mutate({
                      id: script.id,
                      data: { award_score_on_visit: v },
                    })
                  }
                />
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}

export default function VisitorsPage() {
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<'all' | 'identified' | 'anonymous'>('all');
  const [setupOpen, setSetupOpen] = useState(false);

  const { data: stats } = useWebsiteTrackingStats();
  const { data: topPages } = useTopPages();
  const {
    data: visitors,
    isLoading: visitorsLoading,
  } = useWebsiteVisitors({
    search: search || undefined,
    is_identified: filter === 'all' ? undefined : filter === 'identified',
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Website Visitors</h1>
          <p className="text-muted-foreground">
            Track and identify visitors on your website
          </p>
        </div>
        <Button onClick={() => setSetupOpen(true)}>
          <Code className="h-4 w-4 mr-2" />
          Setup Tracking
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Visitors</p>
                <p className="text-2xl font-bold">{stats?.total_visitors ?? 0}</p>
              </div>
              <Users className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Identified</p>
                <p className="text-2xl font-bold text-green-600">
                  {stats?.identified_visitors ?? 0}
                </p>
              </div>
              <UserCheck className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Anonymous</p>
                <p className="text-2xl font-bold text-orange-600">
                  {stats?.anonymous_visitors ?? 0}
                </p>
              </div>
              <UserX className="h-8 w-8 text-orange-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Page Views</p>
                <p className="text-2xl font-bold">{stats?.total_page_views ?? 0}</p>
              </div>
              <Eye className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Avg Duration</p>
                <p className="text-2xl font-bold">
                  {formatDuration(stats?.average_session_duration ?? 0)}
                </p>
              </div>
              <Clock className="h-8 w-8 text-muted-foreground" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        {/* Visitors Table */}
        <Card className="md:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Recent Visitors</CardTitle>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search visitors..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-9 w-[200px]"
                  />
                </div>
                <Select
                  value={filter}
                  onValueChange={(v) => setFilter(v as typeof filter)}
                >
                  <SelectTrigger className="w-[140px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Visitors</SelectItem>
                    <SelectItem value="identified">Identified</SelectItem>
                    <SelectItem value="anonymous">Anonymous</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {visitorsLoading ? (
              <div className="text-center py-8 text-muted-foreground">
                Loading visitors...
              </div>
            ) : visitors?.results?.length === 0 ? (
              <div className="text-center py-8">
                <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No visitors yet</h3>
                <p className="text-muted-foreground mb-4">
                  Add the tracking script to your website to start tracking visitors
                </p>
                <Button onClick={() => setSetupOpen(true)}>
                  <Code className="h-4 w-4 mr-2" />
                  Setup Tracking
                </Button>
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Visitor</TableHead>
                    <TableHead>Device</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead className="text-center">Sessions</TableHead>
                    <TableHead className="text-center">Pages</TableHead>
                    <TableHead className="text-center">Time</TableHead>
                    <TableHead>Last Seen</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {visitors?.results?.map((visitor) => (
                    <VisitorRow key={visitor.id} visitor={visitor} />
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        {/* Top Pages */}
        <Card>
          <CardHeader>
            <CardTitle>Top Pages</CardTitle>
            <CardDescription>Most visited pages on your website</CardDescription>
          </CardHeader>
          <CardContent>
            {topPages?.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                No page data yet
              </p>
            ) : (
              <div className="space-y-3">
                {topPages?.slice(0, 10).map((page, index) => (
                  <div
                    key={page.page_path}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-muted-foreground text-sm w-5">
                        {index + 1}.
                      </span>
                      <span className="text-sm truncate" title={page.page_path}>
                        {page.page_title || page.page_path}
                      </span>
                    </div>
                    <Badge variant="secondary">{page.views}</Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Setup Dialog */}
      <SetupDialog open={setupOpen} onOpenChange={setSetupOpen} />
    </div>
  );
}

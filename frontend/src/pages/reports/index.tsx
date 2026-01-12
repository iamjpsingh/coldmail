import { useState } from 'react';
import {
  BarChart3,
  Mail,
  MousePointerClick,
  Users,
  TrendingUp,
  FileSpreadsheet,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  useEmailStatsOverTime,
  useScoreDistribution,
  useCampaignComparison,
  useExportContacts,
} from '@/hooks/use-reports';
import { useCampaigns } from '@/hooks/use-campaigns';

export default function ReportsPage() {
  const [selectedCampaigns, setSelectedCampaigns] = useState<string[]>([]);
  const [granularity, setGranularity] = useState<'day' | 'week' | 'month'>('day');

  const { data: emailStats } = useEmailStatsOverTime(30, granularity);
  const { data: scoreDistribution } = useScoreDistribution();
  const { data: campaigns } = useCampaigns();
  const { data: comparison } = useCampaignComparison(selectedCampaigns);
  const exportContacts = useExportContacts();

  const handleCampaignSelect = (campaignId: string) => {
    if (selectedCampaigns.includes(campaignId)) {
      setSelectedCampaigns(selectedCampaigns.filter((id) => id !== campaignId));
    } else if (selectedCampaigns.length < 5) {
      setSelectedCampaigns([...selectedCampaigns, campaignId]);
    }
  };

  const handleExportContacts = () => {
    exportContacts.mutate({});
  };

  // Calculate max values for chart scaling
  const maxOpens = Math.max(...(emailStats?.map((s) => s.opens) ?? [0]), 1);
  const maxClicks = Math.max(...(emailStats?.map((s) => s.clicks) ?? [0]), 1);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Reports</h1>
          <p className="text-muted-foreground">
            Detailed analytics and performance reports
          </p>
        </div>
        <Button variant="outline" onClick={handleExportContacts} disabled={exportContacts.isPending}>
          <FileSpreadsheet className="h-4 w-4 mr-2" />
          Export All Contacts
        </Button>
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="campaigns">Campaign Comparison</TabsTrigger>
          <TabsTrigger value="scores">Score Distribution</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          {/* Email Stats Over Time */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Email Activity Over Time
              </CardTitle>
              <Select
                value={granularity}
                onValueChange={(v) => setGranularity(v as 'day' | 'week' | 'month')}
              >
                <SelectTrigger className="w-[130px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="day">Daily</SelectItem>
                  <SelectItem value="week">Weekly</SelectItem>
                  <SelectItem value="month">Monthly</SelectItem>
                </SelectContent>
              </Select>
            </CardHeader>
            <CardContent>
              {/* Simple bar chart visualization */}
              <div className="space-y-4">
                <div className="flex items-center gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-blue-500 rounded" />
                    <span>Opens</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded" />
                    <span>Clicks</span>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <div className="flex gap-1 min-w-max pb-4">
                    {emailStats?.slice(-30).map((stat, idx) => (
                      <div key={idx} className="flex flex-col items-center w-8">
                        <div className="flex gap-0.5 h-32 items-end">
                          <div
                            className="w-3 bg-blue-500 rounded-t"
                            style={{ height: `${(stat.opens / maxOpens) * 100}%` }}
                            title={`Opens: ${stat.opens}`}
                          />
                          <div
                            className="w-3 bg-green-500 rounded-t"
                            style={{ height: `${(stat.clicks / maxClicks) * 100}%` }}
                            title={`Clicks: ${stat.clicks}`}
                          />
                        </div>
                        <span className="text-[10px] text-muted-foreground mt-1 rotate-45 origin-left">
                          {new Date(stat.date).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                          })}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {!emailStats?.length && (
                  <p className="text-center text-muted-foreground py-8">
                    No email activity data available
                  </p>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Summary Stats */}
          <div className="grid gap-4 md:grid-cols-4">
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <Mail className="h-8 w-8 mx-auto text-blue-500 mb-2" />
                  <p className="text-2xl font-bold">
                    {emailStats?.reduce((sum, s) => sum + s.opens, 0).toLocaleString() ?? 0}
                  </p>
                  <p className="text-sm text-muted-foreground">Total Opens (30d)</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <MousePointerClick className="h-8 w-8 mx-auto text-green-500 mb-2" />
                  <p className="text-2xl font-bold">
                    {emailStats?.reduce((sum, s) => sum + s.clicks, 0).toLocaleString() ?? 0}
                  </p>
                  <p className="text-sm text-muted-foreground">Total Clicks (30d)</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <Users className="h-8 w-8 mx-auto text-orange-500 mb-2" />
                  <p className="text-2xl font-bold">
                    {emailStats?.reduce((sum, s) => sum + s.unsubscribes, 0).toLocaleString() ?? 0}
                  </p>
                  <p className="text-sm text-muted-foreground">Unsubscribes (30d)</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <TrendingUp className="h-8 w-8 mx-auto text-purple-500 mb-2" />
                  <p className="text-2xl font-bold">
                    {emailStats?.length ?? 0}
                  </p>
                  <p className="text-sm text-muted-foreground">Active Days</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Campaign Comparison Tab */}
        <TabsContent value="campaigns" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Select Campaigns to Compare (max 5)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2 mb-4">
                {campaigns?.map((campaign) => (
                  <Badge
                    key={campaign.id}
                    variant={selectedCampaigns.includes(campaign.id) ? 'default' : 'outline'}
                    className="cursor-pointer"
                    onClick={() => handleCampaignSelect(campaign.id)}
                  >
                    {campaign.name}
                  </Badge>
                ))}
              </div>

              {selectedCampaigns.length > 0 && comparison && (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Campaign</TableHead>
                      <TableHead className="text-right">Sent</TableHead>
                      <TableHead className="text-right">Opened</TableHead>
                      <TableHead className="text-right">Clicked</TableHead>
                      <TableHead className="text-right">Open Rate</TableHead>
                      <TableHead className="text-right">Click Rate</TableHead>
                      <TableHead className="text-right">Reply Rate</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {comparison.map((campaign) => (
                      <TableRow key={campaign.id}>
                        <TableCell className="font-medium">{campaign.name}</TableCell>
                        <TableCell className="text-right">{campaign.sent}</TableCell>
                        <TableCell className="text-right">{campaign.opened}</TableCell>
                        <TableCell className="text-right">{campaign.clicked}</TableCell>
                        <TableCell className="text-right">
                          <Badge variant="secondary">{campaign.open_rate}%</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Badge variant="secondary">{campaign.click_rate}%</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Badge variant="secondary">{campaign.reply_rate}%</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}

              {selectedCampaigns.length === 0 && (
                <p className="text-center text-muted-foreground py-8">
                  Select campaigns above to compare their performance
                </p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Score Distribution Tab */}
        <TabsContent value="scores" className="space-y-6">
          <div className="grid gap-6 md:grid-cols-2">
            {/* Distribution Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Score Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {scoreDistribution?.distribution.map((item) => {
                    const maxCount = Math.max(
                      ...scoreDistribution.distribution.map((d) => d.count),
                      1
                    );
                    const percentage = (item.count / maxCount) * 100;

                    return (
                      <div key={item.range} className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span>{item.range}</span>
                          <span className="text-muted-foreground">{item.count}</span>
                        </div>
                        <Progress value={percentage} className="h-2" />
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Stats Summary */}
            <Card>
              <CardHeader>
                <CardTitle>Score Statistics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <p className="text-3xl font-bold">
                        {scoreDistribution?.stats.average ?? 0}
                      </p>
                      <p className="text-sm text-muted-foreground">Average Score</p>
                    </div>
                    <div className="text-center p-4 bg-muted rounded-lg">
                      <p className="text-3xl font-bold">
                        {scoreDistribution?.stats.total_contacts ?? 0}
                      </p>
                      <p className="text-sm text-muted-foreground">Total Contacts</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-4 border rounded-lg">
                      <p className="text-2xl font-bold text-green-600">
                        {scoreDistribution?.stats.maximum ?? 0}
                      </p>
                      <p className="text-sm text-muted-foreground">Highest Score</p>
                    </div>
                    <div className="text-center p-4 border rounded-lg">
                      <p className="text-2xl font-bold text-red-600">
                        {scoreDistribution?.stats.minimum ?? 0}
                      </p>
                      <p className="text-sm text-muted-foreground">Lowest Score</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

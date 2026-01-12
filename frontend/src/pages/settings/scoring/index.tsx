import { useState } from 'react';
import { Flame, ThermometerSun, Snowflake, Plus, Settings, TrendingDown, RefreshCw, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useScoringStats, useScoringRules, useScoreThresholds, useScoreDecayConfig } from '@/hooks/use-contacts';
import { ScoringRulesTable } from './components/scoring-rules-table';
import { AddScoringRuleDialog } from './components/add-scoring-rule-dialog';
import { ThresholdsSettings } from './components/thresholds-settings';
import { DecaySettings } from './components/decay-settings';

export default function ScoringSettingsPage() {
  const [isAddRuleDialogOpen, setIsAddRuleDialogOpen] = useState(false);

  const { data: stats, isLoading: statsLoading } = useScoringStats();
  const { data: rules, isLoading: rulesLoading, error: rulesError } = useScoringRules();
  const { data: thresholds, isLoading: thresholdsLoading } = useScoreThresholds();
  const { data: decayConfig, isLoading: decayLoading } = useScoreDecayConfig();

  const isLoading = statsLoading || rulesLoading || thresholdsLoading || decayLoading;

  if (isLoading) {
    return (
      <div className="container mx-auto py-8">
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (rulesError) {
    return (
      <div className="container mx-auto py-8">
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <span>Failed to load scoring settings. Please try again.</span>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Contact Scoring</h1>
          <p className="text-muted-foreground">
            Configure scoring rules and thresholds for your contacts
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Score</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.average_score || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.total_contacts || 0} total contacts
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Hot Leads</CardTitle>
            <Flame className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats?.hot_count || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.hot_percentage || 0}% of contacts
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Warm Leads</CardTitle>
            <ThermometerSun className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">{stats?.warm_count || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.warm_percentage || 0}% of contacts
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cold Leads</CardTitle>
            <Snowflake className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats?.cold_count || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.cold_percentage || 0}% of contacts
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Settings Tabs */}
      <Tabs defaultValue="rules" className="space-y-4">
        <TabsList>
          <TabsTrigger value="rules">Scoring Rules</TabsTrigger>
          <TabsTrigger value="thresholds">Thresholds</TabsTrigger>
          <TabsTrigger value="decay">Score Decay</TabsTrigger>
        </TabsList>

        <TabsContent value="rules" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Scoring Rules</CardTitle>
                  <CardDescription>
                    Define rules to automatically adjust contact scores based on their behavior
                  </CardDescription>
                </div>
                <Button onClick={() => setIsAddRuleDialogOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Rule
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {rules && rules.length > 0 ? (
                <ScoringRulesTable rules={rules} />
              ) : (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Settings className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">No scoring rules yet</h3>
                  <p className="text-muted-foreground mb-4">
                    Create rules to automatically score your contacts
                  </p>
                  <Button onClick={() => setIsAddRuleDialogOpen(true)}>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Rule
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="thresholds" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Score Thresholds</CardTitle>
              <CardDescription>
                Configure the score ranges for hot, warm, and cold leads
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ThresholdsSettings thresholds={thresholds || []} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="decay" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <TrendingDown className="h-5 w-5" />
                <div>
                  <CardTitle>Score Decay</CardTitle>
                  <CardDescription>
                    Automatically decrease scores for inactive contacts
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <DecaySettings config={decayConfig} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add Rule Dialog */}
      <AddScoringRuleDialog
        open={isAddRuleDialogOpen}
        onOpenChange={setIsAddRuleDialogOpen}
      />
    </div>
  );
}

import { useState, useEffect } from 'react';
import { Play, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { useUpdateScoreDecayConfig, useRunScoreDecay } from '@/hooks/use-contacts';
import type { ScoreDecayConfig } from '@/types/contact';

interface DecaySettingsProps {
  config: ScoreDecayConfig | undefined;
}

export function DecaySettings({ config }: DecaySettingsProps) {
  const [isEnabled, setIsEnabled] = useState(config?.is_enabled ?? false);
  const [decayPoints, setDecayPoints] = useState(config?.decay_points ?? 5);
  const [decayIntervalDays, setDecayIntervalDays] = useState(config?.decay_interval_days ?? 7);
  const [minScore, setMinScore] = useState(config?.min_score ?? 0);
  const [inactivityDays, setInactivityDays] = useState(config?.inactivity_days ?? 30);

  const updateMutation = useUpdateScoreDecayConfig();
  const runDecayMutation = useRunScoreDecay();

  useEffect(() => {
    if (config) {
      setIsEnabled(config.is_enabled);
      setDecayPoints(config.decay_points);
      setDecayIntervalDays(config.decay_interval_days);
      setMinScore(config.min_score);
      setInactivityDays(config.inactivity_days);
    }
  }, [config]);

  const handleSave = async () => {
    if (!config) return;

    await updateMutation.mutateAsync({
      id: config.id,
      data: {
        is_enabled: isEnabled,
        decay_points: decayPoints,
        decay_interval_days: decayIntervalDays,
        min_score: minScore,
        inactivity_days: inactivityDays,
      },
    });
  };

  const handleRunNow = async () => {
    if (!config) return;
    await runDecayMutation.mutateAsync(config.id);
  };

  if (!config) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        Score decay configuration not available. Please contact support.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Enable/Disable */}
      <div className="flex items-center justify-between p-4 border rounded-lg">
        <div>
          <Label className="text-base font-medium">Enable Score Decay</Label>
          <p className="text-sm text-muted-foreground">
            Automatically decrease scores for inactive contacts
          </p>
        </div>
        <Switch
          checked={isEnabled}
          onCheckedChange={setIsEnabled}
        />
      </div>

      {isEnabled && (
        <div className="grid gap-6">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="decayPoints">Points to Decrease</Label>
              <Input
                id="decayPoints"
                type="number"
                min={1}
                max={50}
                value={decayPoints}
                onChange={(e) => setDecayPoints(parseInt(e.target.value) || 5)}
              />
              <p className="text-xs text-muted-foreground">
                How many points to decrease per decay interval
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="decayInterval">Decay Interval (days)</Label>
              <Input
                id="decayInterval"
                type="number"
                min={1}
                max={90}
                value={decayIntervalDays}
                onChange={(e) => setDecayIntervalDays(parseInt(e.target.value) || 7)}
              />
              <p className="text-xs text-muted-foreground">
                How often to apply score decay
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="inactivityDays">Inactivity Threshold (days)</Label>
              <Input
                id="inactivityDays"
                type="number"
                min={1}
                max={365}
                value={inactivityDays}
                onChange={(e) => setInactivityDays(parseInt(e.target.value) || 30)}
              />
              <p className="text-xs text-muted-foreground">
                Days without activity before decay starts
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="minScore">Minimum Score</Label>
              <Input
                id="minScore"
                type="number"
                min={0}
                max={100}
                value={minScore}
                onChange={(e) => setMinScore(parseInt(e.target.value) || 0)}
              />
              <p className="text-xs text-muted-foreground">
                Scores will not decay below this value
              </p>
            </div>
          </div>

          {config.last_run_at && (
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-sm">
                <span className="font-medium">Last Run:</span>{' '}
                {new Date(config.last_run_at).toLocaleString()}
              </p>
            </div>
          )}
        </div>
      )}

      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={handleRunNow}
          disabled={!isEnabled || runDecayMutation.isPending}
        >
          <Play className="h-4 w-4 mr-2" />
          {runDecayMutation.isPending ? 'Running...' : 'Run Now'}
        </Button>

        <Button onClick={handleSave} disabled={updateMutation.isPending}>
          <Save className="h-4 w-4 mr-2" />
          {updateMutation.isPending ? 'Saving...' : 'Save Settings'}
        </Button>
      </div>
    </div>
  );
}

import { useState } from 'react';
import { Flame, ThermometerSun, Snowflake, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useUpdateScoreThreshold, useCreateScoreThreshold } from '@/hooks/use-contacts';
import type { ScoreThreshold, ScoreClassification } from '@/types/contact';

interface ThresholdsSettingsProps {
  thresholds: ScoreThreshold[];
}

const defaultThresholds: { classification: ScoreClassification; minScore: number; color: string }[] = [
  { classification: 'hot', minScore: 70, color: '#ef4444' },
  { classification: 'warm', minScore: 40, color: '#f97316' },
  { classification: 'cold', minScore: 0, color: '#3b82f6' },
];

const classificationIcons: Record<ScoreClassification, React.ReactNode> = {
  hot: <Flame className="h-5 w-5 text-red-500" />,
  warm: <ThermometerSun className="h-5 w-5 text-orange-500" />,
  cold: <Snowflake className="h-5 w-5 text-blue-500" />,
};

const classificationLabels: Record<ScoreClassification, string> = {
  hot: 'Hot Leads',
  warm: 'Warm Leads',
  cold: 'Cold Leads',
};

export function ThresholdsSettings({ thresholds }: ThresholdsSettingsProps) {
  const updateMutation = useUpdateScoreThreshold();
  const createMutation = useCreateScoreThreshold();

  // Get existing threshold values or use defaults
  const getThreshold = (classification: ScoreClassification): ScoreThreshold | undefined => {
    return thresholds.find((t) => t.classification === classification);
  };

  const [hotMinScore, setHotMinScore] = useState(
    getThreshold('hot')?.min_score ?? defaultThresholds[0].minScore
  );
  const [warmMinScore, setWarmMinScore] = useState(
    getThreshold('warm')?.min_score ?? defaultThresholds[1].minScore
  );
  // Cold always starts at 0
  const coldMinScore = 0;

  const handleSave = async () => {
    const configs = [
      { classification: 'hot' as ScoreClassification, min_score: hotMinScore, color: '#ef4444' },
      { classification: 'warm' as ScoreClassification, min_score: warmMinScore, color: '#f97316' },
      { classification: 'cold' as ScoreClassification, min_score: coldMinScore, color: '#3b82f6' },
    ];

    for (const config of configs) {
      const existing = getThreshold(config.classification);
      if (existing) {
        await updateMutation.mutateAsync({
          id: existing.id,
          data: { min_score: config.min_score },
        });
      } else {
        await createMutation.mutateAsync(config);
      }
    }
  };

  const isPending = updateMutation.isPending || createMutation.isPending;

  return (
    <div className="space-y-6">
      <div className="grid gap-6">
        {/* Hot Leads */}
        <div className="flex items-start gap-4 p-4 border rounded-lg">
          <div className="p-2 bg-red-100 rounded-lg">
            {classificationIcons.hot}
          </div>
          <div className="flex-1 space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-base font-medium">{classificationLabels.hot}</Label>
              <span className="text-sm text-muted-foreground">
                {getThreshold('hot')?.contacts_count || 0} contacts
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              Contacts with high engagement and ready to convert
            </p>
            <div className="flex items-center gap-2">
              <Label htmlFor="hotMin" className="text-sm">Minimum Score:</Label>
              <Input
                id="hotMin"
                type="number"
                min={0}
                max={100}
                value={hotMinScore}
                onChange={(e) => setHotMinScore(parseInt(e.target.value) || 0)}
                className="w-24"
              />
              <span className="text-sm text-muted-foreground">to 100</span>
            </div>
          </div>
        </div>

        {/* Warm Leads */}
        <div className="flex items-start gap-4 p-4 border rounded-lg">
          <div className="p-2 bg-orange-100 rounded-lg">
            {classificationIcons.warm}
          </div>
          <div className="flex-1 space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-base font-medium">{classificationLabels.warm}</Label>
              <span className="text-sm text-muted-foreground">
                {getThreshold('warm')?.contacts_count || 0} contacts
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              Contacts showing interest but need more nurturing
            </p>
            <div className="flex items-center gap-2">
              <Label htmlFor="warmMin" className="text-sm">Minimum Score:</Label>
              <Input
                id="warmMin"
                type="number"
                min={0}
                max={100}
                value={warmMinScore}
                onChange={(e) => setWarmMinScore(parseInt(e.target.value) || 0)}
                className="w-24"
              />
              <span className="text-sm text-muted-foreground">to {hotMinScore - 1}</span>
            </div>
          </div>
        </div>

        {/* Cold Leads */}
        <div className="flex items-start gap-4 p-4 border rounded-lg">
          <div className="p-2 bg-blue-100 rounded-lg">
            {classificationIcons.cold}
          </div>
          <div className="flex-1 space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-base font-medium">{classificationLabels.cold}</Label>
              <span className="text-sm text-muted-foreground">
                {getThreshold('cold')?.contacts_count || 0} contacts
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              New contacts or those with little engagement
            </p>
            <div className="flex items-center gap-2">
              <Label htmlFor="coldMin" className="text-sm">Score Range:</Label>
              <span className="text-sm">0 to {warmMinScore - 1}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={isPending}>
          <Save className="h-4 w-4 mr-2" />
          {isPending ? 'Saving...' : 'Save Thresholds'}
        </Button>
      </div>
    </div>
  );
}

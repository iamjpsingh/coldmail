import { useState } from 'react';
import { Plus, Minus } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { useCreateScoringRule } from '@/hooks/use-contacts';
import type { ScoringEventType, ScoringCondition } from '@/types/contact';

interface AddScoringRuleDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const eventTypes: { value: ScoringEventType; label: string }[] = [
  { value: 'email_opened', label: 'Email Opened' },
  { value: 'email_clicked', label: 'Email Clicked' },
  { value: 'email_replied', label: 'Email Replied' },
  { value: 'email_bounced', label: 'Email Bounced' },
  { value: 'email_unsubscribed', label: 'Email Unsubscribed' },
  { value: 'link_clicked', label: 'Link Clicked' },
  { value: 'form_submitted', label: 'Form Submitted' },
  { value: 'page_visited', label: 'Page Visited' },
  { value: 'meeting_scheduled', label: 'Meeting Scheduled' },
];

const operators = [
  { value: 'equals', label: 'Equals' },
  { value: 'not_equals', label: 'Not Equals' },
  { value: 'contains', label: 'Contains' },
  { value: 'not_contains', label: 'Not Contains' },
  { value: 'greater_than', label: 'Greater Than' },
  { value: 'less_than', label: 'Less Than' },
  { value: 'is_set', label: 'Is Set' },
  { value: 'is_not_set', label: 'Is Not Set' },
];

export function AddScoringRuleDialog({ open, onOpenChange }: AddScoringRuleDialogProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [eventType, setEventType] = useState<ScoringEventType>('email_opened');
  const [scoreChange, setScoreChange] = useState(5);
  const [maxApplications, setMaxApplications] = useState<number | null>(null);
  const [cooldownHours, setCooldownHours] = useState<number | null>(null);
  const [priority, setPriority] = useState(0);
  const [isActive, setIsActive] = useState(true);
  const [conditions, setConditions] = useState<ScoringCondition[]>([]);

  const createMutation = useCreateScoringRule();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    await createMutation.mutateAsync({
      name,
      description: description || undefined,
      event_type: eventType,
      score_change: scoreChange,
      max_applications: maxApplications,
      cooldown_hours: cooldownHours,
      priority,
      is_active: isActive,
      conditions,
    });

    // Reset form
    setName('');
    setDescription('');
    setEventType('email_opened');
    setScoreChange(5);
    setMaxApplications(null);
    setCooldownHours(null);
    setPriority(0);
    setIsActive(true);
    setConditions([]);

    onOpenChange(false);
  };

  const addCondition = () => {
    setConditions([...conditions, { field: '', operator: 'equals', value: '' }]);
  };

  const removeCondition = (index: number) => {
    setConditions(conditions.filter((_, i) => i !== index));
  };

  const updateCondition = (index: number, field: keyof ScoringCondition, value: string) => {
    const newConditions = [...conditions];
    newConditions[index] = { ...newConditions[index], [field]: value };
    setConditions(newConditions);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Add Scoring Rule</DialogTitle>
          <DialogDescription>
            Create a new rule to automatically adjust contact scores
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">Rule Name</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Email Open Bonus"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="eventType">Event Type</Label>
              <Select value={eventType} onValueChange={(v) => setEventType(v as ScoringEventType)}>
                <SelectTrigger id="eventType">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {eventTypes.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description (optional)</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what this rule does..."
              rows={2}
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="scoreChange">Score Change</Label>
              <Input
                id="scoreChange"
                type="number"
                value={scoreChange}
                onChange={(e) => setScoreChange(parseInt(e.target.value) || 0)}
              />
              <p className="text-xs text-muted-foreground">
                Use negative values to decrease score
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="maxApplications">Max Applications (optional)</Label>
              <Input
                id="maxApplications"
                type="number"
                value={maxApplications || ''}
                onChange={(e) => setMaxApplications(e.target.value ? parseInt(e.target.value) : null)}
                placeholder="Unlimited"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="cooldownHours">Cooldown Hours (optional)</Label>
              <Input
                id="cooldownHours"
                type="number"
                value={cooldownHours || ''}
                onChange={(e) => setCooldownHours(e.target.value ? parseInt(e.target.value) : null)}
                placeholder="No cooldown"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="priority">Priority</Label>
              <Input
                id="priority"
                type="number"
                value={priority}
                onChange={(e) => setPriority(parseInt(e.target.value) || 0)}
              />
              <p className="text-xs text-muted-foreground">
                Higher priority rules are applied first
              </p>
            </div>

            <div className="flex items-center gap-2 pt-6">
              <Switch
                id="isActive"
                checked={isActive}
                onCheckedChange={setIsActive}
              />
              <Label htmlFor="isActive">Active</Label>
            </div>
          </div>

          {/* Conditions */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label>Conditions (optional)</Label>
              <Button type="button" variant="outline" size="sm" onClick={addCondition}>
                <Plus className="h-4 w-4 mr-1" />
                Add Condition
              </Button>
            </div>

            {conditions.length > 0 && (
              <div className="space-y-2 border rounded-lg p-4">
                {conditions.map((condition, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <Input
                      placeholder="Field name"
                      value={condition.field}
                      onChange={(e) => updateCondition(index, 'field', e.target.value)}
                      className="flex-1"
                    />
                    <Select
                      value={condition.operator}
                      onValueChange={(v) => updateCondition(index, 'operator', v)}
                    >
                      <SelectTrigger className="w-[150px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {operators.map((op) => (
                          <SelectItem key={op.value} value={op.value}>
                            {op.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Input
                      placeholder="Value"
                      value={String(condition.value)}
                      onChange={(e) => updateCondition(index, 'value', e.target.value)}
                      className="flex-1"
                      disabled={condition.operator === 'is_set' || condition.operator === 'is_not_set'}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => removeCondition(index)}
                    >
                      <Minus className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={!name || createMutation.isPending}>
              {createMutation.isPending ? 'Creating...' : 'Create Rule'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

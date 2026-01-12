import { useState } from 'react';
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
import { RichTextEditor } from '@/components/ui/rich-text-editor';
import { useCreateCampaign } from '@/hooks/use-campaigns';
import { useEmailAccounts } from '@/hooks/use-email-accounts';
import { useTemplates, useTemplateVariables } from '@/hooks/use-templates';
import type { SendingMode } from '@/types/campaign';

interface AddCampaignDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AddCampaignDialog({ open, onOpenChange }: AddCampaignDialogProps) {
  const [step, setStep] = useState(1);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [subject, setSubject] = useState('');
  const [contentHtml, setContentHtml] = useState('');
  const [emailAccountId, setEmailAccountId] = useState('');
  const [fromName, setFromName] = useState('');
  const [replyTo, setReplyTo] = useState('');
  const [templateId, setTemplateId] = useState<string>('');
  const [sendingMode, setSendingMode] = useState<SendingMode>('immediate');
  const [trackOpens, setTrackOpens] = useState(true);
  const [trackClicks, setTrackClicks] = useState(true);
  const [includeUnsubscribe, setIncludeUnsubscribe] = useState(true);

  const createMutation = useCreateCampaign();
  const { data: emailAccounts } = useEmailAccounts();
  const { data: templates } = useTemplates();
  const { data: variablesData } = useTemplateVariables();

  // Transform variables for the editor
  const editorVariables = variablesData
    ? Object.entries(variablesData).reduce(
        (acc, [category, vars]) => ({
          ...acc,
          [category]: Object.keys(vars),
        }),
        {} as Record<string, string[]>
      )
    : undefined;

  const handleTemplateSelect = (templateId: string) => {
    setTemplateId(templateId);
    const template = templates?.find((t) => t.id === templateId);
    if (template) {
      setSubject(template.subject);
      // We'd need to fetch full template to get content_html
    }
  };

  const handleSubmit = async () => {
    await createMutation.mutateAsync({
      name,
      description: description || undefined,
      subject,
      content_html: contentHtml,
      email_account: emailAccountId,
      from_name: fromName || undefined,
      reply_to: replyTo || undefined,
      template: templateId || undefined,
      sending_mode: sendingMode,
      track_opens: trackOpens,
      track_clicks: trackClicks,
      include_unsubscribe_link: includeUnsubscribe,
    });

    // Reset form
    setStep(1);
    setName('');
    setDescription('');
    setSubject('');
    setContentHtml('');
    setEmailAccountId('');
    setFromName('');
    setReplyTo('');
    setTemplateId('');
    setSendingMode('immediate');

    onOpenChange(false);
  };

  const canProceed = () => {
    if (step === 1) {
      return name && emailAccountId;
    }
    if (step === 2) {
      return subject && contentHtml;
    }
    return true;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Campaign</DialogTitle>
          <DialogDescription>
            {step === 1 && 'Set up campaign basics'}
            {step === 2 && 'Compose your email'}
            {step === 3 && 'Configure sending options'}
          </DialogDescription>
        </DialogHeader>

        {/* Step indicators */}
        <div className="flex items-center justify-center gap-2 py-4">
          {[1, 2, 3].map((s) => (
            <div
              key={s}
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                s === step
                  ? 'bg-primary text-primary-foreground'
                  : s < step
                    ? 'bg-primary/20 text-primary'
                    : 'bg-muted text-muted-foreground'
              }`}
            >
              {s}
            </div>
          ))}
        </div>

        {/* Step 1: Basics */}
        {step === 1 && (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Campaign Name</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., January Newsletter"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description (optional)</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief description of this campaign..."
                rows={2}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email-account">Send From</Label>
              <Select value={emailAccountId} onValueChange={setEmailAccountId}>
                <SelectTrigger id="email-account">
                  <SelectValue placeholder="Select email account" />
                </SelectTrigger>
                <SelectContent>
                  {emailAccounts?.map((account) => (
                    <SelectItem key={account.id} value={account.id}>
                      {account.name} ({account.email})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="from-name">From Name (optional)</Label>
                <Input
                  id="from-name"
                  value={fromName}
                  onChange={(e) => setFromName(e.target.value)}
                  placeholder="Override sender name"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="reply-to">Reply-To (optional)</Label>
                <Input
                  id="reply-to"
                  type="email"
                  value={replyTo}
                  onChange={(e) => setReplyTo(e.target.value)}
                  placeholder="replies@example.com"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Content */}
        {step === 2 && (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="template">Use Template (optional)</Label>
              <Select value={templateId} onValueChange={handleTemplateSelect}>
                <SelectTrigger id="template">
                  <SelectValue placeholder="Start from scratch or select a template" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Start from scratch</SelectItem>
                  {templates?.map((template) => (
                    <SelectItem key={template.id} value={template.id}>
                      {template.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="subject">Subject Line</Label>
              <Input
                id="subject"
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="e.g., Quick question about {{company}}"
              />
              <p className="text-xs text-muted-foreground">
                Use {'{{variable}}'} for personalization
              </p>
            </div>

            <div className="space-y-2">
              <Label>Email Content</Label>
              <RichTextEditor
                content={contentHtml}
                onChange={setContentHtml}
                placeholder="Write your email content here..."
                variables={editorVariables}
              />
            </div>
          </div>
        )}

        {/* Step 3: Options */}
        {step === 3 && (
          <div className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="sending-mode">Sending Mode</Label>
              <Select
                value={sendingMode}
                onValueChange={(v) => setSendingMode(v as SendingMode)}
              >
                <SelectTrigger id="sending-mode">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="immediate">Send Immediately</SelectItem>
                  <SelectItem value="scheduled">Schedule for Later</SelectItem>
                  <SelectItem value="spread">Spread Across Time Window</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-4">
              <h4 className="font-medium">Tracking Options</h4>

              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="track-opens">Track Opens</Label>
                  <p className="text-sm text-muted-foreground">
                    Add tracking pixel to detect email opens
                  </p>
                </div>
                <Switch
                  id="track-opens"
                  checked={trackOpens}
                  onCheckedChange={setTrackOpens}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="track-clicks">Track Clicks</Label>
                  <p className="text-sm text-muted-foreground">
                    Track when recipients click links
                  </p>
                </div>
                <Switch
                  id="track-clicks"
                  checked={trackClicks}
                  onCheckedChange={setTrackClicks}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="unsubscribe">Include Unsubscribe Link</Label>
                  <p className="text-sm text-muted-foreground">
                    Add unsubscribe link to email footer
                  </p>
                </div>
                <Switch
                  id="unsubscribe"
                  checked={includeUnsubscribe}
                  onCheckedChange={setIncludeUnsubscribe}
                />
              </div>
            </div>
          </div>
        )}

        <DialogFooter className="gap-2">
          {step > 1 && (
            <Button
              type="button"
              variant="outline"
              onClick={() => setStep(step - 1)}
            >
              Back
            </Button>
          )}
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          {step < 3 ? (
            <Button
              type="button"
              disabled={!canProceed()}
              onClick={() => setStep(step + 1)}
            >
              Next
            </Button>
          ) : (
            <Button
              type="button"
              disabled={!canProceed() || createMutation.isPending}
              onClick={handleSubmit}
            >
              {createMutation.isPending ? 'Creating...' : 'Create Campaign'}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

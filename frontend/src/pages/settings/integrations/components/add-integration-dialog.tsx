import { useState } from 'react';
import { ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { integrationIcons } from './integration-card';
import type { IntegrationTypeInfo, IntegrationType, DiscordIntegrationCreate } from '@/types/integrations';

interface AddIntegrationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  integrationTypes: IntegrationTypeInfo[];
  onCreateDiscord: (data: DiscordIntegrationCreate) => Promise<void>;
  isCreating: boolean;
}

export function AddIntegrationDialog({
  open,
  onOpenChange,
  integrationTypes,
  onCreateDiscord,
  isCreating,
}: AddIntegrationDialogProps) {
  const [step, setStep] = useState<'select' | 'configure'>('select');
  const [selectedType, setSelectedType] = useState<IntegrationType | null>(null);

  // Discord form state
  const [discordForm, setDiscordForm] = useState<DiscordIntegrationCreate>({
    name: '',
    description: '',
    webhook_url: '',
    bot_username: 'ColdMail',
    bot_avatar_url: '',
  });

  const handleSelectType = (type: IntegrationType) => {
    setSelectedType(type);
    const typeInfo = integrationTypes.find(t => t.value === type);

    if (typeInfo?.requires_oauth) {
      // OAuth integrations would redirect to OAuth flow
      // For now, show a message
      return;
    }

    // Non-OAuth integrations go to configure step
    if (type === 'discord') {
      setStep('configure');
    }
  };

  const handleCreateDiscord = async () => {
    await onCreateDiscord(discordForm);
    handleClose();
  };

  const handleClose = () => {
    setStep('select');
    setSelectedType(null);
    setDiscordForm({
      name: '',
      description: '',
      webhook_url: '',
      bot_username: 'ColdMail',
      bot_avatar_url: '',
    });
    onOpenChange(false);
  };

  const handleBack = () => {
    setStep('select');
    setSelectedType(null);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        {step === 'select' && (
          <>
            <DialogHeader>
              <DialogTitle>Add Integration</DialogTitle>
              <DialogDescription>
                Connect ColdMail with your favorite tools and services.
              </DialogDescription>
            </DialogHeader>
            <div className="grid grid-cols-2 gap-4 py-4">
              {integrationTypes.map((type) => (
                <Card
                  key={type.value}
                  className={`cursor-pointer transition-colors hover:border-primary ${
                    selectedType === type.value ? 'border-primary' : ''
                  }`}
                  onClick={() => handleSelectType(type.value)}
                >
                  <CardHeader className="pb-2">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                        {integrationIcons[type.value]}
                      </div>
                      <div>
                        <CardTitle className="text-base">{type.label}</CardTitle>
                        {type.requires_oauth ? (
                          <Badge variant="secondary" className="mt-1 text-xs">
                            OAuth
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="mt-1 text-xs">
                            Webhook
                          </Badge>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="text-xs">
                      {type.description}
                    </CardDescription>
                  </CardContent>
                </Card>
              ))}
            </div>
            <div className="text-sm text-muted-foreground mt-2">
              <p>
                For automation platforms like Zapier and n8n, use our{' '}
                <a href="/settings/webhooks" className="text-primary hover:underline">
                  webhooks feature
                </a>{' '}
                to connect.
              </p>
            </div>
          </>
        )}

        {step === 'configure' && selectedType === 'discord' && (
          <>
            <DialogHeader>
              <DialogTitle>Configure Discord Integration</DialogTitle>
              <DialogDescription>
                Connect ColdMail to your Discord server using a webhook URL.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="p-4 bg-muted rounded-lg text-sm">
                <p className="font-medium mb-2">How to get a Discord webhook URL:</p>
                <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
                  <li>Open Discord and go to your server settings</li>
                  <li>Navigate to Integrations &gt; Webhooks</li>
                  <li>Click "New Webhook" and configure it</li>
                  <li>Copy the webhook URL and paste it below</li>
                </ol>
                <a
                  href="https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-primary mt-2 hover:underline"
                >
                  Discord webhook documentation
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>

              <div className="space-y-2">
                <Label htmlFor="discord-name">Integration Name</Label>
                <Input
                  id="discord-name"
                  value={discordForm.name}
                  onChange={(e) => setDiscordForm({ ...discordForm, name: e.target.value })}
                  placeholder="My Discord Notifications"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="discord-description">Description (optional)</Label>
                <Textarea
                  id="discord-description"
                  value={discordForm.description}
                  onChange={(e) =>
                    setDiscordForm({ ...discordForm, description: e.target.value })
                  }
                  placeholder="Notifications for sales team channel"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="discord-webhook">Webhook URL</Label>
                <Input
                  id="discord-webhook"
                  type="url"
                  value={discordForm.webhook_url}
                  onChange={(e) =>
                    setDiscordForm({ ...discordForm, webhook_url: e.target.value })
                  }
                  placeholder="https://discord.com/api/webhooks/..."
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="discord-username">Bot Username</Label>
                  <Input
                    id="discord-username"
                    value={discordForm.bot_username}
                    onChange={(e) =>
                      setDiscordForm({ ...discordForm, bot_username: e.target.value })
                    }
                    placeholder="ColdMail"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="discord-avatar">Bot Avatar URL (optional)</Label>
                  <Input
                    id="discord-avatar"
                    type="url"
                    value={discordForm.bot_avatar_url}
                    onChange={(e) =>
                      setDiscordForm({ ...discordForm, bot_avatar_url: e.target.value })
                    }
                    placeholder="https://example.com/avatar.png"
                  />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={handleBack}>
                Back
              </Button>
              <Button
                onClick={handleCreateDiscord}
                disabled={!discordForm.name || !discordForm.webhook_url || isCreating}
              >
                {isCreating ? 'Creating...' : 'Create Integration'}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}

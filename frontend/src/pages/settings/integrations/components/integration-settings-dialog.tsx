import { useState, useEffect } from 'react';
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
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import type {
  Integration,
  SlackIntegrationSettings,
  DiscordIntegrationSettings,
  HubSpotIntegrationSettings,
  SalesforceIntegrationSettings,
  GoogleSheetsIntegrationSettings,
} from '@/types/integrations';
import type { IntegrationSettings } from '@/api/integrations';

interface IntegrationSettingsDialogProps {
  integration: Integration | null;
  settings: IntegrationSettings | undefined;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (settings: Partial<IntegrationSettings>) => Promise<void>;
  isSaving: boolean;
}

export function IntegrationSettingsDialog({
  integration,
  settings,
  open,
  onOpenChange,
  onSave,
  isSaving,
}: IntegrationSettingsDialogProps) {
  const [formData, setFormData] = useState<Partial<IntegrationSettings>>({});

  useEffect(() => {
    if (settings) {
      setFormData(settings);
    }
  }, [settings]);

  const handleSave = async () => {
    await onSave(formData);
    onOpenChange(false);
  };

  if (!integration) return null;

  const renderSettingsForm = () => {
    switch (integration.integration_type) {
      case 'slack':
        return <SlackSettingsForm data={formData as Partial<SlackIntegrationSettings>} onChange={setFormData} />;
      case 'discord':
        return <DiscordSettingsForm data={formData as Partial<DiscordIntegrationSettings>} onChange={setFormData} />;
      case 'hubspot':
        return <HubSpotSettingsForm data={formData as Partial<HubSpotIntegrationSettings>} onChange={setFormData} />;
      case 'salesforce':
        return <SalesforceSettingsForm data={formData as Partial<SalesforceIntegrationSettings>} onChange={setFormData} />;
      case 'google_sheets':
        return <GoogleSheetsSettingsForm data={formData as Partial<GoogleSheetsIntegrationSettings>} onChange={setFormData} />;
      default:
        return <p className="text-muted-foreground">No settings available for this integration type.</p>;
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[85vh]">
        <DialogHeader>
          <DialogTitle>{integration.name} Settings</DialogTitle>
          <DialogDescription>
            Configure {integration.integration_type_display} integration settings.
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="max-h-[60vh] pr-4">
          <div className="py-4">
            {renderSettingsForm()}
          </div>
        </ScrollArea>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isSaving}>
            {isSaving ? 'Saving...' : 'Save Settings'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Slack Settings Form
function SlackSettingsForm({
  data,
  onChange,
}: {
  data: Partial<SlackIntegrationSettings>;
  onChange: (data: Partial<SlackIntegrationSettings>) => void;
}) {
  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <h4 className="font-medium">Team Information</h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-muted-foreground text-sm">Team</Label>
            <p className="font-medium">{data.team_name || 'Not connected'}</p>
          </div>
          <div>
            <Label className="text-muted-foreground text-sm">Default Channel</Label>
            <p className="font-medium">{data.default_channel_name || 'Not set'}</p>
          </div>
        </div>
      </div>

      <Separator />

      <div className="space-y-4">
        <h4 className="font-medium">Notification Settings</h4>

        <NotificationToggle
          label="New Contact"
          description="Notify when a new contact is added"
          checked={data.notify_on_new_contact ?? false}
          onCheckedChange={(checked) => onChange({ ...data, notify_on_new_contact: checked })}
        />

        <NotificationToggle
          label="Hot Lead"
          description="Notify when a contact becomes a hot lead"
          checked={data.notify_on_hot_lead ?? false}
          onCheckedChange={(checked) => onChange({ ...data, notify_on_hot_lead: checked })}
        />

        <NotificationToggle
          label="Email Reply"
          description="Notify when a contact replies to an email"
          checked={data.notify_on_email_reply ?? false}
          onCheckedChange={(checked) => onChange({ ...data, notify_on_email_reply: checked })}
        />

        <NotificationToggle
          label="Campaign Complete"
          description="Notify when a campaign finishes"
          checked={data.notify_on_campaign_complete ?? false}
          onCheckedChange={(checked) => onChange({ ...data, notify_on_campaign_complete: checked })}
        />

        <NotificationToggle
          label="Form Submission"
          description="Notify when a lead submits a form"
          checked={data.notify_on_form_submit ?? false}
          onCheckedChange={(checked) => onChange({ ...data, notify_on_form_submit: checked })}
        />
      </div>

      <Separator />

      <div className="space-y-4">
        <h4 className="font-medium">Hot Lead Threshold</h4>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Score threshold for hot leads</span>
            <span className="font-medium">{data.hot_lead_threshold ?? 80}</span>
          </div>
          <Slider
            value={[data.hot_lead_threshold ?? 80]}
            onValueChange={([value]) => onChange({ ...data, hot_lead_threshold: value })}
            min={0}
            max={100}
            step={5}
          />
        </div>
      </div>
    </div>
  );
}

// Discord Settings Form
function DiscordSettingsForm({
  data,
  onChange,
}: {
  data: Partial<DiscordIntegrationSettings>;
  onChange: (data: Partial<DiscordIntegrationSettings>) => void;
}) {
  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <h4 className="font-medium">Webhook Settings</h4>
        <div className="space-y-2">
          <Label htmlFor="webhook-url">Webhook URL</Label>
          <Input
            id="webhook-url"
            type="url"
            value={data.webhook_url ?? ''}
            onChange={(e) => onChange({ ...data, webhook_url: e.target.value })}
            placeholder="https://discord.com/api/webhooks/..."
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="bot-username">Bot Username</Label>
            <Input
              id="bot-username"
              value={data.bot_username ?? ''}
              onChange={(e) => onChange({ ...data, bot_username: e.target.value })}
              placeholder="ColdMail"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="bot-avatar">Bot Avatar URL</Label>
            <Input
              id="bot-avatar"
              type="url"
              value={data.bot_avatar_url ?? ''}
              onChange={(e) => onChange({ ...data, bot_avatar_url: e.target.value })}
              placeholder="https://..."
            />
          </div>
        </div>
      </div>

      <Separator />

      <div className="space-y-4">
        <h4 className="font-medium">Notification Settings</h4>

        <NotificationToggle
          label="New Contact"
          description="Notify when a new contact is added"
          checked={data.notify_on_new_contact ?? false}
          onCheckedChange={(checked) => onChange({ ...data, notify_on_new_contact: checked })}
        />

        <NotificationToggle
          label="Hot Lead"
          description="Notify when a contact becomes a hot lead"
          checked={data.notify_on_hot_lead ?? false}
          onCheckedChange={(checked) => onChange({ ...data, notify_on_hot_lead: checked })}
        />

        <NotificationToggle
          label="Email Reply"
          description="Notify when a contact replies to an email"
          checked={data.notify_on_email_reply ?? false}
          onCheckedChange={(checked) => onChange({ ...data, notify_on_email_reply: checked })}
        />

        <NotificationToggle
          label="Campaign Complete"
          description="Notify when a campaign finishes"
          checked={data.notify_on_campaign_complete ?? false}
          onCheckedChange={(checked) => onChange({ ...data, notify_on_campaign_complete: checked })}
        />

        <NotificationToggle
          label="Form Submission"
          description="Notify when a lead submits a form"
          checked={data.notify_on_form_submit ?? false}
          onCheckedChange={(checked) => onChange({ ...data, notify_on_form_submit: checked })}
        />
      </div>

      <Separator />

      <div className="space-y-4">
        <h4 className="font-medium">Hot Lead Threshold</h4>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Score threshold for hot leads</span>
            <span className="font-medium">{data.hot_lead_threshold ?? 80}</span>
          </div>
          <Slider
            value={[data.hot_lead_threshold ?? 80]}
            onValueChange={([value]) => onChange({ ...data, hot_lead_threshold: value })}
            min={0}
            max={100}
            step={5}
          />
        </div>
      </div>
    </div>
  );
}

// HubSpot Settings Form
function HubSpotSettingsForm({
  data,
  onChange,
}: {
  data: Partial<HubSpotIntegrationSettings>;
  onChange: (data: Partial<HubSpotIntegrationSettings>) => void;
}) {
  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <h4 className="font-medium">Portal Information</h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-muted-foreground text-sm">Portal</Label>
            <p className="font-medium">{data.portal_name || 'Not connected'}</p>
          </div>
          <div>
            <Label className="text-muted-foreground text-sm">Portal ID</Label>
            <p className="font-medium font-mono text-sm">{data.portal_id || '-'}</p>
          </div>
        </div>
      </div>

      <Separator />

      <div className="space-y-4">
        <h4 className="font-medium">Sync Direction</h4>
        <Tabs
          value={data.sync_direction ?? 'bidirectional'}
          onValueChange={(value) => onChange({ ...data, sync_direction: value as HubSpotIntegrationSettings['sync_direction'] })}
        >
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="to_hubspot">To HubSpot</TabsTrigger>
            <TabsTrigger value="from_hubspot">From HubSpot</TabsTrigger>
            <TabsTrigger value="bidirectional">Both Ways</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <Separator />

      <div className="space-y-4">
        <h4 className="font-medium">Sync Options</h4>

        <NotificationToggle
          label="Sync Contacts"
          description="Sync contact records between systems"
          checked={data.sync_contacts ?? true}
          onCheckedChange={(checked) => onChange({ ...data, sync_contacts: checked })}
        />

        <NotificationToggle
          label="Sync Companies"
          description="Sync company records between systems"
          checked={data.sync_companies ?? false}
          onCheckedChange={(checked) => onChange({ ...data, sync_companies: checked })}
        />

        <NotificationToggle
          label="Sync Deals"
          description="Sync deal records between systems"
          checked={data.sync_deals ?? false}
          onCheckedChange={(checked) => onChange({ ...data, sync_deals: checked })}
        />

        <NotificationToggle
          label="Sync Activities"
          description="Sync email activities and notes"
          checked={data.sync_activities ?? true}
          onCheckedChange={(checked) => onChange({ ...data, sync_activities: checked })}
        />

        <NotificationToggle
          label="Only Sync Hot Leads"
          description="Only sync contacts above the score threshold"
          checked={data.sync_only_hot_leads ?? false}
          onCheckedChange={(checked) => onChange({ ...data, sync_only_hot_leads: checked })}
        />
      </div>

      {data.sync_only_hot_leads && (
        <>
          <Separator />
          <div className="space-y-4">
            <h4 className="font-medium">Minimum Score to Sync</h4>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Minimum lead score</span>
                <span className="font-medium">{data.min_score_to_sync ?? 50}</span>
              </div>
              <Slider
                value={[data.min_score_to_sync ?? 50]}
                onValueChange={([value]) => onChange({ ...data, min_score_to_sync: value })}
                min={0}
                max={100}
                step={5}
              />
            </div>
          </div>
        </>
      )}

      <Separator />

      <div className="space-y-4">
        <h4 className="font-medium">Auto Sync</h4>
        <div className="space-y-2">
          <Label htmlFor="auto-sync">Auto-sync interval (hours)</Label>
          <Input
            id="auto-sync"
            type="number"
            min={0}
            max={168}
            value={data.auto_sync_interval ?? 24}
            onChange={(e) => onChange({ ...data, auto_sync_interval: parseInt(e.target.value) || 0 })}
          />
          <p className="text-xs text-muted-foreground">Set to 0 to disable auto-sync</p>
        </div>
      </div>
    </div>
  );
}

// Salesforce Settings Form
function SalesforceSettingsForm({
  data,
  onChange,
}: {
  data: Partial<SalesforceIntegrationSettings>;
  onChange: (data: Partial<SalesforceIntegrationSettings>) => void;
}) {
  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <h4 className="font-medium">Organization Information</h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label className="text-muted-foreground text-sm">Organization</Label>
            <p className="font-medium">{data.org_name || 'Not connected'}</p>
          </div>
          <div>
            <Label className="text-muted-foreground text-sm">Instance URL</Label>
            <p className="font-medium text-sm truncate">{data.instance_url || '-'}</p>
          </div>
        </div>
      </div>

      <Separator />

      <div className="space-y-4">
        <h4 className="font-medium">Sync Direction</h4>
        <Tabs
          value={data.sync_direction ?? 'bidirectional'}
          onValueChange={(value) => onChange({ ...data, sync_direction: value as SalesforceIntegrationSettings['sync_direction'] })}
        >
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="to_salesforce">To Salesforce</TabsTrigger>
            <TabsTrigger value="from_salesforce">From Salesforce</TabsTrigger>
            <TabsTrigger value="bidirectional">Both Ways</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <Separator />

      <div className="space-y-4">
        <h4 className="font-medium">Record Type</h4>
        <NotificationToggle
          label="Create as Lead"
          description="Create new records as Leads instead of Contacts"
          checked={data.create_as_lead ?? true}
          onCheckedChange={(checked) => onChange({ ...data, create_as_lead: checked })}
        />
      </div>

      <Separator />

      <div className="space-y-4">
        <h4 className="font-medium">Sync Options</h4>

        <NotificationToggle
          label="Sync Leads"
          description="Sync lead records between systems"
          checked={data.sync_leads ?? true}
          onCheckedChange={(checked) => onChange({ ...data, sync_leads: checked })}
        />

        <NotificationToggle
          label="Sync Contacts"
          description="Sync contact records between systems"
          checked={data.sync_contacts ?? true}
          onCheckedChange={(checked) => onChange({ ...data, sync_contacts: checked })}
        />

        <NotificationToggle
          label="Sync Accounts"
          description="Sync account records between systems"
          checked={data.sync_accounts ?? false}
          onCheckedChange={(checked) => onChange({ ...data, sync_accounts: checked })}
        />

        <NotificationToggle
          label="Sync Opportunities"
          description="Sync opportunity records between systems"
          checked={data.sync_opportunities ?? false}
          onCheckedChange={(checked) => onChange({ ...data, sync_opportunities: checked })}
        />

        <NotificationToggle
          label="Sync Activities"
          description="Sync email activities and tasks"
          checked={data.sync_activities ?? true}
          onCheckedChange={(checked) => onChange({ ...data, sync_activities: checked })}
        />

        <NotificationToggle
          label="Only Sync Hot Leads"
          description="Only sync contacts above the score threshold"
          checked={data.sync_only_hot_leads ?? false}
          onCheckedChange={(checked) => onChange({ ...data, sync_only_hot_leads: checked })}
        />
      </div>

      {data.sync_only_hot_leads && (
        <>
          <Separator />
          <div className="space-y-4">
            <h4 className="font-medium">Minimum Score to Sync</h4>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>Minimum lead score</span>
                <span className="font-medium">{data.min_score_to_sync ?? 50}</span>
              </div>
              <Slider
                value={[data.min_score_to_sync ?? 50]}
                onValueChange={([value]) => onChange({ ...data, min_score_to_sync: value })}
                min={0}
                max={100}
                step={5}
              />
            </div>
          </div>
        </>
      )}

      <Separator />

      <div className="space-y-4">
        <h4 className="font-medium">Auto Sync</h4>
        <div className="space-y-2">
          <Label htmlFor="auto-sync">Auto-sync interval (hours)</Label>
          <Input
            id="auto-sync"
            type="number"
            min={0}
            max={168}
            value={data.auto_sync_interval ?? 24}
            onChange={(e) => onChange({ ...data, auto_sync_interval: parseInt(e.target.value) || 0 })}
          />
          <p className="text-xs text-muted-foreground">Set to 0 to disable auto-sync</p>
        </div>
      </div>
    </div>
  );
}

// Google Sheets Settings Form
function GoogleSheetsSettingsForm({
  data,
  onChange,
}: {
  data: Partial<GoogleSheetsIntegrationSettings>;
  onChange: (data: Partial<GoogleSheetsIntegrationSettings>) => void;
}) {
  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <h4 className="font-medium">Spreadsheet Information</h4>
        <div>
          <Label className="text-muted-foreground text-sm">Spreadsheet</Label>
          <p className="font-medium">{data.spreadsheet_name || 'Not connected'}</p>
          {data.spreadsheet_url && (
            <a
              href={data.spreadsheet_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary hover:underline"
            >
              Open in Google Sheets
            </a>
          )}
        </div>
      </div>

      <Separator />

      <div className="space-y-4">
        <h4 className="font-medium">Export Options</h4>

        <NotificationToggle
          label="Export Contacts"
          description="Export all contacts to the spreadsheet"
          checked={data.export_contacts ?? true}
          onCheckedChange={(checked) => onChange({ ...data, export_contacts: checked })}
        />

        <NotificationToggle
          label="Export Hot Leads"
          description="Export hot leads to a separate sheet"
          checked={data.export_hot_leads ?? true}
          onCheckedChange={(checked) => onChange({ ...data, export_hot_leads: checked })}
        />

        <NotificationToggle
          label="Export Campaign Stats"
          description="Export campaign statistics"
          checked={data.export_campaign_stats ?? true}
          onCheckedChange={(checked) => onChange({ ...data, export_campaign_stats: checked })}
        />
      </div>

      <Separator />

      <div className="space-y-4">
        <h4 className="font-medium">Sheet Names</h4>
        <div className="grid grid-cols-1 gap-4">
          <div className="space-y-2">
            <Label htmlFor="contacts-sheet">Contacts Sheet Name</Label>
            <Input
              id="contacts-sheet"
              value={data.contacts_sheet_name ?? 'Contacts'}
              onChange={(e) => onChange({ ...data, contacts_sheet_name: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="hot-leads-sheet">Hot Leads Sheet Name</Label>
            <Input
              id="hot-leads-sheet"
              value={data.hot_leads_sheet_name ?? 'Hot Leads'}
              onChange={(e) => onChange({ ...data, hot_leads_sheet_name: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="campaign-stats-sheet">Campaign Stats Sheet Name</Label>
            <Input
              id="campaign-stats-sheet"
              value={data.campaign_stats_sheet_name ?? 'Campaign Stats'}
              onChange={(e) => onChange({ ...data, campaign_stats_sheet_name: e.target.value })}
            />
          </div>
        </div>
      </div>

      <Separator />

      <div className="space-y-4">
        <h4 className="font-medium">Auto Export</h4>
        <div className="space-y-2">
          <Label htmlFor="auto-export">Auto-export interval (hours)</Label>
          <Input
            id="auto-export"
            type="number"
            min={0}
            max={168}
            value={data.auto_export_interval ?? 24}
            onChange={(e) => onChange({ ...data, auto_export_interval: parseInt(e.target.value) || 0 })}
          />
          <p className="text-xs text-muted-foreground">Set to 0 to disable auto-export</p>
        </div>
      </div>
    </div>
  );
}

// Reusable notification toggle component
function NotificationToggle({
  label,
  description,
  checked,
  onCheckedChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between">
      <div className="space-y-0.5">
        <Label>{label}</Label>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
      <Switch checked={checked} onCheckedChange={onCheckedChange} />
    </div>
  );
}

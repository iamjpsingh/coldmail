// ==================== Integration Types ====================

export type IntegrationType =
  | 'slack'
  | 'discord'
  | 'hubspot'
  | 'salesforce'
  | 'google_sheets'
  | 'zapier'
  | 'n8n'
  | 'custom_webhook';

export type IntegrationStatus = 'connected' | 'disconnected' | 'error' | 'pending';

export interface Integration {
  id: string;
  name: string;
  integration_type: IntegrationType;
  integration_type_display: string;
  description: string;
  status: IntegrationStatus;
  status_display: string;
  is_active: boolean;
  config: Record<string, unknown>;
  last_sync_at: string | null;
  last_error: string;
  last_error_at: string | null;
  total_syncs: number;
  successful_syncs: number;
  failed_syncs: number;
  success_rate: number;
  created_by_email: string | null;
  created_at: string;
  updated_at: string;
}

export interface IntegrationCreate {
  name: string;
  integration_type: IntegrationType;
  description?: string;
  config?: Record<string, unknown>;
}

export interface IntegrationTypeInfo {
  value: IntegrationType;
  label: string;
  description: string;
  requires_oauth: boolean;
  icon: string;
}

// ==================== Slack Types ====================

export interface SlackIntegrationSettings {
  id: string;
  team_id: string;
  team_name: string;
  default_channel_id: string;
  default_channel_name: string;
  notify_on_new_contact: boolean;
  notify_on_hot_lead: boolean;
  notify_on_email_reply: boolean;
  notify_on_campaign_complete: boolean;
  notify_on_sequence_complete: boolean;
  notify_on_form_submit: boolean;
  notify_on_website_visit: boolean;
  hot_lead_threshold: number;
}

// ==================== Discord Types ====================

export interface DiscordIntegrationSettings {
  id: string;
  webhook_url: string;
  notify_on_new_contact: boolean;
  notify_on_hot_lead: boolean;
  notify_on_email_reply: boolean;
  notify_on_campaign_complete: boolean;
  notify_on_sequence_complete: boolean;
  notify_on_form_submit: boolean;
  hot_lead_threshold: number;
  bot_username: string;
  bot_avatar_url: string;
}

export interface DiscordIntegrationCreate {
  name: string;
  description?: string;
  webhook_url: string;
  bot_username?: string;
  bot_avatar_url?: string;
}

// ==================== HubSpot Types ====================

export type HubSpotSyncDirection = 'to_hubspot' | 'from_hubspot' | 'bidirectional';

export interface HubSpotIntegrationSettings {
  id: string;
  portal_id: string;
  portal_name: string;
  sync_direction: HubSpotSyncDirection;
  sync_contacts: boolean;
  sync_companies: boolean;
  sync_deals: boolean;
  sync_activities: boolean;
  auto_sync_interval: number;
  last_auto_sync: string | null;
  field_mapping: Record<string, string>;
  sync_only_hot_leads: boolean;
  min_score_to_sync: number;
}

// ==================== Salesforce Types ====================

export type SalesforceSyncDirection = 'to_salesforce' | 'from_salesforce' | 'bidirectional';

export interface SalesforceIntegrationSettings {
  id: string;
  instance_url: string;
  org_id: string;
  org_name: string;
  sync_direction: SalesforceSyncDirection;
  sync_leads: boolean;
  sync_contacts: boolean;
  sync_accounts: boolean;
  sync_opportunities: boolean;
  sync_activities: boolean;
  auto_sync_interval: number;
  last_auto_sync: string | null;
  field_mapping: Record<string, string>;
  sync_only_hot_leads: boolean;
  min_score_to_sync: number;
  create_as_lead: boolean;
}

// ==================== Google Sheets Types ====================

export interface GoogleSheetsIntegrationSettings {
  id: string;
  spreadsheet_id: string;
  spreadsheet_name: string;
  spreadsheet_url: string;
  contacts_sheet_name: string;
  hot_leads_sheet_name: string;
  campaign_stats_sheet_name: string;
  export_contacts: boolean;
  export_hot_leads: boolean;
  export_campaign_stats: boolean;
  auto_export_interval: number;
  last_auto_export: string | null;
  contact_columns: string[];
  hot_lead_columns: string[];
}

// ==================== Integration Log Types ====================

export type IntegrationLogLevel = 'debug' | 'info' | 'warning' | 'error';
export type IntegrationOperation = 'sync' | 'export' | 'import' | 'notification' | 'auth' | 'test';

export interface IntegrationLog {
  id: string;
  level: IntegrationLogLevel;
  level_display: string;
  operation: IntegrationOperation;
  operation_display: string;
  message: string;
  records_processed: number;
  records_created: number;
  records_updated: number;
  records_failed: number;
  duration_ms: number | null;
  error_details: Record<string, unknown>;
  created_at: string;
}

// ==================== Response Types ====================

export interface TestConnectionResult {
  success: boolean;
  message: string;
}

export interface SyncResult {
  processed: number;
  created: number;
  updated: number;
  failed: number;
  skipped: number;
  errors: Array<{ email: string; error: string }>;
}

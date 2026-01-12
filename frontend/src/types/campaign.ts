export type CampaignStatus =
  | 'draft'
  | 'scheduled'
  | 'sending'
  | 'paused'
  | 'completed'
  | 'cancelled';

export type SendingMode = 'immediate' | 'scheduled' | 'spread';

export type RecipientStatus =
  | 'pending'
  | 'queued'
  | 'sending'
  | 'sent'
  | 'delivered'
  | 'opened'
  | 'clicked'
  | 'replied'
  | 'bounced'
  | 'failed'
  | 'unsubscribed'
  | 'complained'
  | 'skipped';

export type CampaignEventType =
  | 'queued'
  | 'sent'
  | 'delivered'
  | 'opened'
  | 'clicked'
  | 'replied'
  | 'bounced'
  | 'unsubscribed'
  | 'complained'
  | 'failed';

export interface ABTestVariant {
  id: string;
  name: string;
  subject: string;
  content_html: string;
  content_text: string;
  sent_count: number;
  opened_count: number;
  clicked_count: number;
  replied_count: number;
  is_winner: boolean;
  is_control: boolean;
  open_rate: number;
  click_rate: number;
  created_at: string;
  updated_at: string;
}

export interface ABTestVariantCreate {
  name: string;
  subject: string;
  content_html: string;
  content_text?: string;
  is_control?: boolean;
}

export interface Campaign {
  id: string;
  name: string;
  description: string;
  status: CampaignStatus;
  template: string | null;
  template_name: string;
  subject: string;
  content_html: string;
  content_text: string;
  email_account: string | null;
  email_account_name: string;
  email_account_email: string;
  from_name: string;
  reply_to: string;
  contact_lists: string[];
  contact_tags: string[];
  exclude_lists: string[];
  exclude_tags: string[];
  sending_mode: SendingMode;
  min_delay_seconds: number;
  max_delay_seconds: number;
  batch_size: number;
  batch_delay_minutes: number;
  scheduled_at: string | null;
  timezone: string;
  spread_start_time: string | null;
  spread_end_time: string | null;
  spread_days: number[];
  is_ab_test: boolean;
  ab_test_winner_criteria: string;
  ab_test_sample_size: number;
  ab_test_duration_hours: number;
  ab_variants: ABTestVariant[];
  track_opens: boolean;
  track_clicks: boolean;
  use_custom_tracking_domain: boolean;
  tracking_domain: string;
  include_unsubscribe_link: boolean;
  total_recipients: number;
  sent_count: number;
  delivered_count: number;
  opened_count: number;
  clicked_count: number;
  replied_count: number;
  bounced_count: number;
  unsubscribed_count: number;
  complained_count: number;
  failed_count: number;
  unique_opens: number;
  unique_clicks: number;
  open_rate: number;
  click_rate: number;
  reply_rate: number;
  bounce_rate: number;
  progress_percentage: number;
  started_at: string | null;
  completed_at: string | null;
  paused_at: string | null;
  created_by: string | null;
  created_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface CampaignCreate {
  name: string;
  description?: string;
  template?: string | null;
  subject: string;
  content_html: string;
  content_text?: string;
  email_account: string;
  from_name?: string;
  reply_to?: string;
  contact_list_ids?: string[];
  contact_tag_ids?: string[];
  exclude_list_ids?: string[];
  exclude_tag_ids?: string[];
  sending_mode?: SendingMode;
  min_delay_seconds?: number;
  max_delay_seconds?: number;
  batch_size?: number;
  batch_delay_minutes?: number;
  scheduled_at?: string | null;
  timezone?: string;
  spread_start_time?: string | null;
  spread_end_time?: string | null;
  spread_days?: number[];
  is_ab_test?: boolean;
  ab_test_winner_criteria?: string;
  ab_test_sample_size?: number;
  ab_test_duration_hours?: number;
  ab_variants?: ABTestVariantCreate[];
  track_opens?: boolean;
  track_clicks?: boolean;
  use_custom_tracking_domain?: boolean;
  tracking_domain?: string;
  include_unsubscribe_link?: boolean;
}

export interface CampaignListItem {
  id: string;
  name: string;
  status: CampaignStatus;
  email_account_email: string;
  total_recipients: number;
  sent_count: number;
  open_rate: number;
  click_rate: number;
  progress_percentage: number;
  scheduled_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  is_ab_test: boolean;
  created_at: string;
  updated_at: string;
}

export interface CampaignRecipient {
  id: string;
  contact: string;
  contact_email: string;
  contact_name: string;
  status: RecipientStatus;
  status_reason: string;
  ab_variant: string | null;
  ab_variant_name: string;
  rendered_subject: string;
  scheduled_at: string | null;
  send_after: string | null;
  queued_at: string | null;
  sent_at: string | null;
  delivered_at: string | null;
  opened_at: string | null;
  clicked_at: string | null;
  replied_at: string | null;
  bounced_at: string | null;
  unsubscribed_at: string | null;
  open_count: number;
  click_count: number;
  message_id: string;
  retry_count: number;
  last_error: string;
  created_at: string;
}

export interface CampaignEvent {
  id: string;
  event_type: CampaignEventType;
  metadata: Record<string, unknown>;
  clicked_url: string;
  ip_address: string | null;
  user_agent: string;
  device_type: string;
  browser: string;
  os: string;
  country: string;
  city: string;
  is_bot: boolean;
  created_at: string;
}

export interface CampaignLog {
  id: string;
  log_type: string;
  message: string;
  details: Record<string, unknown>;
  created_by: string | null;
  created_by_name: string;
  created_at: string;
}

export interface CampaignStats {
  total_recipients: number;
  sent: number;
  delivered: number;
  opened: number;
  unique_opens: number;
  clicked: number;
  unique_clicks: number;
  replied: number;
  bounced: number;
  unsubscribed: number;
  complained: number;
  failed: number;
  open_rate: number;
  click_rate: number;
  reply_rate: number;
  bounce_rate: number;
  progress: number;
}

export interface CampaignSummary {
  total: number;
  draft: number;
  scheduled: number;
  sending: number;
  paused: number;
  completed: number;
  cancelled: number;
  total_emails_sent: number;
  total_opens: number;
  total_clicks: number;
  total_replies: number;
}

export interface ScheduleCampaignRequest {
  scheduled_at: string;
  timezone?: string;
}

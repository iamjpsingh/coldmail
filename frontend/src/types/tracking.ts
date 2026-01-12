export interface TrackingDomain {
  id: string;
  workspace: string;
  domain: string;
  is_verified: boolean;
  is_default: boolean;
  ssl_enabled: boolean;
  verification_token: string;
  verified_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface TrackingDomainCreate {
  domain: string;
  ssl_enabled?: boolean;
  is_default?: boolean;
}

export interface DNSRecord {
  type: string;
  name: string;
  value: string;
  purpose: string;
}

export interface TrackingLink {
  id: string;
  campaign_recipient: string;
  token: string;
  original_url: string;
  click_count: number;
  first_clicked_at: string | null;
  last_clicked_at: string | null;
  created_at: string;
}

export interface TrackingPixel {
  id: string;
  campaign_recipient: string;
  token: string;
  open_count: number;
  first_opened_at: string | null;
  last_opened_at: string | null;
  created_at: string;
}

export type TrackingEventType =
  | 'open'
  | 'click'
  | 'unsubscribe'
  | 'bounce'
  | 'complaint'
  | 'delivery';

export type BounceType = 'hard' | 'soft' | 'complaint';

export interface TrackingEvent {
  id: string;
  event_type: TrackingEventType;
  campaign_recipient: string;
  tracking_link: string | null;
  clicked_url: string;
  bounce_type: BounceType | '';
  bounce_code: string;
  bounce_message: string;
  ip_address: string | null;
  user_agent: string;
  device_type: string;
  device_brand: string;
  device_model: string;
  browser_name: string;
  browser_version: string;
  os_name: string;
  os_version: string;
  country: string;
  country_code: string;
  region: string;
  city: string;
  is_bot: boolean;
  bot_name: string;
  created_at: string;
}

export interface TrackingEventListItem {
  id: string;
  event_type: TrackingEventType;
  contact_email: string;
  campaign_name: string;
  clicked_url: string;
  device_type: string;
  browser_name: string;
  os_name: string;
  country: string;
  city: string;
  is_bot: boolean;
  created_at: string;
}

export interface UnsubscribeToken {
  id: string;
  contact: string;
  contact_email: string;
  campaign: string | null;
  campaign_name: string | null;
  token: string;
  is_used: boolean;
  used_at: string | null;
  reason: string;
  created_at: string;
}

export type BounceCategory =
  | 'invalid'
  | 'mailbox_full'
  | 'blocked'
  | 'content'
  | 'timeout'
  | 'other';

export interface BounceRecord {
  id: string;
  email: string;
  workspace: string;
  email_account: string | null;
  campaign: string | null;
  campaign_name: string | null;
  campaign_recipient: string | null;
  bounce_type: 'hard' | 'soft';
  bounce_category: BounceCategory;
  bounce_code: string;
  bounce_message: string;
  message_id: string;
  created_at: string;
}

export type ComplaintType = 'spam' | 'abuse' | 'other';

export interface ComplaintRecord {
  id: string;
  email: string;
  workspace: string;
  email_account: string | null;
  campaign: string | null;
  campaign_name: string | null;
  campaign_recipient: string | null;
  complaint_type: ComplaintType;
  feedback_id: string;
  message_id: string;
  created_at: string;
}

export type SuppressionReason =
  | 'hard_bounce'
  | 'complaint'
  | 'unsubscribe'
  | 'manual';

export interface SuppressionListItem {
  id: string;
  email: string;
  workspace: string;
  reason: SuppressionReason;
  source: string;
  notes: string;
  created_at: string;
}

export interface SuppressionListCreate {
  email: string;
  reason: SuppressionReason;
  source?: string;
  notes?: string;
}

export interface TrackingStats {
  total_opens: number;
  unique_opens: number;
  total_clicks: number;
  unique_clicks: number;
  total_unsubscribes: number;
  total_bounces: number;
  hard_bounces: number;
  soft_bounces: number;
  total_complaints: number;
  suppressed_count: number;
  bot_opens: number;
  bot_clicks: number;
}

export interface DeviceBreakdown {
  device_type: string;
  count: number;
  percentage: number;
}

export interface LocationBreakdown {
  country: string;
  country_code: string;
  count: number;
  percentage: number;
}

export interface BrowserBreakdown {
  browser_name: string;
  count: number;
  percentage: number;
}

export interface BounceStats {
  total: number;
  hard: number;
  soft: number;
  by_category: Array<{
    bounce_category: BounceCategory;
    count: number;
  }>;
}

export interface ComplaintStats {
  total: number;
  by_type: Array<{
    complaint_type: ComplaintType;
    count: number;
  }>;
}

export interface SuppressionStats {
  total: number;
  by_reason: Array<{
    reason: SuppressionReason;
    count: number;
  }>;
}

// ==================== Website Tracking Types ====================

export interface WebsiteTrackingScript {
  id: string;
  workspace: string;
  script_id: string;
  is_enabled: boolean;
  track_page_views: boolean;
  track_clicks: boolean;
  track_forms: boolean;
  track_scroll_depth: boolean;
  track_time_on_page: boolean;
  allowed_domains: string;
  award_score_on_visit: boolean;
  visit_score_points: number;
  page_view_score_points: number;
  session_timeout_minutes: number;
  snippet_url: string;
  embed_code: string;
  created_at: string;
  updated_at: string;
}

export interface WebsiteTrackingScriptUpdate {
  is_enabled?: boolean;
  track_page_views?: boolean;
  track_clicks?: boolean;
  track_forms?: boolean;
  track_scroll_depth?: boolean;
  track_time_on_page?: boolean;
  allowed_domains?: string;
  award_score_on_visit?: boolean;
  visit_score_points?: number;
  page_view_score_points?: number;
  session_timeout_minutes?: number;
}

export interface VisitorSession {
  id: string;
  session_id: string;
  started_at: string;
  ended_at: string | null;
  is_active: boolean;
  entry_page: string;
  referrer: string;
  exit_page: string;
  utm_source: string;
  utm_medium: string;
  utm_campaign: string;
  page_views: number;
  duration_seconds: number;
  max_scroll_depth: number;
  ip_address: string | null;
  created_at: string;
}

export interface PageView {
  id: string;
  page_url: string;
  page_path: string;
  page_title: string;
  referrer: string;
  time_on_page: number;
  scroll_depth: number;
  created_at: string;
}

export type WebsiteEventType =
  | 'page_view'
  | 'click'
  | 'form_submit'
  | 'form_start'
  | 'scroll'
  | 'video_play'
  | 'video_complete'
  | 'download'
  | 'outbound_link'
  | 'custom';

export interface WebsiteEvent {
  id: string;
  event_type: WebsiteEventType;
  event_name: string;
  page_url: string;
  page_path: string;
  element_id: string;
  element_class: string;
  element_text: string;
  target_url: string;
  properties: Record<string, unknown>;
  created_at: string;
}

export interface WebsiteVisitor {
  id: string;
  visitor_id: string;
  contact: string | null;
  contact_email: string | null;
  contact_name: string | null;
  is_identified: boolean;
  identified_at: string | null;
  identification_method: string;
  first_seen_at: string;
  first_page_url: string;
  first_referrer: string;
  last_seen_at: string;
  last_page_url: string;
  utm_source: string;
  utm_medium: string;
  utm_campaign: string;
  utm_term: string;
  utm_content: string;
  device_type: string;
  browser_name: string;
  browser_version: string;
  os_name: string;
  os_version: string;
  screen_resolution: string;
  ip_address: string | null;
  country: string;
  country_code: string;
  region: string;
  city: string;
  timezone: string;
  company_name: string;
  company_domain: string;
  company_industry: string;
  company_size: string;
  total_sessions: number;
  total_page_views: number;
  total_time_on_site: number;
  created_at: string;
  updated_at: string;
}

export interface WebsiteVisitorListItem {
  id: string;
  visitor_id: string;
  contact: string | null;
  contact_email: string | null;
  contact_name: string | null;
  is_identified: boolean;
  first_seen_at: string;
  last_seen_at: string;
  device_type: string;
  country: string;
  city: string;
  company_name: string;
  total_sessions: number;
  total_page_views: number;
  total_time_on_site: number;
}

export interface WebsiteVisitorDetail extends WebsiteVisitor {
  sessions: VisitorSession[];
  recent_page_views: PageView[];
  recent_events: WebsiteEvent[];
}

export type VisitorIdentificationMethod =
  | 'email_link'
  | 'form_submit'
  | 'api'
  | 'manual'
  | 'ip_match';

export interface VisitorIdentification {
  id: string;
  visitor: string;
  contact: string;
  method: VisitorIdentificationMethod;
  email: string;
  source: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface WebsiteTrackingStats {
  total_visitors: number;
  identified_visitors: number;
  anonymous_visitors: number;
  total_sessions: number;
  total_page_views: number;
  average_session_duration: number;
  average_pages_per_session: number;
  bounce_rate: number;
  new_visitors_today: number;
  returning_visitors_today: number;
}

export interface TopPage {
  page_path: string;
  page_title: string;
  views: number;
}

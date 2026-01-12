export type ContactStatus = 'active' | 'unsubscribed' | 'bounced' | 'complained';

export interface Tag {
  id: string;
  name: string;
  color: string;
  contact_count: number;
  created_at: string;
  updated_at: string;
}

export interface Contact {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  company: string;
  job_title: string;
  phone: string;
  website: string;
  linkedin_url: string;
  twitter_handle: string;
  city: string;
  state: string;
  country: string;
  timezone: string;
  custom_fields: Record<string, unknown>;
  status: ContactStatus;
  score: number;
  score_updated_at: string | null;
  source: string;
  source_details: Record<string, unknown>;
  tags: Tag[];
  emails_sent: number;
  emails_opened: number;
  emails_clicked: number;
  emails_replied: number;
  emails_bounced: number;
  open_rate: number;
  click_rate: number;
  reply_rate: number;
  last_emailed_at: string | null;
  last_opened_at: string | null;
  last_clicked_at: string | null;
  last_replied_at: string | null;
  unsubscribed_at: string | null;
  unsubscribe_reason: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface ContactCreate {
  email: string;
  first_name?: string;
  last_name?: string;
  company?: string;
  job_title?: string;
  phone?: string;
  website?: string;
  linkedin_url?: string;
  twitter_handle?: string;
  city?: string;
  state?: string;
  country?: string;
  timezone?: string;
  custom_fields?: Record<string, unknown>;
  source?: string;
  source_details?: Record<string, unknown>;
  tag_ids?: string[];
  notes?: string;
}

export interface ContactList {
  id: string;
  name: string;
  description: string;
  list_type: 'static' | 'smart';
  filter_criteria: Record<string, unknown>;
  contact_count: number;
  last_count_updated_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContactActivity {
  id: string;
  activity_type: string;
  description: string;
  metadata: Record<string, unknown>;
  campaign_id: string | null;
  sequence_id: string | null;
  email_id: string | null;
  created_at: string;
}

export interface CustomField {
  id: string;
  name: string;
  field_key: string;
  field_type: 'text' | 'number' | 'date' | 'boolean' | 'select' | 'multiselect' | 'url' | 'email';
  description: string;
  is_required: boolean;
  default_value: string;
  options: string[];
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface ImportJob {
  id: string;
  file_name: string;
  file_type: 'csv' | 'excel' | 'json';
  field_mapping: Record<string, string>;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  total_rows: number;
  processed_rows: number;
  created_count: number;
  updated_count: number;
  skipped_count: number;
  error_count: number;
  errors: Array<{ row: number; error: string }>;
  progress_percentage: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface ContactSearchParams {
  query?: string;
  status?: ContactStatus;
  tags?: string[];
  min_score?: number;
  max_score?: number;
  company?: string;
  job_title?: string;
  country?: string;
  city?: string;
  source?: string;
  has_opened?: boolean;
  has_clicked?: boolean;
  has_replied?: boolean;
}

// Scoring types
export type ScoringEventType =
  | 'email_opened'
  | 'email_clicked'
  | 'email_replied'
  | 'email_bounced'
  | 'email_unsubscribed'
  | 'link_clicked'
  | 'form_submitted'
  | 'page_visited'
  | 'meeting_scheduled'
  | 'manual'
  | 'decay'
  | 'import';

export type ScoreClassification = 'hot' | 'warm' | 'cold';

export interface ScoringRule {
  id: string;
  name: string;
  description: string;
  is_active: boolean;
  event_type: ScoringEventType;
  conditions: ScoringCondition[];
  score_change: number;
  max_applications: number | null;
  cooldown_hours: number | null;
  priority: number;
  applications_count: number;
  created_at: string;
  updated_at: string;
}

export interface ScoringCondition {
  field: string;
  operator: 'equals' | 'not_equals' | 'contains' | 'not_contains' | 'greater_than' | 'less_than' | 'is_set' | 'is_not_set';
  value: string | number | boolean;
}

export interface ScoringRuleCreate {
  name: string;
  description?: string;
  is_active?: boolean;
  event_type: ScoringEventType;
  conditions?: ScoringCondition[];
  score_change: number;
  max_applications?: number | null;
  cooldown_hours?: number | null;
  priority?: number;
}

export interface ScoreHistory {
  id: string;
  previous_score: number;
  new_score: number;
  score_change: number;
  reason: string;
  rule: string | null;
  rule_name: string | null;
  event_type: ScoringEventType;
  event_data: Record<string, unknown>;
  created_at: string;
}

export interface ScoreThreshold {
  id: string;
  classification: ScoreClassification;
  min_score: number;
  max_score: number | null;
  color: string;
  contacts_count: number;
  created_at: string;
  updated_at: string;
}

export interface ScoreThresholdCreate {
  classification: ScoreClassification;
  min_score: number;
  max_score?: number | null;
  color?: string;
}

export interface ScoreDecayConfig {
  id: string;
  is_enabled: boolean;
  decay_points: number;
  decay_interval_days: number;
  min_score: number;
  inactivity_days: number;
  last_run_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScoreDecayConfigUpdate {
  is_enabled?: boolean;
  decay_points?: number;
  decay_interval_days?: number;
  min_score?: number;
  inactivity_days?: number;
}

export interface ScoringStats {
  total_contacts: number;
  average_score: number;
  hot_count: number;
  warm_count: number;
  cold_count: number;
  hot_percentage: number;
  warm_percentage: number;
  cold_percentage: number;
}

export interface ScoreAdjustment {
  score?: number;
  adjustment?: number;
  reason?: string;
}

export interface ApplyEventRequest {
  event_type: ScoringEventType;
  event_data?: Record<string, unknown>;
}

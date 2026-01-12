export type SequenceStatus = 'draft' | 'active' | 'paused' | 'archived';
export type StepType = 'email' | 'delay' | 'condition' | 'task' | 'webhook' | 'tag';
export type DelayUnit = 'minutes' | 'hours' | 'days' | 'weeks';
export type EnrollmentStatus = 'active' | 'paused' | 'completed' | 'stopped' | 'failed';
export type StopReason =
  | 'completed'
  | 'manual'
  | 'reply'
  | 'click'
  | 'open'
  | 'unsubscribe'
  | 'bounce'
  | 'score_high'
  | 'score_low'
  | 'contact_deleted'
  | 'sequence_paused'
  | 'sequence_deleted'
  | 'error';

export type ExecutionStatus =
  | 'pending'
  | 'scheduled'
  | 'sending'
  | 'sent'
  | 'delivered'
  | 'opened'
  | 'clicked'
  | 'replied'
  | 'bounced'
  | 'failed'
  | 'skipped';

export type SequenceEventType =
  | 'enrolled'
  | 'started'
  | 'step_executed'
  | 'email_sent'
  | 'email_opened'
  | 'email_clicked'
  | 'email_replied'
  | 'email_bounced'
  | 'paused'
  | 'resumed'
  | 'stopped'
  | 'completed'
  | 'error'
  | 'tag_added'
  | 'tag_removed'
  | 'webhook_triggered'
  | 'task_created';

export interface SequenceStep {
  id: string;
  sequence: string;
  order: number;
  step_type: StepType;
  name: string;
  // Email fields
  subject: string;
  content_html: string;
  content_text: string;
  template: string | null;
  // Delay fields
  delay_value: number;
  delay_unit: DelayUnit;
  delay_seconds: number;
  // Condition fields
  condition_type: string;
  condition_value: Record<string, unknown>;
  true_branch_step: string | null;
  false_branch_step: string | null;
  // Tag fields
  tag_action: 'add' | 'remove' | '';
  tag: string | null;
  // Webhook fields
  webhook_url: string;
  webhook_method: string;
  webhook_headers: Record<string, string>;
  webhook_payload: Record<string, unknown>;
  // Task fields
  task_title: string;
  task_description: string;
  task_assignee: string | null;
  // Stats
  sent_count: number;
  opened_count: number;
  clicked_count: number;
  replied_count: number;
  bounced_count: number;
  open_rate: number;
  click_rate: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Sequence {
  id: string;
  workspace: string;
  name: string;
  description: string;
  status: SequenceStatus;
  // Sender settings
  email_account: string | null;
  email_account_email?: string;
  from_name: string;
  reply_to: string;
  // Tracking
  track_opens: boolean;
  track_clicks: boolean;
  include_unsubscribe_link: boolean;
  // Sending window
  send_window_enabled: boolean;
  send_window_start: string | null;
  send_window_end: string | null;
  send_window_days: number[];
  send_window_timezone: string;
  // Throttling
  max_emails_per_day: number;
  min_delay_between_emails: number;
  // Stop conditions
  stop_on_reply: boolean;
  stop_on_click: boolean;
  stop_on_open: boolean;
  stop_on_unsubscribe: boolean;
  stop_on_bounce: boolean;
  stop_on_score_above: number | null;
  stop_on_score_below: number | null;
  // Stats
  total_enrolled: number;
  active_enrolled: number;
  completed_count: number;
  stopped_count: number;
  total_sent: number;
  total_opened: number;
  total_clicked: number;
  total_replied: number;
  open_rate: number;
  click_rate: number;
  reply_rate: number;
  // Steps
  steps: SequenceStep[];
  step_count: number;
  // Metadata
  created_by: string | null;
  created_by_email?: string;
  created_at: string;
  updated_at: string;
}

export interface SequenceListItem {
  id: string;
  name: string;
  description: string;
  status: SequenceStatus;
  email_account: string | null;
  total_enrolled: number;
  active_enrolled: number;
  completed_count: number;
  total_sent: number;
  total_opened: number;
  total_clicked: number;
  total_replied: number;
  open_rate: number;
  click_rate: number;
  reply_rate: number;
  step_count: number;
  created_at: string;
  updated_at: string;
}

export interface SequenceEnrollment {
  id: string;
  sequence: string;
  sequence_name: string;
  contact: {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    company: string;
  };
  status: EnrollmentStatus;
  stop_reason: StopReason | '';
  stop_reason_display: string;
  stop_details: string;
  current_step: string | null;
  current_step_name: string | null;
  current_step_index: number;
  next_step_at: string | null;
  last_step_at: string | null;
  enrolled_at: string;
  started_at: string | null;
  completed_at: string | null;
  stopped_at: string | null;
  paused_at: string | null;
  emails_sent: number;
  emails_opened: number;
  emails_clicked: number;
  has_replied: boolean;
  enrolled_by: string | null;
  enrollment_source: string;
  retry_count: number;
  last_error: string;
  created_at: string;
  updated_at: string;
}

export interface SequenceEnrollmentListItem {
  id: string;
  sequence: string;
  contact_email: string;
  contact_name: string;
  status: EnrollmentStatus;
  current_step_index: number;
  current_step_name: string | null;
  next_step_at: string | null;
  emails_sent: number;
  emails_opened: number;
  emails_clicked: number;
  has_replied: boolean;
  enrolled_at: string;
}

export interface SequenceStepExecution {
  id: string;
  enrollment: string;
  step: string;
  step_name: string;
  step_type: StepType;
  status: ExecutionStatus;
  status_reason: string;
  rendered_subject: string;
  rendered_html: string;
  rendered_text: string;
  scheduled_at: string | null;
  executed_at: string | null;
  sent_at: string | null;
  delivered_at: string | null;
  opened_at: string | null;
  clicked_at: string | null;
  replied_at: string | null;
  message_id: string;
  email_account: string | null;
  open_count: number;
  click_count: number;
  clicked_urls: string[];
  retry_count: number;
  last_error: string;
  created_at: string;
  updated_at: string;
}

export interface SequenceEvent {
  id: string;
  enrollment: string;
  contact_email: string;
  step: string | null;
  step_name: string | null;
  event_type: SequenceEventType;
  event_type_display: string;
  message: string;
  metadata: Record<string, unknown>;
  clicked_url: string;
  ip_address: string | null;
  user_agent: string;
  device_type: string;
  browser: string;
  country: string;
  is_bot: boolean;
  created_at: string;
}

export interface SequenceStats {
  total_enrolled: number;
  active_enrolled: number;
  completed: number;
  stopped: number;
  total_sent: number;
  total_opened: number;
  total_clicked: number;
  total_replied: number;
  open_rate: number;
  click_rate: number;
  reply_rate: number;
  steps: number;
}

export interface StepStats {
  order: number;
  type: StepType;
  name: string;
  sent: number;
  opened: number;
  clicked: number;
  replied: number;
  bounced: number;
  open_rate: number;
  click_rate: number;
}

export interface SequenceStatsResponse {
  stats: SequenceStats;
  step_stats: StepStats[];
}

// API Request/Response types
export interface CreateSequenceRequest {
  name: string;
  description?: string;
  email_account?: string;
  from_name?: string;
  reply_to?: string;
  track_opens?: boolean;
  track_clicks?: boolean;
  include_unsubscribe_link?: boolean;
  send_window_enabled?: boolean;
  send_window_start?: string;
  send_window_end?: string;
  send_window_days?: number[];
  send_window_timezone?: string;
  max_emails_per_day?: number;
  min_delay_between_emails?: number;
  stop_on_reply?: boolean;
  stop_on_click?: boolean;
  stop_on_open?: boolean;
  stop_on_unsubscribe?: boolean;
  stop_on_bounce?: boolean;
  stop_on_score_above?: number;
  stop_on_score_below?: number;
  steps?: CreateStepRequest[];
}

export interface UpdateSequenceRequest {
  name?: string;
  description?: string;
  email_account?: string | null;
  from_name?: string;
  reply_to?: string;
  track_opens?: boolean;
  track_clicks?: boolean;
  include_unsubscribe_link?: boolean;
  send_window_enabled?: boolean;
  send_window_start?: string | null;
  send_window_end?: string | null;
  send_window_days?: number[];
  send_window_timezone?: string;
  max_emails_per_day?: number;
  min_delay_between_emails?: number;
  stop_on_reply?: boolean;
  stop_on_click?: boolean;
  stop_on_open?: boolean;
  stop_on_unsubscribe?: boolean;
  stop_on_bounce?: boolean;
  stop_on_score_above?: number | null;
  stop_on_score_below?: number | null;
}

export interface CreateStepRequest {
  sequence?: string;
  order?: number;
  step_type: StepType;
  name?: string;
  subject?: string;
  content_html?: string;
  content_text?: string;
  template?: string;
  delay_value?: number;
  delay_unit?: DelayUnit;
  condition_type?: string;
  condition_value?: Record<string, unknown>;
  tag_action?: 'add' | 'remove';
  tag?: string;
  webhook_url?: string;
  webhook_method?: string;
  webhook_headers?: Record<string, string>;
  webhook_payload?: Record<string, unknown>;
  task_title?: string;
  task_description?: string;
  task_assignee?: string;
  is_active?: boolean;
}

export interface UpdateStepRequest extends Partial<CreateStepRequest> {}

export interface EnrollContactRequest {
  contact_id: string;
  source?: string;
}

export interface BulkEnrollRequest {
  contact_ids: string[];
  source?: string;
}

export interface BulkEnrollResponse {
  success: boolean;
  enrolled: number;
  failed: number;
  errors: string[];
}

export interface EnrollmentsListResponse {
  results: SequenceEnrollmentListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface PaginatedResponse<T> {
  results: T[];
  count: number;
  next: string | null;
  previous: string | null;
}

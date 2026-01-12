// ==================== API Key Types ====================

export type APIKeyPermission = 'read' | 'write' | 'admin';

export interface APIKey {
  id: string;
  name: string;
  description: string;
  key_prefix: string;
  permission: APIKeyPermission;
  allowed_ips: string;
  allowed_ips_list: string[];
  rate_limit_per_minute: number;
  rate_limit_per_day: number;
  is_active: boolean;
  expires_at: string | null;
  is_expired: boolean;
  last_used_at: string | null;
  last_used_ip: string | null;
  total_requests: number;
  created_by_email: string | null;
  created_at: string;
  updated_at: string;
}

export interface APIKeyCreate {
  name: string;
  description?: string;
  permission?: APIKeyPermission;
  allowed_ips?: string;
  rate_limit_per_minute?: number;
  rate_limit_per_day?: number;
  expires_at?: string | null;
}

export interface APIKeyUpdate {
  name?: string;
  description?: string;
  permission?: APIKeyPermission;
  allowed_ips?: string;
  rate_limit_per_minute?: number;
  rate_limit_per_day?: number;
  is_active?: boolean;
  expires_at?: string | null;
}

export interface APIKeyCreateResponse {
  id: string;
  name: string;
  description: string;
  key_prefix: string;
  permission: APIKeyPermission;
  raw_key: string;
  created_at: string;
}

// ==================== Webhook Types ====================

export type WebhookEventType =
  // Contact events
  | 'contact.created'
  | 'contact.updated'
  | 'contact.deleted'
  | 'contact.scored'
  | 'contact.tag_added'
  | 'contact.tag_removed'
  // Campaign events
  | 'campaign.created'
  | 'campaign.started'
  | 'campaign.paused'
  | 'campaign.completed'
  | 'campaign.cancelled'
  // Email events
  | 'email.sent'
  | 'email.delivered'
  | 'email.opened'
  | 'email.clicked'
  | 'email.bounced'
  | 'email.complained'
  | 'email.unsubscribed'
  | 'email.replied'
  // Sequence events
  | 'sequence.enrolled'
  | 'sequence.completed'
  | 'sequence.stopped'
  | 'sequence.step_executed'
  // Website tracking events
  | 'visitor.identified'
  | 'visitor.page_view'
  | 'visitor.form_submit'
  // Special
  | 'webhook.test'
  | '*';

export interface WebhookEventTypeOption {
  value: WebhookEventType;
  label: string;
  category: string;
}

export interface Webhook {
  id: string;
  name: string;
  description: string;
  url: string;
  events: WebhookEventType[];
  verify_ssl: boolean;
  headers: Record<string, string>;
  is_active: boolean;
  timeout_seconds: number;
  max_retries: number;
  retry_delay_seconds: number;
  total_deliveries: number;
  successful_deliveries: number;
  failed_deliveries: number;
  success_rate: number;
  last_delivery_at: string | null;
  last_success_at: string | null;
  last_failure_at: string | null;
  last_error: string;
  consecutive_failures: number;
  disabled_at: string | null;
  disabled_reason: string;
  created_by_email: string | null;
  created_at: string;
  updated_at: string;
}

export interface WebhookCreate {
  name: string;
  description?: string;
  url: string;
  events: WebhookEventType[];
  verify_ssl?: boolean;
  headers?: Record<string, string>;
  timeout_seconds?: number;
  max_retries?: number;
  retry_delay_seconds?: number;
}

export interface WebhookUpdate {
  name?: string;
  description?: string;
  url?: string;
  events?: WebhookEventType[];
  verify_ssl?: boolean;
  headers?: Record<string, string>;
  is_active?: boolean;
  timeout_seconds?: number;
  max_retries?: number;
  retry_delay_seconds?: number;
}

export interface WebhookSecret {
  secret: string;
}

export interface WebhookTestResult {
  success: boolean;
  delivery_id: string;
  status_code: number | null;
  error: string | null;
}

// ==================== Webhook Delivery Types ====================

export type WebhookDeliveryStatus =
  | 'pending'
  | 'processing'
  | 'success'
  | 'failed'
  | 'retrying';

export interface WebhookDelivery {
  id: string;
  webhook: string;
  webhook_name: string;
  event_type: string;
  event_id: string;
  payload: Record<string, unknown>;
  request_headers: Record<string, string>;
  status: WebhookDeliveryStatus;
  response_status_code: number | null;
  response_headers: Record<string, string>;
  response_body: string;
  error_message: string;
  duration_ms: number | null;
  delivered_at: string | null;
  attempt_number: number;
  next_retry_at: string | null;
  created_at: string;
}

export interface WebhookDeliveryListItem {
  id: string;
  webhook: string;
  webhook_name: string;
  event_type: string;
  event_id: string;
  status: WebhookDeliveryStatus;
  response_status_code: number | null;
  duration_ms: number | null;
  attempt_number: number;
  created_at: string;
  delivered_at: string | null;
}

// ==================== Webhook Event Log Types ====================

export interface WebhookEventLog {
  id: string;
  event_id: string;
  event_type: string;
  payload: Record<string, unknown>;
  contact_id: string | null;
  campaign_id: string | null;
  sequence_id: string | null;
  webhooks_triggered: number;
  processed_at: string | null;
  created_at: string;
}

export interface WebhookEventLogListItem {
  id: string;
  event_id: string;
  event_type: string;
  webhooks_triggered: number;
  processed_at: string | null;
  created_at: string;
}

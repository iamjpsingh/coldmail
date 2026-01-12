export type EmailProvider = 'smtp' | 'gmail' | 'outlook' | 'sendgrid' | 'mailgun' | 'aws_ses';
export type EmailAccountStatus = 'active' | 'paused' | 'error' | 'disconnected';

export interface EmailAccount {
  id: string;
  name: string;
  email: string;
  provider: EmailProvider;
  status: EmailAccountStatus;
  from_name: string;
  reply_to: string;
  signature: string;
  daily_limit: number;
  hourly_limit: number;
  emails_sent_today: number;
  emails_sent_this_hour: number;
  is_warming_up: boolean;
  warmup_current_limit: number;
  can_send: boolean;
  remaining_today: number;
  remaining_this_hour: number;
  is_oauth: boolean;
  last_connection_test: string | null;
  last_connection_success: boolean;
  last_email_sent_at: string | null;
  total_emails_sent: number;
  bounce_rate: number;
  reputation_score: number;
  created_at: string;
  updated_at: string;
}

export interface EmailAccountCreate {
  name: string;
  email: string;
  provider: EmailProvider;
  smtp_host?: string;
  smtp_port?: number;
  smtp_username?: string;
  smtp_password?: string;
  smtp_use_tls?: boolean;
  smtp_use_ssl?: boolean;
  from_name?: string;
  reply_to?: string;
  daily_limit?: number;
  hourly_limit?: number;
}

export interface EmailAccountStats {
  total_emails_sent: number;
  emails_sent_today: number;
  emails_sent_this_hour: number;
  remaining_today: number;
  remaining_this_hour: number;
  can_send: boolean;
  bounce_rate: number;
  reputation_score: number;
  is_warming_up: boolean;
  warmup_current_limit: number;
  last_email_sent_at: string | null;
}

export interface EmailAccountLog {
  id: string;
  log_type: string;
  message: string;
  details: Record<string, unknown>;
  is_success: boolean;
  created_at: string;
}

export interface ConnectionTestResult {
  success: boolean;
  results: {
    smtp?: { success: boolean; message: string };
    imap?: { success: boolean; message: string };
  };
}

export interface SendTestEmailRequest {
  to_email: string;
  subject?: string;
  body?: string;
}

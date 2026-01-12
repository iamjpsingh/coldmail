export interface DashboardStats {
  contacts: {
    total: number;
    new: number;
    active: number;
    hot_leads: number;
  };
  campaigns: {
    total: number;
    active: number;
    completed: number;
  };
  emails: {
    sent: number;
    delivered: number;
    opened: number;
    clicked: number;
    replied: number;
    bounced: number;
    unsubscribed: number;
  };
  rates: {
    open_rate: number;
    click_rate: number;
    reply_rate: number;
  };
  suppressed: number;
  period_days: number;
}

export interface EmailStatsOverTime {
  date: string;
  opens: number;
  clicks: number;
  unsubscribes: number;
  bounces: number;
}

export interface CampaignReportStats {
  campaign: {
    id: string;
    name: string;
    status: string;
    created_at: string;
    started_at: string | null;
    completed_at: string | null;
  };
  recipients: {
    total: number;
    sent: number;
    delivered: number;
    pending: number;
    failed: number;
  };
  engagement: {
    opened: number;
    clicked: number;
    replied: number;
    unsubscribed: number;
  };
  deliverability: {
    bounced: number;
    complained: number;
  };
  rates: {
    delivery_rate: number;
    open_rate: number;
    click_rate: number;
    reply_rate: number;
    bounce_rate: number;
  };
  ab_test?: {
    variants: Array<{
      id: string;
      name: string;
      sent: number;
      opened: number;
      clicked: number;
      open_rate: number;
      click_rate: number;
      is_winner: boolean;
      is_control: boolean;
    }>;
    winner_criteria: string;
  };
  timeline: Array<{
    time: string;
    opens: number;
    clicks: number;
  }>;
  top_links: Array<{
    url: string;
    clicks: number;
  }>;
}

export interface CampaignComparison {
  id: string;
  name: string;
  status: string;
  sent: number;
  delivered: number;
  opened: number;
  clicked: number;
  replied: number;
  bounced: number;
  open_rate: number;
  click_rate: number;
  reply_rate: number;
  started_at: string | null;
}

export interface ActivityEvent {
  id: string;
  type: string;
  contact_id: string;
  contact_email: string;
  contact_name: string;
  campaign_id: string;
  campaign_name: string;
  details: {
    clicked_url?: string | null;
    device?: string;
    location?: string | null;
  };
  created_at: string;
}

export interface HotLead {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  company: string;
  score: number;
  score_trend: 'up' | 'down' | 'stable';
  last_activity_at: string | null;
  total_opens: number;
  total_clicks: number;
  total_replies: number;
  created_at: string;
}

export interface HotLeadsReport {
  leads: HotLead[];
  total_hot_leads: number;
  threshold: number;
  distribution: {
    hot: number;
    warm: number;
    cold: number;
  };
}

export interface ScoreDistribution {
  distribution: Array<{
    range: string;
    count: number;
  }>;
  stats: {
    average: number;
    maximum: number;
    minimum: number;
    total_contacts: number;
  };
}

export interface PerformanceSummary {
  current: {
    emails_sent: number;
    emails_opened: number;
    emails_clicked: number;
    replies: number;
    new_contacts: number;
    open_rate: number;
    click_rate: number;
  };
  previous: {
    emails_sent: number;
    emails_opened: number;
    emails_clicked: number;
    replies: number;
    new_contacts: number;
    open_rate: number;
    click_rate: number;
  };
  changes: {
    emails_sent: number;
    emails_opened: number;
    replies: number;
    new_contacts: number;
    open_rate: number;
    click_rate: number;
  };
  period_days: number;
}

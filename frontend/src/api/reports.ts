import { apiClient } from './client';
import type {
  DashboardStats,
  EmailStatsOverTime,
  CampaignReportStats,
  CampaignComparison,
  ActivityEvent,
  HotLeadsReport,
  ScoreDistribution,
  PerformanceSummary,
} from '@/types/reports';

export const reportsApi = {
  // Dashboard
  getDashboardStats: async (days: number = 30): Promise<DashboardStats> => {
    const response = await apiClient.get('/reports/dashboard/', {
      params: { days },
    });
    return response.data;
  },

  getEmailStatsOverTime: async (
    days: number = 30,
    granularity: 'hour' | 'day' | 'week' | 'month' = 'day'
  ): Promise<EmailStatsOverTime[]> => {
    const response = await apiClient.get('/reports/email-stats/', {
      params: { days, granularity },
    });
    return response.data;
  },

  getPerformanceSummary: async (days: number = 7): Promise<PerformanceSummary> => {
    const response = await apiClient.get('/reports/performance/', {
      params: { days },
    });
    return response.data;
  },

  // Campaign Reports
  getCampaignReport: async (campaignId: string): Promise<CampaignReportStats> => {
    const response = await apiClient.get(`/reports/campaigns/${campaignId}/`);
    return response.data;
  },

  compareCampaigns: async (campaignIds: string[]): Promise<CampaignComparison[]> => {
    const response = await apiClient.post('/reports/campaigns/compare/', {
      campaign_ids: campaignIds,
    });
    return response.data;
  },

  // Activity
  getActivityTimeline: async (params?: {
    limit?: number;
    event_types?: string;
    contact_id?: string;
    campaign_id?: string;
  }): Promise<ActivityEvent[]> => {
    const response = await apiClient.get('/reports/activity/', { params });
    return response.data;
  },

  // Hot Leads
  getHotLeadsReport: async (params?: {
    limit?: number;
    min_score?: number;
  }): Promise<HotLeadsReport> => {
    const response = await apiClient.get('/reports/hot-leads/', { params });
    return response.data;
  },

  // Score Distribution
  getScoreDistribution: async (): Promise<ScoreDistribution> => {
    const response = await apiClient.get('/reports/score-distribution/');
    return response.data;
  },

  // Exports
  exportCampaignReport: async (campaignId: string): Promise<Blob> => {
    const response = await apiClient.get(`/reports/campaigns/${campaignId}/export/`, {
      responseType: 'blob',
    });
    return response.data;
  },

  exportContacts: async (params?: {
    filters?: {
      tags?: string[];
      score_min?: number;
      score_max?: number;
      is_unsubscribed?: boolean;
    };
    fields?: string[];
  }): Promise<Blob> => {
    const response = await apiClient.post('/reports/contacts/export/', params, {
      responseType: 'blob',
    });
    return response.data;
  },

  exportHotLeads: async (minScore: number = 70): Promise<Blob> => {
    const response = await apiClient.get('/reports/hot-leads/export/', {
      params: { min_score: minScore },
      responseType: 'blob',
    });
    return response.data;
  },
};

// Utility function for downloading blobs
export function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
}

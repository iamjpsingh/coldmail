import { useQuery, useMutation } from '@tanstack/react-query';
import { reportsApi, downloadBlob } from '@/api/reports';

// Query keys
export const reportKeys = {
  all: ['reports'] as const,
  dashboard: (days?: number) => [...reportKeys.all, 'dashboard', days] as const,
  emailStats: (days?: number, granularity?: string) =>
    [...reportKeys.all, 'emailStats', days, granularity] as const,
  performance: (days?: number) => [...reportKeys.all, 'performance', days] as const,
  campaign: (id: string) => [...reportKeys.all, 'campaign', id] as const,
  campaignComparison: (ids: string[]) =>
    [...reportKeys.all, 'comparison', ids.join(',')] as const,
  activity: (params?: object) => [...reportKeys.all, 'activity', params] as const,
  hotLeads: (params?: object) => [...reportKeys.all, 'hotLeads', params] as const,
  scoreDistribution: () => [...reportKeys.all, 'scoreDistribution'] as const,
};

// Dashboard stats
export function useDashboardStats(days: number = 30) {
  return useQuery({
    queryKey: reportKeys.dashboard(days),
    queryFn: () => reportsApi.getDashboardStats(days),
    refetchInterval: 60000, // Refetch every minute
  });
}

// Email stats over time
export function useEmailStatsOverTime(
  days: number = 30,
  granularity: 'hour' | 'day' | 'week' | 'month' = 'day'
) {
  return useQuery({
    queryKey: reportKeys.emailStats(days, granularity),
    queryFn: () => reportsApi.getEmailStatsOverTime(days, granularity),
  });
}

// Performance summary with comparison
export function usePerformanceSummary(days: number = 7) {
  return useQuery({
    queryKey: reportKeys.performance(days),
    queryFn: () => reportsApi.getPerformanceSummary(days),
    refetchInterval: 60000,
  });
}

// Campaign report
export function useCampaignReport(campaignId: string) {
  return useQuery({
    queryKey: reportKeys.campaign(campaignId),
    queryFn: () => reportsApi.getCampaignReport(campaignId),
    enabled: !!campaignId,
  });
}

// Campaign comparison
export function useCampaignComparison(campaignIds: string[]) {
  return useQuery({
    queryKey: reportKeys.campaignComparison(campaignIds),
    queryFn: () => reportsApi.compareCampaigns(campaignIds),
    enabled: campaignIds.length > 0,
  });
}

// Activity timeline
export function useActivityTimeline(params?: {
  limit?: number;
  event_types?: string;
  contact_id?: string;
  campaign_id?: string;
}) {
  return useQuery({
    queryKey: reportKeys.activity(params),
    queryFn: () => reportsApi.getActivityTimeline(params),
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

// Hot leads report
export function useHotLeadsReport(params?: { limit?: number; min_score?: number }) {
  return useQuery({
    queryKey: reportKeys.hotLeads(params),
    queryFn: () => reportsApi.getHotLeadsReport(params),
    refetchInterval: 60000,
  });
}

// Score distribution
export function useScoreDistribution() {
  return useQuery({
    queryKey: reportKeys.scoreDistribution(),
    queryFn: () => reportsApi.getScoreDistribution(),
  });
}

// Export mutations
export function useExportCampaignReport() {
  return useMutation({
    mutationFn: async (campaignId: string) => {
      const blob = await reportsApi.exportCampaignReport(campaignId);
      downloadBlob(blob, `campaign_${campaignId}_report.csv`);
    },
  });
}

export function useExportContacts() {
  return useMutation({
    mutationFn: async (params?: {
      filters?: {
        tags?: string[];
        score_min?: number;
        score_max?: number;
        is_unsubscribed?: boolean;
      };
      fields?: string[];
    }) => {
      const blob = await reportsApi.exportContacts(params);
      downloadBlob(blob, 'contacts_export.csv');
    },
  });
}

export function useExportHotLeads() {
  return useMutation({
    mutationFn: async (minScore: number = 70) => {
      const blob = await reportsApi.exportHotLeads(minScore);
      downloadBlob(blob, 'hot_leads.csv');
    },
  });
}

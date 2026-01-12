import { apiClient } from '@/lib/api-client';
import type {
  Campaign,
  CampaignCreate,
  CampaignListItem,
  CampaignRecipient,
  CampaignEvent,
  CampaignLog,
  CampaignStats,
  CampaignSummary,
  ABTestVariant,
  ScheduleCampaignRequest,
} from '@/types/campaign';

const BASE_PATH = '/campaigns/campaigns';

export const campaignsApi = {
  list: async (params?: {
    status?: string;
    search?: string;
  }): Promise<CampaignListItem[]> => {
    const response = await apiClient.get<CampaignListItem[]>(`${BASE_PATH}/`, { params });
    return response.data;
  },

  get: async (id: string): Promise<Campaign> => {
    const response = await apiClient.get<Campaign>(`${BASE_PATH}/${id}/`);
    return response.data;
  },

  create: async (data: CampaignCreate): Promise<Campaign> => {
    const response = await apiClient.post<Campaign>(`${BASE_PATH}/`, data);
    return response.data;
  },

  update: async (id: string, data: Partial<CampaignCreate>): Promise<Campaign> => {
    const response = await apiClient.patch<Campaign>(`${BASE_PATH}/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${id}/`);
  },

  // Campaign actions
  prepare: async (id: string): Promise<{ message: string; campaign_id: string }> => {
    const response = await apiClient.post(`${BASE_PATH}/${id}/prepare/`);
    return response.data;
  },

  schedule: async (id: string, data: ScheduleCampaignRequest): Promise<Campaign> => {
    const response = await apiClient.post<Campaign>(`${BASE_PATH}/${id}/schedule/`, data);
    return response.data;
  },

  start: async (id: string): Promise<Campaign> => {
    const response = await apiClient.post<Campaign>(`${BASE_PATH}/${id}/start/`);
    return response.data;
  },

  pause: async (id: string): Promise<Campaign> => {
    const response = await apiClient.post<Campaign>(`${BASE_PATH}/${id}/pause/`);
    return response.data;
  },

  resume: async (id: string): Promise<Campaign> => {
    const response = await apiClient.post<Campaign>(`${BASE_PATH}/${id}/resume/`);
    return response.data;
  },

  cancel: async (id: string): Promise<Campaign> => {
    const response = await apiClient.post<Campaign>(`${BASE_PATH}/${id}/cancel/`);
    return response.data;
  },

  duplicate: async (id: string, name?: string): Promise<Campaign> => {
    const response = await apiClient.post<Campaign>(`${BASE_PATH}/${id}/duplicate/`, { name });
    return response.data;
  },

  retryFailed: async (id: string): Promise<{ message: string; campaign_id: string }> => {
    const response = await apiClient.post(`${BASE_PATH}/${id}/retry_failed/`);
    return response.data;
  },

  // Stats and data
  getStats: async (id: string): Promise<CampaignStats> => {
    const response = await apiClient.get<CampaignStats>(`${BASE_PATH}/${id}/stats/`);
    return response.data;
  },

  getRecipients: async (
    id: string,
    params?: { status?: string; search?: string }
  ): Promise<CampaignRecipient[]> => {
    const response = await apiClient.get<CampaignRecipient[]>(`${BASE_PATH}/${id}/recipients/`, {
      params,
    });
    return response.data;
  },

  getLogs: async (id: string): Promise<CampaignLog[]> => {
    const response = await apiClient.get<CampaignLog[]>(`${BASE_PATH}/${id}/logs/`);
    return response.data;
  },

  getEvents: async (id: string, params?: { type?: string }): Promise<CampaignEvent[]> => {
    const response = await apiClient.get<CampaignEvent[]>(`${BASE_PATH}/${id}/events/`, { params });
    return response.data;
  },

  // A/B Testing
  selectABWinner: async (id: string, variantId?: string): Promise<ABTestVariant> => {
    const response = await apiClient.post<ABTestVariant>(`${BASE_PATH}/${id}/select_ab_winner/`, {
      variant_id: variantId,
    });
    return response.data;
  },

  // Summary
  getSummary: async (): Promise<CampaignSummary> => {
    const response = await apiClient.get<CampaignSummary>(`${BASE_PATH}/summary/`);
    return response.data;
  },
};

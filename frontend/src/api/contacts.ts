import { apiClient } from '@/lib/api-client';
import type {
  Contact,
  ContactCreate,
  Tag,
  ContactList,
  ContactActivity,
  CustomField,
  ImportJob,
  ContactSearchParams,
  ScoringRule,
  ScoringRuleCreate,
  ScoreThreshold,
  ScoreThresholdCreate,
  ScoreDecayConfig,
  ScoreDecayConfigUpdate,
  ScoringStats,
  ScoreHistory,
  ScoreAdjustment,
  ApplyEventRequest,
} from '@/types/contact';

const BASE_PATH = '/contacts';

export const contactsApi = {
  // Contacts
  list: async (params?: Record<string, string>): Promise<Contact[]> => {
    const response = await apiClient.get<Contact[]>(BASE_PATH + '/', { params });
    return response.data;
  },

  get: async (id: string): Promise<Contact> => {
    const response = await apiClient.get<Contact>(`${BASE_PATH}/${id}/`);
    return response.data;
  },

  create: async (data: ContactCreate): Promise<Contact> => {
    const response = await apiClient.post<Contact>(BASE_PATH + '/', data);
    return response.data;
  },

  update: async (id: string, data: Partial<ContactCreate>): Promise<Contact> => {
    const response = await apiClient.patch<Contact>(`${BASE_PATH}/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${id}/`);
  },

  search: async (params: ContactSearchParams): Promise<Contact[]> => {
    const response = await apiClient.post<Contact[]>(`${BASE_PATH}/search/`, params);
    return response.data;
  },

  getActivities: async (id: string): Promise<ContactActivity[]> => {
    const response = await apiClient.get<ContactActivity[]>(`${BASE_PATH}/${id}/activities/`);
    return response.data;
  },

  bulkDelete: async (contactIds: string[]): Promise<{ deleted_count: number }> => {
    const response = await apiClient.post(`${BASE_PATH}/bulk_delete/`, { contact_ids: contactIds });
    return response.data;
  },

  bulkAddTags: async (contactIds: string[], tagIds: string[]): Promise<{ updated_count: number }> => {
    const response = await apiClient.post(`${BASE_PATH}/bulk_add_tags/`, { contact_ids: contactIds, tag_ids: tagIds });
    return response.data;
  },

  bulkRemoveTags: async (contactIds: string[], tagIds: string[]): Promise<{ updated_count: number }> => {
    const response = await apiClient.post(`${BASE_PATH}/bulk_remove_tags/`, { contact_ids: contactIds, tag_ids: tagIds });
    return response.data;
  },

  bulkAddToList: async (contactIds: string[], listId: string): Promise<{ added_count: number }> => {
    const response = await apiClient.post(`${BASE_PATH}/bulk_add_to_list/`, { contact_ids: contactIds, list_id: listId });
    return response.data;
  },

  export: async (params?: { status?: string; tags?: string[] }): Promise<Blob> => {
    const response = await apiClient.get(`${BASE_PATH}/export/`, {
      params,
      responseType: 'blob',
    });
    return response.data;
  },
};

export const tagsApi = {
  list: async (): Promise<Tag[]> => {
    const response = await apiClient.get<Tag[]>(`${BASE_PATH}/tags/`);
    return response.data;
  },

  get: async (id: string): Promise<Tag> => {
    const response = await apiClient.get<Tag>(`${BASE_PATH}/tags/${id}/`);
    return response.data;
  },

  create: async (data: { name: string; color: string }): Promise<Tag> => {
    const response = await apiClient.post<Tag>(`${BASE_PATH}/tags/`, data);
    return response.data;
  },

  update: async (id: string, data: { name?: string; color?: string }): Promise<Tag> => {
    const response = await apiClient.patch<Tag>(`${BASE_PATH}/tags/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/tags/${id}/`);
  },
};

export const contactListsApi = {
  list: async (): Promise<ContactList[]> => {
    const response = await apiClient.get<ContactList[]>(`${BASE_PATH}/lists/`);
    return response.data;
  },

  get: async (id: string): Promise<ContactList> => {
    const response = await apiClient.get<ContactList>(`${BASE_PATH}/lists/${id}/`);
    return response.data;
  },

  create: async (data: {
    name: string;
    description?: string;
    list_type: 'static' | 'smart';
    filter_criteria?: Record<string, unknown>;
    contact_ids?: string[];
  }): Promise<ContactList> => {
    const response = await apiClient.post<ContactList>(`${BASE_PATH}/lists/`, data);
    return response.data;
  },

  update: async (id: string, data: Partial<ContactList>): Promise<ContactList> => {
    const response = await apiClient.patch<ContactList>(`${BASE_PATH}/lists/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/lists/${id}/`);
  },

  getContacts: async (id: string): Promise<Contact[]> => {
    const response = await apiClient.get<Contact[]>(`${BASE_PATH}/lists/${id}/contacts/`);
    return response.data;
  },

  refreshCount: async (id: string): Promise<{ contact_count: number }> => {
    const response = await apiClient.post(`${BASE_PATH}/lists/${id}/refresh_count/`);
    return response.data;
  },
};

export const customFieldsApi = {
  list: async (): Promise<CustomField[]> => {
    const response = await apiClient.get<CustomField[]>(`${BASE_PATH}/custom-fields/`);
    return response.data;
  },

  create: async (data: Partial<CustomField>): Promise<CustomField> => {
    const response = await apiClient.post<CustomField>(`${BASE_PATH}/custom-fields/`, data);
    return response.data;
  },

  update: async (id: string, data: Partial<CustomField>): Promise<CustomField> => {
    const response = await apiClient.patch<CustomField>(`${BASE_PATH}/custom-fields/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/custom-fields/${id}/`);
  },
};

export const importJobsApi = {
  list: async (): Promise<ImportJob[]> => {
    const response = await apiClient.get<ImportJob[]>(`${BASE_PATH}/imports/`);
    return response.data;
  },

  get: async (id: string): Promise<ImportJob> => {
    const response = await apiClient.get<ImportJob>(`${BASE_PATH}/imports/${id}/`);
    return response.data;
  },

  upload: async (file: File): Promise<{
    import_job_id: string;
    file_name: string;
    file_type: string;
    preview: { headers: string[]; rows: Record<string, unknown>[] };
  }> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post(`${BASE_PATH}/imports/upload/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  start: async (id: string, fieldMapping: Record<string, string>): Promise<{ status: string; import_job_id: string }> => {
    const response = await apiClient.post(`${BASE_PATH}/imports/${id}/start/`, { field_mapping: fieldMapping });
    return response.data;
  },

  cancel: async (id: string): Promise<{ status: string }> => {
    const response = await apiClient.post(`${BASE_PATH}/imports/${id}/cancel/`);
    return response.data;
  },
};

// Scoring APIs
export const scoringRulesApi = {
  list: async (): Promise<ScoringRule[]> => {
    const response = await apiClient.get<ScoringRule[]>(`${BASE_PATH}/scoring/rules/`);
    return response.data;
  },

  get: async (id: string): Promise<ScoringRule> => {
    const response = await apiClient.get<ScoringRule>(`${BASE_PATH}/scoring/rules/${id}/`);
    return response.data;
  },

  create: async (data: ScoringRuleCreate): Promise<ScoringRule> => {
    const response = await apiClient.post<ScoringRule>(`${BASE_PATH}/scoring/rules/`, data);
    return response.data;
  },

  update: async (id: string, data: Partial<ScoringRuleCreate>): Promise<ScoringRule> => {
    const response = await apiClient.patch<ScoringRule>(`${BASE_PATH}/scoring/rules/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/scoring/rules/${id}/`);
  },

  toggleActive: async (id: string): Promise<ScoringRule> => {
    const response = await apiClient.post<ScoringRule>(`${BASE_PATH}/scoring/rules/${id}/toggle_active/`);
    return response.data;
  },
};

export const scoreThresholdsApi = {
  list: async (): Promise<ScoreThreshold[]> => {
    const response = await apiClient.get<ScoreThreshold[]>(`${BASE_PATH}/scoring/thresholds/`);
    return response.data;
  },

  get: async (id: string): Promise<ScoreThreshold> => {
    const response = await apiClient.get<ScoreThreshold>(`${BASE_PATH}/scoring/thresholds/${id}/`);
    return response.data;
  },

  create: async (data: ScoreThresholdCreate): Promise<ScoreThreshold> => {
    const response = await apiClient.post<ScoreThreshold>(`${BASE_PATH}/scoring/thresholds/`, data);
    return response.data;
  },

  update: async (id: string, data: Partial<ScoreThresholdCreate>): Promise<ScoreThreshold> => {
    const response = await apiClient.patch<ScoreThreshold>(`${BASE_PATH}/scoring/thresholds/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/scoring/thresholds/${id}/`);
  },
};

export const scoreDecayApi = {
  get: async (): Promise<ScoreDecayConfig> => {
    // Get the first (and only) decay config for the workspace
    const response = await apiClient.get<ScoreDecayConfig[]>(`${BASE_PATH}/scoring/decay-config/`);
    return response.data[0];
  },

  update: async (id: string, data: ScoreDecayConfigUpdate): Promise<ScoreDecayConfig> => {
    const response = await apiClient.patch<ScoreDecayConfig>(`${BASE_PATH}/scoring/decay-config/${id}/`, data);
    return response.data;
  },

  runNow: async (id: string): Promise<{ success: boolean; decayed_count: number; decay_points: number }> => {
    const response = await apiClient.post(`${BASE_PATH}/scoring/decay-config/${id}/run_now/`);
    return response.data;
  },
};

export const scoringApi = {
  getStats: async (): Promise<ScoringStats> => {
    const response = await apiClient.get<ScoringStats>(`${BASE_PATH}/scoring/stats/`);
    return response.data;
  },

  getHotLeads: async (limit?: number): Promise<Contact[]> => {
    const response = await apiClient.get<Contact[]>(`${BASE_PATH}/scoring/hot_leads/`, {
      params: limit ? { limit } : undefined,
    });
    return response.data;
  },

  adjustScore: async (contactId: string, data: ScoreAdjustment): Promise<{
    success: boolean;
    previous_score: number;
    new_score: number;
    score_change: number;
  }> => {
    const response = await apiClient.post(`${BASE_PATH}/scoring/${contactId}/adjust_score/`, data);
    return response.data;
  },

  applyEvent: async (contactId: string, data: ApplyEventRequest): Promise<{
    success: boolean;
    previous_score: number;
    new_score: number;
    score_change: number;
    rules_applied: string[];
  }> => {
    const response = await apiClient.post(`${BASE_PATH}/scoring/${contactId}/apply_event/`, data);
    return response.data;
  },

  getScoreHistory: async (contactId: string): Promise<ScoreHistory[]> => {
    const response = await apiClient.get<ScoreHistory[]>(`${BASE_PATH}/scoring/${contactId}/score_history/`);
    return response.data;
  },
};

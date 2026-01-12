import { api } from './client';
import type {
  Integration,
  IntegrationCreate,
  IntegrationTypeInfo,
  SlackIntegrationSettings,
  DiscordIntegrationSettings,
  DiscordIntegrationCreate,
  HubSpotIntegrationSettings,
  SalesforceIntegrationSettings,
  GoogleSheetsIntegrationSettings,
  IntegrationLog,
  TestConnectionResult,
  SyncResult,
} from '@/types/integrations';
import type { PaginatedResponse } from '@/types/api';

// Union type for all integration settings
export type IntegrationSettings =
  | SlackIntegrationSettings
  | DiscordIntegrationSettings
  | HubSpotIntegrationSettings
  | SalesforceIntegrationSettings
  | GoogleSheetsIntegrationSettings
  | Record<string, unknown>;

// ==================== Integrations API ====================

export const integrationsApi = {
  list: async (params?: {
    integration_type?: string;
    status?: string;
    is_active?: boolean;
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<Integration>> => {
    const response = await api.get('/integrations/', { params });
    return response.data;
  },

  get: async (id: string): Promise<Integration> => {
    const response = await api.get(`/integrations/${id}/`);
    return response.data;
  },

  create: async (data: IntegrationCreate): Promise<Integration> => {
    const response = await api.post('/integrations/', data);
    return response.data;
  },

  update: async (id: string, data: Partial<IntegrationCreate>): Promise<Integration> => {
    const response = await api.patch(`/integrations/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/integrations/${id}/`);
  },

  // Get available integration types
  getTypes: async (): Promise<IntegrationTypeInfo[]> => {
    const response = await api.get('/integrations/types/');
    return response.data;
  },

  // Test connection
  test: async (id: string): Promise<TestConnectionResult> => {
    const response = await api.post(`/integrations/${id}/test/`);
    return response.data;
  },

  // Trigger sync (for CRM integrations)
  sync: async (id: string): Promise<SyncResult> => {
    const response = await api.post(`/integrations/${id}/sync/`);
    return response.data;
  },

  // Activate integration
  activate: async (id: string): Promise<Integration> => {
    const response = await api.post(`/integrations/${id}/activate/`);
    return response.data;
  },

  // Deactivate integration
  deactivate: async (id: string): Promise<Integration> => {
    const response = await api.post(`/integrations/${id}/deactivate/`);
    return response.data;
  },

  // Get logs for an integration
  getLogs: async (id: string): Promise<IntegrationLog[]> => {
    const response = await api.get(`/integrations/${id}/logs/`);
    return response.data;
  },

  // Get integration-specific settings
  getSettings: async (id: string): Promise<IntegrationSettings> => {
    const response = await api.get(`/integrations/${id}/settings/`);
    return response.data;
  },

  // Update integration-specific settings
  updateSettings: async (
    id: string,
    data: Partial<IntegrationSettings>
  ): Promise<IntegrationSettings> => {
    const response = await api.patch(`/integrations/${id}/settings/`, data);
    return response.data;
  },
};

// ==================== Discord Integration API ====================

export const discordIntegrationApi = {
  create: async (data: DiscordIntegrationCreate): Promise<Integration> => {
    const response = await api.post('/integrations/discord/create/', data);
    return response.data;
  },
};

// ==================== Integration Logs API ====================

export const integrationLogsApi = {
  list: async (params?: {
    integration?: string;
    level?: string;
    operation?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<IntegrationLog>> => {
    const response = await api.get('/integration-logs/', { params });
    return response.data;
  },

  get: async (id: string): Promise<IntegrationLog> => {
    const response = await api.get(`/integration-logs/${id}/`);
    return response.data;
  },
};

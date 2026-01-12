import { api } from './client';
import type {
  APIKey,
  APIKeyCreate,
  APIKeyUpdate,
  APIKeyCreateResponse,
  Webhook,
  WebhookCreate,
  WebhookUpdate,
  WebhookSecret,
  WebhookTestResult,
  WebhookDelivery,
  WebhookDeliveryListItem,
  WebhookEventLog,
  WebhookEventLogListItem,
  WebhookEventTypeOption,
} from '@/types/webhooks';
import type { PaginatedResponse } from '@/types/api';

// ==================== API Keys API ====================

export const apiKeysApi = {
  list: async (params?: {
    is_active?: boolean;
    permission?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<APIKey>> => {
    const response = await api.get('/api-keys/', { params });
    return response.data;
  },

  get: async (id: string): Promise<APIKey> => {
    const response = await api.get(`/api-keys/${id}/`);
    return response.data;
  },

  create: async (data: APIKeyCreate): Promise<APIKeyCreateResponse> => {
    const response = await api.post('/api-keys/', data);
    return response.data;
  },

  update: async (id: string, data: APIKeyUpdate): Promise<APIKey> => {
    const response = await api.patch(`/api-keys/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/api-keys/${id}/`);
  },

  revoke: async (id: string): Promise<{ status: string }> => {
    const response = await api.post(`/api-keys/${id}/revoke/`);
    return response.data;
  },

  activate: async (id: string): Promise<{ status: string }> => {
    const response = await api.post(`/api-keys/${id}/activate/`);
    return response.data;
  },
};

// ==================== Webhooks API ====================

export const webhooksApi = {
  list: async (params?: {
    is_active?: boolean;
    event_type?: string;
    search?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<Webhook>> => {
    const response = await api.get('/webhooks/', { params });
    return response.data;
  },

  get: async (id: string): Promise<Webhook> => {
    const response = await api.get(`/webhooks/${id}/`);
    return response.data;
  },

  create: async (data: WebhookCreate): Promise<Webhook> => {
    const response = await api.post('/webhooks/', data);
    return response.data;
  },

  update: async (id: string, data: WebhookUpdate): Promise<Webhook> => {
    const response = await api.patch(`/webhooks/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/webhooks/${id}/`);
  },

  getSecret: async (id: string): Promise<WebhookSecret> => {
    const response = await api.get(`/webhooks/${id}/secret/`);
    return response.data;
  },

  regenerateSecret: async (id: string): Promise<WebhookSecret> => {
    const response = await api.post(`/webhooks/${id}/regenerate_secret/`);
    return response.data;
  },

  test: async (id: string): Promise<WebhookTestResult> => {
    const response = await api.post(`/webhooks/${id}/test/`);
    return response.data;
  },

  activate: async (id: string): Promise<Webhook> => {
    const response = await api.post(`/webhooks/${id}/activate/`);
    return response.data;
  },

  getDeliveries: async (id: string): Promise<WebhookDeliveryListItem[]> => {
    const response = await api.get(`/webhooks/${id}/deliveries/`);
    return response.data;
  },

  getEventTypes: async (): Promise<WebhookEventTypeOption[]> => {
    const response = await api.get('/webhooks/event_types/');
    return response.data;
  },
};

// ==================== Webhook Deliveries API ====================

export const webhookDeliveriesApi = {
  list: async (params?: {
    webhook?: string;
    status?: string;
    event_type?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<WebhookDeliveryListItem>> => {
    const response = await api.get('/webhook-deliveries/', { params });
    return response.data;
  },

  get: async (id: string): Promise<WebhookDelivery> => {
    const response = await api.get(`/webhook-deliveries/${id}/`);
    return response.data;
  },

  retry: async (id: string): Promise<{ status: string }> => {
    const response = await api.post(`/webhook-deliveries/${id}/retry/`);
    return response.data;
  },
};

// ==================== Webhook Event Logs API ====================

export const webhookEventLogsApi = {
  list: async (params?: {
    event_type?: string;
    contact_id?: string;
    campaign_id?: string;
    sequence_id?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<WebhookEventLogListItem>> => {
    const response = await api.get('/webhook-events/', { params });
    return response.data;
  },

  get: async (id: string): Promise<WebhookEventLog> => {
    const response = await api.get(`/webhook-events/${id}/`);
    return response.data;
  },
};

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  apiKeysApi,
  webhooksApi,
  webhookDeliveriesApi,
  webhookEventLogsApi,
} from '@/api/webhooks';
import type {
  APIKeyCreate,
  APIKeyUpdate,
  WebhookCreate,
  WebhookUpdate,
} from '@/types/webhooks';

// Query keys
export const webhooksKeys = {
  all: ['webhooks'] as const,
  // API Keys
  apiKeys: () => [...webhooksKeys.all, 'api-keys'] as const,
  apiKeysList: (params?: Record<string, unknown>) =>
    [...webhooksKeys.apiKeys(), 'list', params] as const,
  apiKey: (id: string) => [...webhooksKeys.apiKeys(), id] as const,
  // Webhooks
  webhooks: () => [...webhooksKeys.all, 'webhooks'] as const,
  webhooksList: (params?: Record<string, unknown>) =>
    [...webhooksKeys.webhooks(), 'list', params] as const,
  webhook: (id: string) => [...webhooksKeys.webhooks(), id] as const,
  webhookSecret: (id: string) => [...webhooksKeys.webhook(id), 'secret'] as const,
  webhookDeliveries: (id: string) =>
    [...webhooksKeys.webhook(id), 'deliveries'] as const,
  eventTypes: () => [...webhooksKeys.webhooks(), 'event-types'] as const,
  // Deliveries
  deliveries: () => [...webhooksKeys.all, 'deliveries'] as const,
  deliveriesList: (params?: Record<string, unknown>) =>
    [...webhooksKeys.deliveries(), 'list', params] as const,
  delivery: (id: string) => [...webhooksKeys.deliveries(), id] as const,
  // Event Logs
  eventLogs: () => [...webhooksKeys.all, 'event-logs'] as const,
  eventLogsList: (params?: Record<string, unknown>) =>
    [...webhooksKeys.eventLogs(), 'list', params] as const,
  eventLog: (id: string) => [...webhooksKeys.eventLogs(), id] as const,
};

// ==================== API Keys Hooks ====================

export function useAPIKeys(params?: {
  is_active?: boolean;
  permission?: string;
  search?: string;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: webhooksKeys.apiKeysList(params),
    queryFn: () => apiKeysApi.list(params),
  });
}

export function useAPIKey(id: string) {
  return useQuery({
    queryKey: webhooksKeys.apiKey(id),
    queryFn: () => apiKeysApi.get(id),
    enabled: !!id,
  });
}

export function useCreateAPIKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: APIKeyCreate) => apiKeysApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: webhooksKeys.apiKeys() });
    },
  });
}

export function useUpdateAPIKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: APIKeyUpdate }) =>
      apiKeysApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: webhooksKeys.apiKey(id) });
      queryClient.invalidateQueries({ queryKey: webhooksKeys.apiKeys() });
    },
  });
}

export function useDeleteAPIKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiKeysApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: webhooksKeys.apiKeys() });
    },
  });
}

export function useRevokeAPIKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiKeysApi.revoke(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: webhooksKeys.apiKey(id) });
      queryClient.invalidateQueries({ queryKey: webhooksKeys.apiKeys() });
    },
  });
}

export function useActivateAPIKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => apiKeysApi.activate(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: webhooksKeys.apiKey(id) });
      queryClient.invalidateQueries({ queryKey: webhooksKeys.apiKeys() });
    },
  });
}

// ==================== Webhooks Hooks ====================

export function useWebhooks(params?: {
  is_active?: boolean;
  event_type?: string;
  search?: string;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: webhooksKeys.webhooksList(params),
    queryFn: () => webhooksApi.list(params),
  });
}

export function useWebhook(id: string) {
  return useQuery({
    queryKey: webhooksKeys.webhook(id),
    queryFn: () => webhooksApi.get(id),
    enabled: !!id,
  });
}

export function useCreateWebhook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: WebhookCreate) => webhooksApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: webhooksKeys.webhooks() });
    },
  });
}

export function useUpdateWebhook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: WebhookUpdate }) =>
      webhooksApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: webhooksKeys.webhook(id) });
      queryClient.invalidateQueries({ queryKey: webhooksKeys.webhooks() });
    },
  });
}

export function useDeleteWebhook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => webhooksApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: webhooksKeys.webhooks() });
    },
  });
}

export function useWebhookSecret(id: string) {
  return useQuery({
    queryKey: webhooksKeys.webhookSecret(id),
    queryFn: () => webhooksApi.getSecret(id),
    enabled: !!id,
  });
}

export function useRegenerateWebhookSecret() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => webhooksApi.regenerateSecret(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: webhooksKeys.webhookSecret(id) });
    },
  });
}

export function useTestWebhook() {
  return useMutation({
    mutationFn: (id: string) => webhooksApi.test(id),
  });
}

export function useActivateWebhook() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => webhooksApi.activate(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: webhooksKeys.webhook(id) });
      queryClient.invalidateQueries({ queryKey: webhooksKeys.webhooks() });
    },
  });
}

export function useWebhookDeliveriesForWebhook(webhookId: string) {
  return useQuery({
    queryKey: webhooksKeys.webhookDeliveries(webhookId),
    queryFn: () => webhooksApi.getDeliveries(webhookId),
    enabled: !!webhookId,
  });
}

export function useWebhookEventTypes() {
  return useQuery({
    queryKey: webhooksKeys.eventTypes(),
    queryFn: webhooksApi.getEventTypes,
    staleTime: 1000 * 60 * 60, // Cache for 1 hour - event types don't change
  });
}

// ==================== Webhook Deliveries Hooks ====================

export function useWebhookDeliveries(params?: {
  webhook?: string;
  status?: string;
  event_type?: string;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: webhooksKeys.deliveriesList(params),
    queryFn: () => webhookDeliveriesApi.list(params),
  });
}

export function useWebhookDelivery(id: string) {
  return useQuery({
    queryKey: webhooksKeys.delivery(id),
    queryFn: () => webhookDeliveriesApi.get(id),
    enabled: !!id,
  });
}

export function useRetryWebhookDelivery() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => webhookDeliveriesApi.retry(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: webhooksKeys.delivery(id) });
      queryClient.invalidateQueries({ queryKey: webhooksKeys.deliveries() });
    },
  });
}

// ==================== Webhook Event Logs Hooks ====================

export function useWebhookEventLogs(params?: {
  event_type?: string;
  contact_id?: string;
  campaign_id?: string;
  sequence_id?: string;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: webhooksKeys.eventLogsList(params),
    queryFn: () => webhookEventLogsApi.list(params),
  });
}

export function useWebhookEventLog(id: string) {
  return useQuery({
    queryKey: webhooksKeys.eventLog(id),
    queryFn: () => webhookEventLogsApi.get(id),
    enabled: !!id,
  });
}

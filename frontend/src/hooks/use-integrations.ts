import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  integrationsApi,
  discordIntegrationApi,
  integrationLogsApi,
  type IntegrationSettings,
} from '@/api/integrations';
import type {
  IntegrationCreate,
  DiscordIntegrationCreate,
} from '@/types/integrations';

// Query keys
export const integrationsKeys = {
  all: ['integrations'] as const,
  // Integrations
  integrations: () => [...integrationsKeys.all, 'list'] as const,
  integrationsList: (params?: Record<string, unknown>) =>
    [...integrationsKeys.integrations(), params] as const,
  integration: (id: string) => [...integrationsKeys.all, id] as const,
  integrationLogs: (id: string) => [...integrationsKeys.integration(id), 'logs'] as const,
  integrationSettings: (id: string) =>
    [...integrationsKeys.integration(id), 'settings'] as const,
  types: () => [...integrationsKeys.all, 'types'] as const,
  // Logs
  logs: () => [...integrationsKeys.all, 'logs'] as const,
  logsList: (params?: Record<string, unknown>) =>
    [...integrationsKeys.logs(), 'list', params] as const,
  log: (id: string) => [...integrationsKeys.logs(), id] as const,
};

// ==================== Integrations Hooks ====================

export function useIntegrations(params?: {
  integration_type?: string;
  status?: string;
  is_active?: boolean;
  search?: string;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: integrationsKeys.integrationsList(params),
    queryFn: () => integrationsApi.list(params),
  });
}

export function useIntegration(id: string) {
  return useQuery({
    queryKey: integrationsKeys.integration(id),
    queryFn: () => integrationsApi.get(id),
    enabled: !!id,
  });
}

export function useCreateIntegration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: IntegrationCreate) => integrationsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: integrationsKeys.integrations() });
    },
  });
}

export function useUpdateIntegration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<IntegrationCreate> }) =>
      integrationsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: integrationsKeys.integration(id) });
      queryClient.invalidateQueries({ queryKey: integrationsKeys.integrations() });
    },
  });
}

export function useDeleteIntegration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => integrationsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: integrationsKeys.integrations() });
    },
  });
}

export function useIntegrationTypes() {
  return useQuery({
    queryKey: integrationsKeys.types(),
    queryFn: integrationsApi.getTypes,
    staleTime: 1000 * 60 * 60, // Cache for 1 hour - types don't change
  });
}

export function useTestIntegration() {
  return useMutation({
    mutationFn: (id: string) => integrationsApi.test(id),
  });
}

export function useSyncIntegration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => integrationsApi.sync(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: integrationsKeys.integration(id) });
    },
  });
}

export function useActivateIntegration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => integrationsApi.activate(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: integrationsKeys.integration(id) });
      queryClient.invalidateQueries({ queryKey: integrationsKeys.integrations() });
    },
  });
}

export function useDeactivateIntegration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => integrationsApi.deactivate(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: integrationsKeys.integration(id) });
      queryClient.invalidateQueries({ queryKey: integrationsKeys.integrations() });
    },
  });
}

export function useIntegrationLogs(integrationId: string) {
  return useQuery({
    queryKey: integrationsKeys.integrationLogs(integrationId),
    queryFn: () => integrationsApi.getLogs(integrationId),
    enabled: !!integrationId,
  });
}

export function useIntegrationSettings(integrationId: string) {
  return useQuery({
    queryKey: integrationsKeys.integrationSettings(integrationId),
    queryFn: () => integrationsApi.getSettings(integrationId),
    enabled: !!integrationId,
  });
}

export function useUpdateIntegrationSettings() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<IntegrationSettings> }) =>
      integrationsApi.updateSettings(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({
        queryKey: integrationsKeys.integrationSettings(id),
      });
    },
  });
}

// ==================== Discord Integration Hook ====================

export function useCreateDiscordIntegration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: DiscordIntegrationCreate) => discordIntegrationApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: integrationsKeys.integrations() });
    },
  });
}

// ==================== Integration Logs Hooks ====================

export function useAllIntegrationLogs(params?: {
  integration?: string;
  level?: string;
  operation?: string;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: integrationsKeys.logsList(params),
    queryFn: () => integrationLogsApi.list(params),
  });
}

export function useIntegrationLog(id: string) {
  return useQuery({
    queryKey: integrationsKeys.log(id),
    queryFn: () => integrationLogsApi.get(id),
    enabled: !!id,
  });
}

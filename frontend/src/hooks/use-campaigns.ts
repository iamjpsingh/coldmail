import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { campaignsApi } from '@/api/campaigns';
import type { CampaignCreate, ScheduleCampaignRequest } from '@/types/campaign';

// Query keys
export const campaignKeys = {
  all: ['campaigns'] as const,
  lists: () => [...campaignKeys.all, 'list'] as const,
  list: (filters: { status?: string; search?: string }) =>
    [...campaignKeys.lists(), filters] as const,
  details: () => [...campaignKeys.all, 'detail'] as const,
  detail: (id: string) => [...campaignKeys.details(), id] as const,
  stats: (id: string) => [...campaignKeys.detail(id), 'stats'] as const,
  recipients: (id: string, filters?: { status?: string; search?: string }) =>
    [...campaignKeys.detail(id), 'recipients', filters] as const,
  logs: (id: string) => [...campaignKeys.detail(id), 'logs'] as const,
  events: (id: string, filters?: { type?: string }) =>
    [...campaignKeys.detail(id), 'events', filters] as const,
  summary: () => [...campaignKeys.all, 'summary'] as const,
};

// List campaigns
export function useCampaigns(params?: { status?: string; search?: string }) {
  return useQuery({
    queryKey: campaignKeys.list(params || {}),
    queryFn: () => campaignsApi.list(params),
  });
}

// Get single campaign
export function useCampaign(id: string) {
  return useQuery({
    queryKey: campaignKeys.detail(id),
    queryFn: () => campaignsApi.get(id),
    enabled: !!id,
  });
}

// Get campaign stats
export function useCampaignStats(id: string) {
  return useQuery({
    queryKey: campaignKeys.stats(id),
    queryFn: () => campaignsApi.getStats(id),
    enabled: !!id,
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

// Get campaign recipients
export function useCampaignRecipients(
  id: string,
  params?: { status?: string; search?: string }
) {
  return useQuery({
    queryKey: campaignKeys.recipients(id, params),
    queryFn: () => campaignsApi.getRecipients(id, params),
    enabled: !!id,
  });
}

// Get campaign logs
export function useCampaignLogs(id: string) {
  return useQuery({
    queryKey: campaignKeys.logs(id),
    queryFn: () => campaignsApi.getLogs(id),
    enabled: !!id,
  });
}

// Get campaign events
export function useCampaignEvents(id: string, params?: { type?: string }) {
  return useQuery({
    queryKey: campaignKeys.events(id, params),
    queryFn: () => campaignsApi.getEvents(id, params),
    enabled: !!id,
  });
}

// Get campaigns summary
export function useCampaignSummary() {
  return useQuery({
    queryKey: campaignKeys.summary(),
    queryFn: () => campaignsApi.getSummary(),
  });
}

// Create campaign
export function useCreateCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CampaignCreate) => campaignsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
      queryClient.invalidateQueries({ queryKey: campaignKeys.summary() });
    },
  });
}

// Update campaign
export function useUpdateCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CampaignCreate> }) =>
      campaignsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
    },
  });
}

// Delete campaign
export function useDeleteCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => campaignsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
      queryClient.invalidateQueries({ queryKey: campaignKeys.summary() });
    },
  });
}

// Prepare campaign recipients
export function usePrepareCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => campaignsApi.prepare(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.detail(id) });
    },
  });
}

// Schedule campaign
export function useScheduleCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ScheduleCampaignRequest }) =>
      campaignsApi.schedule(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
      queryClient.invalidateQueries({ queryKey: campaignKeys.summary() });
    },
  });
}

// Start campaign
export function useStartCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => campaignsApi.start(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
      queryClient.invalidateQueries({ queryKey: campaignKeys.summary() });
    },
  });
}

// Pause campaign
export function usePauseCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => campaignsApi.pause(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
      queryClient.invalidateQueries({ queryKey: campaignKeys.summary() });
    },
  });
}

// Resume campaign
export function useResumeCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => campaignsApi.resume(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
      queryClient.invalidateQueries({ queryKey: campaignKeys.summary() });
    },
  });
}

// Cancel campaign
export function useCancelCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => campaignsApi.cancel(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
      queryClient.invalidateQueries({ queryKey: campaignKeys.summary() });
    },
  });
}

// Duplicate campaign
export function useDuplicateCampaign() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, name }: { id: string; name?: string }) =>
      campaignsApi.duplicate(id, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.lists() });
      queryClient.invalidateQueries({ queryKey: campaignKeys.summary() });
    },
  });
}

// Retry failed recipients
export function useRetryFailedRecipients() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => campaignsApi.retryFailed(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: campaignKeys.recipients(id) });
    },
  });
}

// Select A/B test winner
export function useSelectABWinner() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, variantId }: { id: string; variantId?: string }) =>
      campaignsApi.selectABWinner(id, variantId),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: campaignKeys.detail(id) });
    },
  });
}

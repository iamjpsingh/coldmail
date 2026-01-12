import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  trackingDomainsApi,
  trackingEventsApi,
  bounceRecordsApi,
  complaintRecordsApi,
  suppressionListApi,
} from '@/api/tracking';
import type { TrackingDomainCreate, SuppressionListCreate } from '@/types/tracking';

// Query keys
export const trackingKeys = {
  all: ['tracking'] as const,
  // Domains
  domains: () => [...trackingKeys.all, 'domains'] as const,
  domainsList: () => [...trackingKeys.domains(), 'list'] as const,
  domainDetail: (id: string) => [...trackingKeys.domains(), id] as const,
  domainDns: (id: string) => [...trackingKeys.domains(), id, 'dns'] as const,
  // Events
  events: () => [...trackingKeys.all, 'events'] as const,
  eventsList: (filters?: {
    event_type?: string;
    campaign_id?: string;
    contact_id?: string;
    exclude_bots?: boolean;
  }) => [...trackingKeys.events(), 'list', filters] as const,
  eventDetail: (id: string) => [...trackingKeys.events(), id] as const,
  eventsStats: (campaign_id?: string) =>
    [...trackingKeys.events(), 'stats', campaign_id] as const,
  eventsDevices: (campaign_id?: string) =>
    [...trackingKeys.events(), 'devices', campaign_id] as const,
  eventsLocations: (campaign_id?: string) =>
    [...trackingKeys.events(), 'locations', campaign_id] as const,
  eventsBrowsers: (campaign_id?: string) =>
    [...trackingKeys.events(), 'browsers', campaign_id] as const,
  // Bounces
  bounces: () => [...trackingKeys.all, 'bounces'] as const,
  bouncesList: (filters?: { bounce_type?: string; campaign_id?: string }) =>
    [...trackingKeys.bounces(), 'list', filters] as const,
  bouncesStats: () => [...trackingKeys.bounces(), 'stats'] as const,
  // Complaints
  complaints: () => [...trackingKeys.all, 'complaints'] as const,
  complaintsList: (filters?: { campaign_id?: string }) =>
    [...trackingKeys.complaints(), 'list', filters] as const,
  complaintsStats: () => [...trackingKeys.complaints(), 'stats'] as const,
  // Suppression
  suppression: () => [...trackingKeys.all, 'suppression'] as const,
  suppressionList: (filters?: { reason?: string; search?: string }) =>
    [...trackingKeys.suppression(), 'list', filters] as const,
  suppressionStats: () => [...trackingKeys.suppression(), 'stats'] as const,
};

// ==================== Tracking Domains Hooks ====================

export function useTrackingDomains() {
  return useQuery({
    queryKey: trackingKeys.domainsList(),
    queryFn: () => trackingDomainsApi.list(),
  });
}

export function useTrackingDomain(id: string) {
  return useQuery({
    queryKey: trackingKeys.domainDetail(id),
    queryFn: () => trackingDomainsApi.get(id),
    enabled: !!id,
  });
}

export function useTrackingDomainDns(id: string) {
  return useQuery({
    queryKey: trackingKeys.domainDns(id),
    queryFn: () => trackingDomainsApi.getDnsRecords(id),
    enabled: !!id,
  });
}

export function useCreateTrackingDomain() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TrackingDomainCreate) => trackingDomainsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trackingKeys.domainsList() });
    },
  });
}

export function useUpdateTrackingDomain() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<TrackingDomainCreate> }) =>
      trackingDomainsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: trackingKeys.domainDetail(id) });
      queryClient.invalidateQueries({ queryKey: trackingKeys.domainsList() });
    },
  });
}

export function useDeleteTrackingDomain() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => trackingDomainsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trackingKeys.domainsList() });
    },
  });
}

export function useVerifyTrackingDomain() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => trackingDomainsApi.verify(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: trackingKeys.domainDetail(id) });
      queryClient.invalidateQueries({ queryKey: trackingKeys.domainsList() });
    },
  });
}

export function useSetDefaultTrackingDomain() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => trackingDomainsApi.setDefault(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trackingKeys.domainsList() });
    },
  });
}

// ==================== Tracking Events Hooks ====================

export function useTrackingEvents(params?: {
  event_type?: string;
  campaign_id?: string;
  contact_id?: string;
  exclude_bots?: boolean;
}) {
  return useQuery({
    queryKey: trackingKeys.eventsList(params),
    queryFn: () => trackingEventsApi.list(params),
  });
}

export function useTrackingEvent(id: string) {
  return useQuery({
    queryKey: trackingKeys.eventDetail(id),
    queryFn: () => trackingEventsApi.get(id),
    enabled: !!id,
  });
}

export function useTrackingStats(campaign_id?: string) {
  return useQuery({
    queryKey: trackingKeys.eventsStats(campaign_id),
    queryFn: () => trackingEventsApi.getStats(campaign_id),
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

export function useDeviceBreakdown(campaign_id?: string) {
  return useQuery({
    queryKey: trackingKeys.eventsDevices(campaign_id),
    queryFn: () => trackingEventsApi.getDeviceBreakdown(campaign_id),
  });
}

export function useLocationBreakdown(campaign_id?: string) {
  return useQuery({
    queryKey: trackingKeys.eventsLocations(campaign_id),
    queryFn: () => trackingEventsApi.getLocationBreakdown(campaign_id),
  });
}

export function useBrowserBreakdown(campaign_id?: string) {
  return useQuery({
    queryKey: trackingKeys.eventsBrowsers(campaign_id),
    queryFn: () => trackingEventsApi.getBrowserBreakdown(campaign_id),
  });
}

// ==================== Bounce Records Hooks ====================

export function useBounceRecords(params?: {
  bounce_type?: string;
  campaign_id?: string;
}) {
  return useQuery({
    queryKey: trackingKeys.bouncesList(params),
    queryFn: () => bounceRecordsApi.list(params),
  });
}

export function useBounceStats() {
  return useQuery({
    queryKey: trackingKeys.bouncesStats(),
    queryFn: () => bounceRecordsApi.getStats(),
  });
}

// ==================== Complaint Records Hooks ====================

export function useComplaintRecords(params?: { campaign_id?: string }) {
  return useQuery({
    queryKey: trackingKeys.complaintsList(params),
    queryFn: () => complaintRecordsApi.list(params),
  });
}

export function useComplaintStats() {
  return useQuery({
    queryKey: trackingKeys.complaintsStats(),
    queryFn: () => complaintRecordsApi.getStats(),
  });
}

// ==================== Suppression List Hooks ====================

export function useSuppressionList(params?: { reason?: string; search?: string }) {
  return useQuery({
    queryKey: trackingKeys.suppressionList(params),
    queryFn: () => suppressionListApi.list(params),
  });
}

export function useSuppressionStats() {
  return useQuery({
    queryKey: trackingKeys.suppressionStats(),
    queryFn: () => suppressionListApi.getStats(),
  });
}

export function useAddToSuppressionList() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: SuppressionListCreate) => suppressionListApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trackingKeys.suppressionList() });
      queryClient.invalidateQueries({ queryKey: trackingKeys.suppressionStats() });
    },
  });
}

export function useBulkAddToSuppressionList() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      emails,
      reason,
      source,
    }: {
      emails: string[];
      reason: string;
      source?: string;
    }) => suppressionListApi.bulkAdd(emails, reason, source),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trackingKeys.suppressionList() });
      queryClient.invalidateQueries({ queryKey: trackingKeys.suppressionStats() });
    },
  });
}

export function useRemoveFromSuppressionList() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => suppressionListApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trackingKeys.suppressionList() });
      queryClient.invalidateQueries({ queryKey: trackingKeys.suppressionStats() });
    },
  });
}

export function useCheckSuppression() {
  return useMutation({
    mutationFn: (email: string) => suppressionListApi.check(email),
  });
}

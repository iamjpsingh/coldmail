import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  websiteTrackingScriptApi,
  websiteVisitorsApi,
  visitorSessionsApi,
} from '@/api/website-tracking';
import type { WebsiteTrackingScriptUpdate } from '@/types/tracking';

// Query keys
export const websiteTrackingKeys = {
  all: ['websiteTracking'] as const,
  script: () => [...websiteTrackingKeys.all, 'script'] as const,
  visitors: () => [...websiteTrackingKeys.all, 'visitors'] as const,
  visitorsList: (params?: Record<string, unknown>) =>
    [...websiteTrackingKeys.visitors(), 'list', params] as const,
  visitor: (id: string) => [...websiteTrackingKeys.visitors(), id] as const,
  visitorSessions: (id: string) =>
    [...websiteTrackingKeys.visitor(id), 'sessions'] as const,
  visitorPageViews: (id: string) =>
    [...websiteTrackingKeys.visitor(id), 'pageViews'] as const,
  visitorEvents: (id: string, eventType?: string) =>
    [...websiteTrackingKeys.visitor(id), 'events', eventType] as const,
  stats: () => [...websiteTrackingKeys.all, 'stats'] as const,
  topPages: () => [...websiteTrackingKeys.all, 'topPages'] as const,
  recentVisitors: (limit?: number) =>
    [...websiteTrackingKeys.all, 'recent', limit] as const,
  sessions: () => [...websiteTrackingKeys.all, 'sessions'] as const,
  sessionsList: (params?: Record<string, unknown>) =>
    [...websiteTrackingKeys.sessions(), 'list', params] as const,
  session: (id: string) => [...websiteTrackingKeys.sessions(), id] as const,
  sessionPageViews: (id: string) =>
    [...websiteTrackingKeys.session(id), 'pageViews'] as const,
  sessionEvents: (id: string) =>
    [...websiteTrackingKeys.session(id), 'events'] as const,
};

// Tracking Script hooks
export function useWebsiteTrackingScript() {
  return useQuery({
    queryKey: websiteTrackingKeys.script(),
    queryFn: websiteTrackingScriptApi.get,
  });
}

export function useUpdateWebsiteTrackingScript() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: WebsiteTrackingScriptUpdate }) =>
      websiteTrackingScriptApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: websiteTrackingKeys.script() });
    },
  });
}

export function useWebsiteTrackingSnippet(id: string) {
  return useQuery({
    queryKey: [...websiteTrackingKeys.script(), 'snippet', id],
    queryFn: () => websiteTrackingScriptApi.getSnippet(id),
    enabled: !!id,
  });
}

export function useRegenerateTrackingScript() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => websiteTrackingScriptApi.regenerate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: websiteTrackingKeys.script() });
    },
  });
}

// Visitors hooks
export function useWebsiteVisitors(params?: {
  is_identified?: boolean;
  contact_id?: string;
  search?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: websiteTrackingKeys.visitorsList(params),
    queryFn: () => websiteVisitorsApi.list(params),
  });
}

export function useWebsiteVisitor(id: string) {
  return useQuery({
    queryKey: websiteTrackingKeys.visitor(id),
    queryFn: () => websiteVisitorsApi.get(id),
    enabled: !!id,
  });
}

export function useVisitorSessions(
  visitorId: string,
  params?: { page?: number; page_size?: number }
) {
  return useQuery({
    queryKey: [...websiteTrackingKeys.visitorSessions(visitorId), params],
    queryFn: () => websiteVisitorsApi.getSessions(visitorId, params),
    enabled: !!visitorId,
  });
}

export function useVisitorPageViews(
  visitorId: string,
  params?: { page?: number; page_size?: number }
) {
  return useQuery({
    queryKey: [...websiteTrackingKeys.visitorPageViews(visitorId), params],
    queryFn: () => websiteVisitorsApi.getPageViews(visitorId, params),
    enabled: !!visitorId,
  });
}

export function useVisitorEvents(
  visitorId: string,
  params?: { event_type?: string; page?: number; page_size?: number }
) {
  return useQuery({
    queryKey: websiteTrackingKeys.visitorEvents(visitorId, params?.event_type),
    queryFn: () => websiteVisitorsApi.getEvents(visitorId, params),
    enabled: !!visitorId,
  });
}

export function useIdentifyVisitor() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, contactId }: { id: string; contactId: string }) =>
      websiteVisitorsApi.identify(id, contactId),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: websiteTrackingKeys.visitor(id) });
      queryClient.invalidateQueries({ queryKey: websiteTrackingKeys.visitors() });
      queryClient.invalidateQueries({ queryKey: websiteTrackingKeys.stats() });
    },
  });
}

export function useWebsiteTrackingStats() {
  return useQuery({
    queryKey: websiteTrackingKeys.stats(),
    queryFn: websiteVisitorsApi.getStats,
  });
}

export function useTopPages() {
  return useQuery({
    queryKey: websiteTrackingKeys.topPages(),
    queryFn: websiteVisitorsApi.getTopPages,
  });
}

export function useRecentVisitors(limit?: number) {
  return useQuery({
    queryKey: websiteTrackingKeys.recentVisitors(limit),
    queryFn: () => websiteVisitorsApi.getRecent(limit),
  });
}

// Sessions hooks
export function useSessions(params?: {
  visitor_id?: string;
  is_active?: boolean;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: websiteTrackingKeys.sessionsList(params),
    queryFn: () => visitorSessionsApi.list(params),
  });
}

export function useSession(id: string) {
  return useQuery({
    queryKey: websiteTrackingKeys.session(id),
    queryFn: () => visitorSessionsApi.get(id),
    enabled: !!id,
  });
}

export function useSessionPageViews(sessionId: string) {
  return useQuery({
    queryKey: websiteTrackingKeys.sessionPageViews(sessionId),
    queryFn: () => visitorSessionsApi.getPageViews(sessionId),
    enabled: !!sessionId,
  });
}

export function useSessionEvents(sessionId: string) {
  return useQuery({
    queryKey: websiteTrackingKeys.sessionEvents(sessionId),
    queryFn: () => visitorSessionsApi.getEvents(sessionId),
    enabled: !!sessionId,
  });
}

import { apiClient } from './client';
import type {
  WebsiteTrackingScript,
  WebsiteTrackingScriptUpdate,
  WebsiteVisitorListItem,
  WebsiteVisitorDetail,
  VisitorSession,
  PageView,
  WebsiteEvent,
  WebsiteTrackingStats,
  TopPage,
} from '@/types/tracking';

// Website Tracking Script API
export const websiteTrackingScriptApi = {
  get: async (): Promise<WebsiteTrackingScript> => {
    const response = await apiClient.get<WebsiteTrackingScript>(
      '/tracking/website/script/'
    );
    return response.data;
  },

  update: async (
    id: string,
    data: WebsiteTrackingScriptUpdate
  ): Promise<WebsiteTrackingScript> => {
    const response = await apiClient.patch<WebsiteTrackingScript>(
      `/tracking/website/script/${id}/`,
      data
    );
    return response.data;
  },

  getSnippet: async (id: string): Promise<{ snippet: string }> => {
    const response = await apiClient.get<{ snippet: string }>(
      `/tracking/website/script/${id}/snippet/`
    );
    return response.data;
  },

  regenerate: async (id: string): Promise<WebsiteTrackingScript> => {
    const response = await apiClient.post<WebsiteTrackingScript>(
      `/tracking/website/script/${id}/regenerate/`
    );
    return response.data;
  },
};

// Website Visitors API
export const websiteVisitorsApi = {
  list: async (params?: {
    is_identified?: boolean;
    contact_id?: string;
    search?: string;
    start_date?: string;
    end_date?: string;
    page?: number;
    page_size?: number;
  }): Promise<{
    count: number;
    next: string | null;
    previous: string | null;
    results: WebsiteVisitorListItem[];
  }> => {
    const response = await apiClient.get('/tracking/website/visitors/', {
      params,
    });
    return response.data;
  },

  get: async (id: string): Promise<WebsiteVisitorDetail> => {
    const response = await apiClient.get<WebsiteVisitorDetail>(
      `/tracking/website/visitors/${id}/`
    );
    return response.data;
  },

  getSessions: async (
    id: string,
    params?: { page?: number; page_size?: number }
  ): Promise<{
    count: number;
    next: string | null;
    previous: string | null;
    results: VisitorSession[];
  }> => {
    const response = await apiClient.get(
      `/tracking/website/visitors/${id}/sessions/`,
      { params }
    );
    return response.data;
  },

  getPageViews: async (
    id: string,
    params?: { page?: number; page_size?: number }
  ): Promise<{
    count: number;
    next: string | null;
    previous: string | null;
    results: PageView[];
  }> => {
    const response = await apiClient.get(
      `/tracking/website/visitors/${id}/page_views/`,
      { params }
    );
    return response.data;
  },

  getEvents: async (
    id: string,
    params?: { event_type?: string; page?: number; page_size?: number }
  ): Promise<{
    count: number;
    next: string | null;
    previous: string | null;
    results: WebsiteEvent[];
  }> => {
    const response = await apiClient.get(
      `/tracking/website/visitors/${id}/events/`,
      { params }
    );
    return response.data;
  },

  identify: async (
    id: string,
    contactId: string
  ): Promise<WebsiteVisitorDetail> => {
    const response = await apiClient.post<WebsiteVisitorDetail>(
      `/tracking/website/visitors/${id}/identify/`,
      { contact_id: contactId }
    );
    return response.data;
  },

  getStats: async (): Promise<WebsiteTrackingStats> => {
    const response = await apiClient.get<WebsiteTrackingStats>(
      '/tracking/website/visitors/stats/'
    );
    return response.data;
  },

  getTopPages: async (): Promise<TopPage[]> => {
    const response = await apiClient.get<TopPage[]>(
      '/tracking/website/visitors/top_pages/'
    );
    return response.data;
  },

  getRecent: async (limit?: number): Promise<WebsiteVisitorListItem[]> => {
    const response = await apiClient.get<WebsiteVisitorListItem[]>(
      '/tracking/website/visitors/recent/',
      { params: { limit } }
    );
    return response.data;
  },
};

// Visitor Sessions API
export const visitorSessionsApi = {
  list: async (params?: {
    visitor_id?: string;
    is_active?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<{
    count: number;
    next: string | null;
    previous: string | null;
    results: VisitorSession[];
  }> => {
    const response = await apiClient.get('/tracking/website/sessions/', {
      params,
    });
    return response.data;
  },

  get: async (id: string): Promise<VisitorSession> => {
    const response = await apiClient.get<VisitorSession>(
      `/tracking/website/sessions/${id}/`
    );
    return response.data;
  },

  getPageViews: async (id: string): Promise<PageView[]> => {
    const response = await apiClient.get<PageView[]>(
      `/tracking/website/sessions/${id}/page_views/`
    );
    return response.data;
  },

  getEvents: async (id: string): Promise<WebsiteEvent[]> => {
    const response = await apiClient.get<WebsiteEvent[]>(
      `/tracking/website/sessions/${id}/events/`
    );
    return response.data;
  },
};

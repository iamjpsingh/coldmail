import { apiClient } from './client';
import type {
  TrackingDomain,
  TrackingDomainCreate,
  DNSRecord,
  TrackingEvent,
  TrackingEventListItem,
  BounceRecord,
  ComplaintRecord,
  SuppressionListItem,
  SuppressionListCreate,
  TrackingStats,
  DeviceBreakdown,
  LocationBreakdown,
  BrowserBreakdown,
  BounceStats,
  ComplaintStats,
  SuppressionStats,
} from '@/types/tracking';

// Tracking Domains API
export const trackingDomainsApi = {
  list: async (): Promise<TrackingDomain[]> => {
    const response = await apiClient.get('/tracking/domains/');
    return response.data;
  },

  get: async (id: string): Promise<TrackingDomain> => {
    const response = await apiClient.get(`/tracking/domains/${id}/`);
    return response.data;
  },

  create: async (data: TrackingDomainCreate): Promise<TrackingDomain> => {
    const response = await apiClient.post('/tracking/domains/', data);
    return response.data;
  },

  update: async (
    id: string,
    data: Partial<TrackingDomainCreate>
  ): Promise<TrackingDomain> => {
    const response = await apiClient.patch(`/tracking/domains/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/tracking/domains/${id}/`);
  },

  verify: async (id: string): Promise<TrackingDomain> => {
    const response = await apiClient.post(`/tracking/domains/${id}/verify/`);
    return response.data;
  },

  setDefault: async (id: string): Promise<TrackingDomain> => {
    const response = await apiClient.post(`/tracking/domains/${id}/set_default/`);
    return response.data;
  },

  getDnsRecords: async (id: string): Promise<{ records: DNSRecord[] }> => {
    const response = await apiClient.get(`/tracking/domains/${id}/dns_records/`);
    return response.data;
  },
};

// Tracking Events API
export const trackingEventsApi = {
  list: async (params?: {
    event_type?: string;
    campaign_id?: string;
    contact_id?: string;
    exclude_bots?: boolean;
  }): Promise<TrackingEventListItem[]> => {
    const response = await apiClient.get('/tracking/events/', { params });
    return response.data;
  },

  get: async (id: string): Promise<TrackingEvent> => {
    const response = await apiClient.get(`/tracking/events/${id}/`);
    return response.data;
  },

  getStats: async (campaign_id?: string): Promise<TrackingStats> => {
    const response = await apiClient.get('/tracking/events/stats/', {
      params: { campaign_id },
    });
    return response.data;
  },

  getDeviceBreakdown: async (campaign_id?: string): Promise<DeviceBreakdown[]> => {
    const response = await apiClient.get('/tracking/events/device_breakdown/', {
      params: { campaign_id },
    });
    return response.data;
  },

  getLocationBreakdown: async (
    campaign_id?: string
  ): Promise<LocationBreakdown[]> => {
    const response = await apiClient.get('/tracking/events/location_breakdown/', {
      params: { campaign_id },
    });
    return response.data;
  },

  getBrowserBreakdown: async (
    campaign_id?: string
  ): Promise<BrowserBreakdown[]> => {
    const response = await apiClient.get('/tracking/events/browser_breakdown/', {
      params: { campaign_id },
    });
    return response.data;
  },
};

// Bounce Records API
export const bounceRecordsApi = {
  list: async (params?: {
    bounce_type?: string;
    campaign_id?: string;
  }): Promise<BounceRecord[]> => {
    const response = await apiClient.get('/tracking/bounces/', { params });
    return response.data;
  },

  get: async (id: string): Promise<BounceRecord> => {
    const response = await apiClient.get(`/tracking/bounces/${id}/`);
    return response.data;
  },

  getStats: async (): Promise<BounceStats> => {
    const response = await apiClient.get('/tracking/bounces/stats/');
    return response.data;
  },
};

// Complaint Records API
export const complaintRecordsApi = {
  list: async (params?: { campaign_id?: string }): Promise<ComplaintRecord[]> => {
    const response = await apiClient.get('/tracking/complaints/', { params });
    return response.data;
  },

  get: async (id: string): Promise<ComplaintRecord> => {
    const response = await apiClient.get(`/tracking/complaints/${id}/`);
    return response.data;
  },

  getStats: async (): Promise<ComplaintStats> => {
    const response = await apiClient.get('/tracking/complaints/stats/');
    return response.data;
  },
};

// Suppression List API
export const suppressionListApi = {
  list: async (params?: {
    reason?: string;
    search?: string;
  }): Promise<SuppressionListItem[]> => {
    const response = await apiClient.get('/tracking/suppression/', { params });
    return response.data;
  },

  get: async (id: string): Promise<SuppressionListItem> => {
    const response = await apiClient.get(`/tracking/suppression/${id}/`);
    return response.data;
  },

  create: async (data: SuppressionListCreate): Promise<SuppressionListItem> => {
    const response = await apiClient.post('/tracking/suppression/', data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/tracking/suppression/${id}/`);
  },

  bulkAdd: async (
    emails: string[],
    reason: string,
    source?: string
  ): Promise<{ added: number }> => {
    const response = await apiClient.post('/tracking/suppression/bulk_add/', {
      emails,
      reason,
      source,
    });
    return response.data;
  },

  check: async (email: string): Promise<{ email: string; is_suppressed: boolean }> => {
    const response = await apiClient.post('/tracking/suppression/check/', {
      email,
    });
    return response.data;
  },

  getStats: async (): Promise<SuppressionStats> => {
    const response = await apiClient.get('/tracking/suppression/stats/');
    return response.data;
  },
};

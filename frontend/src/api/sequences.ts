import { apiClient } from './client';
import type {
  Sequence,
  SequenceListItem,
  SequenceStep,
  SequenceEnrollment,
  SequenceEnrollmentListItem,
  SequenceEvent,
  SequenceStepExecution,
  SequenceStatsResponse,
  CreateSequenceRequest,
  UpdateSequenceRequest,
  CreateStepRequest,
  UpdateStepRequest,
  EnrollContactRequest,
  BulkEnrollRequest,
  BulkEnrollResponse,
  EnrollmentsListResponse,
} from '@/types/sequences';

// Sequences API
export const sequencesApi = {
  list: async (): Promise<SequenceListItem[]> => {
    const response = await apiClient.get<SequenceListItem[]>('/sequences/');
    return response.data;
  },

  get: async (id: string): Promise<Sequence> => {
    const response = await apiClient.get<Sequence>(`/sequences/${id}/`);
    return response.data;
  },

  create: async (data: CreateSequenceRequest): Promise<Sequence> => {
    const response = await apiClient.post<Sequence>('/sequences/', data);
    return response.data;
  },

  update: async (id: string, data: UpdateSequenceRequest): Promise<Sequence> => {
    const response = await apiClient.patch<Sequence>(`/sequences/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/sequences/${id}/`);
  },

  activate: async (id: string): Promise<Sequence> => {
    const response = await apiClient.post<Sequence>(`/sequences/${id}/activate/`);
    return response.data;
  },

  pause: async (id: string): Promise<Sequence> => {
    const response = await apiClient.post<Sequence>(`/sequences/${id}/pause/`);
    return response.data;
  },

  resume: async (id: string): Promise<Sequence> => {
    const response = await apiClient.post<Sequence>(`/sequences/${id}/resume/`);
    return response.data;
  },

  archive: async (id: string): Promise<Sequence> => {
    const response = await apiClient.post<Sequence>(`/sequences/${id}/archive/`);
    return response.data;
  },

  duplicate: async (id: string): Promise<Sequence> => {
    const response = await apiClient.post<Sequence>(`/sequences/${id}/duplicate/`);
    return response.data;
  },

  enroll: async (
    id: string,
    data: EnrollContactRequest
  ): Promise<{ success: boolean; message: string; enrollment_id: string }> => {
    const response = await apiClient.post(`/sequences/${id}/enroll/`, data);
    return response.data;
  },

  bulkEnroll: async (id: string, data: BulkEnrollRequest): Promise<BulkEnrollResponse> => {
    const response = await apiClient.post<BulkEnrollResponse>(
      `/sequences/${id}/bulk_enroll/`,
      data
    );
    return response.data;
  },

  getEnrollments: async (
    id: string,
    params?: { status?: string; page?: number; page_size?: number }
  ): Promise<EnrollmentsListResponse> => {
    const response = await apiClient.get<EnrollmentsListResponse>(
      `/sequences/${id}/enrollments/`,
      { params }
    );
    return response.data;
  },

  getStats: async (id: string): Promise<SequenceStatsResponse> => {
    const response = await apiClient.get<SequenceStatsResponse>(`/sequences/${id}/stats/`);
    return response.data;
  },

  getEvents: async (
    id: string,
    params?: { event_type?: string; limit?: number }
  ): Promise<SequenceEvent[]> => {
    const response = await apiClient.get<SequenceEvent[]>(`/sequences/${id}/events/`, {
      params,
    });
    return response.data;
  },
};

// Steps API
export const stepsApi = {
  list: async (sequenceId: string): Promise<SequenceStep[]> => {
    const response = await apiClient.get<SequenceStep[]>('/sequence-steps/', {
      params: { sequence: sequenceId },
    });
    return response.data;
  },

  get: async (id: string): Promise<SequenceStep> => {
    const response = await apiClient.get<SequenceStep>(`/sequence-steps/${id}/`);
    return response.data;
  },

  create: async (data: CreateStepRequest): Promise<SequenceStep> => {
    const response = await apiClient.post<SequenceStep>('/sequence-steps/', data);
    return response.data;
  },

  update: async (id: string, data: UpdateStepRequest): Promise<SequenceStep> => {
    const response = await apiClient.patch<SequenceStep>(`/sequence-steps/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/sequence-steps/${id}/`);
  },

  toggleActive: async (id: string): Promise<SequenceStep> => {
    const response = await apiClient.post<SequenceStep>(
      `/sequence-steps/${id}/toggle_active/`
    );
    return response.data;
  },

  reorder: async (
    sequenceId: string,
    stepIds: string[]
  ): Promise<SequenceStep[]> => {
    const response = await apiClient.post<SequenceStep[]>('/sequence-steps/reorder/', {
      sequence: sequenceId,
      step_ids: stepIds,
    });
    return response.data;
  },
};

// Enrollments API
export const enrollmentsApi = {
  list: async (params?: {
    sequence?: string;
    contact?: string;
    status?: string;
  }): Promise<SequenceEnrollmentListItem[]> => {
    const response = await apiClient.get<SequenceEnrollmentListItem[]>('/enrollments/', {
      params,
    });
    return response.data;
  },

  get: async (id: string): Promise<SequenceEnrollment> => {
    const response = await apiClient.get<SequenceEnrollment>(`/enrollments/${id}/`);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/enrollments/${id}/`);
  },

  pause: async (id: string): Promise<SequenceEnrollment> => {
    const response = await apiClient.post<SequenceEnrollment>(`/enrollments/${id}/pause/`);
    return response.data;
  },

  resume: async (id: string): Promise<SequenceEnrollment> => {
    const response = await apiClient.post<SequenceEnrollment>(
      `/enrollments/${id}/resume/`
    );
    return response.data;
  },

  stop: async (
    id: string,
    reason?: string,
    details?: string
  ): Promise<SequenceEnrollment> => {
    const response = await apiClient.post<SequenceEnrollment>(`/enrollments/${id}/stop/`, {
      reason,
      details,
    });
    return response.data;
  },

  getExecutions: async (id: string): Promise<SequenceStepExecution[]> => {
    const response = await apiClient.get<SequenceStepExecution[]>(
      `/enrollments/${id}/executions/`
    );
    return response.data;
  },

  getEvents: async (id: string, limit?: number): Promise<SequenceEvent[]> => {
    const response = await apiClient.get<SequenceEvent[]>(`/enrollments/${id}/events/`, {
      params: { limit },
    });
    return response.data;
  },
};

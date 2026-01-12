import { apiClient } from '@/lib/api-client';
import type {
  EmailAccount,
  EmailAccountCreate,
  EmailAccountStats,
  EmailAccountLog,
  ConnectionTestResult,
  SendTestEmailRequest,
} from '@/types/email-account';

const BASE_PATH = '/email-accounts';

export const emailAccountsApi = {
  // List all email accounts
  list: async (params?: { status?: string; provider?: string }): Promise<EmailAccount[]> => {
    const response = await apiClient.get<EmailAccount[]>(BASE_PATH + '/', { params });
    return response.data;
  },

  // Get single email account
  get: async (id: string): Promise<EmailAccount> => {
    const response = await apiClient.get<EmailAccount>(`${BASE_PATH}/${id}/`);
    return response.data;
  },

  // Create email account
  create: async (data: EmailAccountCreate): Promise<EmailAccount> => {
    const response = await apiClient.post<EmailAccount>(BASE_PATH + '/', data);
    return response.data;
  },

  // Update email account
  update: async (id: string, data: Partial<EmailAccountCreate>): Promise<EmailAccount> => {
    const response = await apiClient.patch<EmailAccount>(`${BASE_PATH}/${id}/`, data);
    return response.data;
  },

  // Delete email account
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/${id}/`);
  },

  // Test connection
  testConnection: async (
    id: string,
    options?: { test_smtp?: boolean; test_imap?: boolean }
  ): Promise<ConnectionTestResult> => {
    const response = await apiClient.post<ConnectionTestResult>(
      `${BASE_PATH}/${id}/test_connection/`,
      options || { test_smtp: true }
    );
    return response.data;
  },

  // Send test email
  sendTestEmail: async (id: string, data: SendTestEmailRequest): Promise<{ success: boolean; message: string; message_id?: string }> => {
    const response = await apiClient.post(`${BASE_PATH}/${id}/send_test_email/`, data);
    return response.data;
  },

  // Pause account
  pause: async (id: string): Promise<{ status: string }> => {
    const response = await apiClient.post(`${BASE_PATH}/${id}/pause/`);
    return response.data;
  },

  // Resume account
  resume: async (id: string): Promise<{ status: string }> => {
    const response = await apiClient.post(`${BASE_PATH}/${id}/resume/`);
    return response.data;
  },

  // Start warmup
  startWarmup: async (
    id: string,
    options?: { daily_increase?: number; starting_limit?: number }
  ): Promise<{ status: string; current_limit: number; daily_increase: number }> => {
    const response = await apiClient.post(`${BASE_PATH}/${id}/start_warmup/`, options);
    return response.data;
  },

  // Stop warmup
  stopWarmup: async (id: string): Promise<{ status: string }> => {
    const response = await apiClient.post(`${BASE_PATH}/${id}/stop_warmup/`);
    return response.data;
  },

  // Get logs
  getLogs: async (id: string): Promise<EmailAccountLog[]> => {
    const response = await apiClient.get<EmailAccountLog[]>(`${BASE_PATH}/${id}/logs/`);
    return response.data;
  },

  // Get stats
  getStats: async (id: string): Promise<EmailAccountStats> => {
    const response = await apiClient.get<EmailAccountStats>(`${BASE_PATH}/${id}/stats/`);
    return response.data;
  },

  // OAuth - Get Google authorization URL
  getGoogleAuthUrl: async (): Promise<{ authorization_url: string }> => {
    const response = await apiClient.get(`${BASE_PATH}/oauth/google/`);
    return response.data;
  },

  // OAuth - Get Microsoft authorization URL
  getMicrosoftAuthUrl: async (): Promise<{ authorization_url: string }> => {
    const response = await apiClient.get(`${BASE_PATH}/oauth/microsoft/`);
    return response.data;
  },
};

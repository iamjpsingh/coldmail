import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { emailAccountsApi } from '@/api/email-accounts';
import type { EmailAccountCreate, SendTestEmailRequest } from '@/types/email-account';

export const emailAccountKeys = {
  all: ['email-accounts'] as const,
  lists: () => [...emailAccountKeys.all, 'list'] as const,
  list: (filters: Record<string, string>) => [...emailAccountKeys.lists(), filters] as const,
  details: () => [...emailAccountKeys.all, 'detail'] as const,
  detail: (id: string) => [...emailAccountKeys.details(), id] as const,
  stats: (id: string) => [...emailAccountKeys.detail(id), 'stats'] as const,
  logs: (id: string) => [...emailAccountKeys.detail(id), 'logs'] as const,
};

export function useEmailAccounts(filters?: { status?: string; provider?: string }) {
  return useQuery({
    queryKey: emailAccountKeys.list(filters || {}),
    queryFn: () => emailAccountsApi.list(filters),
  });
}

export function useEmailAccount(id: string) {
  return useQuery({
    queryKey: emailAccountKeys.detail(id),
    queryFn: () => emailAccountsApi.get(id),
    enabled: !!id,
  });
}

export function useEmailAccountStats(id: string) {
  return useQuery({
    queryKey: emailAccountKeys.stats(id),
    queryFn: () => emailAccountsApi.getStats(id),
    enabled: !!id,
  });
}

export function useEmailAccountLogs(id: string) {
  return useQuery({
    queryKey: emailAccountKeys.logs(id),
    queryFn: () => emailAccountsApi.getLogs(id),
    enabled: !!id,
  });
}

export function useCreateEmailAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: EmailAccountCreate) => emailAccountsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: emailAccountKeys.lists() });
    },
  });
}

export function useUpdateEmailAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<EmailAccountCreate> }) =>
      emailAccountsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: emailAccountKeys.lists() });
      queryClient.invalidateQueries({ queryKey: emailAccountKeys.detail(id) });
    },
  });
}

export function useDeleteEmailAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => emailAccountsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: emailAccountKeys.lists() });
    },
  });
}

export function useTestConnection() {
  return useMutation({
    mutationFn: ({ id, options }: { id: string; options?: { test_smtp?: boolean; test_imap?: boolean } }) =>
      emailAccountsApi.testConnection(id, options),
  });
}

export function useSendTestEmail() {
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SendTestEmailRequest }) =>
      emailAccountsApi.sendTestEmail(id, data),
  });
}

export function usePauseEmailAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => emailAccountsApi.pause(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: emailAccountKeys.lists() });
      queryClient.invalidateQueries({ queryKey: emailAccountKeys.detail(id) });
    },
  });
}

export function useResumeEmailAccount() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => emailAccountsApi.resume(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: emailAccountKeys.lists() });
      queryClient.invalidateQueries({ queryKey: emailAccountKeys.detail(id) });
    },
  });
}

export function useStartWarmup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      options,
    }: {
      id: string;
      options?: { daily_increase?: number; starting_limit?: number };
    }) => emailAccountsApi.startWarmup(id, options),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: emailAccountKeys.lists() });
      queryClient.invalidateQueries({ queryKey: emailAccountKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: emailAccountKeys.stats(id) });
    },
  });
}

export function useStopWarmup() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => emailAccountsApi.stopWarmup(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: emailAccountKeys.lists() });
      queryClient.invalidateQueries({ queryKey: emailAccountKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: emailAccountKeys.stats(id) });
    },
  });
}

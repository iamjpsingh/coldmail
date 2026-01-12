import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  contactsApi,
  tagsApi,
  contactListsApi,
  importJobsApi,
  scoringRulesApi,
  scoreThresholdsApi,
  scoreDecayApi,
  scoringApi,
} from '@/api/contacts';
import type {
  ContactCreate,
  ContactSearchParams,
  ScoringRuleCreate,
  ScoreThresholdCreate,
  ScoreDecayConfigUpdate,
  ScoreAdjustment,
  ApplyEventRequest,
} from '@/types/contact';

export const contactKeys = {
  all: ['contacts'] as const,
  lists: () => [...contactKeys.all, 'list'] as const,
  list: (filters: Record<string, string>) => [...contactKeys.lists(), filters] as const,
  details: () => [...contactKeys.all, 'detail'] as const,
  detail: (id: string) => [...contactKeys.details(), id] as const,
  activities: (id: string) => [...contactKeys.detail(id), 'activities'] as const,
};

export const tagKeys = {
  all: ['tags'] as const,
  lists: () => [...tagKeys.all, 'list'] as const,
};

export const contactListKeys = {
  all: ['contact-lists'] as const,
  lists: () => [...contactListKeys.all, 'list'] as const,
  detail: (id: string) => [...contactListKeys.all, 'detail', id] as const,
  contacts: (id: string) => [...contactListKeys.detail(id), 'contacts'] as const,
};

export const importJobKeys = {
  all: ['import-jobs'] as const,
  lists: () => [...importJobKeys.all, 'list'] as const,
  detail: (id: string) => [...importJobKeys.all, 'detail', id] as const,
};

// Contacts hooks
export function useContacts(filters?: Record<string, string>) {
  return useQuery({
    queryKey: contactKeys.list(filters || {}),
    queryFn: () => contactsApi.list(filters),
  });
}

export function useContact(id: string) {
  return useQuery({
    queryKey: contactKeys.detail(id),
    queryFn: () => contactsApi.get(id),
    enabled: !!id,
  });
}

export function useContactActivities(id: string) {
  return useQuery({
    queryKey: contactKeys.activities(id),
    queryFn: () => contactsApi.getActivities(id),
    enabled: !!id,
  });
}

export function useCreateContact() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ContactCreate) => contactsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contactKeys.lists() });
    },
  });
}

export function useUpdateContact() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ContactCreate> }) =>
      contactsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: contactKeys.lists() });
      queryClient.invalidateQueries({ queryKey: contactKeys.detail(id) });
    },
  });
}

export function useDeleteContact() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => contactsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contactKeys.lists() });
    },
  });
}

export function useSearchContacts() {
  return useMutation({
    mutationFn: (params: ContactSearchParams) => contactsApi.search(params),
  });
}

export function useBulkDeleteContacts() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (contactIds: string[]) => contactsApi.bulkDelete(contactIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contactKeys.lists() });
    },
  });
}

export function useBulkAddTags() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ contactIds, tagIds }: { contactIds: string[]; tagIds: string[] }) =>
      contactsApi.bulkAddTags(contactIds, tagIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contactKeys.lists() });
    },
  });
}

export function useBulkRemoveTags() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ contactIds, tagIds }: { contactIds: string[]; tagIds: string[] }) =>
      contactsApi.bulkRemoveTags(contactIds, tagIds),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contactKeys.lists() });
    },
  });
}

// Tags hooks
export function useTags() {
  return useQuery({
    queryKey: tagKeys.lists(),
    queryFn: () => tagsApi.list(),
  });
}

export function useCreateTag() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; color: string }) => tagsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tagKeys.lists() });
    },
  });
}

export function useDeleteTag() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => tagsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tagKeys.lists() });
    },
  });
}

// Contact Lists hooks
export function useContactLists() {
  return useQuery({
    queryKey: contactListKeys.lists(),
    queryFn: () => contactListsApi.list(),
  });
}

export function useContactList(id: string) {
  return useQuery({
    queryKey: contactListKeys.detail(id),
    queryFn: () => contactListsApi.get(id),
    enabled: !!id,
  });
}

export function useContactListContacts(id: string) {
  return useQuery({
    queryKey: contactListKeys.contacts(id),
    queryFn: () => contactListsApi.getContacts(id),
    enabled: !!id,
  });
}

export function useCreateContactList() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof contactListsApi.create>[0]) =>
      contactListsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contactListKeys.lists() });
    },
  });
}

export function useDeleteContactList() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => contactListsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: contactListKeys.lists() });
    },
  });
}

// Import Jobs hooks
export function useImportJobs() {
  return useQuery({
    queryKey: importJobKeys.lists(),
    queryFn: () => importJobsApi.list(),
  });
}

export function useImportJob(id: string) {
  return useQuery({
    queryKey: importJobKeys.detail(id),
    queryFn: () => importJobsApi.get(id),
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data && (data.status === 'processing' || data.status === 'pending')) {
        return 2000; // Poll every 2 seconds while processing
      }
      return false;
    },
  });
}

export function useUploadImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => importJobsApi.upload(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: importJobKeys.lists() });
    },
  });
}

export function useStartImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, fieldMapping }: { id: string; fieldMapping: Record<string, string> }) =>
      importJobsApi.start(id, fieldMapping),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: importJobKeys.lists() });
    },
  });
}

export function useCancelImport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => importJobsApi.cancel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: importJobKeys.lists() });
    },
  });
}

// Scoring keys
export const scoringKeys = {
  all: ['scoring'] as const,
  rules: () => [...scoringKeys.all, 'rules'] as const,
  rule: (id: string) => [...scoringKeys.rules(), id] as const,
  thresholds: () => [...scoringKeys.all, 'thresholds'] as const,
  threshold: (id: string) => [...scoringKeys.thresholds(), id] as const,
  decayConfig: () => [...scoringKeys.all, 'decay-config'] as const,
  stats: () => [...scoringKeys.all, 'stats'] as const,
  hotLeads: () => [...scoringKeys.all, 'hot-leads'] as const,
  history: (contactId: string) => [...scoringKeys.all, 'history', contactId] as const,
};

// Scoring Rules hooks
export function useScoringRules() {
  return useQuery({
    queryKey: scoringKeys.rules(),
    queryFn: () => scoringRulesApi.list(),
  });
}

export function useScoringRule(id: string) {
  return useQuery({
    queryKey: scoringKeys.rule(id),
    queryFn: () => scoringRulesApi.get(id),
    enabled: !!id,
  });
}

export function useCreateScoringRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ScoringRuleCreate) => scoringRulesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scoringKeys.rules() });
    },
  });
}

export function useUpdateScoringRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ScoringRuleCreate> }) =>
      scoringRulesApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: scoringKeys.rules() });
      queryClient.invalidateQueries({ queryKey: scoringKeys.rule(id) });
    },
  });
}

export function useDeleteScoringRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => scoringRulesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scoringKeys.rules() });
    },
  });
}

export function useToggleScoringRule() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => scoringRulesApi.toggleActive(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scoringKeys.rules() });
    },
  });
}

// Score Thresholds hooks
export function useScoreThresholds() {
  return useQuery({
    queryKey: scoringKeys.thresholds(),
    queryFn: () => scoreThresholdsApi.list(),
  });
}

export function useCreateScoreThreshold() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ScoreThresholdCreate) => scoreThresholdsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scoringKeys.thresholds() });
      queryClient.invalidateQueries({ queryKey: scoringKeys.stats() });
    },
  });
}

export function useUpdateScoreThreshold() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ScoreThresholdCreate> }) =>
      scoreThresholdsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scoringKeys.thresholds() });
      queryClient.invalidateQueries({ queryKey: scoringKeys.stats() });
    },
  });
}

export function useDeleteScoreThreshold() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => scoreThresholdsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scoringKeys.thresholds() });
    },
  });
}

// Score Decay Config hooks
export function useScoreDecayConfig() {
  return useQuery({
    queryKey: scoringKeys.decayConfig(),
    queryFn: () => scoreDecayApi.get(),
  });
}

export function useUpdateScoreDecayConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ScoreDecayConfigUpdate }) =>
      scoreDecayApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scoringKeys.decayConfig() });
    },
  });
}

export function useRunScoreDecay() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => scoreDecayApi.runNow(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: scoringKeys.decayConfig() });
      queryClient.invalidateQueries({ queryKey: scoringKeys.stats() });
      queryClient.invalidateQueries({ queryKey: contactKeys.lists() });
    },
  });
}

// Scoring Stats and Actions hooks
export function useScoringStats() {
  return useQuery({
    queryKey: scoringKeys.stats(),
    queryFn: () => scoringApi.getStats(),
  });
}

export function useHotLeads(limit?: number) {
  return useQuery({
    queryKey: [...scoringKeys.hotLeads(), limit] as const,
    queryFn: () => scoringApi.getHotLeads(limit),
  });
}

export function useAdjustScore() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ contactId, data }: { contactId: string; data: ScoreAdjustment }) =>
      scoringApi.adjustScore(contactId, data),
    onSuccess: (_, { contactId }) => {
      queryClient.invalidateQueries({ queryKey: contactKeys.detail(contactId) });
      queryClient.invalidateQueries({ queryKey: contactKeys.lists() });
      queryClient.invalidateQueries({ queryKey: scoringKeys.stats() });
      queryClient.invalidateQueries({ queryKey: scoringKeys.history(contactId) });
    },
  });
}

export function useApplyEvent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ contactId, data }: { contactId: string; data: ApplyEventRequest }) =>
      scoringApi.applyEvent(contactId, data),
    onSuccess: (_, { contactId }) => {
      queryClient.invalidateQueries({ queryKey: contactKeys.detail(contactId) });
      queryClient.invalidateQueries({ queryKey: contactKeys.lists() });
      queryClient.invalidateQueries({ queryKey: scoringKeys.stats() });
      queryClient.invalidateQueries({ queryKey: scoringKeys.history(contactId) });
    },
  });
}

export function useScoreHistory(contactId: string) {
  return useQuery({
    queryKey: scoringKeys.history(contactId),
    queryFn: () => scoringApi.getScoreHistory(contactId),
    enabled: !!contactId,
  });
}

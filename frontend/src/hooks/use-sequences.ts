import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sequencesApi, stepsApi, enrollmentsApi } from '@/api/sequences';
import type {
  CreateSequenceRequest,
  UpdateSequenceRequest,
  CreateStepRequest,
  UpdateStepRequest,
  EnrollContactRequest,
  BulkEnrollRequest,
} from '@/types/sequences';

// Query keys
export const sequenceKeys = {
  all: ['sequences'] as const,
  lists: () => [...sequenceKeys.all, 'list'] as const,
  list: () => [...sequenceKeys.lists()] as const,
  details: () => [...sequenceKeys.all, 'detail'] as const,
  detail: (id: string) => [...sequenceKeys.details(), id] as const,
  stats: (id: string) => [...sequenceKeys.detail(id), 'stats'] as const,
  events: (id: string) => [...sequenceKeys.detail(id), 'events'] as const,
  enrollments: (id: string) => [...sequenceKeys.detail(id), 'enrollments'] as const,
  steps: (sequenceId: string) => [...sequenceKeys.detail(sequenceId), 'steps'] as const,
};

export const enrollmentKeys = {
  all: ['enrollments'] as const,
  lists: () => [...enrollmentKeys.all, 'list'] as const,
  list: (params?: { sequence?: string; contact?: string; status?: string }) =>
    [...enrollmentKeys.lists(), params] as const,
  details: () => [...enrollmentKeys.all, 'detail'] as const,
  detail: (id: string) => [...enrollmentKeys.details(), id] as const,
  executions: (id: string) => [...enrollmentKeys.detail(id), 'executions'] as const,
  events: (id: string) => [...enrollmentKeys.detail(id), 'events'] as const,
};

// Sequences hooks
export function useSequences() {
  return useQuery({
    queryKey: sequenceKeys.list(),
    queryFn: sequencesApi.list,
  });
}

export function useSequence(id: string) {
  return useQuery({
    queryKey: sequenceKeys.detail(id),
    queryFn: () => sequencesApi.get(id),
    enabled: !!id,
  });
}

export function useSequenceStats(id: string) {
  return useQuery({
    queryKey: sequenceKeys.stats(id),
    queryFn: () => sequencesApi.getStats(id),
    enabled: !!id,
  });
}

export function useSequenceEvents(
  id: string,
  params?: { event_type?: string; limit?: number }
) {
  return useQuery({
    queryKey: [...sequenceKeys.events(id), params],
    queryFn: () => sequencesApi.getEvents(id, params),
    enabled: !!id,
  });
}

export function useSequenceEnrollments(
  id: string,
  params?: { status?: string; page?: number; page_size?: number }
) {
  return useQuery({
    queryKey: [...sequenceKeys.enrollments(id), params],
    queryFn: () => sequencesApi.getEnrollments(id, params),
    enabled: !!id,
  });
}

export function useCreateSequence() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateSequenceRequest) => sequencesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sequenceKeys.lists() });
    },
  });
}

export function useUpdateSequence() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateSequenceRequest }) =>
      sequencesApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: sequenceKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: sequenceKeys.lists() });
    },
  });
}

export function useDeleteSequence() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => sequencesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sequenceKeys.lists() });
    },
  });
}

export function useActivateSequence() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => sequencesApi.activate(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: sequenceKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: sequenceKeys.lists() });
    },
  });
}

export function usePauseSequence() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => sequencesApi.pause(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: sequenceKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: sequenceKeys.lists() });
    },
  });
}

export function useResumeSequence() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => sequencesApi.resume(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: sequenceKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: sequenceKeys.lists() });
    },
  });
}

export function useArchiveSequence() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => sequencesApi.archive(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: sequenceKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: sequenceKeys.lists() });
    },
  });
}

export function useDuplicateSequence() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => sequencesApi.duplicate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: sequenceKeys.lists() });
    },
  });
}

export function useEnrollContact() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      sequenceId,
      data,
    }: {
      sequenceId: string;
      data: EnrollContactRequest;
    }) => sequencesApi.enroll(sequenceId, data),
    onSuccess: (_, { sequenceId }) => {
      queryClient.invalidateQueries({ queryKey: sequenceKeys.detail(sequenceId) });
      queryClient.invalidateQueries({ queryKey: sequenceKeys.enrollments(sequenceId) });
      queryClient.invalidateQueries({ queryKey: sequenceKeys.stats(sequenceId) });
    },
  });
}

export function useBulkEnroll() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      sequenceId,
      data,
    }: {
      sequenceId: string;
      data: BulkEnrollRequest;
    }) => sequencesApi.bulkEnroll(sequenceId, data),
    onSuccess: (_, { sequenceId }) => {
      queryClient.invalidateQueries({ queryKey: sequenceKeys.detail(sequenceId) });
      queryClient.invalidateQueries({ queryKey: sequenceKeys.enrollments(sequenceId) });
      queryClient.invalidateQueries({ queryKey: sequenceKeys.stats(sequenceId) });
    },
  });
}

// Steps hooks
export function useSequenceSteps(sequenceId: string) {
  return useQuery({
    queryKey: sequenceKeys.steps(sequenceId),
    queryFn: () => stepsApi.list(sequenceId),
    enabled: !!sequenceId,
  });
}

export function useCreateStep() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateStepRequest) => stepsApi.create(data),
    onSuccess: (step) => {
      queryClient.invalidateQueries({
        queryKey: sequenceKeys.steps(step.sequence),
      });
      queryClient.invalidateQueries({
        queryKey: sequenceKeys.detail(step.sequence),
      });
    },
  });
}

export function useUpdateStep() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateStepRequest }) =>
      stepsApi.update(id, data),
    onSuccess: (step) => {
      queryClient.invalidateQueries({
        queryKey: sequenceKeys.steps(step.sequence),
      });
      queryClient.invalidateQueries({
        queryKey: sequenceKeys.detail(step.sequence),
      });
    },
  });
}

export function useDeleteStep() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id }: { id: string; sequenceId: string }) =>
      stepsApi.delete(id),
    onSuccess: (_, { sequenceId }) => {
      queryClient.invalidateQueries({ queryKey: sequenceKeys.steps(sequenceId) });
      queryClient.invalidateQueries({ queryKey: sequenceKeys.detail(sequenceId) });
    },
  });
}

export function useToggleStepActive() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => stepsApi.toggleActive(id),
    onSuccess: (step) => {
      queryClient.invalidateQueries({
        queryKey: sequenceKeys.steps(step.sequence),
      });
    },
  });
}

export function useReorderSteps() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      sequenceId,
      stepIds,
    }: {
      sequenceId: string;
      stepIds: string[];
    }) => stepsApi.reorder(sequenceId, stepIds),
    onSuccess: (_, { sequenceId }) => {
      queryClient.invalidateQueries({ queryKey: sequenceKeys.steps(sequenceId) });
    },
  });
}

// Enrollments hooks
export function useEnrollments(params?: {
  sequence?: string;
  contact?: string;
  status?: string;
}) {
  return useQuery({
    queryKey: enrollmentKeys.list(params),
    queryFn: () => enrollmentsApi.list(params),
  });
}

export function useEnrollment(id: string) {
  return useQuery({
    queryKey: enrollmentKeys.detail(id),
    queryFn: () => enrollmentsApi.get(id),
    enabled: !!id,
  });
}

export function useEnrollmentExecutions(id: string) {
  return useQuery({
    queryKey: enrollmentKeys.executions(id),
    queryFn: () => enrollmentsApi.getExecutions(id),
    enabled: !!id,
  });
}

export function useEnrollmentEvents(id: string, limit?: number) {
  return useQuery({
    queryKey: [...enrollmentKeys.events(id), limit],
    queryFn: () => enrollmentsApi.getEvents(id, limit),
    enabled: !!id,
  });
}

export function useDeleteEnrollment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => enrollmentsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: enrollmentKeys.lists() });
      queryClient.invalidateQueries({ queryKey: sequenceKeys.all });
    },
  });
}

export function usePauseEnrollment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => enrollmentsApi.pause(id),
    onSuccess: (enrollment) => {
      queryClient.invalidateQueries({ queryKey: enrollmentKeys.detail(enrollment.id) });
      queryClient.invalidateQueries({ queryKey: enrollmentKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: sequenceKeys.enrollments(enrollment.sequence),
      });
    },
  });
}

export function useResumeEnrollment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => enrollmentsApi.resume(id),
    onSuccess: (enrollment) => {
      queryClient.invalidateQueries({ queryKey: enrollmentKeys.detail(enrollment.id) });
      queryClient.invalidateQueries({ queryKey: enrollmentKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: sequenceKeys.enrollments(enrollment.sequence),
      });
    },
  });
}

export function useStopEnrollment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      reason,
      details,
    }: {
      id: string;
      reason?: string;
      details?: string;
    }) => enrollmentsApi.stop(id, reason, details),
    onSuccess: (enrollment) => {
      queryClient.invalidateQueries({ queryKey: enrollmentKeys.detail(enrollment.id) });
      queryClient.invalidateQueries({ queryKey: enrollmentKeys.lists() });
      queryClient.invalidateQueries({
        queryKey: sequenceKeys.enrollments(enrollment.sequence),
      });
      queryClient.invalidateQueries({
        queryKey: sequenceKeys.stats(enrollment.sequence),
      });
    },
  });
}

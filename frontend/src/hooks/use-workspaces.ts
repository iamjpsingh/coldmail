import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  workspacesApi,
  workspaceMembersApi,
  workspaceInvitationsApi,
  workspaceActivityApi,
} from '@/api/workspaces';
import type {
  WorkspaceCreate,
  WorkspaceUpdate,
  WorkspaceMemberUpdate,
  WorkspaceInvitationCreate,
} from '@/types/workspaces';

// Query keys
export const workspacesKeys = {
  all: ['workspaces'] as const,
  // Workspaces
  workspaces: () => [...workspacesKeys.all, 'list'] as const,
  workspace: (id: string) => [...workspacesKeys.all, id] as const,
  current: () => [...workspacesKeys.all, 'current'] as const,
  workspaceMembers: (id: string) => [...workspacesKeys.workspace(id), 'members'] as const,
  workspaceInvitations: (id: string) => [...workspacesKeys.workspace(id), 'invitations'] as const,
  workspaceActivity: (id: string) => [...workspacesKeys.workspace(id), 'activity'] as const,
  workspaceStats: (id: string) => [...workspacesKeys.workspace(id), 'stats'] as const,
  // Members
  members: () => [...workspacesKeys.all, 'members'] as const,
  member: (id: string) => [...workspacesKeys.members(), id] as const,
  // Invitations
  invitations: () => [...workspacesKeys.all, 'invitations'] as const,
  invitation: (id: string) => [...workspacesKeys.invitations(), id] as const,
  invitationByToken: (token: string) => [...workspacesKeys.invitations(), 'token', token] as const,
  // Activity
  activity: () => [...workspacesKeys.all, 'activity'] as const,
  activityList: (params?: Record<string, unknown>) => [...workspacesKeys.activity(), params] as const,
};

// ==================== Workspace Hooks ====================

export function useWorkspaces() {
  return useQuery({
    queryKey: workspacesKeys.workspaces(),
    queryFn: workspacesApi.list,
  });
}

export function useWorkspace(id: string) {
  return useQuery({
    queryKey: workspacesKeys.workspace(id),
    queryFn: () => workspacesApi.get(id),
    enabled: !!id,
  });
}

export function useCurrentWorkspace() {
  return useQuery({
    queryKey: workspacesKeys.current(),
    queryFn: workspacesApi.getCurrent,
  });
}

export function useCreateWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: WorkspaceCreate) => workspacesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspacesKeys.workspaces() });
      queryClient.invalidateQueries({ queryKey: workspacesKeys.current() });
    },
  });
}

export function useUpdateWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: WorkspaceUpdate }) =>
      workspacesApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: workspacesKeys.workspace(id) });
      queryClient.invalidateQueries({ queryKey: workspacesKeys.workspaces() });
      queryClient.invalidateQueries({ queryKey: workspacesKeys.current() });
    },
  });
}

export function useDeleteWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => workspacesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspacesKeys.workspaces() });
      queryClient.invalidateQueries({ queryKey: workspacesKeys.current() });
    },
  });
}

export function useSwitchWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (workspaceId: string) => workspacesApi.switch(workspaceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspacesKeys.current() });
      // Invalidate all queries since workspace changed
      queryClient.invalidateQueries();
    },
  });
}

export function useWorkspaceMembers(workspaceId: string) {
  return useQuery({
    queryKey: workspacesKeys.workspaceMembers(workspaceId),
    queryFn: () => workspacesApi.getMembers(workspaceId),
    enabled: !!workspaceId,
  });
}

export function useWorkspaceInvitations(workspaceId: string) {
  return useQuery({
    queryKey: workspacesKeys.workspaceInvitations(workspaceId),
    queryFn: () => workspacesApi.getInvitations(workspaceId),
    enabled: !!workspaceId,
  });
}

export function useInviteToWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ workspaceId, data }: { workspaceId: string; data: WorkspaceInvitationCreate }) =>
      workspacesApi.invite(workspaceId, data),
    onSuccess: (_, { workspaceId }) => {
      queryClient.invalidateQueries({ queryKey: workspacesKeys.workspaceInvitations(workspaceId) });
      queryClient.invalidateQueries({ queryKey: workspacesKeys.invitations() });
    },
  });
}

export function useWorkspaceActivity(workspaceId: string) {
  return useQuery({
    queryKey: workspacesKeys.workspaceActivity(workspaceId),
    queryFn: () => workspacesApi.getActivity(workspaceId),
    enabled: !!workspaceId,
  });
}

export function useWorkspaceStats(workspaceId: string) {
  return useQuery({
    queryKey: workspacesKeys.workspaceStats(workspaceId),
    queryFn: () => workspacesApi.getStats(workspaceId),
    enabled: !!workspaceId,
  });
}

// ==================== Member Hooks ====================

export function useMembers() {
  return useQuery({
    queryKey: workspacesKeys.members(),
    queryFn: workspaceMembersApi.list,
  });
}

export function useMember(id: string) {
  return useQuery({
    queryKey: workspacesKeys.member(id),
    queryFn: () => workspaceMembersApi.get(id),
    enabled: !!id,
  });
}

export function useUpdateMember() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: WorkspaceMemberUpdate }) =>
      workspaceMembersApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: workspacesKeys.member(id) });
      queryClient.invalidateQueries({ queryKey: workspacesKeys.members() });
    },
  });
}

export function useRemoveMember() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => workspaceMembersApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspacesKeys.members() });
    },
  });
}

export function useLeaveWorkspace() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: workspaceMembersApi.leave,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspacesKeys.workspaces() });
      queryClient.invalidateQueries({ queryKey: workspacesKeys.current() });
    },
  });
}

// ==================== Invitation Hooks ====================

export function useInvitations() {
  return useQuery({
    queryKey: workspacesKeys.invitations(),
    queryFn: workspaceInvitationsApi.list,
  });
}

export function useRevokeInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => workspaceInvitationsApi.revoke(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspacesKeys.invitations() });
    },
  });
}

export function useResendInvitation() {
  return useMutation({
    mutationFn: (id: string) => workspaceInvitationsApi.resend(id),
  });
}

export function useInvitationByToken(token: string) {
  return useQuery({
    queryKey: workspacesKeys.invitationByToken(token),
    queryFn: () => workspaceInvitationsApi.getByToken(token),
    enabled: !!token,
    retry: false,
  });
}

export function useAcceptInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (token: string) => workspaceInvitationsApi.accept(token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: workspacesKeys.workspaces() });
      queryClient.invalidateQueries({ queryKey: workspacesKeys.current() });
    },
  });
}

export function useDeclineInvitation() {
  return useMutation({
    mutationFn: (token: string) => workspaceInvitationsApi.decline(token),
  });
}

// ==================== Activity Hooks ====================

export function useActivityLog(params?: {
  action?: string;
  user?: string;
  page?: number;
  page_size?: number;
}) {
  return useQuery({
    queryKey: workspacesKeys.activityList(params),
    queryFn: () => workspaceActivityApi.list(params),
  });
}

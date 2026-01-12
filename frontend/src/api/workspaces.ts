import { api } from './client';
import type {
  Workspace,
  WorkspaceCreate,
  WorkspaceUpdate,
  WorkspaceMember,
  WorkspaceMemberUpdate,
  WorkspaceInvitation,
  WorkspaceInvitationCreate,
  WorkspaceActivity,
  WorkspaceStats,
  InvitationDetails,
} from '@/types/workspaces';
import type { PaginatedResponse } from '@/types/api';

// ==================== Workspaces API ====================

export const workspacesApi = {
  list: async (): Promise<PaginatedResponse<Workspace>> => {
    const response = await api.get('/workspaces/');
    return response.data;
  },

  get: async (id: string): Promise<Workspace> => {
    const response = await api.get(`/workspaces/${id}/`);
    return response.data;
  },

  getCurrent: async (): Promise<Workspace> => {
    const response = await api.get('/workspaces/current/');
    return response.data;
  },

  create: async (data: WorkspaceCreate): Promise<Workspace> => {
    const response = await api.post('/workspaces/', data);
    return response.data;
  },

  update: async (id: string, data: WorkspaceUpdate): Promise<Workspace> => {
    const response = await api.patch(`/workspaces/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`/workspaces/${id}/`);
  },

  switch: async (workspaceId: string): Promise<Workspace> => {
    const response = await api.post('/workspaces/switch/', { workspace_id: workspaceId });
    return response.data;
  },

  getMembers: async (id: string): Promise<WorkspaceMember[]> => {
    const response = await api.get(`/workspaces/${id}/members/`);
    return response.data;
  },

  getInvitations: async (id: string): Promise<WorkspaceInvitation[]> => {
    const response = await api.get(`/workspaces/${id}/invitations/`);
    return response.data;
  },

  invite: async (id: string, data: WorkspaceInvitationCreate): Promise<WorkspaceInvitation> => {
    const response = await api.post(`/workspaces/${id}/invite/`, data);
    return response.data;
  },

  getActivity: async (id: string): Promise<WorkspaceActivity[]> => {
    const response = await api.get(`/workspaces/${id}/activity/`);
    return response.data;
  },

  getStats: async (id: string): Promise<WorkspaceStats> => {
    const response = await api.get(`/workspaces/${id}/stats/`);
    return response.data;
  },
};

// ==================== Members API ====================

export const workspaceMembersApi = {
  list: async (): Promise<PaginatedResponse<WorkspaceMember>> => {
    const response = await api.get('/workspace-members/');
    return response.data;
  },

  get: async (id: string): Promise<WorkspaceMember> => {
    const response = await api.get(`/workspace-members/${id}/`);
    return response.data;
  },

  update: async (id: string, data: WorkspaceMemberUpdate): Promise<WorkspaceMember> => {
    const response = await api.patch(`/workspace-members/${id}/`, data);
    return response.data;
  },

  remove: async (id: string): Promise<void> => {
    await api.delete(`/workspace-members/${id}/`);
  },

  leave: async (): Promise<{ status: string }> => {
    const response = await api.post('/workspace-members/leave/');
    return response.data;
  },
};

// ==================== Invitations API ====================

export const workspaceInvitationsApi = {
  list: async (): Promise<PaginatedResponse<WorkspaceInvitation>> => {
    const response = await api.get('/workspace-invitations/');
    return response.data;
  },

  revoke: async (id: string): Promise<{ status: string }> => {
    const response = await api.post(`/workspace-invitations/${id}/revoke/`);
    return response.data;
  },

  resend: async (id: string): Promise<{ status: string }> => {
    const response = await api.post(`/workspace-invitations/${id}/resend/`);
    return response.data;
  },

  // Public invitation endpoints
  getByToken: async (token: string): Promise<InvitationDetails> => {
    const response = await api.get(`/invitations/${token}/`);
    return response.data;
  },

  accept: async (token: string): Promise<{ status: string; workspace: Workspace }> => {
    const response = await api.post(`/invitations/${token}/accept/`);
    return response.data;
  },

  decline: async (token: string): Promise<{ status: string }> => {
    const response = await api.post(`/invitations/${token}/decline/`);
    return response.data;
  },
};

// ==================== Activity API ====================

export const workspaceActivityApi = {
  list: async (params?: {
    action?: string;
    user?: string;
    page?: number;
    page_size?: number;
  }): Promise<PaginatedResponse<WorkspaceActivity>> => {
    const response = await api.get('/workspace-activity/', { params });
    return response.data;
  },

  get: async (id: string): Promise<WorkspaceActivity> => {
    const response = await api.get(`/workspace-activity/${id}/`);
    return response.data;
  },
};

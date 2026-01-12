/**
 * Workspace and Team Management Types
 */

export type WorkspaceMemberRole = 'owner' | 'admin' | 'member' | 'viewer';

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
  timezone: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login: string | null;
}

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  description: string;
  logo_url: string | null;
  owner: User;
  default_timezone: string;
  default_from_name: string;
  default_reply_to: string;
  primary_color: string;
  company_name: string;
  company_website: string;
  max_members: number;
  max_contacts: number;
  max_emails_per_day: number;
  is_active: boolean;
  member_count: number;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceMember {
  id: string;
  user: User;
  workspace_id: string;
  role: WorkspaceMemberRole;
  invited_by: User | null;
  invited_at: string;
  accepted_at: string | null;
  email_notifications: boolean;
  daily_digest: boolean;
  created_at: string;
}

export interface WorkspaceInvitation {
  id: string;
  workspace_id: string;
  email: string;
  role: WorkspaceMemberRole;
  invited_by: User;
  status: 'pending' | 'accepted' | 'declined' | 'expired' | 'revoked';
  message: string;
  expires_at: string;
  created_at: string;
}

export interface WorkspaceActivity {
  id: string;
  user: User | null;
  action: string;
  description: string;
  target_user: User | null;
  target_type: string;
  target_id: string;
  target_name: string;
  metadata: Record<string, unknown>;
  ip_address: string | null;
  created_at: string;
}

export interface WorkspaceStats {
  member_count: number;
  max_members: number;
  contact_count: number;
  max_contacts: number;
  campaign_count: number;
  sequence_count: number;
  emails_sent_today: number;
  max_emails_per_day: number;
}

// API Request Types
export interface CreateWorkspaceRequest {
  name: string;
  slug?: string;
  description?: string;
  company_name?: string;
  company_website?: string;
  default_timezone?: string;
}

export interface UpdateWorkspaceRequest {
  name?: string;
  description?: string;
  company_name?: string;
  company_website?: string;
  default_timezone?: string;
  default_from_name?: string;
  default_reply_to?: string;
  primary_color?: string;
  logo_url?: string;
}

export interface InviteMemberRequest {
  email: string;
  role: WorkspaceMemberRole;
  message?: string;
}

export interface UpdateMemberRoleRequest {
  role: WorkspaceMemberRole;
}

// Role permissions for UI display
export const ROLE_LABELS: Record<WorkspaceMemberRole, string> = {
  owner: 'Owner',
  admin: 'Admin',
  member: 'Member',
  viewer: 'Viewer',
};

export const ROLE_DESCRIPTIONS: Record<WorkspaceMemberRole, string> = {
  owner: 'Full access to all features and settings. Can transfer or delete the workspace.',
  admin: 'Can manage team members, integrations, and all content. Cannot delete workspace.',
  member: 'Can create and manage campaigns, contacts, and templates.',
  viewer: 'Read-only access to reports and analytics.',
};

export const ROLE_COLORS: Record<WorkspaceMemberRole, string> = {
  owner: 'bg-amber-500/10 text-amber-600 border-amber-500/20',
  admin: 'bg-violet-500/10 text-violet-600 border-violet-500/20',
  member: 'bg-blue-500/10 text-blue-600 border-blue-500/20',
  viewer: 'bg-slate-500/10 text-slate-600 border-slate-500/20',
};

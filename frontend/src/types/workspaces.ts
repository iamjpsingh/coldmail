// ==================== User Types ====================

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url: string | null;
}

// ==================== Workspace Types ====================

export type WorkspaceMemberRole = 'owner' | 'admin' | 'member' | 'viewer';

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
  member_count: number;
  can_add_members: boolean;
  current_user_role: WorkspaceMemberRole | null;
  current_user_permissions: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceCreate {
  name: string;
  description?: string;
  default_timezone?: string;
  company_name?: string;
}

export interface WorkspaceUpdate {
  name?: string;
  description?: string;
  logo_url?: string;
  default_timezone?: string;
  default_from_name?: string;
  default_reply_to?: string;
  primary_color?: string;
  company_name?: string;
  company_website?: string;
}

// ==================== Member Types ====================

export interface WorkspaceMember {
  id: string;
  user: User;
  role: WorkspaceMemberRole;
  role_display: string;
  permissions: string[];
  invited_by: User | null;
  invited_at: string;
  accepted_at: string | null;
  email_notifications: boolean;
  daily_digest: boolean;
  is_admin: boolean;
  is_owner: boolean;
  created_at: string;
}

export interface WorkspaceMemberUpdate {
  role?: WorkspaceMemberRole;
  email_notifications?: boolean;
  daily_digest?: boolean;
}

// ==================== Invitation Types ====================

export type InvitationStatus = 'pending' | 'accepted' | 'declined' | 'expired' | 'revoked';

export interface WorkspaceInvitation {
  id: string;
  email: string;
  role: WorkspaceMemberRole;
  role_display: string;
  invited_by: User;
  status: InvitationStatus;
  status_display: string;
  message: string;
  expires_at: string;
  is_expired: boolean;
  is_valid: boolean;
  created_at: string;
}

export interface WorkspaceInvitationCreate {
  email: string;
  role?: WorkspaceMemberRole;
  message?: string;
}

export interface InvitationDetails {
  workspace: {
    id: string;
    name: string;
  };
  role: WorkspaceMemberRole;
  role_display: string;
  invited_by: {
    email: string;
    name: string;
  };
  message: string;
  expires_at: string;
}

// ==================== Activity Types ====================

export type WorkspaceActivityAction =
  | 'workspace_created'
  | 'workspace_updated'
  | 'workspace_deleted'
  | 'member_invited'
  | 'member_joined'
  | 'member_left'
  | 'member_removed'
  | 'member_role_changed'
  | 'invitation_revoked'
  | 'campaign_created'
  | 'campaign_started'
  | 'campaign_paused'
  | 'campaign_completed'
  | 'campaign_deleted'
  | 'sequence_created'
  | 'sequence_activated'
  | 'sequence_paused'
  | 'sequence_deleted'
  | 'contacts_imported'
  | 'contacts_exported'
  | 'contacts_deleted'
  | 'integration_connected'
  | 'integration_disconnected'
  | 'settings_updated'
  | 'api_key_created'
  | 'api_key_revoked'
  | 'webhook_created'
  | 'webhook_deleted';

export interface WorkspaceActivity {
  id: string;
  user: User | null;
  action: WorkspaceActivityAction;
  action_display: string;
  description: string;
  target_user: User | null;
  target_type: string;
  target_id: string;
  target_name: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

// ==================== Stats Types ====================

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

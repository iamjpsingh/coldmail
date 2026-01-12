import { useState } from 'react';
import {
  Users,
  UserPlus,
  Mail,
  MoreHorizontal,
  Trash2,
  Shield,
  Crown,
  Clock,
  RefreshCw,
  X,
  Activity,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import {
  useCurrentWorkspace,
  useWorkspaceMembers,
  useWorkspaceInvitations,
  useWorkspaceActivity,
  useInviteToWorkspace,
  useUpdateMember,
  useRemoveMember,
  useRevokeInvitation,
  useResendInvitation,
} from '@/hooks/use-workspaces';
import type {
  WorkspaceMember,
  WorkspaceInvitation,
  WorkspaceMemberRole,
} from '@/types/workspaces';
import { formatDistanceToNow } from 'date-fns';

const roleIcons: Record<WorkspaceMemberRole, React.ReactNode> = {
  owner: <Crown className="h-4 w-4 text-yellow-500" />,
  admin: <Shield className="h-4 w-4 text-blue-500" />,
  member: <Users className="h-4 w-4 text-gray-500" />,
  viewer: <Users className="h-4 w-4 text-gray-400" />,
};

const roleColors: Record<WorkspaceMemberRole, string> = {
  owner: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
  admin: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
  member: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
  viewer: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
};

export default function TeamSettingsPage() {
  const { toast } = useToast();
  const [showInviteDialog, setShowInviteDialog] = useState(false);
  const [showRemoveDialog, setShowRemoveDialog] = useState<WorkspaceMember | null>(null);
  const [selectedTab, setSelectedTab] = useState('members');

  // Form state
  const [inviteForm, setInviteForm] = useState({
    email: '',
    role: 'member' as WorkspaceMemberRole,
    message: '',
  });

  // Queries
  const { data: workspace, isLoading: isLoadingWorkspace } = useCurrentWorkspace();
  const { data: members, isLoading: isLoadingMembers } = useWorkspaceMembers(workspace?.id || '');
  const { data: invitations } = useWorkspaceInvitations(workspace?.id || '');
  const { data: activities } = useWorkspaceActivity(workspace?.id || '');

  // Mutations
  const inviteMutation = useInviteToWorkspace();
  const updateMemberMutation = useUpdateMember();
  const removeMemberMutation = useRemoveMember();
  const revokeInvitationMutation = useRevokeInvitation();
  const resendInvitationMutation = useResendInvitation();

  const handleInvite = async () => {
    if (!workspace) return;
    try {
      await inviteMutation.mutateAsync({
        workspaceId: workspace.id,
        data: inviteForm,
      });
      setShowInviteDialog(false);
      setInviteForm({ email: '', role: 'member', message: '' });
      toast({
        title: 'Invitation Sent',
        description: `An invitation has been sent to ${inviteForm.email}.`,
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to send invitation.',
        variant: 'destructive',
      });
    }
  };

  const handleChangeRole = async (member: WorkspaceMember, newRole: WorkspaceMemberRole) => {
    try {
      await updateMemberMutation.mutateAsync({
        id: member.id,
        data: { role: newRole },
      });
      toast({
        title: 'Role Updated',
        description: `${member.user.email}'s role has been changed to ${newRole}.`,
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to update role.',
        variant: 'destructive',
      });
    }
  };

  const handleRemoveMember = async () => {
    if (!showRemoveDialog) return;
    try {
      await removeMemberMutation.mutateAsync(showRemoveDialog.id);
      setShowRemoveDialog(null);
      toast({
        title: 'Member Removed',
        description: `${showRemoveDialog.user.email} has been removed from the workspace.`,
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to remove member.',
        variant: 'destructive',
      });
    }
  };

  const handleRevokeInvitation = async (invitation: WorkspaceInvitation) => {
    try {
      await revokeInvitationMutation.mutateAsync(invitation.id);
      toast({
        title: 'Invitation Revoked',
        description: `The invitation to ${invitation.email} has been revoked.`,
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to revoke invitation.',
        variant: 'destructive',
      });
    }
  };

  const handleResendInvitation = async (invitation: WorkspaceInvitation) => {
    try {
      await resendInvitationMutation.mutateAsync(invitation.id);
      toast({
        title: 'Invitation Resent',
        description: `A new invitation email has been sent to ${invitation.email}.`,
      });
    } catch {
      toast({
        title: 'Error',
        description: 'Failed to resend invitation.',
        variant: 'destructive',
      });
    }
  };

  const canManageMembers = workspace?.current_user_permissions?.includes('manage_members');
  const pendingInvitations = invitations?.filter(i => i.status === 'pending') || [];

  if (isLoadingWorkspace) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Team Settings</h1>
          <p className="text-muted-foreground">
            Manage your team members and permissions
          </p>
        </div>
        {canManageMembers && (
          <Button onClick={() => setShowInviteDialog(true)}>
            <UserPlus className="mr-2 h-4 w-4" />
            Invite Member
          </Button>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Team Members</CardDescription>
            <CardTitle className="text-3xl">
              {workspace?.member_count || 0} / {workspace?.max_members || 0}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Pending Invitations</CardDescription>
            <CardTitle className="text-3xl">{pendingInvitations.length}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Your Role</CardDescription>
            <CardTitle className="text-3xl flex items-center gap-2">
              {roleIcons[workspace?.current_user_role || 'viewer']}
              <span className="capitalize">{workspace?.current_user_role}</span>
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList>
          <TabsTrigger value="members">
            <Users className="mr-2 h-4 w-4" />
            Members
          </TabsTrigger>
          <TabsTrigger value="invitations">
            <Mail className="mr-2 h-4 w-4" />
            Invitations
            {pendingInvitations.length > 0 && (
              <Badge variant="secondary" className="ml-2">
                {pendingInvitations.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="activity">
            <Activity className="mr-2 h-4 w-4" />
            Activity
          </TabsTrigger>
        </TabsList>

        <TabsContent value="members" className="mt-4">
          <Card>
            <CardContent className="pt-6">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Member</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Joined</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoadingMembers ? (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center py-8">
                        Loading...
                      </TableCell>
                    </TableRow>
                  ) : members?.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center py-8">
                        No members yet
                      </TableCell>
                    </TableRow>
                  ) : (
                    members?.map((member) => (
                      <TableRow key={member.id}>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-medium">
                              {member.user.name?.[0]?.toUpperCase() ||
                                member.user.email[0].toUpperCase()}
                            </div>
                            <div>
                              <div className="font-medium">
                                {member.user.name || member.user.email}
                              </div>
                              <div className="text-sm text-muted-foreground">
                                {member.user.email}
                              </div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className={roleColors[member.role]}>
                            {roleIcons[member.role]}
                            <span className="ml-1">{member.role_display}</span>
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {member.accepted_at
                            ? formatDistanceToNow(new Date(member.accepted_at), {
                                addSuffix: true,
                              })
                            : 'Pending'}
                        </TableCell>
                        <TableCell>
                          {canManageMembers && !member.is_owner && (
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon">
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem
                                  onClick={() => handleChangeRole(member, 'admin')}
                                  disabled={member.role === 'admin'}
                                >
                                  <Shield className="mr-2 h-4 w-4" />
                                  Make Admin
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  onClick={() => handleChangeRole(member, 'member')}
                                  disabled={member.role === 'member'}
                                >
                                  <Users className="mr-2 h-4 w-4" />
                                  Make Member
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  onClick={() => handleChangeRole(member, 'viewer')}
                                  disabled={member.role === 'viewer'}
                                >
                                  <Users className="mr-2 h-4 w-4" />
                                  Make Viewer
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                  className="text-destructive"
                                  onClick={() => setShowRemoveDialog(member)}
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Remove
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          )}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="invitations" className="mt-4">
          <Card>
            <CardContent className="pt-6">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Email</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Expires</TableHead>
                    <TableHead></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {invitations?.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-8">
                        No pending invitations
                      </TableCell>
                    </TableRow>
                  ) : (
                    invitations?.map((invitation) => (
                      <TableRow key={invitation.id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Mail className="h-4 w-4 text-muted-foreground" />
                            {invitation.email}
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className={roleColors[invitation.role]}>
                            {invitation.role_display}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={
                              invitation.status === 'pending'
                                ? 'secondary'
                                : invitation.status === 'accepted'
                                  ? 'default'
                                  : 'destructive'
                            }
                          >
                            {invitation.status_display}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          {invitation.is_expired ? (
                            <span className="text-destructive">Expired</span>
                          ) : (
                            <span className="flex items-center gap-1 text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              {formatDistanceToNow(new Date(invitation.expires_at), {
                                addSuffix: true,
                              })}
                            </span>
                          )}
                        </TableCell>
                        <TableCell>
                          {canManageMembers && invitation.status === 'pending' && (
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" size="icon">
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem
                                  onClick={() => handleResendInvitation(invitation)}
                                >
                                  <RefreshCw className="mr-2 h-4 w-4" />
                                  Resend
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  className="text-destructive"
                                  onClick={() => handleRevokeInvitation(invitation)}
                                >
                                  <X className="mr-2 h-4 w-4" />
                                  Revoke
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          )}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity" className="mt-4">
          <Card>
            <CardContent className="pt-6">
              <div className="space-y-4">
                {activities?.length === 0 ? (
                  <p className="text-center text-muted-foreground py-8">
                    No activity yet
                  </p>
                ) : (
                  activities?.map((activity) => (
                    <div
                      key={activity.id}
                      className="flex items-start gap-4 p-4 rounded-lg border"
                    >
                      <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center">
                        <Activity className="h-5 w-5 text-muted-foreground" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm">
                          <span className="font-medium">
                            {activity.user?.name || activity.user?.email || 'System'}
                          </span>{' '}
                          {activity.description}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {formatDistanceToNow(new Date(activity.created_at), {
                            addSuffix: true,
                          })}
                        </p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Invite Dialog */}
      <Dialog open={showInviteDialog} onOpenChange={setShowInviteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Invite Team Member</DialogTitle>
            <DialogDescription>
              Send an invitation to join your workspace.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                value={inviteForm.email}
                onChange={(e) => setInviteForm({ ...inviteForm, email: e.target.value })}
                placeholder="colleague@example.com"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="role">Role</Label>
              <Select
                value={inviteForm.role}
                onValueChange={(value) =>
                  setInviteForm({ ...inviteForm, role: value as WorkspaceMemberRole })
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="admin">
                    <div className="flex items-center gap-2">
                      <Shield className="h-4 w-4" />
                      Admin - Full access except billing
                    </div>
                  </SelectItem>
                  <SelectItem value="member">
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4" />
                      Member - Create and manage content
                    </div>
                  </SelectItem>
                  <SelectItem value="viewer">
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4" />
                      Viewer - View only access
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="message">Personal Message (optional)</Label>
              <Textarea
                id="message"
                value={inviteForm.message}
                onChange={(e) => setInviteForm({ ...inviteForm, message: e.target.value })}
                placeholder="Add a personal message to the invitation..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowInviteDialog(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleInvite}
              disabled={!inviteForm.email || inviteMutation.isPending}
            >
              {inviteMutation.isPending ? 'Sending...' : 'Send Invitation'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Remove Member Dialog */}
      <Dialog open={showRemoveDialog !== null} onOpenChange={() => setShowRemoveDialog(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Remove Team Member</DialogTitle>
            <DialogDescription>
              Are you sure you want to remove {showRemoveDialog?.user.email} from this workspace?
              They will lose access to all workspace resources.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRemoveDialog(null)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleRemoveMember}
              disabled={removeMemberMutation.isPending}
            >
              {removeMemberMutation.isPending ? 'Removing...' : 'Remove Member'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

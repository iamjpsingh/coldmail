from django.contrib import admin
from .models import Workspace, WorkspaceMember, WorkspaceInvitation, WorkspaceActivity


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'owner', 'member_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'owner__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['owner']

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'


@admin.register(WorkspaceMember)
class WorkspaceMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'workspace', 'role', 'accepted_at', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__email', 'workspace__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['workspace', 'user', 'invited_by']


@admin.register(WorkspaceInvitation)
class WorkspaceInvitationAdmin(admin.ModelAdmin):
    list_display = ['email', 'workspace', 'role', 'status', 'invited_by', 'expires_at', 'created_at']
    list_filter = ['status', 'role', 'created_at']
    search_fields = ['email', 'workspace__name', 'invited_by__email']
    readonly_fields = ['id', 'token', 'created_at', 'updated_at']
    raw_id_fields = ['workspace', 'invited_by']


@admin.register(WorkspaceActivity)
class WorkspaceActivityAdmin(admin.ModelAdmin):
    list_display = ['action', 'user', 'workspace', 'description', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['description', 'user__email', 'workspace__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    raw_id_fields = ['workspace', 'user', 'target_user']

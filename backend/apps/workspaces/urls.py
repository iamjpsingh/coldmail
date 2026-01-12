"""URL configuration for workspaces app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'workspaces', views.WorkspaceViewSet, basename='workspace')
router.register(r'workspace-members', views.WorkspaceMemberViewSet, basename='workspace-member')
router.register(r'workspace-invitations', views.WorkspaceInvitationViewSet, basename='workspace-invitation')
router.register(r'workspace-activity', views.WorkspaceActivityViewSet, basename='workspace-activity')

urlpatterns = [
    path('', include(router.urls)),
    # Public invitation acceptance endpoints
    path('invitations/<str:token>/', views.InvitationAcceptViewSet.as_view({
        'get': 'get_invitation',
    }), name='invitation-detail'),
    path('invitations/<str:token>/accept/', views.InvitationAcceptViewSet.as_view({
        'post': 'accept',
    }), name='invitation-accept'),
    path('invitations/<str:token>/decline/', views.InvitationAcceptViewSet.as_view({
        'post': 'decline',
    }), name='invitation-decline'),
]

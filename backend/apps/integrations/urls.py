"""URL configuration for integrations app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'integrations', views.IntegrationViewSet, basename='integration')
router.register(r'integration-logs', views.IntegrationLogViewSet, basename='integration-log')

urlpatterns = [
    path('', include(router.urls)),
    path('integrations/discord/create/', views.DiscordIntegrationViewSet.as_view({'post': 'create_integration'})),
]

"""URL configuration for webhooks app."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'api-keys', views.APIKeyViewSet, basename='api-key')
router.register(r'webhooks', views.WebhookViewSet, basename='webhook')
router.register(r'webhook-deliveries', views.WebhookDeliveryViewSet, basename='webhook-delivery')
router.register(r'webhook-events', views.WebhookEventLogViewSet, basename='webhook-event')

urlpatterns = [
    path('', include(router.urls)),
]

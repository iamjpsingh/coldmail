from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.tracking.views import (
    TrackingDomainViewSet,
    TrackingEventViewSet,
    BounceRecordViewSet,
    ComplaintRecordViewSet,
    SuppressionListViewSet,
    handle_bounce_webhook,
    handle_complaint_webhook,
)

# API Router
router = DefaultRouter()
router.register(r'domains', TrackingDomainViewSet, basename='tracking-domain')
router.register(r'events', TrackingEventViewSet, basename='tracking-event')
router.register(r'bounces', BounceRecordViewSet, basename='bounce-record')
router.register(r'complaints', ComplaintRecordViewSet, basename='complaint-record')
router.register(r'suppression', SuppressionListViewSet, basename='suppression-list')

urlpatterns = [
    path('', include(router.urls)),
    # Webhooks
    path('webhooks/bounce/', handle_bounce_webhook, name='webhook-bounce'),
    path('webhooks/complaint/', handle_complaint_webhook, name='webhook-complaint'),
]

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.tracking.views import (
    # Public endpoints
    track_open,
    track_click,
    unsubscribe,
    one_click_unsubscribe,
    website_track,
    website_script,
    # API ViewSets
    TrackingDomainViewSet,
    TrackingEventViewSet,
    BounceRecordViewSet,
    ComplaintRecordViewSet,
    SuppressionListViewSet,
    WebsiteTrackingScriptViewSet,
    WebsiteVisitorViewSet,
    VisitorSessionViewSet,
    # Webhooks
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
router.register(r'website/script', WebsiteTrackingScriptViewSet, basename='website-tracking-script')
router.register(r'website/visitors', WebsiteVisitorViewSet, basename='website-visitor')
router.register(r'website/sessions', VisitorSessionViewSet, basename='visitor-session')

# API URL patterns
api_urlpatterns = [
    path('', include(router.urls)),
    # Webhooks
    path('webhooks/bounce/', handle_bounce_webhook, name='webhook-bounce'),
    path('webhooks/complaint/', handle_complaint_webhook, name='webhook-complaint'),
]

# Public tracking URL patterns (no /api/ prefix)
tracking_urlpatterns = [
    # Open tracking pixel
    path('o/<str:token>.gif', track_open, name='track-open'),
    # Click tracking redirect
    path('c/<str:token>', track_click, name='track-click'),
    # Unsubscribe
    path('u/<str:token>', unsubscribe, name='unsubscribe'),
    path('u/<str:token>/one-click', one_click_unsubscribe, name='one-click-unsubscribe'),
    # Website tracking
    path('w/track', website_track, name='website-track'),
    path('w/script/<str:script_id>.js', website_script, name='website-script'),
]

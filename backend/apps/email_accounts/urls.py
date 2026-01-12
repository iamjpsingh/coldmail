from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    EmailAccountViewSet,
    GoogleOAuthInitView,
    GoogleOAuthCallbackView,
    MicrosoftOAuthInitView,
    MicrosoftOAuthCallbackView,
)

router = DefaultRouter()
router.register(r'', EmailAccountViewSet, basename='email-account')

urlpatterns = [
    # OAuth endpoints
    path('oauth/google/', GoogleOAuthInitView.as_view(), name='google-oauth-init'),
    path('oauth/google/callback/', GoogleOAuthCallbackView.as_view(), name='google-oauth-callback'),
    path('oauth/microsoft/', MicrosoftOAuthInitView.as_view(), name='microsoft-oauth-init'),
    path('oauth/microsoft/callback/', MicrosoftOAuthCallbackView.as_view(), name='microsoft-oauth-callback'),

    # ViewSet routes
    path('', include(router.urls)),
]

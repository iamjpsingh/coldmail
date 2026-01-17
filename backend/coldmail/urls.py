"""
URL configuration for ColdMail project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API v1
    path('api/v1/', include([
        # Authentication
        path('auth/', include('apps.users.urls')),  # register, login, logout, me
        path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

        # App URLs
        path('email-accounts/', include('apps.email_accounts.urls')),
        path('', include('apps.workspaces.urls')),  # workspaces, members, invitations
        path('contacts/', include('apps.contacts.urls')),
        path('campaigns/', include('apps.campaigns.urls')),
        path('', include('apps.sequences.urls')),  # sequences and enrollments
        path('tracking/', include('apps.tracking.api_urls')),
        path('reports/', include('apps.core.urls')),
        path('', include('apps.webhooks.urls')),  # api-keys and webhooks
        path('', include('apps.integrations.urls')),  # integrations
    ])),

    # Public tracking endpoints (no authentication required)
    path('t/', include('apps.tracking.public_urls')),

    # Health check
    path('health/', lambda request: __import__('django.http', fromlist=['JsonResponse']).JsonResponse({'status': 'ok'})),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass

"""API key authentication for Django REST Framework."""
from rest_framework import authentication, exceptions
from django.utils import timezone
from django.core.cache import cache

from .models import APIKey


class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    API Key authentication.

    Clients should authenticate by passing the API key in the Authorization header:
    Authorization: Bearer cm_xxxxxxxxxxxx

    Or via X-API-Key header:
    X-API-Key: cm_xxxxxxxxxxxx
    """

    keyword = 'Bearer'

    def authenticate(self, request):
        """Authenticate the request and return a tuple of (user, api_key) or None."""
        api_key = self.get_api_key(request)
        if not api_key:
            return None

        return self.authenticate_credentials(api_key, request)

    def get_api_key(self, request):
        """Extract API key from request headers."""
        # Try X-API-Key header first
        api_key = request.META.get('HTTP_X_API_KEY')
        if api_key:
            return api_key

        # Try Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2:
            return None

        if parts[0].lower() != self.keyword.lower():
            return None

        return parts[1]

    def authenticate_credentials(self, raw_key, request):
        """Validate the API key and return (user, api_key) or raise exception."""
        api_key = APIKey.get_by_key(raw_key)

        if not api_key:
            raise exceptions.AuthenticationFailed('Invalid API key.')

        if not api_key.is_valid():
            raise exceptions.AuthenticationFailed('API key is expired or disabled.')

        # Check IP restrictions
        client_ip = self.get_client_ip(request)
        if not api_key.is_ip_allowed(client_ip):
            raise exceptions.AuthenticationFailed('IP address not allowed for this API key.')

        # Check rate limiting
        if not self.check_rate_limit(api_key, client_ip):
            raise exceptions.Throttled(detail='Rate limit exceeded for this API key.')

        # Record usage (async to avoid slowing down requests)
        api_key.record_usage(client_ip)

        # Return the workspace's first admin user as the authenticated user
        # The api_key is passed as auth_info for permission checking
        user = api_key.workspace.members.filter(
            role='owner'
        ).first()

        if not user:
            user = api_key.workspace.members.filter(
                role='admin'
            ).first()

        if not user:
            user = api_key.workspace.members.first()

        if user:
            user = user.user

        return (user, api_key)

    def get_client_ip(self, request):
        """Get the client's IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def check_rate_limit(self, api_key, client_ip):
        """Check if the API key has exceeded rate limits."""
        now = timezone.now()

        # Per-minute rate limit
        minute_key = f"api_rate:{api_key.id}:minute:{now.strftime('%Y%m%d%H%M')}"
        minute_count = cache.get(minute_key, 0)
        if minute_count >= api_key.rate_limit_per_minute:
            return False

        # Per-day rate limit
        day_key = f"api_rate:{api_key.id}:day:{now.strftime('%Y%m%d')}"
        day_count = cache.get(day_key, 0)
        if day_count >= api_key.rate_limit_per_day:
            return False

        # Increment counters
        cache.set(minute_key, minute_count + 1, timeout=60)
        cache.set(day_key, day_count + 1, timeout=86400)

        return True

    def authenticate_header(self, request):
        """Return a string to be used as the WWW-Authenticate header."""
        return self.keyword


class APIKeyPermission:
    """Permission checking for API key access levels."""

    READ = 'read'
    WRITE = 'write'
    ADMIN = 'admin'

    # Permission hierarchy
    HIERARCHY = {
        'read': ['read'],
        'write': ['read', 'write'],
        'admin': ['read', 'write', 'admin'],
    }

    @classmethod
    def has_permission(cls, api_key, required_permission):
        """Check if an API key has the required permission level."""
        if not api_key:
            return False

        allowed = cls.HIERARCHY.get(api_key.permission, [])
        return required_permission in allowed


class RequiresAPIKeyPermission:
    """DRF Permission class for API key permission checking."""

    permission_required = 'read'  # Override in subclass

    def has_permission(self, request, view):
        """Check if the request has the required API key permission."""
        api_key = getattr(request, 'auth', None)

        # If not using API key auth, allow (session auth should use regular permissions)
        if not isinstance(api_key, APIKey):
            return True

        # Get required permission from view or class default
        required = getattr(view, 'api_key_permission', self.permission_required)

        return APIKeyPermission.has_permission(api_key, required)


class RequiresReadPermission(RequiresAPIKeyPermission):
    """Requires at least read permission."""
    permission_required = 'read'


class RequiresWritePermission(RequiresAPIKeyPermission):
    """Requires at least write permission."""
    permission_required = 'write'


class RequiresAdminPermission(RequiresAPIKeyPermission):
    """Requires admin permission."""
    permission_required = 'admin'

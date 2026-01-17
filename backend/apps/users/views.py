"""
User views for authentication and profile management.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    LoginSerializer,
    ProfileUpdateSerializer,
    PasswordChangeSerializer,
)
from .services import UserService


class RegisterView(APIView):
    """User registration endpoint."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=UserCreateSerializer,
        responses={
            201: OpenApiResponse(description='User created successfully'),
            400: OpenApiResponse(description='Validation error'),
        },
        tags=['Authentication'],
    )
    def post(self, request):
        """Register a new user account."""
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        tokens = UserService.get_tokens_for_user(user)
        UserService.update_last_login(user)

        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens,
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """User login endpoint."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(description='Login successful'),
            400: OpenApiResponse(description='Invalid credentials'),
        },
        tags=['Authentication'],
    )
    def post(self, request):
        """Authenticate user and return tokens."""
        serializer = LoginSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        tokens = UserService.get_tokens_for_user(user)
        UserService.update_last_login(user)

        user_data = UserService.get_user_with_workspaces(user)

        return Response({
            'user': user_data,
            'tokens': tokens,
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """User logout endpoint."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request={'type': 'object', 'properties': {'refresh': {'type': 'string'}}},
        responses={
            200: OpenApiResponse(description='Logout successful'),
            400: OpenApiResponse(description='Invalid token'),
        },
        tags=['Authentication'],
    )
    def post(self, request):
        """Logout user by blacklisting refresh token."""
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {'detail': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        success = UserService.blacklist_token(refresh_token)

        if success:
            return Response(
                {'detail': 'Successfully logged out.'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'detail': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class MeView(APIView):
    """Current user profile endpoint."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: OpenApiResponse(description='User profile data'),
        },
        tags=['Authentication'],
    )
    def get(self, request):
        """Get current user profile with workspaces."""
        user_data = UserService.get_user_with_workspaces(request.user)
        return Response(user_data, status=status.HTTP_200_OK)

    @extend_schema(
        request=ProfileUpdateSerializer,
        responses={
            200: OpenApiResponse(description='Profile updated'),
            400: OpenApiResponse(description='Validation error'),
        },
        tags=['Authentication'],
    )
    def patch(self, request):
        """Update current user profile."""
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        user_data = UserService.get_user_with_workspaces(request.user)
        return Response(user_data, status=status.HTTP_200_OK)


class PasswordChangeView(APIView):
    """Password change endpoint."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=PasswordChangeSerializer,
        responses={
            200: OpenApiResponse(description='Password changed'),
            400: OpenApiResponse(description='Validation error'),
        },
        tags=['Authentication'],
    )
    def post(self, request):
        """Change current user password."""
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {'detail': 'Password changed successfully.'},
            status=status.HTTP_200_OK
        )

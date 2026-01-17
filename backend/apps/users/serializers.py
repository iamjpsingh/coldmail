"""
User serializers for authentication and profile management.
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data."""

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'name',
            'avatar_url',
            'timezone',
            'is_verified',
            'created_at',
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'created_at']


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['email', 'name', 'password', 'password_confirm']

    def validate_email(self, value: str) -> str:
        """Validate email is unique."""
        email = value.lower().strip()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return email

    def validate_password(self, value: str) -> str:
        """Validate password strength."""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs: dict) -> dict:
        """Validate passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match.'
            })
        return attrs

    def create(self, validated_data: dict) -> User:
        """Create a new user with a default workspace."""
        from django.utils.text import slugify
        from apps.workspaces.models import Workspace, WorkspaceMember

        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)

        # Create a default workspace for the new user
        workspace_name = f"{user.name}'s Workspace" if user.name else "My Workspace"
        base_slug = slugify(workspace_name)

        # Ensure unique slug
        slug = base_slug
        counter = 1
        while Workspace.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        workspace = Workspace.objects.create(
            name=workspace_name,
            slug=slug,
            owner=user,
            description="Your default workspace"
        )

        # Add user as owner member
        WorkspaceMember.objects.create(
            workspace=workspace,
            user=user,
            role=WorkspaceMember.Role.OWNER,
        )

        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    email = serializers.EmailField(
        error_messages={
            'required': 'Email address is required.',
            'blank': 'Email address is required.',
            'invalid': 'Please enter a valid email address.',
        }
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        error_messages={
            'required': 'Password is required.',
            'blank': 'Password is required.',
        }
    )

    def validate(self, attrs: dict) -> dict:
        """Validate credentials and authenticate user."""
        email = attrs.get('email', '').lower().strip()
        password = attrs.get('password', '')

        if not email:
            raise serializers.ValidationError({
                'email': ['Email address is required.']
            })

        if not password:
            raise serializers.ValidationError({
                'password': ['Password is required.']
            })

        user = authenticate(
            request=self.context.get('request'),
            email=email,
            password=password
        )

        if not user:
            # Check if user exists to provide better error message
            # Note: For security, we still use a generic message to prevent user enumeration
            raise serializers.ValidationError({
                'non_field_errors': ['Invalid email or password. Please check your credentials and try again.']
            })

        if not user.is_active:
            raise serializers.ValidationError({
                'non_field_errors': ['This account has been deactivated. Please contact support.']
            })

        attrs['user'] = user
        return attrs


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = ['name', 'avatar_url', 'timezone']

    def validate_timezone(self, value: str) -> str:
        """Validate timezone is valid."""
        import pytz
        if value and value not in pytz.all_timezones:
            raise serializers.ValidationError('Invalid timezone.')
        return value


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for changing password."""

    current_password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )

    def validate_current_password(self, value: str) -> str:
        """Validate current password is correct."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def validate_new_password(self, value: str) -> str:
        """Validate new password strength."""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs: dict) -> dict:
        """Validate new passwords match."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Passwords do not match.'
            })
        return attrs

    def save(self) -> User:
        """Update user password."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

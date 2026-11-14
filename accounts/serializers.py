from rest_framework import serializers
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model. Username is read-only after registration."""

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'username', 'date_joined']


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Requires username, password, and password confirmation.
    First name and last name are optional.
    """
    password = serializers.CharField(
        write_only=True,
        min_length=6,
        style={'input_type': 'password'},
        help_text='Password must be at least 6 characters long'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        min_length=6,
        style={'input_type': 'password'},
        help_text='Must match the password field'
    )

    class Meta:
        model = User
        fields = ['username', 'password', 'password_confirm', 'first_name', 'last_name']
        extra_kwargs = {
            'username': {'help_text': 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'},
            'first_name': {'help_text': 'Optional. First name of the user.', 'required': False},
            'last_name': {'help_text': 'Optional. Last name of the user.', 'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login with username and password.

    Returns JWT access and refresh tokens on successful authentication.
    """
    username = serializers.CharField(help_text='Your username')
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Your password'
    )

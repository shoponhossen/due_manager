from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from .serializers import RegisterSerializer, LoginSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """Register a new user and receive JWT tokens."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Register a new user",
        description="Create a new user account with username and password. Returns user data and JWT tokens.",
        tags=["Authentication"],
        responses={
            201: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'user': {'type': 'object'},
                        'access': {'type': 'string', 'description': 'JWT access token (valid for 1 hour)'},
                        'refresh': {'type': 'string', 'description': 'JWT refresh token (valid for 7 days)'},
                    }
                },
                description="User successfully registered",
                examples=[
                    OpenApiExample(
                        'Success Response',
                        value={
                            'user': {
                                'id': 1,
                                'username': 'johndoe',
                                'first_name': 'John',
                                'last_name': 'Doe',
                                'date_joined': '2026-11-13T09:35:00Z'
                            },
                            'access': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
                            'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGc...'
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid input data"),
        },
        examples=[
            OpenApiExample(
                'Registration Request',
                value={
                    'username': 'johndoe',
                    'password': 'securepass123',
                    'password_confirm': 'securepass123',
                    'first_name': 'John',
                    'last_name': 'Doe'
                },
                request_only=True,
            )
        ]
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Login with username and password to receive JWT tokens."""
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    @extend_schema(
        summary="Login with username and password",
        description="Authenticate with username and password. Returns user data and JWT tokens.",
        tags=["Authentication"],
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                response={
                    'type': 'object',
                    'properties': {
                        'user': {'type': 'object'},
                        'access': {'type': 'string', 'description': 'JWT access token (valid for 1 hour)'},
                        'refresh': {'type': 'string', 'description': 'JWT refresh token (valid for 7 days)'},
                    }
                },
                description="Login successful",
                examples=[
                    OpenApiExample(
                        'Success Response',
                        value={
                            'user': {
                                'id': 1,
                                'username': 'johndoe',
                                'first_name': 'John',
                                'last_name': 'Doe',
                                'date_joined': '2026-11-13T09:35:00Z'
                            },
                            'access': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
                            'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGc...'
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Missing credentials"),
            401: OpenApiResponse(
                description="Invalid credentials",
                examples=[
                    OpenApiExample(
                        'Invalid Credentials',
                        value={'error': 'Invalid username or password.'}
                    )
                ]
            ),
        },
        examples=[
            OpenApiExample(
                'Login Request',
                value={
                    'username': 'johndoe',
                    'password': 'securepass123'
                },
                request_only=True,
            )
        ]
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {'error': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        })


class LogoutView(APIView):
    """Logout by blacklisting the refresh token."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Logout and blacklist refresh token",
        description="Logout the current user by blacklisting their refresh token. The token cannot be used again after this.",
        tags=["Authentication"],
        request={
            'type': 'object',
            'properties': {
                'refresh': {'type': 'string', 'description': 'The refresh token to blacklist'}
            },
            'required': ['refresh']
        },
        responses={
            205: OpenApiResponse(
                description="Successfully logged out",
                examples=[
                    OpenApiExample(
                        'Success Response',
                        value={'message': 'Successfully logged out.'}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Invalid token",
                examples=[
                    OpenApiExample(
                        'Error Response',
                        value={'error': 'Invalid token.'}
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required"),
        },
        examples=[
            OpenApiExample(
                'Logout Request',
                value={'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGc...'},
                request_only=True,
            )
        ]
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Successfully logged out.'}, status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({'error': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get or update the authenticated user's profile."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get user profile",
        description="Retrieve the authenticated user's profile information. Username cannot be changed after registration.",
        tags=["User Profile"],
        responses={
            200: OpenApiResponse(
                response=UserSerializer,
                description="User profile retrieved successfully",
                examples=[
                    OpenApiExample(
                        'Profile Response',
                        value={
                            'id': 1,
                            'username': 'johndoe',
                            'first_name': 'John',
                            'last_name': 'Doe',
                            'date_joined': '2026-11-13T09:35:00Z'
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required"),
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Update user profile",
        description="Update the authenticated user's profile. Only first_name and last_name can be updated. Username is read-only.",
        tags=["User Profile"],
        request=UserSerializer,
        responses={
            200: OpenApiResponse(
                response=UserSerializer,
                description="Profile updated successfully",
                examples=[
                    OpenApiExample(
                        'Updated Profile',
                        value={
                            'id': 1,
                            'username': 'johndoe',
                            'first_name': 'Jane',
                            'last_name': 'Smith',
                            'date_joined': '2026-11-13T09:35:00Z'
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid input data"),
            401: OpenApiResponse(description="Authentication required"),
        },
        examples=[
            OpenApiExample(
                'Update Request',
                value={
                    'first_name': 'Jane',
                    'last_name': 'Smith'
                },
                request_only=True,
            )
        ]
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @extend_schema(
        summary="Replace user profile",
        description="Replace the authenticated user's profile. Only first_name and last_name can be updated. Username is read-only.",
        tags=["User Profile"],
        request=UserSerializer,
        responses={
            200: OpenApiResponse(response=UserSerializer, description="Profile replaced successfully"),
            400: OpenApiResponse(description="Invalid input data"),
            401: OpenApiResponse(description="Authentication required"),
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    def get_object(self):
        return self.request.user

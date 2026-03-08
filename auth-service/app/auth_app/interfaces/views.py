import logging

import requests
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from auth_app.infrastructure.serializers import LoginSerializer, TokenVerifySerializer

logger = logging.getLogger(__name__)

ROLE_SERVICE_MAP = {
    'CUSTOMER': lambda: settings.CUSTOMER_SERVICE_URL,
    'STAFF': lambda: settings.STAFF_SERVICE_URL,
    'MANAGER': lambda: settings.MANAGER_SERVICE_URL,
}

ROLE_LOGIN_PATH = {
    'CUSTOMER': '/api/customers/login/',
    'STAFF': '/api/staff/login/',
    'MANAGER': '/api/managers/login/',
}


@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'service': 'auth-service', 'version': '2.0.0'})


class LoginView(APIView):
    """
    POST /auth/login/
    Validates credentials against the appropriate downstream service,
    then issues JWT access + refresh tokens.
    """

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        role = serializer.validated_data['role']

        service_url_fn = ROLE_SERVICE_MAP.get(role)
        login_path = ROLE_LOGIN_PATH.get(role)
        if not service_url_fn or not login_path:
            return Response({'detail': 'Unsupported role.'}, status=status.HTTP_400_BAD_REQUEST)

        service_url = service_url_fn()
        try:
            resp = requests.post(
                f"{service_url.rstrip('/')}{login_path}",
                json={'email': email, 'password': password},
                timeout=5,
            )
        except requests.RequestException as exc:
            logger.error('Downstream login error for role %s: %s', role, exc)
            return Response({'detail': 'Authentication service unavailable.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if resp.status_code != 200:
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        user_data = resp.json()
        user_id = user_data.get('id') or user_data.get('customer_id') or user_data.get('staff_id') or user_data.get('manager_id')

        refresh = RefreshToken()
        refresh['user_id'] = user_id
        refresh['email'] = email
        refresh['role'] = role

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user_id': user_id,
            'email': email,
            'role': role,
        }, status=status.HTTP_200_OK)


class TokenVerifyView(APIView):
    """
    POST /auth/token/verify/
    Validates a JWT access token and returns its claims.
    """

    def post(self, request):
        serializer = TokenVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token_str = serializer.validated_data['token']
        from rest_framework_simplejwt.tokens import AccessToken
        try:
            token = AccessToken(token_str)
        except (TokenError, InvalidToken) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({
            'valid': True,
            'user_id': token.get('user_id'),
            'email': token.get('email'),
            'role': token.get('role'),
        }, status=status.HTTP_200_OK)


class TokenRefreshView(APIView):
    """
    POST /auth/token/refresh/
    Issues a new access token from a valid refresh token.
    """

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            access = refresh.access_token
        except (TokenError, InvalidToken) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        return Response({'access': str(access)}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    POST /auth/logout/
    Blacklists the provided refresh token.
    """

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'detail': 'refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except (TokenError, InvalidToken) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            logger.error('Logout blacklist error: %s', exc)
            return Response({'detail': 'Could not blacklist token.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)

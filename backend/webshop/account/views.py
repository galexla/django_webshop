from django.contrib.auth import authenticate, login, logout
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Profile
from .serializers import (
    AvatarUpdateSerializer,
    ProfileSerializer,
    SetPasswordSerializer,
    SignInSerializer,
    SignUpSerializer,
)


class SignInView(APIView):
    """View for signing in user."""

    def post(self, request: Request) -> Response:
        """
        Sign in user.

        :param request: Request
        :type request: Request
        :return: Response
        :rtype: Response
        """
        data = request.data
        serializer = SignInSerializer(data=data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            user = authenticate(
                username=validated_data.get('username'),
                password=validated_data.get('password'),
            )

            if user and user.is_active:
                login(self.request, user)
                return Response()

        return Response(
            serializer.errors, status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class SignOutView(APIView):
    """View for signing out user."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """
        Sign out user.

        :param request: Request
        :type request: Request
        :return: Response
        :rtype: Response
        """
        logout(request)
        response = Response()
        response.delete_cookie('basket_id')
        return response


class SignUpView(APIView):
    """View for signing up user."""

    def post(self, request: Request) -> Response:
        """
        Sign up user.

        :param request: Request
        :type request: Request
        :return: Response
        :rtype: Response
        """
        data = request.data
        serializer = SignUpSerializer(data=data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            serializer.save()

            user = authenticate(
                username=validated_data.get('username'),
                password=validated_data.get('password'),
            )
            if user and user.is_active:
                login(self.request, user)

            return Response()

        return Response(
            serializer.errors, status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class SetPasswordView(APIView):
    """View for setting new password."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Set new password.

        :param request: Request
        :type request: Request
        :return: Response
        :rtype: Response
        """
        serializer = SetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user
            if not user.check_password(
                serializer.validated_data['currentPassword']
            ):
                return Response(
                    {'currentPassword': ['Wrong password.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(serializer.validated_data['newPassword'])
            user.save()

            return Response()

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """View for getting and updating user profile."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """
        Get user profile.

        :param request: Request
        :type request: Request
        :return: Response
        :rtype: Response
        """
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        """
        Update user profile.

        :param request: Request
        :type request: Request
        :return: Response
        :rtype: Response
        """
        serializer = ProfileSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AvatarUpdateView(APIView):
    """View for updating user avatar."""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        """
        Update user avatar.

        :param request: Request
        :type request: Request
        :return: Response
        :rtype: Response
        """
        profile = Profile.objects.get(user=request.user)
        serializer = AvatarUpdateSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response()

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

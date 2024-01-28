import json

from django.contrib.auth import authenticate, login, logout
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Profile
from .serializers import (AvatarUpdateSerializer, ProfileSerializer,
                          SetPasswordSerializer, SignInSerializer,
                          SignUpSerializer)


class SignInView(APIView):
    def post(self, request: Request) -> Response:
        data = json.loads(request.body)
        serializer = SignInSerializer(data=data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            user = authenticate(
                username=validated_data.get('username'),
                password=validated_data.get('password'),
            )

            if user and user.is_active:
                login(self.request, user)
                return Response(None, status.HTTP_200_OK)

        return Response(
            serializer.errors, status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class SignOutView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        logout(request)
        return Response(None, status.HTTP_200_OK)


class SignUpView(APIView):
    def post(self, request: Request) -> Response:
        data = json.loads(list(request.data.keys())[0])
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

            return Response(None, status.HTTP_200_OK)

        return Response(
            serializer.errors, status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class SetPasswordView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
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

            return Response(None, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    def post(self, request: Request) -> Response:
        serializer = ProfileSerializer(request.user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AvatarUpdateView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        profile = Profile.objects.get(user=request.user)
        serializer = AvatarUpdateSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(None, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

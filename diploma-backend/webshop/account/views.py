import json

from django.contrib.auth import login, logout
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
    UserLoginSerializer,
    UserRegistrationSerializer,
)


class LoginView(APIView):
    def post(self, request: Request) -> Response:
        data = json.loads(request.body)
        serializer = UserLoginSerializer(data=data)
        if serializer.is_valid():
            user = serializer.validated_data
            login(self.request, user)

            return Response(None, status.HTTP_200_OK)

        return Response(
            serializer.errors, status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class LogoutView(APIView):
    def post(self, request: Request) -> Response:
        logout(request)
        return Response(None, status.HTTP_200_OK)


class RegistrationView(APIView):
    def post(self, request: Request) -> Response:
        data = json.loads(list(request.data.keys())[0])
        serializer = UserRegistrationSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            Profile.objects.create(user=user)
            login(self.request, user)

            return Response(None, status.HTTP_200_OK)

        return Response(
            serializer.errors, status.HTTP_500_INTERNAL_SERVER_ERROR
        )


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

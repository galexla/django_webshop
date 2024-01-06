import json

from django.contrib.auth import login
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserLoginSerializer


class LoginView(APIView):
    def post(self, request: Request) -> Response:
        data = json.loads(request.body)
        serializer = UserLoginSerializer(data=data)
        if serializer.is_valid():
            user = serializer.validated_data
            login(self.request, user)
            return Response(None, status.HTTP_200_OK)
        return Response(None, status.HTTP_500_INTERNAL_SERVER_ERROR)

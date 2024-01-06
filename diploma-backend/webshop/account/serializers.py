from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.serializers import CharField, ModelSerializer, Serializer

# class UserRegistrationSerializer(ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['name', 'username', 'password']
#         extra_kwargs = {
#             'password': {'write_only': True},
#         }

#     def validate(self, attrs):
#         validated_data = super().validate(attrs)
#         if validated_data:
#             user = authenticate(
#                 username=attrs.get('username'),
#                 password=attrs.get('password'),
#             )
#             if user:
#                 return user
#             raise serializers.ValidationError(
#                 'Unable to log in with provided credentials.'
#             )


class UserLoginSerializer(Serializer):
    username = CharField()
    password = CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs.get('username'),
            password=attrs.get('password'),
        )
        if user and user.is_active:
            return user
        raise serializers.ValidationError(
            'Unable to log in with provided credentials.'
        )

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import CharField, ModelSerializer, Serializer


class UserRegistrationSerializer(ModelSerializer):
    first_name_validators = User._meta.get_field('first_name').validators
    name = CharField(validators=first_name_validators)

    class Meta:
        model = User
        fields = ['name', 'username', 'password']
        extra_kwargs = {
            'name': {'write_only': True},
            'password': {'write_only': True},
        }

    def validate(self, attrs):
        attrs['first_name'] = attrs['name']

        user = User(
            first_name=attrs['first_name'],
            username=attrs['username'],
        )

        try:
            validate_password(attrs['password'], user)
        except ValidationError as exc:
            raise serializers.ValidationError(exc.messages)

        return attrs

    def create(self, validated_data):
        user = User(
            first_name=validated_data['first_name'],
            username=validated_data['username'],
        )
        user.set_password(validated_data['password'])
        user.save()

        authenticated_user = authenticate(
            username=validated_data['username'],
            password=validated_data['password'],
        )
        if authenticated_user and authenticated_user.is_active:
            return authenticated_user

        raise serializers.ValidationError(
            'Unable to log in with provided credentials.'
        )


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

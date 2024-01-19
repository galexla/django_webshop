from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import CharField, ModelSerializer, Serializer
from rest_framework.validators import UniqueValidator

from .models import Profile

User = get_user_model()


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

    @transaction.atomic
    def create(self, validated_data):
        user = User(
            first_name=validated_data['first_name'],
            username=validated_data['username'],
        )
        user.set_password(validated_data['password'])
        user.save()

        profile = Profile(user=user)
        profile.save()

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
    username = CharField(
        validators=User._meta.get_field('username').validators
    )
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


class ProfileSerializer(Serializer):
    fullName = serializers.CharField(
        required=True,
        allow_blank=False,
        validators=User._meta.get_field('first_name').validators,
    )
    email = serializers.EmailField(
        required=True,
        allow_blank=False,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    phone = serializers.CharField(
        required=True,
        allow_blank=False,
        validators=Profile._meta.get_field('phone').validators
        + [UniqueValidator(queryset=Profile.objects.all())],
    )

    @transaction.atomic
    def update(self, user: User, validated_data):
        if not isinstance(user, User):
            raise TypeError('user must be of a type User')

        user.first_name = validated_data['fullName']
        user.email = validated_data['email']
        user.save()

        user.profile.phone = validated_data['phone']
        user.profile.save()

        return user

    def to_representation(self, user: User):
        if not isinstance(user, User):
            raise TypeError('user must be of a type User')

        profile = user.profile

        data = {
            'fullName': user.get_full_name(),
            'email': user.email,
            'phone': profile.phone,
            'avatar': {
                'src': profile.avatar.url if profile.avatar else None,
                'alt': profile.avatar_alt,
            },
        }

        return data


class AvatarUpdateSerializer(ModelSerializer):
    class Meta:
        model = Profile
        fields = ['avatar']
        extra_kwargs = {'avatar': {'write_only': True}}

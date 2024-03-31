from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator
from django.db import transaction
from django.forms import ValidationError
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Profile, User


class SignUpSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=150, write_only=True)

    class Meta:
        model = User
        fields = ['name', 'username', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, attrs):
        attrs['first_name'] = attrs.pop('name')

        user = User(username=attrs['username'])
        validate_password(attrs['password'], user)

        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            first_name=validated_data['first_name'],
            username=validated_data['username'],
        )
        user.set_password(validated_data['password'])
        user.save()

        return user


class SignInSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        validators=[
            UnicodeUsernameValidator(),
        ],
    )
    password = serializers.CharField(max_length=128, write_only=True)


class SetPasswordSerializer(serializers.Serializer):
    currentPassword = serializers.CharField(max_length=128)
    newPassword = serializers.CharField(max_length=128)

    def validate_newPassword(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs['currentPassword'] == attrs['newPassword']:
            raise ValidationError('New password must be different')
        return super().validate(attrs)


class ProfileSerializer(serializers.Serializer):
    fullName = serializers.CharField(
        required=True, allow_blank=False, max_length=150
    )
    email = serializers.EmailField(
        required=True,
        allow_blank=False,
        validators=[
            UniqueValidator(queryset=User.objects.all()),
        ],
    )
    phone = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=32,
        validators=[
            UniqueValidator(queryset=Profile.objects.all()),
            RegexValidator(
                r'^\+\d{5,}(\#\d+)?$',
                message='Phone must be in format: +123456789[#123].',
            ),
        ],
    )

    @transaction.atomic
    def update(self, user: User, validated_data):
        if not isinstance(user, User):
            raise TypeError('user must be of type User')

        user.first_name = validated_data['fullName']
        user.email = validated_data['email']
        user.save()

        user.profile.phone = validated_data['phone']
        user.profile.save()

        return user

    def to_representation(self, user: User):
        if not isinstance(user, User):
            raise TypeError('user must be of type User')

        profile = user.profile

        data = {
            'fullName': user.get_full_name(),
            'email': user.email,
            'phone': profile.phone,
            'avatar': {
                'src': profile.avatar.url if profile.avatar else '',
                'alt': profile.avatar_alt,
            },
        }

        return data


class AvatarUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['avatar']
        extra_kwargs = {'avatar': {'write_only': True}}

    MAX_FILE_SIZE = 2 * 1024 * 1024

    def validate_avatar(self, value):
        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError(
                f'Maximum file size is {self.MAX_FILE_SIZE} bytes'
            )
        return value

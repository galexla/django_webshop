from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.files import File
from django.core.validators import RegexValidator
from django.db import transaction
from rest_framework import serializers
from rest_framework.serializers import ValidationError
from rest_framework.validators import UniqueValidator

from .models import Profile, User


class SignUpSerializer(serializers.ModelSerializer):
    """Serializer for signing up user."""

    name = serializers.CharField(max_length=150, write_only=True)

    class Meta:
        model = User
        fields = ['name', 'username', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, attrs: dict) -> dict:
        """
        Validate data.

        :param attrs: Data
        :type attrs: dict
        :raises ValidationError: If password is invalid
        :return: Data
        :rtype: dict
        """
        attrs['first_name'] = attrs.pop('name')

        user = User(username=attrs['username'])
        validate_password(attrs['password'], user)

        return attrs

    def create(self, validated_data: dict) -> User:
        """
        Create user.

        :param validated_data: Validated data
        :type validated_data: dict
        :return: User
        :rtype: User
        """
        user = User.objects.create(
            first_name=validated_data['first_name'],
            username=validated_data['username'],
        )
        user.set_password(validated_data['password'])
        user.save()

        return user


class SignInSerializer(serializers.Serializer):
    """Serializer for signing in user."""

    username = serializers.CharField(
        max_length=150,
        validators=[
            UnicodeUsernameValidator(),
        ],
    )
    password = serializers.CharField(max_length=128, write_only=True)


class SetPasswordSerializer(serializers.Serializer):
    """Serializer for changing user password."""

    currentPassword = serializers.CharField(max_length=128)
    newPassword = serializers.CharField(max_length=128)

    def validate_newPassword(self, value: str) -> str:
        """
        Validate new password.

        :param value: New password
        :type value: str
        :raises ValidationError: If password is invalid
        :return: New password
        """
        validate_password(value)
        return value

    def validate(self, attrs: dict) -> dict:
        """
        Validate data.

        :param attrs: Data
        :type attrs: dict
        :raises ValidationError: If new password is the same as the current
            password
        :return: Data
        """
        if attrs['currentPassword'] == attrs['newPassword']:
            raise ValidationError('New password must be different')
        return super().validate(attrs)


class ProfileSerializer(serializers.Serializer):
    """Serializer for updating user profile."""

    fullName = serializers.CharField(allow_blank=False, max_length=150)
    email = serializers.EmailField(
        allow_blank=False,
        validators=[
            UniqueValidator(queryset=User.objects.all()),
        ],
    )
    phone = serializers.CharField(
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
    def update(self, user: User, validated_data: dict) -> User:
        """
        Update user profile.

        :param user: User
        :type user: User
        :param validated_data: Validated data
        :type validated_data: dict
        :return: User
        :rtype: User
        """
        if not isinstance(user, User):
            raise TypeError('user must be of type User')

        user.first_name = validated_data['fullName']
        user.email = validated_data['email']
        user.save()

        user.profile.phone = validated_data['phone']
        user.profile.save()

        return user

    def to_representation(self, user: User) -> dict:
        """
        Serialize user profile.

        :param user: User
        :type user: User
        :raises TypeError: If user is not of type User
        :return: User profile data
        :rtype: dict
        """
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
    """Serializer for updating user avatar."""

    class Meta:
        model = Profile
        fields = ['avatar']
        extra_kwargs = {'avatar': {'write_only': True}}

    MAX_FILE_SIZE = 2 * 1024 * 1024

    def validate_avatar(self, value: File) -> File:
        """
        Validate avatar file size.

        :param value: File
        :type value: File
        :raises ValidationError: If file size is greater than MAX_FILE_SIZE
        :return: File
        :rtype: File
        """
        if value.size > self.MAX_FILE_SIZE:
            raise ValidationError(
                f'Maximum file size is {self.MAX_FILE_SIZE} bytes'
            )
        return value

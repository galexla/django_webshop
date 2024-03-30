from typing import Any

from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _


def get_avatar_upload_path(instance: 'Profile', filename: str) -> str:
    return f'users/user{instance.user.pk}/avatar/{filename}'


class Profile(models.Model):
    user = models.OneToOneField(
        'User', on_delete=models.CASCADE, related_name='profile'
    )
    # to make phone unique & allow null: null=True, blank=False, unique=True
    phone = models.CharField(
        verbose_name=_('phone number'),
        null=True,
        unique=True,
        max_length=32,
        validators=[
            RegexValidator(
                r'^\+\d{5,}(\#\d+)?$',
                message='Phone must be in format: +123456789[#123].',
            )
        ],
        error_messages={
            'unique': _('Phone number belongs to another user.'),
        },
    )
    avatar = models.ImageField(
        verbose_name=_('avatar'),
        null=True,
        blank=True,
        upload_to=get_avatar_upload_path,
    )
    avatar_alt = models.CharField(
        verbose_name=_('avatar description'), blank=True, max_length=100
    )


class CustomUserManager(UserManager):
    @transaction.atomic
    def create(self, **kwargs: Any) -> Any:
        user = super().create(**kwargs)
        Profile.objects.create(user=user)
        return user

    @transaction.atomic
    def create_superuser(
        self,
        username: str,
        email: str | None,
        password: str | None,
        **extra_fields: Any,
    ) -> Any:
        user = super().create_superuser(
            username, email, password, **extra_fields
        )
        Profile.objects.create(user=user)
        return user


class User(AbstractUser):
    objects = CustomUserManager()
    # to make email unique & allow null: null=True, blank=False, unique=True
    email = models.EmailField(
        verbose_name=_('email address'),
        null=True,
        unique=True,
        error_messages={
            'unique': _('Email address belongs to another user.'),
        },
    )

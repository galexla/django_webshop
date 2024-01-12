from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

ALLOWED_AVATAR_EXTENSIONS = 'png,jpg,gif'.split(',')


class User(AbstractUser):
    email = models.EmailField(
        verbose_name=_('email address'),
        blank=True,
        unique=True,
        error_messages={
            'unique': _('Email address belongs to another user.'),
        },
    )


def get_avatar_upload_path(instance: 'Profile', filename: str):
    pk = instance.user.pk
    return f'users/user{pk}/avatar/{filename}'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(
        verbose_name=_('phone number'),
        blank=True,
        unique=True,
        max_length=32,
        validators=[
            RegexValidator(
                r'^\+\d{5,}(\#\d+)?$',
                message='Phone must be in format: +123456789[#123].',
            )
        ],
    )
    avatar = models.ImageField(
        verbose_name=_('avatar'),
        null=True,
        blank=True,
        max_length=2 * 1024 * 1024,
        validators=[
            FileExtensionValidator(
                allowed_extensions=ALLOWED_AVATAR_EXTENSIONS,
            ),
        ],
        upload_to=get_avatar_upload_path,
    )
    avatar_alt = models.CharField(
        verbose_name=_('avatar description'), blank=True, max_length=100
    )

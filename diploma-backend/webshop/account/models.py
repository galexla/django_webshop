from typing import Any

from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import (
    FileExtensionValidator,
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

ALLOWED_AVATAR_EXTENSIONS = 'png,jpg,gif'.split(',')


def get_avatar_upload_path(instance: 'Profile', filename: str) -> str:
    return f'users/user{instance.user.pk}/avatar/{filename}'


class Profile(models.Model):
    """
    Arguments null=True, blank=False, unique=True for phone field are
    neccessary because a user is created with an empty phone, but users cannot
    have same phone, blank included.
    """

    user = models.OneToOneField(
        'User',
        on_delete=models.CASCADE,
    )
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
        max_length=2 * 1024 * 1024,
        validators=[
            FileExtensionValidator(
                allowed_extensions=ALLOWED_AVATAR_EXTENSIONS,
            ),
        ],
        upload_to=get_avatar_upload_path,
    )
    avatar_alt = models.CharField(
        verbose_name=_('avatar description'),
        blank=True,
        max_length=100,
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
    """
    Arguments null=True, blank=False, unique=True for email field are
    neccessary because a user is created with an empty email, but users cannot
    have same email, blank included.
    """

    objects = CustomUserManager()
    email = models.EmailField(
        verbose_name=_('email address'),
        null=True,
        unique=True,
        error_messages={
            'unique': _('Email address belongs to another user.'),
        },
    )


class Tag(models.Model):
    name = models.CharField(
        max_length=100,
    )


class Specification(models.Model):
    name = models.CharField(
        max_length=200,
    )
    value = models.CharField(
        max_length=200,
    )


def category_image_upload_path(instance: 'Category', filename: str) -> str:
    return f'categories/images/{filename}'


class Category(models.Model):
    title = models.CharField(
        max_length=200,
    )
    parent = models.ForeignKey(
        'Category',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='subcategories',
    )
    image = models.ImageField(
        null=True,
        blank=True,
        upload_to=category_image_upload_path,
    )
    image_alt = models.CharField(
        max_length=200,
    )


class Product(models.Model):
    title = models.CharField(
        max_length=200,
    )
    price = models.DecimalField(
        default=0,
        max_digits=8,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
        ],
    )
    category = models.ForeignKey(
        Category,
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        related_name='products',
    )
    count = models.PositiveIntegerField(
        default=0,
    )
    date = models.DateTimeField(
        auto_now_add=True,
    )
    description = models.TextField(
        blank=True,
    )
    full_description = models.TextField(
        blank=True,
    )
    free_delivery = models.BooleanField(
        default=True,
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='products',
    )
    specifications = models.ManyToManyField(
        Specification,
        related_name='products',
    )
    rating = models.DecimalField(
        blank=True,
        max_digits=2,
        decimal_places=1,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
    )
    archived = models.BooleanField(
        default=False,
    )


def product_image_upload_path(instance: 'ProductImage', filename: str) -> str:
    return 'products/product{pk}/images/{filename}'.format(
        pk=instance.product.pk,
        filename=filename,
    )


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
    )
    image = models.ImageField(
        null=True,
        blank=True,
        upload_to=product_image_upload_path,
    )
    image_alt = models.CharField(
        max_length=200,
    )


class Review(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    author = models.CharField(
        max_length=200,
    )
    email = models.EmailField()
    text = models.TextField()
    rate = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
    )
    date = models.DateTimeField(
        auto_now_add=True,
    )

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


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
        blank=True,
    )

    def save(self, *args, **kwargs):
        if self == self.parent:
            raise ValidationError('Category cannot be parent of itself')
        super().save(*args, **kwargs)


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
        blank=True,
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

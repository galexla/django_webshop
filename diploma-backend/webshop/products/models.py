import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(
        max_length=100,
    )

    def __str__(self) -> str:
        return self.name


class Specification(models.Model):
    name = models.CharField(
        max_length=200,
    )
    value = models.CharField(
        max_length=200,
    )

    def __str__(self) -> str:
        return f'{self.name}: {self.value}'


def category_image_upload_path(instance: 'Category', filename: str) -> str:
    return f'categories/category{instance.pk}/image/{filename}'


class Category(models.Model):
    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        indexes = [
            models.Index(fields=['parent'], name='idx_category_parent'),
        ]

    title = models.CharField(
        max_length=200,
    )
    parent = models.ForeignKey(
        'Category',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='subcategories',
    )
    image = models.ImageField(
        blank=True,
        null=True,
        upload_to=category_image_upload_path,
    )
    image_alt = models.CharField(
        max_length=200,
        blank=True,
    )
    archived = models.BooleanField(
        default=False,
    )

    def clean(self) -> None:
        if self.parent is not None:
            if self == self.parent:
                raise ValidationError(
                    _('Category cannot be a parent of itself')
                )
            if self.parent.parent is not None:
                raise ValidationError(
                    _('Category can only be subcategory of top-level category')
                )
            if self.pk is not None and len(self.subcategories.all()) > 0:
                raise ValidationError(
                    _('Subcategory cannot have subcategories')
                )

        return super().clean()

    def __str__(self) -> str:
        return self.title


class Product(models.Model):
    class Meta:
        indexes = [
            models.Index(Lower('title'), name='idx_product_title_lower'),
            models.Index(fields=['price'], name='idx_product_price'),
            models.Index(fields=['category'], name='idx_product_category'),
            models.Index(fields=['count'], name='idx_product_count'),
            models.Index(fields=['date'], name='idx_product_date'),
            models.Index(
                fields=['free_delivery'], name='idx_product_free_delivery'
            ),
            models.Index(fields=['rating'], name='idx_product_rating'),
            models.Index(
                fields=['is_limited_edition'],
                name='idx_product_is_limited_edition',
            ),
            models.Index(fields=['is_banner'], name='idx_product_is_banner'),
            models.Index(fields=['archived'], name='idx_product_archived'),
        ]

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
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='products',
    )
    count = models.PositiveIntegerField(
        default=0,
    )
    purchases = models.PositiveIntegerField(
        default=0,
    )
    date = models.DateTimeField(
        auto_now_add=True,
    )
    description = models.CharField(
        blank=True,
        max_length=3000,
    )
    full_description = models.CharField(
        blank=True,
        max_length=20000,
    )
    free_delivery = models.BooleanField(
        default=True,
    )
    is_limited_edition = models.BooleanField(
        default=False,
    )
    is_banner = models.BooleanField(
        default=False,
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='products',
    )
    specifications = models.ManyToManyField(
        Specification,
        blank=True,
        related_name='products',
    )
    rating = models.DecimalField(
        blank=True,
        default=1,
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

    def __str__(self) -> str:
        return self.title


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
        blank=True,
        null=True,
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
    text = models.CharField(
        max_length=2000,
    )
    rate = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
    )
    date = models.DateTimeField(
        auto_now_add=True,
    )


class BasketProduct(models.Model):
    class Meta:
        unique_together = ('basket', 'product')

    basket = models.ForeignKey('Basket', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    count = models.PositiveIntegerField()


class Basket(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='basket',
    )
    products = models.ManyToManyField(
        Product,
        through=BasketProduct,
    )
    last_accessed = models.DateTimeField(
        auto_now=True,
    )

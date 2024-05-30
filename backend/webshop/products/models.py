import uuid
from decimal import Decimal

from account.models import User
from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models
from django.db.models import Count, QuerySet
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _


class Tag(models.Model):
    """Tag model for products"""

    name = models.CharField(max_length=100)

    def __str__(self) -> str:
        """
        Return tag name.

        :return: Tag name
        :rtype: str
        """
        return self.name


class Specification(models.Model):
    """
    Specification model for products. For example, color, weight, and other
    product characteristics.
    """

    class Meta:
        unique_together = ('name', 'value')

    name = models.CharField(max_length=200)
    value = models.CharField(max_length=200)

    def __str__(self) -> str:
        """
        Return specification in format "name: value".

        :return: Specification in format "name: value"
        :rtype: str
        """
        return f'{self.name}: {self.value}'


def category_image_upload_path(instance: 'Category', filename: str) -> str:
    """
    Return category image upload path.

    :param instance: Category instance
    :type instance: Category
    :param filename: Image filename
    :type filename: str
    :return: Category image upload path
    :rtype: str
    """
    return f'categories/category{instance.pk}/image/{filename}'


class Category(models.Model):
    """
    Category model for products. Categories can be nested, but only one level
    deep.
    """

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        indexes = [
            models.Index(fields=['title'], name='idx_category_title'),
            models.Index(fields=['archived'], name='idx_category_archived'),
        ]

    title = models.CharField(max_length=200)
    parent = models.ForeignKey(
        'Category',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='subcategories',
    )
    image = models.ImageField(
        blank=True, null=True, upload_to=category_image_upload_path
    )
    image_alt = models.CharField(max_length=200, blank=True)
    archived = models.BooleanField(default=False)

    def clean(self) -> None:
        """
        Validate category parent and subcategories.

        :raises ValidationError: If category is parent of itself, has parent
            with a parent, or has subcategories.
        :return: None
        """
        if self.parent is not None:
            if self == self.parent:
                raise ValidationError(
                    _('Category cannot be a parent of itself')
                )
            if self.parent.parent is not None:
                msg = (
                    'Category can only be subcategory of a top-level category'
                )
                raise ValidationError(_(msg))
            if self.pk is not None and self.subcategories.count() > 0:
                raise ValidationError(
                    _('Subcategory cannot have subcategories')
                )

        return super().clean()

    def __str__(self) -> str:
        """
        Return category title.

        :return: Category title
        :rtype: str
        """
        return self.title


class Product(models.Model):
    """
    Product model for webshop. Products can have multiple images, tags,
    specifications, and reviews. Products can be on sale, and can be added to
    a basket. Products can be archived. Products can have a category.

    Attributes:
        title (str): Product title
        price (Decimal): Product price
        category (Category): Product category. Can be None
        count (int): Product count in stock
        sold_count (int): Product sold count
        created_at (datetime): Product creation date
        description (str): Product short description
        full_description (str): Product full description
        free_delivery (bool): Whether delivery is free
        is_limited_edition (bool): If product is shown in the limited edition
            section
        is_banner (bool): If product is shown in the banner section
        tags (QuerySet): Product tags
        specifications (QuerySet): Product specifications (characteristics)
        rating (Decimal): Product rating from 1 to 5
        archived (bool): If product is archived
    """

    class Meta:
        indexes = [
            models.Index(Lower('title'), name='idx_product_title_lower'),
            models.Index(fields=['price'], name='idx_product_price'),
            models.Index(fields=['count'], name='idx_product_count'),
            models.Index(fields=['created_at'], name='idx_product_created_at'),
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

    title = models.CharField(max_length=200)
    price = models.DecimalField(
        default=0,
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal(0))],
    )
    category = models.ForeignKey(
        Category,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='products',
    )
    count = models.PositiveIntegerField(default=0)
    sold_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(blank=True, max_length=3000)
    full_description = models.CharField(blank=True, max_length=20000)
    free_delivery = models.BooleanField(default=False)
    is_limited_edition = models.BooleanField(default=False)
    is_banner = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tag, blank=True, related_name='products')
    specifications = models.ManyToManyField(
        Specification, blank=True, related_name='products'
    )
    rating = models.DecimalField(
        blank=True,
        default=1,
        max_digits=2,
        decimal_places=1,
        validators=[
            MinValueValidator(Decimal(1)),
            MaxValueValidator(Decimal(5)),
        ],
    )
    archived = models.BooleanField(default=False)

    def __str__(self) -> str:
        """
        Return product title.

        :return: Product title
        :rtype: str
        """
        return self.title


def product_image_upload_path(instance: 'ProductImage', filename: str) -> str:
    """
    Return product image upload path.

    :param instance: ProductImage instance
    :type instance: ProductImage
    :param filename: Image filename
    :type filename: str
    :return: Product image upload path
    :rtype: str
    """
    return 'products/product{pk}/images/{filename}'.format(
        pk=instance.product.pk, filename=filename
    )


class ProductImage(models.Model):
    """Image model for products. Product can have multiple images."""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='images'
    )
    image = models.ImageField(
        blank=True, null=True, upload_to=product_image_upload_path
    )
    image_alt = models.CharField(max_length=200, blank=True)


def get_products_queryset() -> 'QuerySet[Product]':
    """
    Return products queryset with all related data.

    :return: Products queryset
    :rtype: QuerySet[Product]
    """
    return (
        Product.objects.select_related('category')
        .prefetch_related(
            'images',
            'tags',
        )
        .annotate(reviews_count=Count('reviews'))
        .filter(archived=False)
        .all()
    )


class Sale(models.Model):
    """
    Sale model for products. Products can be on sale for a specific time with a
    specific price.
    """

    class Meta:
        indexes = [
            models.Index(fields=['date_from'], name='idx_sale_date_from'),
            models.Index(fields=['date_to'], name='idx_sale_date_to'),
            models.Index(fields=['sale_price'], name='idx_sale_sale_price'),
        ]

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='sales'
    )
    date_from = models.DateTimeField()
    date_to = models.DateTimeField()
    sale_price = models.DecimalField(
        blank=False,
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal(0))],
    )


class Review(models.Model):
    """
    Review model for products. Users can leave reviews for products. Reviews
    have a rate from 1 to 5.
    """

    class Meta:
        indexes = [
            models.Index(fields=['created_at'], name='idx_review_created_at'),
        ]

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='reviews'
    )
    author = models.CharField(max_length=200)
    email = models.EmailField()
    text = models.CharField(max_length=2000)
    rate = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
    )
    created_at = models.DateTimeField(auto_now_add=True)


class BasketProduct(models.Model):
    """
    BasketProduct model for products. Basket can have multiple products in it.
    Each product has count.
    """

    class Meta:
        unique_together = ('basket', 'product')

    basket = models.ForeignKey('Basket', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(validators=[MinValueValidator(1)])


class Basket(models.Model):
    """
    Basket model for products. Basket can have multiple products in it. Basket
    has a user and last accessed date which is updated each time basket is
    saved.
    """

    class Meta:
        indexes = [
            models.Index(
                fields=['last_accessed'], name='idx_basket_last_accessed'
            ),
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User,
        blank=True,
        null=True,
        unique=True,
        on_delete=models.CASCADE,
        related_name='basket',
    )
    products = models.ManyToManyField(Product, through=BasketProduct)
    last_accessed = models.DateTimeField(auto_now=True)


class OrderProduct(models.Model):
    """
    OrderProduct model for products. Order can have multiple products in it.
    Each product has count.
    """

    class Meta:
        unique_together = ('order', 'product')

    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(validators=[MinValueValidator(1)])


class Order(models.Model):
    """
    Order model for products. Order can have multiple products in it.

    Attributes:
        DELIVERY_ORDINARY (str): Ordinary (regular) delivery type
        DELIVERY_EXPRESS (str): Express delivery type
        PAYMENT_ONLINE (str): Online payment type
        PAYMENT_SOMEONE (str): Payment by someone type
        STATUS_NEW (str): Order status when it is just created
        STATUS_PROCESSING (str): Order status when all fields are filled but it
            is not paid yet
        STATUS_PAID (str): Paid order status
        DELIVERY_TYPES (tuple): Delivery types choices
        PAYMENT_TYPES (tuple): Payment types choices
        STATUSES (tuple): Order statuses choices

        user (User): Customer who made the order
        basket (Basket): Basket to identify an anonymous user
        products (QuerySet): Order products
        created_at (datetime): Order creation date
        full_name (str): Customer full name
        email (str): Customer email
        phone (str): Customer phone
        delivery_type (str): Order delivery type
        payment_type (str): Order payment type
        total_cost (Decimal): Order total cost
        status (str): Order status
        city (str): City where order is delivered
        address (str): Address where order is delivered
        archived (bool): If order is archived
    """

    class Meta:
        indexes = [
            models.Index(fields=['created_at'], name='idx_order_created_at'),
            models.Index(fields=['full_name'], name='idx_order_full_name'),
            models.Index(fields=['address'], name='idx_order_address'),
            models.Index(fields=['city'], name='idx_order_city'),
            models.Index(fields=['email'], name='idx_order_email'),
            models.Index(fields=['phone'], name='idx_order_phone'),
            models.Index(fields=['total_cost'], name='idx_order_total_cost'),
            models.Index(fields=['status'], name='idx_order_status'),
            models.Index(
                fields=['delivery_type'], name='idx_order_delivery_type'
            ),
            models.Index(
                fields=['payment_type'], name='idx_order_payment_type'
            ),
            models.Index(fields=['archived'], name='idx_order_archived'),
        ]

    DELIVERY_ORDINARY = 'ordinary'
    DELIVERY_EXPRESS = 'express'
    PAYMENT_ONLINE = 'online'
    PAYMENT_SOMEONE = 'someone'
    STATUS_NEW = 'new'
    STATUS_PROCESSING = 'processing'
    STATUS_PAID = 'paid'

    DELIVERY_TYPES = (
        ('', ''),
        (DELIVERY_ORDINARY, DELIVERY_ORDINARY),
        (DELIVERY_EXPRESS, DELIVERY_EXPRESS),
    )
    PAYMENT_TYPES = (
        ('', ''),
        (PAYMENT_ONLINE, PAYMENT_ONLINE),
        (PAYMENT_SOMEONE, PAYMENT_SOMEONE),
    )
    STATUSES = (
        (STATUS_NEW, STATUS_NEW),
        (STATUS_PROCESSING, STATUS_PROCESSING),
        (STATUS_PAID, STATUS_PAID),
    )

    user = models.ForeignKey(
        User,
        blank=True,
        null=True,
        related_name='orders',
        on_delete=models.SET_NULL,
    )
    basket = models.ForeignKey(
        Basket, blank=True, null=True, on_delete=models.SET_NULL
    )
    products = models.ManyToManyField(
        Product, through=OrderProduct, related_name='orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    full_name = models.CharField(blank=True, max_length=120)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(
        blank=True,
        max_length=32,
        validators=[RegexValidator(r'^\+\d{5,}(\#\d+)?$')],
    )
    delivery_type = models.CharField(
        blank=True, max_length=15, choices=DELIVERY_TYPES
    )
    payment_type = models.CharField(
        blank=True, max_length=15, choices=PAYMENT_TYPES
    )
    total_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal(0))],
    )
    status = models.CharField(
        max_length=15, choices=STATUSES, default=STATUS_NEW
    )
    city = models.CharField(blank=True, max_length=150)
    address = models.CharField(blank=True, max_length=300)
    archived = models.BooleanField(default=False)

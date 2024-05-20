import logging
from decimal import Decimal
from typing import Any

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import transaction
from django.db.models import Model
from django.shortcuts import get_object_or_404
from django.templatetags.static import static
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import (
    Category,
    Order,
    OrderProduct,
    Product,
    Review,
    Specification,
    Tag,
    get_products_queryset,
)

log = logging.getLogger(__name__)


FOLDER_ICON = 'products/folder_icon.png'
GOODS_ICON = 'products/goods_icon.png'


def get_last_reviews(product_id: int, count: int) -> list[dict]:
    """
    Get last N reviews for product with id=product_id ordered by created_at

    :param product_id: product id
    :type product_id: int
    :param count: number of reviews to return
    :type count: int
    :return: list of reviews
    :rtype: list[dict]
    """
    reviews = Review.objects.filter(product_id=product_id).order_by(
        '-created_at'
    )[:count]
    serializer = ReviewSerializer(reviews, many=True)

    return serializer.data


class ImageSerializer(serializers.Serializer):
    """
    Serializer for image field. If there is no image, a default image is
    added.
    """

    src = serializers.SerializerMethodField()
    alt = serializers.SerializerMethodField()

    def get_src(self, instance: Model) -> str:
        """
        Get image url. If image is not found, return default image url

        :param instance: model instance
        :type instance: Model
        :return: image url
        :rtype: str
        """
        try:
            return instance.image.url
        except Exception:
            return self.default_image_url

    def get_alt(self, instance: Model) -> str:
        """
        Get image alt text

        :param instance: model instance
        :type instance: Model
        :return: image alt text
        :rtype: str
        """
        return getattr(instance, 'image_alt', '')

    @property
    def default_image_url(self) -> str:
        """
        Get default image url

        :return: default image url
        :rtype: str
        """
        return ''


class CategoryImageSerializer(ImageSerializer):
    """
    Serializer for category image field. If there is no image, a default image
    is added.
    """

    @property
    def default_image_url(self) -> str:
        """
        Get default image url

        :return: default image url
        :rtype: str
        """
        return static(FOLDER_ICON)


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for category model. Image field is serialized with
    `CategoryImageSerializer`. If there is no image, a default image is added.
    """

    class Meta:
        model = Category
        fields = ['id', 'title', 'image']
        read_only_fields = ['id', 'title', 'image']

    image = CategoryImageSerializer(source='*')


class TopLevelCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for top level category and its subcategories. Image field is
    serialized with `CategoryImageSerializer`. If there is no image, a default
    image is added.
    """

    class Meta:
        model = Category
        fields = ['id', 'title', 'image', 'subcategories']
        read_only_fields = ['id', 'title', 'image', 'subcategories']

    image = CategoryImageSerializer(source='*')
    subcategories = CategorySerializer(many=True, read_only=True)


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tag model"""

    class Meta:
        model = Tag
        fields = ['id', 'name']


class SpecificationSerializer(serializers.ModelSerializer):
    """Serializer for specification (product characteristics) model"""

    class Meta:
        model = Specification
        fields = ['name', 'value']


class ProductShortSerializer(serializers.ModelSerializer):
    """
    Serializer for `Product` model. `Reviews` field is replaced with the number
    of reviews. If there are no images, a default image is added.
    """

    class Meta:
        model = Product
        fields = [
            'id',
            'category',
            'price',
            'count',
            'date',
            'title',
            'description',
            'freeDelivery',
            'images',
            'tags',
            'reviews',
            'rating',
        ]

    date = serializers.DateTimeField(source='created_at', read_only=True)
    images = ImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    reviews = serializers.IntegerField(source='reviews_count')
    freeDelivery = serializers.CharField(source='free_delivery')

    def to_representation(self, instance: Product) -> dict[str, Any]:
        """
        Replace empty images with default image

        :param instance: product instance
        :type instance: Product
        :return: product data
        :rtype: dict[str, Any]
        """
        data = super().to_representation(instance)
        if not data['images']:
            data['images'] = [{'src': static(GOODS_ICON), 'alt': ''}]
        return data


class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for review model. Date field is formatted as
    'YYYY-MM-DD HH:MM'
    """

    class Meta:
        model = Review
        fields = ['id', 'author', 'email', 'text', 'rate', 'date']

    date = serializers.DateTimeField(
        source='created_at', format='%Y-%m-%d %H:%M'
    )


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for `Product` model. `Reviews` field is replaced with the last
    `REVIEWS_COUNT` reviews. If there are no images, a default image is added.
    """

    class Meta:
        model = Product
        fields = [
            'id',
            'category',
            'price',
            'count',
            'date',
            'title',
            'description',
            'fullDescription',
            'freeDelivery',
            'images',
            'tags',
            'specifications',
            'reviews',
            'rating',
        ]

    REVIEWS_COUNT = 10

    date = serializers.DateTimeField(source='created_at', read_only=True)
    images = ImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    specifications = SpecificationSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField(read_only=True)
    fullDescription = serializers.CharField(source='full_description')
    freeDelivery = serializers.CharField(source='free_delivery')

    def get_reviews(self, instance: Product) -> list[dict]:
        """
        Get last `REVIEWS_COUNT` reviews for product ordered by created_at

        :param instance: product instance
        :type instance: Product
        :return: list of reviews
        :rtype: list[dict]
        """
        return get_last_reviews(instance.id, self.REVIEWS_COUNT)

    def to_representation(self, instance: Product) -> dict[str, Any]:
        """
        Replace empty images with default image

        :param instance: product instance
        :type instance: Product
        :return: product data
        :rtype: dict[str, Any]
        """
        data = super().to_representation(instance)
        if not data['images']:
            data['images'] = [{'src': static(GOODS_ICON), 'alt': ''}]
        return data


class SaleSerializer(serializers.Serializer):
    """
    Serializer for sale model

    Attributes:
        id: product id
        price: product price
        salePrice: sale price
        dateFrom: sale start date in format 'MM-DD'
        dateTo: sale end date in format 'MM-DD'
        title: product title
        images: product images
    """

    id = serializers.IntegerField(source='product.id')
    price = serializers.DecimalField(
        source='product.price', max_digits=8, decimal_places=2
    )
    salePrice = serializers.DecimalField(
        source='sale_price', max_digits=8, decimal_places=2
    )
    dateFrom = serializers.DateTimeField(source='date_from', format='%m-%d')
    dateTo = serializers.DateTimeField(source='date_to', format='%m-%d')
    title = serializers.CharField(source='product.title')
    images = ImageSerializer(source='product.images', many=True)


class ReviewCreateSerializer(serializers.Serializer):
    """
    Serializer for review creation. Date field is formatted as
    'YYYY-MM-DD HH:MM'
    """

    author = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    text = serializers.CharField(max_length=2000)
    rate = serializers.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5),
        ],
    )
    date = serializers.DateTimeField(
        source='created_at', read_only=True, format='%Y-%m-%d %H:%M'
    )

    def save(self, product_id: int, **kwargs) -> Any:
        """
        Save review for a product

        :param product_id: product id
        :type product_id: int
        :param kwargs: additional keyword arguments
        :raises Http404: if product is not found
        :return: created review
        :rtype: Any
        """
        product = get_object_or_404(Product, pk=product_id, archived=False)
        kwargs['product'] = product

        return super().save(**kwargs)

    @transaction.atomic
    def create(self, validated_data: Any) -> Review:
        """
        Create review

        :param validated_data: validated data
        :type validated_data: Any
        :return: created review
        :rtype: Review
        """
        review = Review.objects.create(**validated_data)
        review.product = validated_data.pop('product')
        review.save()

        return review


class ProductCountSerializer(serializers.Serializer):
    """Serializer for product count in basket and in an order"""

    id = serializers.IntegerField(
        required=True,
        validators=[
            MinValueValidator(0),
        ],
    )
    count = serializers.IntegerField(
        required=True,
        validators=[
            MinValueValidator(1),
        ],
    )


class BasketIdSerializer(serializers.Serializer):
    """Serializer for basket id. The id format is UUID"""

    basket_id = serializers.UUIDField()


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for `Order` model. CreatedAt field is formatted as
    'YYYY-MM-DD HH:MM'
    """

    class Meta:
        model = Order
        fields = [
            'id',
            'createdAt',
            'fullName',
            'email',
            'phone',
            'deliveryType',
            'paymentType',
            'totalCost',
            'status',
            'city',
            'address',
            'products',
        ]

    createdAt = serializers.DateTimeField(
        source='created_at', read_only=True, format='%Y-%m-%d %H:%M'
    )
    fullName = serializers.CharField(source='full_name', max_length=120)
    deliveryType = serializers.ChoiceField(
        source='delivery_type', choices=Order.DELIVERY_TYPES
    )
    paymentType = serializers.ChoiceField(
        source='payment_type', choices=Order.PAYMENT_TYPES
    )
    totalCost = serializers.DecimalField(
        source='total_cost',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal(0))],
    )
    products = serializers.SerializerMethodField(read_only=True)

    def get_products(self, obj: Order) -> list[dict]:
        """
        Get products in order with their count

        :param obj: order instance
        :type obj: Order
        :return: list of products with their count
        :rtype: list[dict]
        """
        order_products = OrderProduct.objects.filter(order=obj).all()
        product_counts = {op.product_id: op.count for op in order_products}

        products = get_products_queryset()
        product_ids = list(product_counts.keys())
        products = products.filter(id__in=product_ids).all()

        result = ProductShortSerializer(products, many=True).data

        for item in result:
            item['count'] = product_counts[item['id']]

        return result

    def validate(self, data: dict) -> dict:
        """
        Validate order data. Some empty fields are only allowed in a new order.

        :param data: order data
        :type data: dict
        :raises ValidationError: if order is not new and some fields are empty
        :return: validated order data
        :rtype: dict
        """
        if data['status'] == Order.STATUS_NEW:
            return data

        allowed_empty = [
            'full_name',
            'email',
            'delivery_type',
            'payment_type',
            'city',
            'address',
        ]
        any_is_empty = any(
            str(data.get(field, '')).strip() == '' for field in allowed_empty
        )

        if any_is_empty:
            raise ValidationError(
                'These fields can only be empty in a new order: {}'.format(
                    ', '.join(allowed_empty)
                )
            )

        return data

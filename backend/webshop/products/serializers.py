import logging
from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import transaction
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


def get_last_reviews(product_id: int, count: int):
    reviews = Review.objects.filter(product_id=product_id).order_by(
        '-created_at'
    )[:count]
    serializer = ReviewSerializer(reviews, many=True)

    return serializer.data


class ImageSerializer(serializers.Serializer):
    src = serializers.SerializerMethodField()
    alt = serializers.SerializerMethodField()

    def get_src(self, instance):
        try:
            return instance.image.url
        except Exception:
            return self.default_image_url

    @property
    def default_image_url(self):
        return ''

    def get_alt(self, instance):
        return getattr(instance, 'image_alt', '')


class CategoryImageSerializer(ImageSerializer):
    @property
    def default_image_url(self):
        return static(FOLDER_ICON)


class ProductImageSerializer(ImageSerializer):
    @property
    def default_image_url(self):
        return static(FOLDER_ICON)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'image']
        read_only_fields = ['id', 'title', 'image']

    image = CategoryImageSerializer(source='*')


class TopLevelCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'image', 'subcategories']
        read_only_fields = ['id', 'title', 'image', 'subcategories']

    image = CategoryImageSerializer(source='*')
    subcategories = CategorySerializer(many=True, read_only=True)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class SpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specification
        fields = ['name', 'value']


class ProductShortSerializer(serializers.ModelSerializer):
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
    images = ProductImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    reviews = serializers.IntegerField(source='reviews_count')
    freeDelivery = serializers.CharField(source='free_delivery')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not data['images']:
            data['images'] = [{'src': static(GOODS_ICON), 'alt': ''}]
        return data


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'author', 'email', 'text', 'rate', 'date']

    REVIEWS_COUNT = 10

    date = serializers.DateTimeField(
        source='created_at', format='%Y-%m-%d %H:%M'
    )


class ProductDetailSerializer(serializers.ModelSerializer):
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

    date = serializers.DateTimeField(source='created_at', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    specifications = SpecificationSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField(read_only=True)
    fullDescription = serializers.CharField(source='full_description')
    freeDelivery = serializers.CharField(source='free_delivery')

    def get_reviews(self, obj):
        return get_last_reviews(obj.id, ReviewSerializer.REVIEWS_COUNT)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not data['images']:
            data['images'] = [{'src': static(GOODS_ICON), 'alt': ''}]
        return data


class SaleSerializer(serializers.Serializer):
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

    def save(self, product_id, **kwargs):
        product = get_object_or_404(Product, pk=product_id, archived=False)
        kwargs['product'] = product

        return super().save(**kwargs)

    @transaction.atomic
    def create(self, validated_data):
        review = Review.objects.create(**validated_data)
        review.product = validated_data.pop('product')
        review.save()

        return review


class ProductCountSerializer(serializers.Serializer):
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
    basket_id = serializers.UUIDField()


class OrderSerializer(serializers.ModelSerializer):
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

    def get_products(self, obj):
        order_products = OrderProduct.objects.filter(order=obj).all()
        product_counts = {op.product_id: op.count for op in order_products}

        products = get_products_queryset()
        product_ids = list(product_counts.keys())
        products = products.filter(id__in=product_ids).all()

        result = ProductShortSerializer(products, many=True).data

        for item in result:
            item['count'] = product_counts[item['id']]

        return result

    def validate(self, data):
        """Allow empty fields only for order with status Order.STATUS_NEW"""
        if data['status'] == Order.STATUS_NEW:
            return data

        fields = [
            'full_name',
            'email',
            'phone',
            'delivery_type',
            'payment_type',
            'city',
            'address',
        ]
        is_empty = (str(data.get(field, '')).strip() == '' for field in fields)

        if any(is_empty):
            raise ValidationError(
                'These fields can only be empty in a new order: {}'.format(
                    ', '.join(fields)
                )
            )

        return data

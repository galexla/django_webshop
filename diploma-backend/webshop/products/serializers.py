import logging

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers

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
User = get_user_model()


class ImageSerializer(serializers.Serializer):
    src = serializers.SerializerMethodField()
    alt = serializers.SerializerMethodField()

    def get_src(self, instance):
        return instance.image.url

    def get_alt(self, instance):
        return getattr(instance, 'image_alt', '')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'image']
        read_only_fields = ['id', 'title', 'image']

    image = ImageSerializer(source='*')


class TopLevelCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'image', 'subcategories']
        read_only_fields = ['id', 'title', 'image', 'subcategories']

    image = ImageSerializer(source='*')
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

    images = ImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    reviews = serializers.IntegerField(source='reviews_count')
    freeDelivery = serializers.CharField(source='free_delivery')


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'author', 'email', 'text', 'rate', 'date']


class ProductSerializer(serializers.ModelSerializer):
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

    images = ImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    specifications = SpecificationSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    fullDescription = serializers.CharField(source='full_description')
    freeDelivery = serializers.CharField(source='free_delivery')


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
    date = serializers.DateTimeField(read_only=True)

    def save(self, product_id, **kwargs):
        product = get_object_or_404(Product, pk=product_id)
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
            MinValueValidator(0),
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

    createdAt = serializers.CharField(source='created_at', read_only=True)
    fullName = serializers.CharField(source='full_name')
    deliveryType = serializers.ChoiceField(
        source='delivery_type', choices=Order.DELIVERY_TYPES
    )
    paymentType = serializers.ChoiceField(
        source='payment_type', choices=Order.PAYMENT_TYPES
    )
    totalCost = serializers.DecimalField(
        source='total_cost', max_digits=10, decimal_places=2
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

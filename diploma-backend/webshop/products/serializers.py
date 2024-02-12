from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Category, Product, Specification, Tag

User = get_user_model()


class ImageSerializer(serializers.Serializer):
    src = serializers.SerializerMethodField()
    alt = serializers.SerializerMethodField()

    def get_src(self, instance):
        return instance.image.url

    def get_alt(self, instance):
        return getattr(instance, 'image_alt', '')


class CategorySerializer(serializers.ModelSerializer):
    image = ImageSerializer(source='*')

    class Meta:
        model = Category
        fields = ['id', 'title', 'image']
        read_only_fields = ('id', 'title', 'image')


class TopLevelCategorySerializer(serializers.ModelSerializer):
    image = ImageSerializer(source='*')
    subcategories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'title', 'image', 'subcategories']
        read_only_fields = (
            'id',
            'title',
            'image',
            'subcategories',
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = 'id', 'name'


class SpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specification
        fields = 'name', 'value'


class ProductShortSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    reviews = serializers.IntegerField(source='reviews_count')
    freeDelivery = serializers.CharField(source='free_delivery')

    class Meta:
        model = Product
        fields = (
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
        )


class ProductSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    specifications = SpecificationSerializer(many=True, read_only=True)
    fullDescription = serializers.CharField(source='full_description')
    freeDelivery = serializers.CharField(source='free_delivery')

    class Meta:
        model = Product
        fields = (
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
        )

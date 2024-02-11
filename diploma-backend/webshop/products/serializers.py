from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Category, Product, ProductImage, Tag

User = get_user_model()


class CategoryImageRepresentationMixin:
    def to_representation(self, instance):
        data = super().to_representation(instance)
        image = {
            'src': data['image'],
            'alt': data['image_alt'],
        }
        data['image'] = image
        data.pop('image_alt')

        return data


class CategorySerializer(
    CategoryImageRepresentationMixin, serializers.ModelSerializer
):
    class Meta:
        model = Category
        fields = ['id', 'title', 'image', 'image_alt']
        read_only_fields = ('id', 'title', 'image', 'image_alt')


class TopLevelCategorySerializer(
    CategoryImageRepresentationMixin, serializers.ModelSerializer
):
    subcategories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'title', 'image', 'image_alt', 'subcategories']
        read_only_fields = (
            'id',
            'title',
            'image',
            'image_alt',
            'subcategories',
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = 'id', 'name'


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = 'image', 'image_alt'

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['src'] = instance.image.url
        data['alt'] = data.pop('image_alt', '')
        data.pop('image', 0)

        return data


class ProductShortSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)

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
            'free_delivery',
            'images',
            'tags',
            'reviews',
            'rating',
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        reviews_count = data.pop('reviews_count', 0)
        data['reviews'] = reviews_count

        return data

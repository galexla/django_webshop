from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Category, Tag

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
        fields = ('id', 'name')

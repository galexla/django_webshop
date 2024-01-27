from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Category

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'title', 'parent', 'image', 'image_alt']
        read_only_fields = ('id', 'title', 'parent', 'image', 'image_alt')

    def validate(self, data):
        if data.get('parent') == self.instance:
            raise serializers.ValidationError(
                "Category cannot be parent of itself"
            )
        return data


class TopLevelCategorySerializer(serializers.ModelSerializer):
    subcategories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'title', 'image', 'image_alt', 'subcategories']
        read_only_fields = ('id', 'title', 'parent', 'image', 'image_alt')

from rest_framework import generics

from .models import Category, Tag
from .serializers import TagSerializer, TopLevelCategorySerializer


class TopLevelCategoryListView(generics.ListAPIView):
    serializer_class = TopLevelCategorySerializer
    queryset = Category.objects.filter(parent=None).prefetch_related(
        'subcategories'
    )


class TagListView(generics.ListAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()

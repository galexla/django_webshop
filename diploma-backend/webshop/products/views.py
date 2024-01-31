from django.db.models import Count, Prefetch
from rest_framework import generics, mixins, viewsets

from .models import Category, Product, Tag
from .serializers import (
    CatalogSerializer,
    TagSerializer,
    TopLevelCategorySerializer,
)


class TopLevelCategoryListView(generics.ListAPIView):
    serializer_class = TopLevelCategorySerializer
    queryset = Category.objects.filter(parent=None).prefetch_related(
        'subcategories'
    )


class TagListView(generics.ListAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class CatalogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = (
        Product.objects.prefetch_related(
            'images',
            Prefetch('tags', queryset=Tag.objects.only('id', 'name')),
            'reviews',
        )
        .annotate(reviews_count=Count('reviews'))
        .defer('full_description')
        .all()
    )
    serializer_class = CatalogSerializer
    # filter_backends = [
    #     SearchFilter,
    #     DjangoFilterBackend,
    #     OrderingFilter,
    # ]
    # search_fields = ['name', 'description']
    # filterset_fields = [
    #     'name',
    #     'description',
    #     'price',
    #     'discount',
    #     'archived',
    # ]
    # ordering_fields = [
    #     'name',
    #     'price',
    #     'discount',
    # ]

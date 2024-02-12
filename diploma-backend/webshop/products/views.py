import django_filters
from django.db.models import (
    Case,
    Count,
    IntegerField,
    Prefetch,
    Q,
    Value,
    When,
)
from django.http.request import QueryDict
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins, pagination, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Product, Review, Tag
from .serializers import (
    ProductSerializer,
    ProductShortSerializer,
    TagSerializer,
    TopLevelCategorySerializer,
)


class TopLevelCategoryListView(APIView):
    def get(self, request):
        queryset = Category.objects.prefetch_related('subcategories').filter(
            parent=None, archived=False
        )
        serialzier = TopLevelCategorySerializer(queryset, many=True)
        return Response(serialzier.data)


class TagFilter(django_filters.FilterSet):
    category = django_filters.NumberFilter(
        field_name='category', method='filter_by_category_or_parent'
    )

    def filter_by_category_or_parent(self, queryset, name, value):
        queryset = queryset.filter(
            Q(products__category=value) | Q(products__category__parent=value)
        )
        return queryset


class TagListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filterset_class = TagFilter
    pagination_class = None


class CatalogPagination(pagination.PageNumberPagination):
    page_query_param = 'currentPage'
    page_size_query_param = 'limit'

    def get_paginated_response(self, data):
        return Response(
            {
                'items': data,
                'currentPage': self.page.number,
                'lastPage': self.page.paginator.num_pages,
            }
        )


class CatalogFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name='title', lookup_expr='iexact')
    category = django_filters.NumberFilter(
        field_name='category', method='filter_by_category_or_parent'
    )
    minPrice = django_filters.NumberFilter(
        field_name='price', lookup_expr='gte'
    )
    maxPrice = django_filters.NumberFilter(
        field_name='price', lookup_expr='lte'
    )
    freeDelivery = django_filters.BooleanFilter(
        field_name='free_delivery', method='no_filtering_on_false'
    )
    available = django_filters.BooleanFilter(
        field_name='available', method='no_filtering_on_false'
    )

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        queryset = self.filter_by_tags_list(queryset)
        return queryset

    def filter_by_tags_list(self, queryset):
        """
        Filters by tag list from URL parameter 'tags[]'
        """
        tags = self.request.query_params.getlist('tags[]')
        for tag_id in tags:
            queryset = queryset.filter(tags__id=tag_id)

        return queryset

    def filter_by_category_or_parent(self, queryset, name, value):
        queryset = queryset.filter(
            Q(category=value) | Q(category__parent=value)
        )
        return queryset

    def no_filtering_on_false(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(**{name: value})


class CatalogFilterBackend(DjangoFilterBackend):
    def get_filterset_kwargs(self, request, queryset, view):
        filter_kwargs = super().get_filterset_kwargs(request, queryset, view)
        original_data = filter_kwargs.get('data', {})

        if isinstance(original_data, QueryDict):
            data = original_data.copy()
        else:
            data = original_data

        new_data = {}
        for key, value in data.items():
            if key.startswith('filter[') and key.endswith(']'):
                new_key = key[7:-1]  # Remove 'filter[' and ']'
                new_data[new_key] = value
            else:
                new_data[key] = value

        filter_kwargs['data'] = new_data

        return filter_kwargs


class CatalogOrderingFilter(OrderingFilter):
    ordering_fields = [
        'rating',
        'price',
        'reviews',
        'date',
    ]

    def filter_queryset(self, request, queryset, view):
        """
        Adds ordering by URL parameter 'sort' and sort direction 'sortType'
        """
        sort_field = request.query_params.get('sort')
        if not sort_field or sort_field not in self.ordering_fields:
            return queryset

        sort_type = request.query_params.get('sortType')
        sort_sign = '-' if sort_type == 'dec' else ''

        return queryset.order_by(sort_sign + sort_field)


class CatalogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = (
        Product.objects.select_related('category')
        .prefetch_related(
            'images',
            'tags',
            Prefetch('reviews', queryset=Review.objects.only('id')),
        )
        .annotate(reviews_count=Count('reviews'))
        .annotate(
            available=Case(
                When(count=0, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        )
        .defer('full_description')
        .filter(archived=False)
        .all()
    )
    serializer_class = ProductShortSerializer
    filter_backends = [
        CatalogFilterBackend,
        CatalogOrderingFilter,
    ]
    filterset_class = CatalogFilter
    pagination_class = CatalogPagination


class PopularProductsListView(generics.ListAPIView):
    queryset = (
        Product.objects.select_related('category')
        .prefetch_related(
            'images',
            'tags',
            Prefetch('reviews', queryset=Review.objects.only('id')),
        )
        .annotate(reviews_count=Count('reviews'))
        .defer('full_description')
        .filter(archived=False)
        .order_by('-rating', '-purchases')
        .all()[:8]
    )
    serializer_class = ProductShortSerializer
    pagination_class = None


class LimitedProductsListView(generics.ListAPIView):
    queryset = (
        Product.objects.select_related('category')
        .prefetch_related(
            'images',
            'tags',
            Prefetch('reviews', queryset=Review.objects.only('id')),
        )
        .annotate(reviews_count=Count('reviews'))
        .defer('full_description')
        .filter(is_limited_edition=True)
        .filter(archived=False)
        .all()[:16]
    )
    serializer_class = ProductShortSerializer
    pagination_class = None


class BannerProductsListView(generics.ListAPIView):
    queryset = (
        Product.objects.select_related('category')
        .prefetch_related(
            'images',
            'tags',
            Prefetch('reviews', queryset=Review.objects.only('id')),
        )
        .annotate(reviews_count=Count('reviews'))
        .defer('full_description')
        .filter(is_banner=True)
        .filter(archived=False)
        .all()[:3]
    )
    serializer_class = ProductShortSerializer
    pagination_class = None


class ProductDetailView(generics.RetrieveAPIView):
    queryset = (
        Product.objects.select_related('category')
        .prefetch_related(
            'images',
            'tags',
            'reviews',
        )
        .filter(archived=False)
        .all()
    )
    serializer_class = ProductSerializer


# TODO: create a real basket view
# class BasketStubViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
# class BasketStubViewSet(generics.ListAPIView):
#     queryset = (
#         Product.objects.prefetch_related(
#             'images',
#             Prefetch('tags', queryset=Tag.objects.only('id', 'name')),
#             'reviews',
#         )
#         .annotate(reviews_count=Count('reviews'))
#         .defer('full_description')
#         .all()
#     )
#     # TODO: change serializer
#     serializer_class = CatalogSerializer


class BasketStubViewSet(generics.ListAPIView):
    def get(self, request, *args, **kwargs):
        data = [
            {
                "category": 3,
                "price": "799.00",
                "count": 1,
                "date": "2024-01-30T15:29:54.733294Z",
                "title": "Smartphone",
                "description": "Nulla in libero volutpat, pellentesque erat eget, viverra nisi.",
                "freeDelivery": True,
                "images": [
                    {
                        "src": "http://127.0.0.1:8000/media/categories/category1/image/mobile-devices.jpg",
                        "alt": "some alt",
                    }
                ],
                "tags": [],
                "reviews": 0,
                "rating": "4.0",
            },
            # {
            #     "category": 4,
            #     "price": "490.00",
            #     "count": 2,
            #     "date": "2024-01-30T15:30:48.823393Z",
            #     "title": "Monitor",
            #     "description": "Maecenas in nisi in eros sagittis sagittis eget in purus.",
            #     "freeDelivery": True,
            #     "images": [
            #         {
            #             "src": "http://127.0.0.1:8000/media/categories/category1/image/mobile-devices.jpg",
            #             "alt": "some alt",
            #         }
            #     ],
            #     "tags": [{"id": 1, "name": "Tag1"}, {"id": 2, "name": "Tag2"}],
            #     "reviews": 0,
            #     "rating": "5.0",
            # },
        ]
        return Response(data)

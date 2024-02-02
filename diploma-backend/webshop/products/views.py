import django_filters
from django.db.models import Case, Count, IntegerField, Prefetch, Value, When
from django.http.request import QueryDict
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins, pagination, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Product, Tag
from .serializers import (
    CatalogSerializer,
    TagSerializer,
    TopLevelCategorySerializer,
)


class TopLevelCategoryListView(APIView):
    def get(self, request):
        queryset = Category.objects.filter(parent=None).prefetch_related(
            'subcategories'
        )
        serialzier = TopLevelCategorySerializer(queryset, many=True)
        return Response(serialzier.data)


class TagListView(APIView):
    def get(self, request):
        queryset = Tag.objects.all()
        serialzier = TagSerializer(queryset, many=True)
        return Response(serialzier.data)


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
    class Meta:
        model = Product
        fields = ['minPrice', 'maxPrice', 'freeDelivery', 'available']

    name = django_filters.CharFilter(
        field_name='title', lookup_expr='icontains'
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

        filter_kwargs['data'] = new_data
        return filter_kwargs


class CatalogViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = (
        Product.objects.prefetch_related(
            'images',
            Prefetch('tags', queryset=Tag.objects.only('id', 'name')),
            'reviews',
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
        .all()
    )
    serializer_class = CatalogSerializer
    pagination_class = CatalogPagination
    filter_backends = [
        CatalogFilterBackend,
        OrderingFilter,
    ]
    search_fields = ['name']
    filterset_class = CatalogFilter
    filterset_fields = [
        'minPrice',
        'maxPrice',
        'freeDelivery',
        'available',
    ]
    ordering_fields = [
        'rating',
        'price',
        'reviews',
        'date',
    ]

    def get_queryset(self):
        queryset = super().get_queryset()
        sort_field = self.request.query_params.get('sort')
        if not sort_field or sort_field not in self.ordering_fields:
            return queryset

        sort_type = self.request.query_params.get('sortType')
        sort_sign = '-' if sort_type == 'dec' else ''

        return queryset.order_by(sort_sign + sort_field)


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
                "free_delivery": True,
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
            #     "free_delivery": True,
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

import django_filters
from django.db.models import Case, Count, IntegerField, Prefetch, Value, When
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins, pagination, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category, Product, Tag
from .serializers import (CatalogSerializer, TagSerializer,
                          TopLevelCategorySerializer)


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


# class YachtTypeFilterSet(django_filters.FilterSet):
#     type_in = django_filters.CharFilter(
#         method='filter_guest_level', field_name='guest_level')

#     def filter_type_in(self, queryset, field_name, value):
#         if value != "":
#             id_array = json.loads(value)
#             if isinstance(id_array, list):
#                 return queryset.filter(type__id__in=id_array)
#         return queryset


class CatalogPagination(pagination.PageNumberPagination):
    def get_paginated_response(self, data):
        return Response(
            {
                'items': data,
                'currentPage': self.page.number,
                'lastPage': self.page.paginator.num_pages,
            }
        )


class CatalogFilter(django_filters.FilterSet):
    minPrice = django_filters.NumberFilter(
        field_name='price', lookup_expr='gte'
    )
    maxPrice = django_filters.NumberFilter(
        field_name='price', lookup_expr='lte'
    )
    freeDelivery = django_filters.NumberFilter(
        field_name='free_delivery', lookup_expr='eq'
    )
    available = django_filters.NumberFilter(
        field_name='available', lookup_expr='eq'
    )


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
        SearchFilter,
        DjangoFilterBackend,
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

    # TODO: take sort & sort direction params from URL: /api/catalog/?filter[name]=&filter[minPrice]=1&filter[maxPrice]=230&filter[freeDelivery]=false&filter[available]=false&currentPage=1&sort=price&sortType=inc&limit=20
    # def get_queryset(self):
    ## from: https://stackoverflow.com/questions/53835232/django-custom-ordering-in-url-queries
    #     queryset = super(DatastreamViewSet, self).get_queryset()

    #     order_by = self.request.query_params.get('order_by', '')
    #     if order_by:
    #         order_by_name = order_by.split(' ')[1]
    #         order_by_sign = order_by.split(' ')[0]
    #         order_by_sign = '' if order_by_sign == 'asc' else '-'
    #         queryset = queryset.order_by(order_by_sign + order_by_name)

    #     return queryset


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

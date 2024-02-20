import logging
from datetime import datetime, timedelta, timezone

import django_filters
from django.db import transaction
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
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Basket, BasketProduct, Category, Product, Review, Tag
from .serializers import (
    BasketIdSerializer,
    BasketItem,
    BasketProductSerializer,
    ProductSerializer,
    ProductShortSerializer,
    ReviewCreateSerializer,
    TagSerializer,
    TopLevelCategorySerializer,
)

log = logging.getLogger(__name__)


def get_product_short_qs():
    return (
        Product.objects.select_related('category')
        .prefetch_related(
            'images',
            'tags',
            Prefetch('reviews', queryset=Review.objects.only('id')),
        )
        .annotate(reviews_count=Count('reviews'))
        .filter(archived=False)
        .all()
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

        if sort_field == 'reviews':
            sort_field = 'reviews_count'

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


class ReviewCreateView(APIView):
    def post(self, request: Request, pk):
        serializer = ReviewCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data=serializer.errors, status=400)

        serializer.save(product_id=pk)
        return Response([serializer.data])


class BasketView(generics.ListCreateAPIView):
    COOKIE_MAX_AGE = 14 * 24 * 3600

    def get(self, request, *args, **kwargs):
        """Get basket contents or return []"""
        basket = self._get_basket(request)
        log.debug('Got basket: %s', basket)
        if basket:
            products = self._get_products(basket)
            serializer = ProductShortSerializer(products, many=True)

            response = Response(serializer.data)
            self._set_basket_cookie(basket, response)

            return response

        return Response([])

    def _set_basket_cookie(self, basket: Basket, response: Response):
        response.set_cookie(
            'basket_id', basket.id, max_age=self.COOKIE_MAX_AGE
        )

    def _get_basket(self, request: Request) -> Basket:
        """Get basket by COOKIES.basket_id or by current user"""
        COOKIES = request._request.COOKIES or {}
        user = request.user
        queryset = Basket.objects.all()

        if not user.is_anonymous:
            queryset = queryset.filter(user=user)
        else:
            basket_id = COOKIES.get('basket_id')
            serializer = BasketIdSerializer(data={'basket_id': basket_id})
            if serializer.is_valid():
                queryset = queryset.filter(
                    id=serializer.validated_data['basket_id']
                )

        if not queryset:
            return None
        else:
            basket = queryset[0]
            self._update_access_time(basket)
            return basket

    def _update_access_time(self, basket: Basket) -> None:
        """Update basket last access time"""
        seconds = timedelta(seconds=120)
        # TODO: are timezones the same in DB & in code?
        now = datetime.now(timezone(timedelta(0)))
        if now - seconds > basket.last_accessed:
            basket.save()  # updates basket.last_accessed

    def _get_products(self, basket: Basket) -> list[Product]:
        """Get products with real count in basket"""
        basketproduct_set = basket.basketproduct_set.all()
        product_counts = {}
        for item in basketproduct_set:
            product_counts[item.product_id] = item.count
        log.debug('Got product counts: %s', product_counts)

        products = get_product_short_qs()
        products = list(products.filter(id__in=basket.products.all()))
        log.debug('Got products: %s', products)
        for product in products:
            product.count = product_counts[product.id]

        return products

    def post(self, request, *args, **kwargs):
        """Inc/dec product counts; add/remove BasketProduct items"""
        counts_serializer = BasketItem(data=request.data, many=True)
        if not counts_serializer.is_valid():
            return Response(None, status=400)

        product_counts = {
            item['id']: item['count']
            for item in counts_serializer.validated_data
        }
        log.debug('Product counts: %s', product_counts)

        basket = self._get_basket(request)
        if not basket:
            user = None if request.user.is_anonymous else request.user
            basket = Basket.objects.create(user=user)

        basket_products = list(
            BasketProduct.objects.filter(basket_id=basket.id)
        )

        basket_products_to_update = []
        for basket_product in basket_products:
            product_id = basket_product.product_id
            if product_id in product_counts:
                product_count = product_counts[product_id]
                if basket_product.count != product_count:
                    basket_product.count = product_count
                    basket_products_to_update.append(basket_product)
                product_counts.pop(product_id)

        basket_products_to_add = []
        for product_id, product_count in product_counts.items():
            basket_product = BasketProduct(
                basket_id=basket.id, product_id=product_id, count=product_count
            )
            basket_products_to_add.append(basket_product)

        log.debug('BasketProduct to add: %s', basket_products_to_add)
        log.debug('BasketProduct to update: %s', basket_products_to_update)

        with transaction.atomic():
            created = BasketProduct.objects.bulk_create(basket_products_to_add)
            n_created = len(created)
            n_updated = BasketProduct.objects.bulk_update(
                basket_products_to_update, fields=['count']
            )
            log.debug('BasketProduct created: %s', n_created)
            log.debug('BasketProduct updated: %s', n_updated)

        response = Response([])
        self._set_basket_cookie(basket, response)

        return response

    def post_old2(self, request, *args, **kwargs):
        # queryset = Basket.objects.prefetch_related(
        #     Prefetch(
        #         'products',
        #         queryset=BasketProduct.objects.select_related('product').all(),
        #     )
        # ).filter(id='60ac1520a1104db49090d934a0b9f8f9')

        # queryset = (
        #     Basket.objects.all()
        #     .prefetch_related(
        #         Prefetch(
        #             'products',
        #             queryset=BasketProduct.objects.select_related(
        #                 'product'
        #             ).all(),
        #         )
        #     )
        #     .filter(id='60ac1520a1104db49090d934a0b9f8f9')
        # )

        # queryset = (
        #     Basket.objects.all()
        #     .prefetch_related(
        #         Prefetch(
        #             'products',
        #             queryset=BasketProduct.objects.all(),
        #         )
        #     )
        #     .filter(id='60ac1520a1104db49090d934a0b9f8f9')
        # )

        # queryset = Basket.objects.filter(id='60ac1520a1104db49090d934a0b9f8f9')

        # basket = Basket.objects.get(id='60ac1520a1104db49090d934a0b9f8f9')
        # basket = (
        #     Basket.objects.all()
        #     .prefetch_related('products')
        #     .get(id='60ac1520a1104db49090d934a0b9f8f9')
        # )

        # basket = queryset[0]
        # basket = Basket.objects.prefetch_related('basketproduct_set').get(
        #     id='60ac1520a1104db49090d934a0b9f8f9'
        # )
        basket_products = list(
            BasketProduct.objects.filter(
                basket_id='60ac1520a1104db49090d934a0b9f8f9'
            )
        )
        print('########', basket_products)

        # print('########', basket)
        # print('########', dir(basket))
        # print('########', basket.basketproduct_set)
        # print('########', basket.products)

        return Response([])

    def post_old1(self, request, *args, **kwargs):
        data = request.data.copy()
        if not isinstance(data, list):
            return Response(None, status=400)

        basket = self._get_basket(request)
        print('########', basket)
        if not basket:
            user = None if request.user.is_anonymous else request.user
            basket = Basket.objects.create(user=user)

        print('#########', basket.products)
        # print('#########', basket.basketproduct)

        for item in data:
            item['basket'] = basket.id
            item['product'] = item.pop('id')

        serializer = BasketProductSerializer(data=data, many=True)
        if serializer.is_valid():
            print('##########', serializer.validated_data)
            pass
            # with transaction.atomic():
            #     serializer.save()
            #     basket.save()
        else:
            return Response(serializer.errors, status=400)

        return Response([])

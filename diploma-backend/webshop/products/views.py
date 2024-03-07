import logging

import django_filters
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Case, IntegerField, Q, Value, When
from django.http.request import QueryDict
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins, pagination, status, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .common import get_basket
from .models import (
    Basket,
    BasketProduct,
    Category,
    Order,
    OrderProduct,
    Product,
    Tag,
    get_products_queryset,
)
from .serializers import (
    OrderSerializer,
    ProductCountSerializer,
    ProductSerializer,
    ProductShortSerializer,
    ReviewCreateSerializer,
    TagSerializer,
    TopLevelCategorySerializer,
)

log = logging.getLogger(__name__)


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
        get_products_queryset()
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
    serializer_class = ProductShortSerializer
    filter_backends = [
        CatalogFilterBackend,
        CatalogOrderingFilter,
    ]
    filterset_class = CatalogFilter
    pagination_class = CatalogPagination


class PopularProductsListView(generics.ListAPIView):
    queryset = (
        get_products_queryset()
        .defer('full_description')
        .order_by('-rating', '-purchases')
        .all()[:8]
    )
    serializer_class = ProductShortSerializer
    pagination_class = None


class LimitedProductsListView(generics.ListAPIView):
    queryset = (
        get_products_queryset()
        .defer('full_description')
        .filter(is_limited_edition=True)
        .all()[:16]
    )
    serializer_class = ProductShortSerializer
    pagination_class = None


class BannerProductsListView(generics.ListAPIView):
    queryset = (
        get_products_queryset()
        .defer('full_description')
        .filter(is_banner=True)
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
            return Response(
                data=serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save(product_id=pk)
        return Response([serializer.data])


class BasketView(
    generics.mixins.DestroyModelMixin, generics.ListCreateAPIView
):
    COOKIE_MAX_AGE = 14 * 24 * 3600

    def get(self, request, *args, **kwargs):
        """Get basket contents"""
        basket = get_basket(request)
        if basket:
            log.debug('Got basket: %s', basket.id)
            products = self._get_products(basket)
            return self._get_response(products, basket.id)

        return Response([])

    def _get_products(self, basket: Basket) -> list[Product]:
        """Get products in basket"""
        basketproduct_set = basket.basketproduct_set.all()
        product_counts = {}
        for basket_product in basketproduct_set:
            product_counts[basket_product.product_id] = basket_product.count
        log.debug(
            'Got product counts %s in basket %s', product_counts, basket.id
        )

        products = get_products_queryset()
        products = list(products.filter(id__in=basket.products.all()))
        log.debug('Got products %s from basket %s', products, basket.id)
        for product in products:
            product.count = product_counts[product.id]

        return products

    def _get_response(self, products, basket_id) -> Response:
        serializer = ProductShortSerializer(products, many=True)
        response = Response(serializer.data)
        response.set_cookie(
            'basket_id', basket_id, max_age=self.COOKIE_MAX_AGE
        )

        return response

    def post(self, request, *args, **kwargs):
        """Add some quantity of a product to basket"""
        serializer = ProductCountSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        basket = get_basket(request)
        if not basket:
            user = request.user if not request.user.is_anonymous else None
            basket = Basket.objects.create(user=user)

        basket_id = basket.id.hex

        product_id = serializer.validated_data['id']
        product_count = serializer.validated_data['count']
        log.debug(
            'To add %s of product %s to basket %s',
            product_count,
            product_id,
            basket_id,
        )

        if not self._increment(basket_id, product_id, product_count):
            return Response(
                {'count': ['Product quantity is not available.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        products = self._get_products(basket)
        return self._get_response(products, basket_id)

    def _increment(self, basket_id, product_id, product_count):
        product = get_object_or_404(Product, id=product_id, archived=False)

        queryset = BasketProduct.objects.filter(
            basket_id=basket_id, product_id=product_id
        ).all()
        basket_product = queryset[0] if queryset else None

        if basket_product is None:
            if product.count < product_count:
                return False

            basket_product = BasketProduct(
                basket_id=basket_id,
                product_id=product_id,
                count=product_count,
            )
            basket_product.save()
        else:
            if product.count < basket_product.count + product_count:
                return False

            basket_product.count += product_count
            basket_product.save()

        log.info(
            'Added %s item(s) of product %s to basket %s',
            product_count,
            product_id,
            basket_id,
        )

        return True

    def delete(self, request, *args, **kwargs):
        """Delete from basket some quantity of a product"""
        serializer = ProductCountSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        basket = get_basket(request)
        if not basket:
            return Response([])

        basket_id = basket.id.hex

        product_id = serializer.validated_data['id']
        product_count = serializer.validated_data['count']
        log.debug(
            'To delete %s of product %s from basket %s',
            product_count,
            product_id,
            basket_id,
        )

        if not self._decrement(basket_id, product_id, product_count):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        products = self._get_products(basket)
        return self._get_response(products, basket_id)

    def _decrement(self, basket_id, product_id, product_count):
        queryset = BasketProduct.objects.filter(
            basket_id=basket_id, product_id=product_id
        ).all()
        basket_product = queryset[0] if queryset else None

        if basket_product is None:
            log.debug('Product %s is not in basket %s', product_id, basket_id)
            return False

        basket_product.count -= product_count
        if basket_product.count <= 0:
            basket_product.delete()
        else:
            basket_product.save()
        log.info(
            'Deleted %s of product %s from basket %s',
            product_count,
            product_id,
            basket_id,
        )

        return True


class OrdersView(LoginRequiredMixin, APIView):
    def get(self, request, *args, **kwargs):
        user = request.user
        orders = (
            Order.objects.prefetch_related('products').filter(user=user).all()
        )
        serializer = OrderSerializer(orders, many=True)
        log.debug('Got %s orders, user=%s', len(serializer.data), user.id)

        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        product_counts = [
            {
                'id': item.get('id'),
                'count': item.get('count'),
            }
            for item in request.data
        ]
        serializer = ProductCountSerializer(data=product_counts, many=True)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        log.debug('validated product_counts: %s', serializer.validated_data)

        product_counts_dict = {
            item['id']: item['count'] for item in serializer.validated_data
        }
        with transaction.atomic():
            if self._are_available(product_counts_dict):
                order = self._create_order(product_counts_dict, request.user)
                return Response({'orderId': order.id})
            else:
                return Response(
                    {'count': ['Product quantities are not available.']},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_order(self, product_counts_dict, user):
        order = Order(user=user)
        order.save()

        order_products = []
        for product_id, product_count in product_counts_dict.items():
            order_product = OrderProduct(
                order_id=order.id,
                product_id=product_id,
                count=product_count,
            )
            order_products.append(order_product)
        OrderProduct.objects.bulk_create(order_products)

        product_ids = list(product_counts_dict.keys())
        log.debug('product_ids: %s', product_ids)
        products = list(
            Product.objects.filter(id__in=product_ids, archived=False).all()
        )
        for product in products:
            product.count -= product_counts_dict[product.id]
        Product.objects.bulk_update(products, fields=['count'])

        return order

    def _are_available(self, product_counts_dict: dict[str, int]) -> bool:
        ids = set(product_counts_dict.keys())
        products = Product.objects.filter(id__in=ids, archived=False).all()
        ids_fetched = set(product.id for product in products)

        if ids_fetched != ids:
            return False

        for product in products:
            if product.count < product_counts_dict[product.id]:
                return False

        return True


class OrderView(LoginRequiredMixin, APIView):
    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, user=request.user)
        serializer = OrderSerializer(order, data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save()

        return Response()

import logging

import django_filters
from account.models import User
from configurations.models import get_all_shop_configurations
from django.db import transaction
from django.db.models import Case, IntegerField, Q, Value, When
from django.http.request import QueryDict
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, mixins, pagination, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
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
    Sale,
    Tag,
    get_products_queryset,
)
from .serializers import (
    OrderSerializer,
    ProductCountSerializer,
    ProductDetailSerializer,
    ProductShortSerializer,
    ReviewCreateSerializer,
    SaleSerializer,
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


class Pagination(pagination.PageNumberPagination):
    page_query_param = 'currentPage'

    def get_paginated_response(self, data):
        return Response(
            {
                'items': data,
                'currentPage': self.page.number,
                'lastPage': self.page.paginator.num_pages,
            }
        )


class CatalogPagination(Pagination):
    page_size_query_param = 'limit'


class CatalogFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name='title', lookup_expr='icontains'
    )
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
    sort_fields = {
        'rating': 'rating',
        'price': 'price',
        'reviews': 'reviews_count',
        'date': 'created_at',
    }

    def filter_queryset(self, request, queryset, view):
        """
        Adds ordering by URL parameter 'sort' and sort direction 'sortType'
        """
        sort_field = request.query_params.get('sort')
        if not sort_field or sort_field not in self.sort_fields:
            return queryset.order_by('id')

        sort_type = request.query_params.get('sortType')
        sort_sign = '-' if sort_type == 'dec' else ''

        sort_field = self.sort_fields[sort_field]
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
        .order_by('-rating', '-sold_count')
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


class SalesView(generics.ListAPIView):
    queryset = (
        Sale.objects.prefetch_related('product', 'product__images')
        .filter(product__archived=False)
        .order_by('id')
    )
    serializer_class = SaleSerializer

    @property
    def paginator(self):
        """
        The paginator instance associated with the view.
        """
        if not hasattr(self, '_paginator'):
            self._paginator = Pagination()
            self._paginator.page_size = 10
        return self._paginator


class ProductDetailView(generics.RetrieveAPIView):
    queryset = (
        Product.objects.select_related('category')
        .prefetch_related(
            'images',
            'tags',
        )
        .filter(archived=False)
        .all()
    )
    serializer_class = ProductDetailSerializer


class ReviewCreateView(APIView):
    def post(self, request: Request, pk):
        serializer = ReviewCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data=serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save(product_id=pk)
        return Response([serializer.data])


def basket_decrement(basket_id, product_counts: dict[str, int]) -> bool:
    product_ids = list(product_counts.keys())
    basket_products = BasketProduct.objects.filter(
        basket_id=basket_id, product__in=product_ids, product__archived=False
    ).all()

    if basket_products is None:
        log.info(
            'Unable to delete, products %s are not in basket %s',
            product_ids,
            basket_id,
        )
        return False

    for basket_product in basket_products:
        basket_product.count -= product_counts[basket_product.product_id]
        if basket_product.count <= 0:
            basket_product.delete()
        else:
            basket_product.save()

    log.info('Deleted products from basket %s', basket_id)

    return True


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

        basket_product = BasketProduct.objects.filter(
            basket_id=basket_id, product_id=product_id, product__archived=False
        ).first()

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
        return basket_decrement(basket_id, {product_id: product_count})


class OrdersView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        orders = (
            Order.objects.prefetch_related('products')
            .filter(user=user)
            .order_by('-created_at')
            .all()
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
        ] or None
        serializer = ProductCountSerializer(data=product_counts, many=True)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        log.debug('validated product_counts: %s', serializer.validated_data)

        product_counts_dict = {
            item['id']: item['count'] for item in serializer.validated_data
        }

        data, success = self._create_order_if_avail(
            product_counts_dict, request.user
        )
        if success:
            return Response(data)
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def _create_order_if_avail(
        self, product_counts_dict, user
    ) -> tuple[dict, bool]:
        """Create order if products are available"""
        if self._are_available(product_counts_dict):
            order = self._create_order(product_counts_dict, user)
            basket = Basket.objects.filter(user=user).first()
            if basket:
                basket_decrement(basket.id, product_counts_dict)
            return {'orderId': order.id}, True
        else:
            return {'count': ['Product quantities are not available']}, False

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

    def _create_order(self, product_counts: dict[str, int], user: User):
        """Must always be used inside transaction.atomic block"""
        order = Order(user=user)
        order.full_name = user.get_full_name()
        order.phone = user.profile.phone or ''
        order.email = user.email or ''
        order.status = order.STATUS_NEW
        order.save()

        self._bulk_create_order_products(product_counts, order.id)

        product_ids = list(product_counts.keys())
        log.debug('product_ids: %s', product_ids)
        products = list(
            Product.objects.filter(id__in=product_ids, archived=False).all()
        )
        for product in products:
            count = product_counts[product.id]
            product.count -= count
            product.sold_count += count
        Product.objects.bulk_update(products, fields=['count', 'sold_count'])

        order.total_cost = 0
        for product in products:
            order.total_cost += product.price * count
        order.save()

        return order

    def _bulk_create_order_products(self, product_counts, order_id):
        order_products = []
        for product_id, count in product_counts.items():
            order_product = OrderProduct(
                order_id=order_id,
                product_id=product_id,
                count=count,
            )
            order_products.append(order_product)
        return OrderProduct.objects.bulk_create(order_products)


class OrderView(APIView):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = get_object_or_404(
            Order, pk=pk, user=request.user, archived=False
        )
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def post(self, request, pk):
        order = get_object_or_404(
            Order, pk=pk, user=request.user, archived=False
        )

        if order.status == Order.STATUS_PROCESSING:  # return unmodified order
            serializer = OrderSerializer(order)
            data = serializer.data
            data['orderId'] = data['id']  # fix bug in frontend
            return Response(data)

        if order.status != Order.STATUS_NEW:
            msg = 'Only orders with status "{}" can be modified.'.format(
                Order.STATUS_NEW
            )
            return Response(
                {'status': [msg]}, status=status.HTTP_400_BAD_REQUEST
            )

        request.data['status'] = Order.STATUS_PROCESSING
        serializer = OrderSerializer(order, data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        data['total_cost'] += self._get_delivery_cost(
            order.id, data['delivery_type'], data['total_cost']
        )
        serializer.save()

        return Response(data)

    def _get_delivery_cost(self, order_id, delivery_type, order_cost):
        shop_confs = get_all_shop_configurations()
        if delivery_type == Order.DELIVERY_EXPRESS:
            return shop_confs['express_delivery_price']
        elif delivery_type == Order.DELIVERY_ORDINARY:
            if self._is_delivery_free(order_id, delivery_type):
                return 0
            if order_cost < shop_confs['free_delivery_limit']:
                return shop_confs['ordinary_delivery_price']

        return 0

    def _is_delivery_free(self, order_id, delivery_type) -> bool:
        if delivery_type == Order.DELIVERY_ORDINARY:
            free_deliveries = (
                OrderProduct.objects.prefetch_related('product')
                .filter(order_id=order_id)
                .values_list('product__free_delivery')
            )
            return all(item[0] for item in free_deliveries)
        return False

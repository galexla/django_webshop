import decimal
import logging
from uuid import UUID

import django_filters
from account.models import User
from configurations.models import get_all_shop_configurations
from django.db import transaction
from django.db.models import Case, IntegerField, Q, Value, When
from django.db.models.query import QuerySet
from django.http.request import QueryDict
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import pagination, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.filters import OrderingFilter
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
)
from rest_framework.mixins import DestroyModelMixin, ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from .common import (
    delete_unused_baskets,
    fill_order_fields_if_needed,
    get_basket,
    get_basket_id_cookie,
)
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
    get_last_reviews,
)

log = logging.getLogger(__name__)


class TopLevelCategoryListView(APIView):
    """View for getting top-level categories with subcategories"""

    def get(self, request: Request) -> Response:
        """
        Get top-level categories with subcategories

        :param request: request
        :type request: Request
        :return: response
        :rtype: Response
        """
        queryset = Category.objects.prefetch_related('subcategories').filter(
            parent=None, archived=False
        )
        serialzier = TopLevelCategorySerializer(queryset, many=True)
        return Response(serialzier.data)


class TagFilter(django_filters.FilterSet):
    """Filter for tags"""

    category = django_filters.NumberFilter(
        field_name='category', method='filter_by_category_or_parent'
    )

    def filter_by_category_or_parent(
        self, queryset: QuerySet, name: str, value: int
    ) -> QuerySet:
        """
        Filter by category or its parent

        :param queryset: queryset to filter
        :type queryset: QuerySet
        :param name: field name
        :type name: str
        :param value: category id
        :type value: int
        :return: filtered queryset
        :rtype: QuerySet
        """
        queryset = queryset.filter(
            Q(products__category=value) | Q(products__category__parent=value)
        )
        return queryset


class TagListViewSet(ListModelMixin, GenericViewSet):
    """View for getting tags"""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filterset_class = TagFilter
    pagination_class = None


class Pagination(pagination.PageNumberPagination):
    """Custom pagination class"""

    page_query_param = 'currentPage'

    def get_paginated_response(self, data: dict) -> Response:
        """
        Get paginated response

        :param data: data
        :type data: dict
        :return: response
        :rtype: Response
        """
        return Response(
            {
                'items': data,
                'currentPage': self.page.number,
                'lastPage': self.page.paginator.num_pages,
            }
        )


class CatalogPagination(Pagination):
    """Pagination for catalog"""

    page_size_query_param = 'limit'


class CatalogFilter(django_filters.FilterSet):
    """
    Filter for catalog by. It can filter by product name, its category, price,
    free delivery and availability.
    """

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
        field_name='free_delivery', method='filter_only_on_true'
    )
    available = django_filters.BooleanFilter(
        field_name='available', method='filter_only_on_true'
    )

    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        """
        Filter queryset by tags list

        :param queryset: queryset to filter
        :type queryset: QuerySet
        :return: filtered queryset
        :rtype: QuerySet
        """
        queryset = super().filter_queryset(queryset)
        queryset = self.filter_by_tags_list(queryset)
        return queryset

    def filter_by_tags_list(self, queryset: QuerySet) -> QuerySet:
        """
        Filter by tag list from URL parameter 'tags[]'

        :param queryset: queryset to filter
        :type queryset: QuerySet
        :return: filtered queryset
        :rtype: QuerySet
        """
        tags = self.request.query_params.getlist('tags[]')
        for tag_id in tags:
            queryset = queryset.filter(tags__id=tag_id)

        return queryset

    def filter_by_category_or_parent(
        self, queryset: QuerySet, name: str, value: int
    ) -> QuerySet:
        """
        Filter by category or its parent

        :param queryset: queryset to filter
        :type queryset: QuerySet
        :param name: field name
        :type name: str
        :param value: category id
        :type value: int
        :return: filtered queryset
        :rtype: QuerySet
        """
        queryset = queryset.filter(
            Q(category=value) | Q(category__parent=value)
        )
        return queryset

    def filter_only_on_true(
        self, queryset: QuerySet, name: str, value: bool
    ) -> QuerySet:
        """
        Filter by boolean value. If value is False, then return queryset as is.

        :param queryset: queryset to filter
        :type queryset: QuerySet
        :param name: field name
        :type name: str
        :param value: value
        :type value: bool
        :return: queryset
        :rtype: QuerySet
        """
        if not value:
            return queryset
        return queryset.filter(**{name: value})


class CatalogFilterBackend(DjangoFilterBackend):
    """
    Custom filter backend for catalog. It transforms URL parameters like
    'filter[key_name]' to just 'key_name' for django_filters.FilterSet.
    """

    def get_filterset_kwargs(
        self, request: Request, queryset: QuerySet, view: GenericViewSet
    ) -> dict:
        """
        Get filter kwargs

        :param request: request
        :type request: Request
        :param queryset: queryset
        :type queryset: QuerySet
        :param view: view
        :type view: GenericViewSet
        :return: filter kwargs
        :rtype: dict
        """
        filter_kwargs = super().get_filterset_kwargs(request, queryset, view)
        original_data = filter_kwargs.get('data', {})

        if isinstance(original_data, QueryDict):
            data = original_data.copy()
        else:
            data = original_data

        new_data = {}
        for key, value in data.items():
            if key.startswith('filter[') and key.endswith(']'):
                # Remove 'filter[' and ']' from key
                new_key = key[7:-1]
                new_data[new_key] = value
            else:
                new_data[key] = value

        filter_kwargs['data'] = new_data

        return filter_kwargs


class CatalogOrderingFilter(OrderingFilter):
    """
    Custom ordering filter for catalog. It adds sorting by rating, price,
    reviews, and date.
    """

    sort_fields = {
        'rating': 'rating',
        'price': 'price',
        'reviews': 'reviews_count',
        'date': 'created_at',
    }

    def filter_queryset(
        self, request: Request, queryset: QuerySet, view: GenericViewSet
    ) -> QuerySet:
        """
        Add ordering by URL parameter 'sort' and 'sortType' (asc or dec)

        :param request: request
        :type request: Request
        :param queryset: queryset
        :type queryset: QuerySet
        :param view: view
        :type view: GenericViewSet
        :return: ordered queryset
        :rtype: QuerySet
        """
        sort_field = request.query_params.get('sort')
        if not sort_field or sort_field not in self.sort_fields:
            return queryset.order_by('id')

        sort_type = request.query_params.get('sortType')
        sort_sign = '-' if sort_type == 'dec' else ''

        sort_field = self.sort_fields[sort_field]
        return queryset.order_by(sort_sign + sort_field)


class CatalogViewSet(ListModelMixin, GenericViewSet):
    """View for catalog"""

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


class PopularProductsListView(ListAPIView):
    """View for getting for popular products section"""

    queryset = (
        get_products_queryset()
        .defer('full_description')
        .order_by('-rating', '-sold_count')
        .all()[:8]
    )
    serializer_class = ProductShortSerializer
    pagination_class = None


class LimitedProductsListView(ListAPIView):
    """View for getting products for limited edition section"""

    queryset = (
        get_products_queryset()
        .defer('full_description')
        .filter(is_limited_edition=True)
        .all()[:16]
    )
    serializer_class = ProductShortSerializer
    pagination_class = None


class BannerProductsListView(ListAPIView):
    """View for getting products for banner section"""

    queryset = (
        get_products_queryset()
        .defer('full_description')
        .filter(is_banner=True)
        .all()[:3]
    )
    serializer_class = ProductShortSerializer
    pagination_class = None


class SalesView(ListAPIView):
    """View for getting sales"""

    queryset = (
        Sale.objects.prefetch_related('product', 'product__images')
        .filter(product__archived=False)
        .order_by('id')
    )
    serializer_class = SaleSerializer

    @property
    def paginator(self) -> Pagination:
        """
        Paginator instance for sales

        :return: paginator
        :rtype: Pagination
        """
        if not hasattr(self, '_paginator'):
            self._paginator = Pagination()
            self._paginator.page_size = 10
        return self._paginator


class ProductDetailView(RetrieveAPIView):
    """View for getting product details"""

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
    """View for creating a review"""

    def post(self, request: Request, pk: int) -> Response:
        """
        Create a review for a product

        :param request: request
        :type request: Request
        :param pk: product id
        :type pk: int
        :return: response
        :rtype: Response
        """
        serializer = ReviewCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data=serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        serializer.save(product_id=pk)
        return Response(
            get_last_reviews(pk, ProductDetailSerializer.REVIEWS_COUNT)
        )


def basket_remove_products(
    basket_id: str | UUID, product_counts: dict[int, int]
) -> bool:
    """
    Remove products from basket

    :param basket_id: basket id
    :type basket_id: str | UUID
    :param product_counts: product id and its count
    :type product_counts: dict[int, int]
    :return: True if products were removed, False otherwise
    :rtype: bool
    """
    product_ids = list(product_counts.keys())
    basket_products = BasketProduct.objects.filter(
        basket_id=basket_id, product__in=product_ids, product__archived=False
    ).all()

    if len(basket_products) == 0:
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


class BasketView(DestroyModelMixin, ListCreateAPIView):
    """View for basket"""

    COOKIE_MAX_AGE = 14 * 24 * 3600

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Get basket contents

        :param request: request
        :type request: Request
        :return: response
        :rtype: Response
        """
        basket = get_basket(request)
        delete_unused_baskets(self.COOKIE_MAX_AGE)
        if basket:
            log.debug('Got basket: %s', basket.id)
            products = self._get_products(basket)
            return self._get_response(products, basket.id)
        else:
            return Response([])

    def _get_products(self, basket: Basket) -> list[Product]:
        """
        Get products in basket

        :param basket: basket
        :type basket: Basket
        :return: products
        :rtype: list[Product]
        """
        basketproduct_set = basket.basketproduct_set.all()
        product_counts = {}
        for basket_product in basketproduct_set:
            product_counts[basket_product.product_id] = basket_product.count

        if not product_counts:
            return []

        log.debug(
            'Got product counts %s in basket %s', product_counts, basket.id
        )

        products = get_products_queryset()
        products = list(products.filter(id__in=basket.products.all()))
        log.debug('Got products %s from basket %s', products, basket.id)
        for product in products:
            product.count = product_counts[product.id]

        return products

    def _set_cookie(self, response: Response, basket_id: str) -> None:
        """
        Set basket id to cookie

        :param response: response
        :type response: Response
        :param basket_id: basket id
        :type basket_id: str
        :return: None
        """
        response.set_cookie(
            'basket_id', basket_id, max_age=self.COOKIE_MAX_AGE
        )

    def _get_response(
        self, products: list[Product], basket_id: str
    ) -> Response:
        """
        Get response with products and set cookie

        :param products: products
        :type products: list[Product]
        :param basket_id: basket id
        :type basket_id: str
        :return: response
        :rtype: Response
        """
        serializer = ProductShortSerializer(products, many=True)
        response = Response(serializer.data)
        self._set_cookie(response, basket_id)

        return response

    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Add some quantity of a product to basket

        :param request: request
        :type request: Request
        :return: response
        :rtype: Response
        """
        serializer = ProductCountSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        product_id = serializer.validated_data['id']
        product_count = serializer.validated_data['count']
        product = get_object_or_404(Product, id=product_id, archived=False)

        basket = get_basket(request)
        if not basket:
            user = request.user if not request.user.is_anonymous else None
            basket = Basket.objects.create(user=user)

        basket_id = basket.id.hex
        log.debug(
            'To add %s of product %s to basket %s',
            product_count,
            product_id,
            basket_id,
        )

        if not self._add_products(basket_id, product, product_count):
            response = Response(
                {'count': ['Product quantity is not available.']},
                status=status.HTTP_400_BAD_REQUEST,
            )
            self._set_cookie(response, basket_id)
            return response

        products = self._get_products(basket)
        return self._get_response(products, basket_id)

    def _add_products(
        self, basket_id: str | UUID, product: Product, product_count: int
    ) -> bool:
        """
        Add specified quantity of a product to basket

        :param basket_id: basket id
        :type basket_id: str | UUID
        :param product: product
        :type product: Product
        :param product_count: product count
        :type product_count: int
        :return: True if product was added, False otherwise
        :rtype: bool
        """
        basket_product = BasketProduct.objects.filter(
            basket_id=basket_id, product_id=product.id, product__archived=False
        ).first()

        if basket_product is None:
            if product.count < product_count:
                return False

            basket_product = BasketProduct(
                basket_id=basket_id,
                product_id=product.id,
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
            product.id,
            basket_id,
        )

        return True

    def delete(self, request: Request, *args, **kwargs) -> Response:
        """
        Delete from basket some quantity of a product

        :param request: request
        :type request: Request
        :return: response
        :rtype: Response
        """
        serializer = ProductCountSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        basket = get_basket(request)
        if not basket:
            return Response(
                {'non_field_errors': ['Basket not found']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        basket_id = basket.id.hex

        product_id = serializer.validated_data['id']
        product_count = serializer.validated_data['count']
        log.debug(
            'To delete %s of product %s from basket %s',
            product_count,
            product_id,
            basket_id,
        )

        if not basket_remove_products(basket_id, {product_id: product_count}):
            msg = 'Unable to delete product {} from basket {}'.format(
                product_id, basket_id
            )
            return Response(
                {'non_field_errors': [msg]}, status=status.HTTP_400_BAD_REQUEST
            )

        products = self._get_products(basket)
        return self._get_response(products, basket_id)


class OrdersView(APIView):
    """View for orders"""

    def get(self, request: Request, *args, **kwargs) -> Response:
        """
        Get orders of a user

        :param request: request
        :type request: Request
        :return: response
        :rtype: Response
        """
        user = request.user
        if user.is_anonymous:
            basket_id = get_basket_id_cookie(request)
            orders = (
                Order.objects.prefetch_related('products')
                .filter(basket_id=basket_id)
                .order_by('-created_at')
                .all()
            )
        else:
            orders = (
                Order.objects.prefetch_related('products')
                .filter(user=user)
                .order_by('-created_at')
                .all()
            )
        serializer = OrderSerializer(orders, many=True)
        log.debug('Got %s orders of user %s', len(serializer.data), user.id)

        return Response(serializer.data)

    def post(self, request: Request, *args, **kwargs) -> Response:
        """
        Create an order

        :param request: request
        :type request: Request
        :return: response
        :rtype: Response
        """
        if request.data == []:
            return Response(
                {'non_field_errors': ['Zero products provided']},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ProductCountSerializer(data=request.data, many=True)
        if not serializer.is_valid():
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        log.debug('validated product_counts: %s', serializer.validated_data)

        product_counts_dict = {
            item['id']: item['count'] for item in serializer.validated_data
        }
        order_created = False
        with transaction.atomic():
            if self._are_available(product_counts_dict):
                basket = get_basket(request)
                order = self._create_order(
                    product_counts_dict, request.user, basket
                )
                if basket:
                    basket_remove_products(basket.id, product_counts_dict)
                order_created = True

        if order_created:
            return Response({'orderId': order.id})
        else:
            return Response(
                {'count': ['Product quantities are not available']},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def _are_available(self, product_counts_dict: dict[str, int]) -> bool:
        """
        Check if all products are available

        :param product_counts_dict: product id and its count
        :type product_counts_dict: dict[str, int]
        :return: True if all products are available, False otherwise
        :rtype: bool
        """
        ids = set(product_counts_dict.keys())
        products = Product.objects.filter(id__in=ids, archived=False).all()
        ids_fetched = set(product.id for product in products)

        if ids_fetched != ids:
            return False

        for product in products:
            if product.count < product_counts_dict[product.id]:
                return False

        return True

    def _create_order(
        self,
        product_counts: dict[str, int],
        user: User,
        basket: Basket | None = None,
    ) -> Order:
        """
        Create an order with products. Needs to be always called from within a
        transaction.atomic block.

        :param product_counts: product id and its count
        :type product_counts: dict[str, int]
        :param user: order owner
        :type user: User
        :param basket: user's basket
        :type basket: Basket | None
        :return: order
        :rtype: Order
        """
        order = Order()
        if not user.is_anonymous:
            order.user = user
            order.full_name = user.get_full_name()
            order.phone = user.profile.phone or ''
            order.email = user.email or ''
        elif basket:
            order.basket = basket
        order.status = order.STATUS_NEW
        order.save()

        products = self._add_products(order.id, product_counts)

        order.total_cost = 0
        for product in products:
            order.total_cost += product.price * product_counts[product.id]
        order.save()

        return order

    def _add_products(
        self, order_id: int, product_counts: dict[int, int]
    ) -> list[Product]:
        """
        Add products to an empty order. Needs to be always called from within a
        transaction.atomic block. All products need to be available: not
        archived and have enough count.

        :param order_id: order id
        :type order_id: int
        :param product_counts: product id and its count
        :type product_counts: dict[int, int]
        :return: products
        :rtype: list[Product]
        """
        order_products = []
        for product_id, count in product_counts.items():
            order_product = OrderProduct(
                order_id=order_id, product_id=product_id, count=count
            )
            order_products.append(order_product)
        OrderProduct.objects.bulk_create(order_products)

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

        return products


class OrderView(APIView):
    """View for an order"""

    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, pk: int) -> Response:
        """
        Get an order by id

        :param request: request
        :type request: Request
        :param pk: order id
        :type pk: int
        :return: response
        :rtype: Response
        """
        order = get_object_or_404(
            Order, pk=pk, user=request.user, archived=False
        )
        order.save()
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def post(self, request: Request, pk: int) -> Response:
        """
        Modify an order by id

        :param request: request
        :type request: Request
        :param pk: order id
        :type pk: int
        :return: response
        :rtype: Response
        """
        order = get_object_or_404(
            Order, pk=pk, user=request.user, archived=False
        )

        # Only orders with status 'new' can be modified
        if order.status == Order.STATUS_PROCESSING:
            # Return order id instead of '' as defined in swagger.yaml
            return Response({'orderId': order.id})
        elif order.status != Order.STATUS_NEW:
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
        data['total_cost'] = order.total_cost + self._get_delivery_cost(
            order.id, data['delivery_type'], order.total_cost
        )
        serializer.save()

        # Return order id instead of '' as defined in swagger.yaml
        return Response({'orderId': order.id})

    def _get_delivery_cost(
        self, order_id: int, delivery_type: str, order_cost: decimal.Decimal
    ) -> decimal.Decimal:
        """
        Get delivery cost for an order

        :param order_id: order id
        :type order_id: int
        :param delivery_type: delivery type
        :type delivery_type: str
        :param order_cost: order cost
        :type order_cost: decimal.Decimal
        :return: delivery cost
        :rtype: decimal.Decimal
        """
        result = 0
        shop_confs = get_all_shop_configurations()
        if delivery_type == Order.DELIVERY_EXPRESS:
            result = shop_confs['express_delivery_price']
        elif delivery_type == Order.DELIVERY_ORDINARY:
            if self._is_delivery_free(order_id, delivery_type):
                result = 0
            elif order_cost < shop_confs['free_delivery_limit']:
                result = shop_confs['ordinary_delivery_price']
            else:
                result = 0

        return decimal.Decimal(result)

    def _is_delivery_free(self, order_id: int, delivery_type: str) -> bool:
        """
        Check if delivery is free for an order

        :param order_id: order id
        :type order_id: int
        :param delivery_type: delivery type
        :type delivery_type: str
        :return: True if delivery is free, False otherwise
        :rtype: bool
        """
        if delivery_type == Order.DELIVERY_ORDINARY:
            free_deliveries = (
                OrderProduct.objects.prefetch_related('product')
                .filter(order_id=order_id)
                .values_list('product__free_delivery')
            )
            return all(item[0] for item in free_deliveries)
        return False

from datetime import timedelta
from unittest.mock import Mock, patch

import pytest
from account.models import User
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from products.common import (
    can_access_basket,
    delete_old_orders,
    delete_order,
    delete_unused_baskets,
    fill_order_fields_if_needed,
    get_basket,
    get_basket_by_cookie,
    get_basket_by_user,
    get_basket_id,
    get_client_ip,
    update_basket_access_time,
)
from products.models import Basket, Order, Product
from products.views import OrdersView
from rest_framework.test import APIClient
from tests.common import is_date_almost_equal


@pytest.mark.django_db(transaction=True)
class TestCommon:
    @classmethod
    def setup_class(cls):
        cls.client = APIClient()

    @pytest.mark.parametrize(
        'expected, user, cookies, meta',
        [
            (None, None, {}, {}),
            ('60ac1520a1104db49090d934a0b9f8f9', 1, {}, {}),
            (
                None,
                None,
                {'basket_id': '60ac1520a1104db49090d934a0b9f8f9'},
                {'REMOTE_ADDR': '2.2.2.2'},
            ),
            (
                None,
                2,
                {'basket_id': '60ac1520a1104db49090d934a0b9f8f9'},
                {'REMOTE_ADDR': '2.2.2.2'},
            ),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_get_basket(self, db_data, expected, user, cookies, meta):
        request = Mock()
        request.user = None if user is None else User.objects.get(id=user)
        request.COOKIES = cookies
        request.META = meta
        if expected is None:
            assert get_basket(request) is None
        else:
            assert get_basket(request).id.hex == expected

    @pytest.mark.django_db(transaction=True)
    def test_get_basket_by_user(self, db_data):
        assert get_basket_by_user(None) is None
        assert get_basket_by_user(AnonymousUser) is None
        assert get_basket_by_user(
            User.objects.get(id=1)
        ) == Basket.objects.get(user_id=1)

    @pytest.mark.django_db(transaction=True)
    def test_get_basket_by_cookie(self, db_data):
        request = Mock()
        request.COOKIES = {'basket_id': '122423sfqaw23rf'}
        assert get_basket_by_cookie(request) is None

        basket = Basket.objects.get(user_id=1)
        request.COOKIES = {'basket_id': basket.id.hex}
        assert basket == get_basket_by_cookie(request)

    def test_get_basket_id(self):
        request = Mock()
        request.COOKIES = {'basket_id': '122423sfqaw23rf'}
        assert '122423sfqaw23rf' == get_basket_id(request)

    def test_get_client_ip(self):
        request = Mock()

        request.META = {'HTTP_X_FORWARDED_FOR': '1.1.1.1,2.2.2.2,3.3.3.3'}
        assert '1.1.1.1' == get_client_ip(request)

        request.META = {'REMOTE_ADDR': '2.2.2.2'}
        assert '2.2.2.2' == get_client_ip(request)

    @pytest.mark.django_db(transaction=True)
    def test_can_access_basket(self, db_data):
        data = [
            (True, Basket(), None),
            (True, Basket.objects.get(user_id=1), User.objects.get(id=1)),
            (False, Basket.objects.get(user_id=1), User.objects.get(id=2)),
        ]
        for expected, basket, user in data:
            assert expected == can_access_basket(basket, user)

    @pytest.mark.django_db(transaction=True)
    def test_update_basket_access_time(self):
        basket = Basket.objects.create()

        future_date = timezone.now() + timedelta(seconds=100)
        last_accessed = basket.last_accessed
        with patch('django.utils.timezone.now', return_value=future_date):
            update_basket_access_time(basket, 120)
            basket.refresh_from_db()
            assert basket.last_accessed == last_accessed

        future_date = timezone.now() + timedelta(seconds=150)
        with patch('django.utils.timezone.now', return_value=future_date):
            update_basket_access_time(basket, 120)
            basket.refresh_from_db()
            assert is_date_almost_equal(basket.last_accessed, future_date, 3)

    @pytest.mark.django_db(transaction=True)
    def test_delete_unused_baskets(self):
        future_date = timezone.now() + timedelta(seconds=100)
        for _ in range(10):
            Basket.objects.create(user=None)
        assert 10 == Basket.objects.filter(user=None).count()
        with patch('django.utils.timezone.now', return_value=future_date):
            delete_unused_baskets(90)
            assert 0 == Basket.objects.filter(user=None).count()

    @pytest.mark.django_db(transaction=True)
    def test_fill_order_fields_if_needed(self, db_data):
        order = Order()
        fill_order_fields_if_needed(order, User.objects.get(id=1))
        assert order.full_name == 'Nick'
        assert order.phone == '+712334361'
        assert order.email == 'kva@kva.com'

        user = User.objects.get(id=2)
        user.first_name = ''
        user.save()
        order = Order()
        fill_order_fields_if_needed(order, user)
        assert order.full_name == ''
        assert order.phone == ''
        assert order.email == ''

    @pytest.mark.django_db(transaction=True)
    def test_delete_old_orders(self, db_data):
        products = list(Product.objects.all())
        initial_counts = {}
        for product in products:
            product.count += 100
            initial_counts[product.id] = product.count
        Product.objects.bulk_update(products, fields=['count'])

        view = OrdersView()
        product_counts = {1: 2, 2: 3, 3: 1, 4: 2}
        basket = Basket.objects.create()
        for _ in range(10):
            view._create_order(product_counts, AnonymousUser, basket)

        orders = list(basket.order_set.all())
        assert len(orders) == 10
        assert all(
            is_date_almost_equal(order.created_at, timezone.now(), 3)
            for order in orders
        )

        orders = Order.objects.filter(basket=basket)
        new_created_at = timezone.now() - timedelta(seconds=2000)
        for order in orders:
            order.created_at = new_created_at
        Order.objects.bulk_update(orders, fields=['created_at'])

        orders = Order.objects.filter(basket=basket)
        assert all(
            is_date_almost_equal(order.created_at, new_created_at, 3)
            for order in orders
        )

        delete_old_orders()

        n_orders = Order.objects.filter(basket=basket).count()
        assert n_orders == 0

        products = list(Product.objects.all())
        initial_counts2 = {}
        for product in products:
            initial_counts2[product.id] = product.count
        assert initial_counts2 == initial_counts

        basket.delete()

    @pytest.mark.django_db(transaction=True)
    def test_delete_order(self, db_data):
        product_counts = {1: 2, 4: 1}
        view = OrdersView()
        basket = Basket.objects.create()

        initial_counts = self.get_product_counts(product_counts.keys())
        order = view._create_order(product_counts, AnonymousUser, basket)
        after_counts = self.get_product_counts(product_counts.keys())
        self.assert_product_counts_changed(
            initial_counts, product_counts, after_counts, False
        )

        order_id = order.id
        orders = list(basket.order_set.all())
        assert len(orders) == 1

        delete_order(order)

        assert not Order.objects.filter(id=order_id).exists()
        after_counts2 = self.get_product_counts(product_counts.keys())
        self.assert_product_counts_changed(
            after_counts, product_counts, after_counts2, True
        )

        basket.delete()

    def assert_product_counts_changed(
        self,
        prev_counts: dict[dict],
        counts: dict,
        after_counts: dict[dict],
        incremented: bool,
    ) -> bool:
        for id, after in after_counts.items():
            n_expected = counts[id]
            n_expected = n_expected if incremented else -n_expected
            prev = prev_counts[id]
            assert after['count'] - prev['count'] == n_expected
            assert prev['sold_count'] - after['sold_count'] == n_expected

    def get_product_counts(self, ids) -> dict:
        queryset = Product.objects.filter(id__in=ids).values(
            'id', 'count', 'sold_count'
        )
        result = {id: {'count': 0, 'sold_count': 0} for id in ids}
        for row in queryset:
            result[row['id']] = {
                'count': row['count'],
                'sold_count': row['sold_count'],
            }
        return result

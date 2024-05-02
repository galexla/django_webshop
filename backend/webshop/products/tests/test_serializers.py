import pytest
from django.http import Http404
from rest_framework.exceptions import ValidationError
from tests.common import (
    assert_dict_equal_exclude,
    assert_not_raises,
    camelcase_keys_to_underscore,
    slice_to_dict,
)
from tests.fixtures.products import (
    INVALID_EMAILS,
    INVALID_PHONES,
    MONITOR_SHORT_SRLZD,
    VALID_EMAILS,
    VALID_PHONES,
)

from ..models import Order, Review
from ..serializers import (
    BasketIdSerializer,
    OrderSerializer,
    ProductCountSerializer,
    ReviewCreateSerializer,
)


class TestReviewCreateSerializer:
    base_ok_data = {
        'author': 'Nick',
        'email': 'test@test.com',
        'text': 'text',
        'rate': 5,
    }

    @pytest.mark.parametrize(
        'is_valid, field, values',
        [
            (False, 'author', [None, '', 'a' * 201]),
            (True, 'author', ['a' * 200]),
            (False, 'email', [None, ''] + INVALID_EMAILS),
            (True, 'email', VALID_EMAILS),
            (False, 'text', [None, '', 'a' * 2001]),
            (True, 'text', ['a' * 2000]),
            (False, 'rate', [0, 6, 0.1, 'a']),
            (True, 'rate', [1, 5]),
        ],
    )
    def test_fields(self, is_valid, field, values):
        for value in values:
            data = self.base_ok_data.copy()
            data[field] = value
            if value is None:
                data.pop(field, None)
            serializer = ReviewCreateSerializer(data=data)
            valid_str = 'valid' if is_valid else 'invalid'
            assert (
                serializer.is_valid() == is_valid
            ), 'Data should be {} for field {} = {}'.format(
                valid_str, field, value
            )

    @pytest.mark.django_db(transaction=True)
    def test_save(self, db_data):
        serializer = ReviewCreateSerializer(data=self.base_ok_data)
        assert serializer.is_valid()
        with pytest.raises(Http404):
            serializer.save(20)
        assert serializer.instance is None

        serializer = ReviewCreateSerializer(data=self.base_ok_data)
        assert serializer.is_valid()
        with assert_not_raises(Http404):
            serializer.save(2)
        serializer.instance.refresh_from_db()
        review = Review.objects.get(id=serializer.instance.id)
        data = review.__dict__
        assert_dict_equal_exclude(
            data,
            self.base_ok_data,
            ['_state', 'id', 'product_id', 'created_at'],
        )


class TestProductCountSerializer:
    @pytest.mark.parametrize(
        'is_valid, value',
        [
            (False, {'count': 1}),
            (False, {'id': 1}),
            (False, {'id': 1, 'count': 0}),
            (True, {'id': 1, 'count': 1}),
            (True, {'id': 1000000, 'count': 1000000}),
        ],
    )
    def test_fields(self, is_valid, value):
        serializer = ProductCountSerializer(data=value)
        assert serializer.is_valid() == is_valid


class TestBasketIdSerializer:
    @pytest.mark.parametrize(
        'is_valid, value',
        [
            (True, 'fabc8c6c-0f0b-47c2-a5d2-8981fba5fa8a'),
            (True, 'fabc8c6c0f0b47c2a5d28981fba5fa8a'),
            (False, 'fabc8c6c0f0b47c2a5d28981fba5fa8'),
            (False, 'fabc8c6c-0f0b-47c2-a5d2-8981fba5fa8a2'),
            (False, 'fabc8c6c-0f0b-47c2-a5d2-8981fba5fa8x'),
            (False, ''),
            (False, 'abc'),
        ],
    )
    def test_fields(self, is_valid, value):
        serializer = BasketIdSerializer(data={'basket_id': value})
        assert serializer.is_valid() == is_valid


class TestOrderSerializer:
    base_ok_data = {
        'fullName': 'Nick',
        'email': 'test@test.com',
        'phone': '+712334361',
        'deliveryType': Order.DELIVERY_ORDINARY,
        'paymentType': Order.PAYMENT_SOMEONE,
        'totalCost': 0,
        'city': 'Moscow',
        'address': 'Sretensky blvd 1',
    }
    base_ok_data_undscr = camelcase_keys_to_underscore(base_ok_data)

    @pytest.mark.parametrize(
        'is_valid, field, values',
        [
            (False, 'fullName', ['a' * 121]),
            (True, 'fullName', ['a' * 120]),
            (False, 'email', INVALID_EMAILS),
            (True, 'email', VALID_EMAILS),
            (False, 'phone', INVALID_PHONES),
            (True, 'phone', VALID_PHONES),
            (False, 'deliveryType', ['asdsf', '123']),
            (
                True,
                'deliveryType',
                [Order.DELIVERY_ORDINARY, Order.DELIVERY_EXPRESS],
            ),
            (False, 'paymentType', ['asdsf', '123']),
            (
                True,
                'paymentType',
                [Order.PAYMENT_ONLINE, Order.PAYMENT_SOMEONE],
            ),
            (False, 'totalCost', ['asdsf', -1, -100, 100000000]),
            (True, 'totalCost', ['0', 0, 123, 100, 99999999.99]),
            (False, 'city', ['a' * 151]),
            (True, 'city', ['a' * 150]),
            (False, 'address', ['a' * 301]),
            (True, 'address', ['a' * 300]),
        ],
    )
    def test_fields(self, is_valid: bool, field: str, values: list):
        statuses = [
            Order.STATUS_PROCESSING,
            Order.STATUS_PAID,
            Order.STATUS_NEW,
        ]
        values_w_none_empty = values.copy()
        values_w_none_empty.extend([None, ''])
        values_w_empty = values.copy()
        values_w_empty.extend([''])

        for status in statuses:
            values_to_loop = values
            if (
                status in (Order.STATUS_PROCESSING, Order.STATUS_PAID)
                and not is_valid
            ):
                values_to_loop = values_w_none_empty
            elif status == Order.STATUS_NEW and is_valid:
                if field not in ['totalCost', 'fullName']:
                    values_to_loop = values_w_empty

            for value in values_to_loop:
                data = self.base_ok_data.copy()
                data['status'] = status
                data[field] = value
                if value is None:
                    data.pop(field, None)

                serializer = OrderSerializer(data=data)
                valid_str = 'valid' if is_valid else 'invalid'
                assert (
                    serializer.is_valid() == is_valid
                ), 'Data should be {} for status {} and field {} = {}'.format(
                    valid_str, status, field, value
                )

    def test_status(self):
        statuses = ['ddsghd', '443']
        for status in statuses:
            data = self.base_ok_data.copy()
            data['status'] = status
            serializer = OrderSerializer(data=data)
            assert (
                not serializer.is_valid()
            ), f'Data should be invalid for status {status}'

    @pytest.mark.parametrize(
        'is_valid, status, field, values',
        [
            (True, Order.STATUS_NEW, 'full_name', [None, '', '  ']),
            (True, Order.STATUS_NEW, 'email', [None, '', '  ']),
            (True, Order.STATUS_NEW, 'phone', [None, '', '  ']),
            (True, Order.STATUS_NEW, 'delivery_type', [None, '', '  ']),
            (True, Order.STATUS_NEW, 'payment_type', [None, '', '  ']),
            (True, Order.STATUS_NEW, 'city', [None, '', '  ', 'abc']),
            (True, Order.STATUS_NEW, 'address', [None, '', '  ', 'abc']),
            (False, Order.STATUS_PROCESSING, 'full_name', [None, '', '  ']),
            (True, Order.STATUS_PROCESSING, 'full_name', ['abc']),
            (False, Order.STATUS_PROCESSING, 'email', [None, '', '  ']),
            (True, Order.STATUS_PROCESSING, 'email', ['abc@abc.com']),
            (False, Order.STATUS_PROCESSING, 'phone', [None, '', '  ']),
            (True, Order.STATUS_PROCESSING, 'phone', ['+1234567']),
            (
                False,
                Order.STATUS_PROCESSING,
                'delivery_type',
                [None, '', '  '],
            ),
            (
                True,
                Order.STATUS_PROCESSING,
                'delivery_type',
                [Order.DELIVERY_EXPRESS],
            ),
            (False, Order.STATUS_PROCESSING, 'payment_type', [None, '', '  ']),
            (
                True,
                Order.STATUS_PROCESSING,
                'payment_type',
                [Order.PAYMENT_SOMEONE],
            ),
            (False, Order.STATUS_PROCESSING, 'city', [None, '', '  ']),
            (True, Order.STATUS_PROCESSING, 'city', ['abc']),
            (False, Order.STATUS_PROCESSING, 'address', [None, '', '  ']),
            (True, Order.STATUS_PROCESSING, 'address', ['abc']),
        ],
    )
    def test_validate(self, is_valid, status, field, values):
        for value in values:
            data = self.base_ok_data_undscr.copy()
            data['status'] = status
            data[field] = value
            if value is None:
                data.pop(field, None)

            serializer = OrderSerializer()
            exception_raised = False
            try:
                serializer.validate(data)
            except ValidationError:
                exception_raised = True

            if not is_valid and not exception_raised:
                msg = 'Exception not raised for status {}, field {} = {}'
                assert False, msg.format(data['status'], field, value)
            elif is_valid and exception_raised:
                msg = 'Raised exception for status {}, field {} = {}'
                assert False, msg.format(data['status'], field, value)

    @pytest.mark.parametrize(
        'order_id, expected_result',
        [
            (3, {3: {'id': 3, 'count': 1}, 4: {'id': 4, 'count': 2}}),
            (
                2,
                {
                    3: {'id': 3, 'count': 1},
                    4: {'id': 4, 'count': 2},
                    2: {'id': 2, 'count': 1},
                },
            ),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_get_products(self, db_data, order_id, expected_result):
        order = Order.objects.get(id=order_id)
        serializer = OrderSerializer()
        products = serializer.get_products(order)
        product_counts = slice_to_dict(products, ['id', 'count'], 'id')
        assert product_counts == expected_result

    @pytest.mark.django_db(transaction=True)
    def test_get_product_fields(self, db_data):
        order = Order.objects.get(id=3)
        serializer = OrderSerializer()
        products = serializer.get_products(order)
        found_product = None
        for product in products:
            if product['id'] == MONITOR_SHORT_SRLZD['id']:
                found_product = product
                break
        assert found_product is not None
        assert found_product == MONITOR_SHORT_SRLZD

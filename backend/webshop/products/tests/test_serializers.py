import re
from typing import Any

import pytest
from rest_framework.exceptions import ValidationError

from ..models import Order
from ..serializers import OrderSerializer


def assert_dict_equal_excl(dict1, dict2, exclude_keys):
    dict1 = dict1.copy()
    dict2 = dict2.copy()
    for key in exclude_keys:
        dict1.pop(key, None)
        dict2.pop(key, None)
    assert dict1 == dict2, f'Dict {dict1} should be equal to {dict2}'


def camelcase_keys_to_underscore(d: dict[str, Any]):
    result = {}
    for key, value in d.items():
        key2 = re.sub(r'([A-Z])', r'_\1', key).lower()
        result[key2] = value
    return result


class TestOrderSerializer:
    base_ok_data = {
        'fullName': 'Nick',
        'email': 'kva@kva.com',
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
            (
                False,
                'email',
                [
                    'a@' + 'a' * 260 + '.com',
                    'test',
                    'test@test',
                    '.test@test.com',
                ],
            ),
            (True, 'email', ['test@test.com', 'a@a.com']),
            (False, 'phone', ['+' + '1' * 32, '+1234', '1234567']),
            (
                True,
                'phone',
                ['+' + '1' * 31, '+12345', '+1234567'],
            ),
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
    def test_valid_invalid_values(
        self, is_valid: bool, field: str, values: list
    ):
        statuses = [Order.STATUS_PROCESSING, Order.STATUS_NEW]
        values_w_none_empty = values.copy()
        values_w_none_empty.extend([None, ''])
        values_w_empty = values.copy()
        values_w_empty.extend([''])

        for status in statuses:
            values_to_loop = values
            if status == Order.STATUS_PROCESSING and not is_valid:
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
                serializer.is_valid() == False
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
    def test_valid_new_order(self, is_valid, status, field, values):
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

import pytest

from ..models import Order
from ..serializers import OrderSerializer


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

    @pytest.mark.parametrize(
        'is_valid, field, values',
        [
            (False, 'fullName', ['a' * 121]),
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
            (False, 'phone', ['+' + '1' * 32, '+1234', '1234567']),
            (False, 'deliveryType', ['asdsf', '123']),
            (False, 'paymentType', []),
            (False, 'totalCost', ['asdsf', -1, -100, 100000000]),
            (False, 'city', ['a' * 151]),
            (False, 'address', ['a' * 301]),
            (True, 'fullName', ['a' * 120]),
            (True, 'email', ['test@test.com', 'a@a.com']),
            (
                True,
                'phone',
                ['+' + '1' * 31, '+12345', '+1234567'],
            ),
            (
                True,
                'deliveryType',
                [Order.DELIVERY_ORDINARY, Order.DELIVERY_EXPRESS],
            ),
            (
                True,
                'paymentType',
                [Order.PAYMENT_ONLINE, Order.PAYMENT_SOMEONE],
            ),
            (True, 'totalCost', ['0', 0, 123, 100, 99999999.99]),
            (True, 'city', ['a' * 150]),
            (True, 'address', ['a' * 300]),
        ],
    )
    def test_invalid_values(self, is_valid: bool, field: str, values: list):
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

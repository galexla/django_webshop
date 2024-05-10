from decimal import Decimal

import pytest
from django.utils import timezone
from tests.common import get_not_equal_values, is_date_almost_equal

from ..serializers import PaymentSerializer


class TestPaymentSerializer:
    base_ok_data = {
        'order_id': 3,
        'number': 142384,
        'name': 'JOHN SMITH',
        'paid_sum': Decimal(1000),
    }

    @pytest.mark.parametrize(
        'should_be_ok, field, values',
        [
            # 20, 2
            # 3
            (False, 'order_id', [None, -1, '', 'abc']),
            (True, 'order_id', [1, 3]),
            (False, 'number', [None, '', 'abc', -1, 0, 999_999_999]),
            (True, 'number', [99_999_999]),
            (False, 'name', [None, '', 'a' * 256]),
            (True, 'name', ['a', 'a' * 255]),
            (
                False,
                'paid_sum',
                ['', 'abc', -1, 100000000, Decimal('99999999.999')],
            ),
            (
                True,
                'paid_sum',
                [Decimal('0.99'), 0, 1, 99999999, Decimal('99999999.99')],
            ),
        ],
    )
    def test_fields(self, should_be_ok, field, values):
        for value in values:
            data = self.base_ok_data.copy()
            data[field] = value
            if value is None:
                data.pop(field, None)
            serializer = PaymentSerializer(data=data)
            valid_str = 'valid' if should_be_ok else 'invalid'
            assert (
                serializer.is_valid() == should_be_ok
            ), 'Data should be {} for field {} = {}, errors: {}'.format(
                valid_str, field, value, serializer.errors
            )

    @pytest.mark.django_db(transaction=True)
    def test_create(self, db_data):
        data = self.base_ok_data.copy()
        data['order_id'] = 3
        data['paid_at'] = '2024-01-01T01:30:00.823000Z'
        serializer = PaymentSerializer(data=data)
        assert serializer.is_valid()

        instance = serializer.create(serializer.validated_data)
        instance.refresh_from_db()
        data['card_number'] = data.pop('number')
        data.pop('paid_at')
        not_equal_fields = get_not_equal_values(instance, data)
        assert all(
            data[k] == getattr(instance, k) for k in data
        ), 'All fields should be equal, not equal: {}'.format(not_equal_fields)
        assert is_date_almost_equal(timezone.now(), instance.paid_at, 3)

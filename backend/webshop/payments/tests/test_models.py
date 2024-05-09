from datetime import datetime
from decimal import Decimal

import pytest
from tests.common import AbstractModelTest

from ..models import Payment


class TestPayment(AbstractModelTest):
    model = Payment
    base_ok_data = {
        'order_id': 3,
        'card_number': 142384,
        'name': 'JOHN SMITH',
        'paid_sum': 1000,
    }

    @pytest.mark.parametrize(
        'should_be_ok, field, values',
        [
            (False, 'order_id', [None, 20, -1, 2, '', 'abc']),
            (True, 'order_id', [3]),
            (False, 'card_number', [None, '', 'abc', -1, 0, 999_999_999]),
            (True, 'card_number', [99_999_999]),
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
            (False, 'paid_at', ['', 'abc', 1]),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_fields(self, db_data, should_be_ok, field, values):
        super().fields_test(db_data, should_be_ok, field, values)

    @pytest.mark.parametrize(
        'expected, field, values',
        [
            (
                'now',
                'paid_at',
                [
                    None,
                    '',
                    datetime.fromisoformat('2024-01-30T15:30:48.823000Z'),
                ],
            ),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_field_defaults(self, db_data, expected, field, values):
        super().field_defaults_test(db_data, expected, field, values)

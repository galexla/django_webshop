from account.models import User
from webshop.common import SerializerTestCase

from ..models import Order
from ..serializers import OrderSerializer


class OrderSerializerTest(SerializerTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.user = User.objects.create(username='test2', password='test')

    @classmethod
    def tearDownClass(cls) -> None:
        cls.user.delete()

    def test_fields(self):
        ok_data = {
            'fullName': 'Nick',
            'email': 'kva@kva.com',
            'phone': '+712334361',
            'deliveryType': Order.DELIVERY_ORDINARY,
            'paymentType': Order.PAYMENT_SOMEONE,
            'status': Order.STATUS_PROCESSING,
            'totalCost': 0,
            'city': 'Moscow',
            'address': 'Sretensky blvd 1',
        }

        self.assert_all_invalid(
            OrderSerializer, ok_data, 'fullName', [None, '', 'a' * 121]
        )
        self.assert_all_valid(
            OrderSerializer, ok_data, 'fullName', ['a' * 120]
        )

        self.assert_all_invalid(
            OrderSerializer,
            ok_data,
            'email',
            [
                None,
                '',
                'a@' + 'a' * 260 + '.com',
                'test',
                'test@test',
                '.test@test.com',
            ],
        )
        self.assert_all_valid(
            OrderSerializer,
            ok_data,
            'email',
            ['test@test.com', 'a@a.com'],
        )

        self.assert_all_invalid(
            OrderSerializer,
            ok_data,
            'phone',
            [None, '', '+' + '1' * 32, '+1234', '1234567'],
        )
        self.assert_all_valid(
            OrderSerializer,
            ok_data,
            'phone',
            ['+' + '1' * 31, '+12345', '+1234567'],
        )

        self.assert_all_invalid(
            OrderSerializer,
            ok_data,
            'deliveryType',
            [None, '', 'asdsf', '123'],
        )
        self.assert_all_valid(
            OrderSerializer,
            ok_data,
            'deliveryType',
            [Order.DELIVERY_ORDINARY, Order.DELIVERY_EXPRESS],
        )

        self.assert_all_invalid(
            OrderSerializer,
            ok_data,
            'paymentType',
            [None, '', 'asdsf', '123'],
        )
        self.assert_all_valid(
            OrderSerializer,
            ok_data,
            'paymentType',
            [Order.PAYMENT_ONLINE, Order.PAYMENT_SOMEONE],
        )

        # self.assert_all_invalid(
        #     OrderSerializer,
        #     ok_data,
        #     'status',
        #     [None, '', 'asdsf', '123'],
        # )
        # self.assert_all_valid(
        #     OrderSerializer,
        #     ok_data,
        #     'status',
        #     [Order.STATUS_NEW, Order.STATUS_PROCESSING, Order.STATUS_PAID],
        # )

        # self.assert_all_invalid(
        #     OrderSerializer,
        #     ok_data,
        #     'totalCost',
        #     [None, '', 'asdsf', '123', -1, -100, 100000000],
        # )
        # self.assert_all_valid(
        #     OrderSerializer,
        #     ok_data,
        #     'totalCost',
        #     ['0', 0, 123, 100, 99999999.99],
        # )

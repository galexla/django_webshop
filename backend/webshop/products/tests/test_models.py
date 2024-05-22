from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from django.core.files.images import ImageFile
from django.core.files.storage import default_storage
from django.forms import ValidationError
from django.utils import timezone
from tests.common import AbstractModelTest, RandomImage
from tests.fixtures.products import (
    INVALID_EMAILS,
    INVALID_PHONES,
    MONITOR_DETAIL_SRLZD,
    VALID_EMAILS,
    VALID_PHONES,
)

from ..models import (
    Basket,
    BasketProduct,
    Category,
    Order,
    OrderProduct,
    Product,
    ProductImage,
    Review,
    Sale,
    Specification,
    Tag,
    get_products_queryset,
    product_image_upload_path,
)
from ..serializers import ProductDetailSerializer


class TestTag(AbstractModelTest):
    model = Tag
    base_ok_data = {
        'name': 'test',
    }

    @pytest.mark.parametrize(
        'should_be_ok, field, values',
        [
            (False, 'name', [None, '', 'a' * 101]),
            (True, 'name', ['a' * 100]),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_fields(self, db_data, should_be_ok, field, values):
        super().fields_test(db_data, should_be_ok, field, values)

    @pytest.mark.django_db(transaction=True)
    def test__str__(self, db_data):
        instance = Tag.objects.get(id=1)
        assert str(instance) == 'Tag1'


class TestSpecification(AbstractModelTest):
    model = Specification
    base_ok_data = {
        'name': 'test',
        'value': 'test',
    }

    @pytest.mark.parametrize(
        'should_be_ok, field, values',
        [
            (False, 'name', [None, '', 'a' * 201]),
            (True, 'name', ['a' * 200]),
            (False, 'value', [None, '', 'a' * 201]),
            (True, 'value', ['a' * 200]),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_fields(self, db_data, should_be_ok, field, values):
        super().fields_test(db_data, should_be_ok, field, values)

    @pytest.mark.django_db(transaction=True)
    def test__str__(self, db_data):
        instance = Specification.objects.get(id=1)
        assert str(instance) == 'Screen diagonal: 17"'


class TestCategory(AbstractModelTest):
    model = Category
    base_ok_data = {
        'title': 'test',
        'parent_id': 1,
        'image': '',
        'image_alt': '',
        'archived': False,
    }

    @pytest.mark.parametrize(
        'should_be_ok, field, values',
        [
            (False, 'title', [None, '', 'a' * 201]),
            (True, 'title', ['a' * 200]),
            (False, 'parent_id', [20, 3, '']),
            (True, 'parent_id', [None, 1]),
            (False, 'image', [123]),
            (True, 'image', ['', 'file.png']),
            (False, 'image_alt', ['a' * 201]),
            (True, 'image_alt', ['', 'a' * 200]),
            (False, 'archived', ['', 'a', 4]),
            (True, 'archived', [True, False]),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_fields(self, db_data, should_be_ok, field, values):
        super().fields_test(db_data, should_be_ok, field, values)

    @pytest.mark.django_db(transaction=True)
    def test_clean(self, db_data):
        instance = Category.objects.get(id=1)
        instance.parent_id = 1
        with pytest.raises(ValidationError) as exc_info:
            instance.full_clean()
            instance.save()

        instance = Category.objects.get(id=2)
        instance.parent_id = 3
        with pytest.raises(ValidationError) as exc_info:
            instance.full_clean()
            instance.save()

        instance = Category.objects.get(id=3)
        instance.subcategories.add(Category.objects.create(title='test'))
        with pytest.raises(ValidationError) as exc_info:
            instance.full_clean()
            instance.save()

    @pytest.mark.django_db(transaction=True)
    def test__str__(self, db_data):
        instance = Category.objects.get(id=1)
        assert (
            str(instance) == 'Phones, tablets, laptops and portable equipment'
        )

    @pytest.mark.parametrize(
        'expected, field, values',
        [
            ('', 'image', [None]),
            ('', 'image_alt', [None]),
            (False, 'archived', [None]),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_field_defaults(self, db_data, expected, field, values):
        super().field_defaults_test(db_data, expected, field, values)


class TestProduct(AbstractModelTest):
    model = Product
    base_ok_data = {
        'title': 'Monitor',
        'price': Decimal('490.00'),
        'category_id': 4,
        'count': 2,
        'sold_count': 4,
        'description': 'Maecenas',
        'full_description': 'Maecenas in nisi',
        'free_delivery': False,
        'is_limited_edition': True,
        'is_banner': True,
        'rating': Decimal('4.0'),
        'archived': False,
    }

    @pytest.mark.parametrize(
        'should_be_ok, field, values',
        [
            (False, 'title', [None, '', 'a' * 201]),
            (True, 'title', ['a' * 200]),
            (False, 'price', ['', 'abc', -1, 1000000, Decimal('999999.999')]),
            (
                True,
                'price',
                [Decimal('0.99'), 0, 1, 999999, Decimal('999999.99')],
            ),
            (False, 'category_id', [20, -1, '', 'abc']),
            (True, 'category_id', [None, 1, 3]),
            (False, 'count', ['', 'abc', -1]),
            (True, 'count', [0, 200, 1000000]),
            (False, 'sold_count', ['', 'abc', -1]),
            (True, 'sold_count', [0, 200, 1000000]),
            (False, 'description', ['a' * 3001]),
            (True, 'description', [None, '', 'a' * 3000]),
            (False, 'full_description', ['a' * 20001]),
            (True, 'full_description', [None, '', 'a' * 20000]),
            (False, 'free_delivery', ['', 'abc']),
            (True, 'free_delivery', [True, False, 1, 0]),
            (False, 'is_limited_edition', ['', 'abc']),
            (True, 'is_limited_edition', [True, False, 1, 0]),
            (False, 'is_banner', ['', 'abc']),
            (True, 'is_banner', [True, False, 1, 0]),
            (False, 'rating', ['', 'abc', -1, 0, 6, '3.2']),
            (True, 'rating', [1, 5, 4.5]),
            (False, 'archived', ['', 'abc']),
            (True, 'archived', [True, False, 1, 0]),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_fields(self, db_data, should_be_ok, field, values):
        super().fields_test(db_data, should_be_ok, field, values)

    @pytest.mark.parametrize(
        'expected, field, values',
        [
            (0, 'count', [None]),
            (0, 'sold_count', [None]),
            (False, 'free_delivery', [None]),
            (False, 'is_limited_edition', [None]),
            (False, 'is_banner', [None]),
            (False, 'archived', [None]),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_field_defaults(self, db_data, expected, field, values):
        super().field_defaults_test(db_data, expected, field, values)

    @pytest.mark.django_db(transaction=True)
    def test_created_at(self, db_data):
        for value in None, '', '2024-01-30T15:30:48.823000Z':
            instance, _, _, valid_and_saved, _ = self.create_instance(
                'created_at', value
            )
            assert valid_and_saved
            assert instance.created_at - timezone.now() <= timedelta(seconds=3)

    @pytest.mark.django_db(transaction=True)
    def test_tags(self, db_data):
        instance, _, _, valid_and_saved, _ = self.create_instance('count', 3)
        assert valid_and_saved
        instance.tags.add(Tag.objects.create(name='test1'))
        instance.tags.add(Tag.objects.create(name='test2'))
        instance.refresh_from_db()
        assert instance.tags.all().count() == 2
        assert list(instance.tags.all().values('name')) == [
            {'name': 'test1'},
            {'name': 'test2'},
        ]

    @pytest.mark.django_db(transaction=True)
    def test_specifications(self, db_data):
        instance, _, _, valid_and_saved, _ = self.create_instance('count', 3)
        assert valid_and_saved
        instance.specifications.add(
            Specification.objects.create(name='test1', value='a')
        )
        instance.specifications.add(
            Specification.objects.create(name='test2', value='b')
        )
        instance.refresh_from_db()
        assert instance.specifications.all().count() == 2
        assert list(instance.specifications.all().values('name', 'value')) == [
            {'name': 'test1', 'value': 'a'},
            {'name': 'test2', 'value': 'b'},
        ]

    @pytest.mark.django_db(transaction=True)
    def test_images(self, db_data):
        instance, _, _, valid_and_saved, _ = self.create_instance('count', 3)
        assert valid_and_saved
        rand_image = RandomImage(40 * 40)
        image_bytes = rand_image.get_bytes(size=(100, 100), format='jpeg')

        image1 = ProductImage(
            product_id=instance.id,
            image=ImageFile(image_bytes, name='test1.jpg'),
        )
        image1.save()
        instance.images.add(image1)

        image2 = ProductImage(
            product_id=instance.id,
            image=ImageFile(image_bytes, name='test2.jpg'),
        )
        image2.save()
        instance.images.add(image2)

        instance.refresh_from_db()
        assert instance.images.all().count() == 2

        file_data = default_storage.open(
            instance.images.all()[0].image.path
        ).read()
        assert file_data == image_bytes.getvalue()

        file_data = default_storage.open(
            instance.images.all()[1].image.path
        ).read()
        assert file_data == image_bytes.getvalue()


class TestProductImage(AbstractModelTest):
    model = ProductImage
    base_ok_data = {
        'product_id': 1,
        'image_alt': '',
    }

    @classmethod
    def setup_class(cls):
        cls.rand_image = RandomImage(20 * 20)

    @pytest.mark.parametrize(
        'should_be_ok, field, values',
        [
            (False, 'product_id', [None, '', 20]),
            (True, 'product_id', [1, 4]),
            (False, 'image_alt', ['a' * 201]),
            (True, 'image_alt', ['', 'a' * 200]),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_fields(self, db_data, should_be_ok, field, values):
        super().fields_test(db_data, should_be_ok, field, values)

    @pytest.mark.parametrize(
        'expected, field, values',
        [
            ('', 'image_alt', [None]),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_field_defaults(self, db_data, expected, field, values):
        super().field_defaults_test(db_data, expected, field, values)

    @pytest.mark.django_db(transaction=True)
    def test_image(self, db_data):
        image_bytes = self.rand_image.get_bytes(size=(100, 100), format='jpeg')
        image = ProductImage(
            product_id=1,
            image=ImageFile(image_bytes, name='test2.jpg'),
        )
        image.save()
        image.refresh_from_db()
        file_data = default_storage.open(image.image.path).read()
        assert file_data == image_bytes.getvalue()


@pytest.mark.django_db(transaction=True)
def test_product_image_upload_path(db_data):
    rand_image = RandomImage(10 * 10)
    image_bytes = rand_image.get_bytes(size=(100, 100), format='png')
    image = ProductImage(
        product_id=1,
        image=ImageFile(image_bytes, name='test.png'),
    )
    path = product_image_upload_path(image, 'test.png')
    assert path == 'products/product1/images/test.png'


@pytest.mark.django_db(transaction=True)
def test_get_products_queryset(db_data):
    queryset = get_products_queryset()
    monitor = queryset.filter(id=4)[0]
    serializer = ProductDetailSerializer(monitor)
    data = serializer.data
    data.pop('fullDescription')
    assert data == MONITOR_DETAIL_SRLZD


class TestSale(AbstractModelTest):
    model = Sale
    base_ok_data = {
        'product_id': 1,
        'date_from': datetime.fromisoformat('2024-01-30T15:30:48.823000Z'),
        'date_to': datetime.fromisoformat('2024-03-30T15:30:48.823000Z'),
        'sale_price': Decimal('400.00'),
    }

    @pytest.mark.parametrize(
        'should_be_ok, field, values',
        [
            (False, 'product_id', [None, 20, -1, '', 'abc']),
            (True, 'product_id', [1, 3]),
            (False, 'date_from', [None, '', 'abc', 1]),
            (
                True,
                'date_from',
                [datetime.fromisoformat('2024-01-30T15:30:48.823000Z')],
            ),
            (False, 'date_to', [None, '', 'abc', 1]),
            (
                True,
                'date_to',
                [datetime.fromisoformat('2024-03-30T15:30:48.823000Z')],
            ),
            (
                False,
                'sale_price',
                [None, '', 'abc', -1, 1000000, Decimal('999999.999')],
            ),
            (
                True,
                'sale_price',
                [Decimal('0.99'), 0, 1, 999999, Decimal('999999.99')],
            ),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_fields(self, db_data, should_be_ok, field, values):
        super().fields_test(db_data, should_be_ok, field, values)


class TestReview(AbstractModelTest):
    model = Review
    base_ok_data = {
        'product_id': 1,
        'author': 'Name',
        'email': 'test@test.com',
        'text': 'text',
        'rate': 4,
    }

    @pytest.mark.parametrize(
        'should_be_ok, field, values',
        [
            (False, 'product_id', [None, 20, -1, '', 'abc']),
            (True, 'product_id', [1, 3]),
            (False, 'author', [None, '', 'a' * 201]),
            (True, 'author', ['a' * 200]),
            (False, 'email', [None, ''] + INVALID_EMAILS),
            (True, 'email', VALID_EMAILS),
            (False, 'text', [None, '', 'a' * 2001]),
            (True, 'text', ['a' * 2000]),
            (False, 'rate', ['', 'abc', -1, 0, 6, 3.2]),
            (True, 'rate', [1, 5, 4]),
            (False, 'created_at', ['', 'abc', 1]),
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
                'created_at',
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


class TestBasketProduct(AbstractModelTest):
    model = BasketProduct
    base_ok_data = {
        'product_id': 1,
        'basket_id': UUID('60ac1520a1104db49090d934a0b9f8f9'),
        'count': 3,
    }

    @pytest.mark.parametrize(
        'should_be_ok, field, values',
        [
            (False, 'product_id', [None, 3, 4, 20, -1, '', 'abc']),
            (True, 'product_id', [1, 2]),
            (
                False,
                'basket_id',
                [None, '', 'a' * 20, UUID('db49090d934a0b9f8f960ac1520a1104')],
            ),
            (True, 'basket_id', [UUID('60ac1520a1104db49090d934a0b9f8f9')]),
            (False, 'count', ['', 'abc', -1, 0, 3.2]),
            (True, 'count', [1, 5, 4]),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_fields(self, db_data, should_be_ok, field, values):
        super().fields_test(db_data, should_be_ok, field, values)


class TestBasket(AbstractModelTest):
    model = Basket
    base_ok_data = {
        'user_id': 2,
    }

    @pytest.mark.parametrize(
        'should_be_ok, field, values',
        [
            (False, 'user_id', [20, -1, 1, '', 'abc']),
            (True, 'user_id', [None, 2]),
            (False, 'last_accessed', ['', 'abc', 1]),
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
                'last_accessed',
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


class TestOrderProduct(AbstractModelTest):
    model = OrderProduct
    base_ok_data = {
        'product_id': 1,
        'order_id': 2,
        'count': 3,
    }

    @pytest.mark.parametrize(
        'should_be_ok, field, values',
        [
            (False, 'product_id', [None, 2, 3, 4, 20, -1, '', 'abc']),
            (True, 'product_id', [1]),
            (
                False,
                'order_id',
                [None, '', 'a' * 20, 30],
            ),
            (True, 'order_id', [2, 3]),
            (False, 'count', ['', 'abc', -1, 0, 3.2]),
            (True, 'count', [1, 5, 4]),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_fields(self, db_data, should_be_ok, field, values):
        super().fields_test(db_data, should_be_ok, field, values)


class TestOrder(AbstractModelTest):
    model = Order
    base_ok_data = {
        'user_id': 1,
        'full_name': 'test test',
        'email': 'test@test.com',
        'phone': '+123456789',
        'delivery_type': Order.DELIVERY_ORDINARY,
        'payment_type': Order.PAYMENT_ONLINE,
        'total_cost': Decimal('1000.00'),
        'status': Order.STATUS_NEW,
        'city': 'test',
        'address': 'test',
        'archived': False,
    }

    @pytest.mark.parametrize(
        'should_be_ok, field, values',
        [
            (False, 'user_id', [20, -1, '', 'abc']),
            (True, 'user_id', [None, 1, 2]),
            (False, 'basket_id', ['abc']),
            (
                True,
                'basket_id',
                [None, UUID('60ac1520a1104db49090d934a0b9f8f9')],
            ),
            (False, 'created_at', ['', 'abc', 1]),
            (False, 'full_name', ['a' * 121]),
            (True, 'full_name', [None, '', 'a' * 120]),
            (False, 'email', INVALID_EMAILS),
            (True, 'email', [None, ''] + VALID_EMAILS),
            (False, 'phone', INVALID_PHONES),
            (True, 'phone', [None, ''] + VALID_PHONES),
            (False, 'delivery_type', ['asdsf', '123']),
            (
                True,
                'delivery_type',
                [None, '', Order.DELIVERY_ORDINARY, Order.DELIVERY_EXPRESS],
            ),
            (False, 'payment_type', ['asdsf', '123']),
            (
                True,
                'payment_type',
                [None, '', Order.PAYMENT_ONLINE, Order.PAYMENT_SOMEONE],
            ),
            (
                False,
                'total_cost',
                ['', 'abc', -1, 100000000, Decimal('99999999.999')],
            ),
            (
                True,
                'total_cost',
                [Decimal('0.99'), 0, 1, 99999999, Decimal('99999999.99')],
            ),
            (False, 'city', ['a' * 151]),
            (True, 'city', [None, '', 'a' * 150]),
            (False, 'address', ['a' * 301]),
            (True, 'address', [None, '', 'a' * 300]),
            (False, 'archived', ['', 'abc']),
            (True, 'archived', [True, False, 1, 0]),
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
                'created_at',
                [
                    None,
                    '',
                    datetime.fromisoformat('2024-01-30T15:30:48.823000Z'),
                ],
            ),
            (0, 'total_cost', [None]),
            (Order.STATUS_NEW, 'status', [None]),
            (False, 'archived', [None]),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_field_defaults(self, db_data, expected, field, values):
        super().field_defaults_test(db_data, expected, field, values)

from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.files.images import ImageFile
from django.core.files.storage import default_storage
from django.forms import ValidationError
from django.utils import timezone
from tests.common import RandomImage

from ..models import Category, Product, ProductImage, Specification, Tag


class AbstractModelTest:
    model = None
    base_ok_data = {}

    def create_instance(self, field, value):
        data = self.base_ok_data.copy()
        data[field] = value
        if value is None:
            data.pop(field)

        instance = self.model(**data)
        valid_and_saved = True
        try:
            instance.full_clean()
            instance.save()
        except Exception:
            valid_and_saved = False

        if valid_and_saved:
            instance.refresh_from_db()

        return instance, data, value, valid_and_saved

    def iterate_values(self, field, values):
        for value in values:
            yield self.create_instance(field, value)

    @pytest.mark.parametrize('should_be_ok, field, values', [])
    @pytest.mark.django_db(transaction=True)
    def fields_test(self, db_data, should_be_ok, field, values):
        if not self.model:
            pytest.skip('No model set for testing')

        for instance, data, value, valid_and_saved in self.iterate_values(
            field, values
        ):
            if not valid_and_saved:
                if should_be_ok:
                    msg = 'Data should be valid with {}={}'.format(
                        field, value
                    )
                    pytest.fail(msg)
                else:
                    pass
            elif valid_and_saved:
                if value is None:
                    data[field] = None

                if should_be_ok:
                    assert all(
                        data[k] == getattr(instance, k) for k in data
                    ), 'All fields should be equal for {}={}'.format(
                        field, value
                    )
                if not should_be_ok:
                    assert not all(
                        data[k] == getattr(instance, k) for k in data
                    ), 'Not all fields should be equal for {}={}'.format(
                        field, value
                    )

    @pytest.mark.parametrize('default, field, values', [])
    @pytest.mark.django_db(transaction=True)
    def field_defaults_test(self, db_data, default, field, values):
        if not self.model:
            pytest.skip('No model set for testing')

        for instance, data, value, valid_and_saved in self.iterate_values(
            field, values
        ):
            if not valid_and_saved:
                msg = 'Data should be valid with {}={}'.format(field, value)
                pytest.fail(msg)
            elif valid_and_saved:
                instance.refresh_from_db()
                data[field] = default
                assert all(
                    data[k] == getattr(instance, k) for k in data
                ), 'All fields should be equal for {}={}'.format(field, value)


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
        'default, field, values',
        [
            ('', 'image', [None]),
            ('', 'image_alt', [None]),
            (False, 'archived', [None]),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_field_defaults(self, db_data, default, field, values):
        super().field_defaults_test(db_data, default, field, values)


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
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_fields(self, db_data, should_be_ok, field, values):
        super().fields_test(db_data, should_be_ok, field, values)

    @pytest.mark.parametrize(
        'default, field, values',
        [
            (0, 'count', [None]),
            (0, 'sold_count', [None]),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_field_defaults(self, db_data, default, field, values):
        super().field_defaults_test(db_data, default, field, values)

    @pytest.mark.django_db(transaction=True)
    def test_created_at(self, db_data):
        for value in None, '', '2024-01-30T15:30:48.823000Z':
            instance, _, _, valid_and_saved = self.create_instance(
                'created_at', value
            )
            assert valid_and_saved
            assert instance.created_at - timezone.now() <= timedelta(seconds=3)

    @pytest.mark.django_db(transaction=True)
    def test_tags(self, db_data):
        instance, _, _, valid_and_saved = self.create_instance('count', 3)
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
        instance, _, _, valid_and_saved = self.create_instance('count', 3)
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
        instance, _, _, valid_and_saved = self.create_instance('count', 3)
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
        cls.rand_image = RandomImage(40 * 40)

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
        'default, field, values',
        [
            ('', 'image_alt', [None]),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_field_defaults(self, db_data, default, field, values):
        super().field_defaults_test(db_data, default, field, values)

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

    def test_product_image_upload_path(self):
        pass
        # product_image_upload_path()

import pytest
from django.forms import ValidationError

from ..models import Category, Specification, Tag


class AbstractModelTest:
    model = None
    base_ok_data = {}

    @pytest.mark.parametrize('is_valid, field, values', [])
    @pytest.mark.django_db(transaction=True)
    def test_fields(self, db_data, is_valid, field, values):
        if not self.model:
            pytest.skip('No model set for testing')
        for value in values:
            data = self.base_ok_data.copy()
            data[field] = value
            if value is None:
                data.pop(field)

            instance = self.model(**data)
            failed = False
            try:
                instance.full_clean()
                instance.save()
            except Exception:
                failed = True

            if not failed and not is_valid:
                msg = 'Should be invalid for {}={}'.format(field, value)
                pytest.fail(msg)
            if failed and is_valid:
                msg = 'Should be valid for {}={}'.format(field, value)
                pytest.fail(msg)
            if instance.pk is not None:
                assert all(data[k] == getattr(instance, k) for k in data)


class TestTag(AbstractModelTest):
    model = Tag
    base_ok_data = {
        'name': 'test',
    }

    @pytest.mark.parametrize(
        'is_valid, field, values',
        [
            (False, 'name', [None, '', 'a' * 101]),
            (True, 'name', ['a' * 100]),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_fields(self, db_data, is_valid, field, values):
        super().test_fields(db_data, is_valid, field, values)

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
        'is_valid, field, values',
        [
            (False, 'name', [None, '', 'a' * 201]),
            (True, 'name', ['a' * 200]),
            (False, 'value', [None, '', 'a' * 201]),
            (True, 'value', ['a' * 200]),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_fields(self, db_data, is_valid, field, values):
        super().test_fields(db_data, is_valid, field, values)

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
        'is_valid, field, values',
        [
            (False, 'title', [None, '', 'a' * 201]),
            (True, 'title', ['a' * 200]),
            (False, 'parent_id', [20, 3, '']),
            (True, 'parent_id', [None, 1]),
            (False, 'image', [123]),
            (True, 'image', [None, '', 'file.png']),
            (False, 'image_alt', ['a' * 201]),
            (True, 'image_alt', [None, '', 'a' * 200]),
            (False, 'archived', ['', 'a', 4]),
            (True, 'archived', [None, True, False]),
        ],
    )
    @pytest.mark.django_db(transaction=True)
    def test_fields(self, db_data, is_valid, field, values):
        super().test_fields(db_data, is_valid, field, values)

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

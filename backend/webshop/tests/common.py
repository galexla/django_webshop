import io
import re
from contextlib import contextmanager
from datetime import datetime, timedelta
from random import randint
from typing import Any, Iterable, Iterator

import pytest
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase


class RandomImage:
    def __init__(self, size: int) -> None:
        self.rand_pixels = self._create_random_pixels(size)

    def _create_random_pixels(self, n: int) -> list[tuple[int, int, int]]:
        return [
            (
                randint(0, 255),
                randint(0, 255),
                randint(0, 255),
            )
            for i in range(n)
        ]

    def get_bytes(
        self, size=(100, 100), filename='test', format='png'
    ) -> io.BytesIO:
        """Generate a random image made of self.rand_pixels"""
        file = io.BytesIO()
        n_pixels = size[0] * size[1]
        ratio = n_pixels // len(self.rand_pixels) + 1
        pixel_data = self.rand_pixels * ratio
        pixel_data = pixel_data[:n_pixels]

        image = Image.new('RGB', size=size, color=(0, 0, 0))
        image.putdata(pixel_data)

        image.save(file, format)
        file.name = f'{filename}.{format}'
        file.seek(0)

        return file


class SerializerTestCase(APITestCase):
    def assert_all_invalid(
        self, serializer_class, ok_data: dict, field_name: str, values: list
    ):
        """
        Assert that all values of the specified field are invalid. None
        in values means the field is missing.
        """
        for value in values:
            data = ok_data.copy()
            if value is None:
                data.pop(field_name)
            else:
                data[field_name] = value
            serializer = serializer_class(data=data)
            self.assertFalse(serializer.is_valid())

    def assert_all_valid(
        self, serializer_class, ok_data: dict, field_name: str, values: list
    ):
        """
        Assert that all values of the specified field are valid. None
        in values means the field is missing.
        """
        for value in values:
            data = ok_data.copy()
            if value is None:
                data.pop(field_name)
            else:
                data[field_name] = value
            serializer = serializer_class(data=data)
            self.assertTrue(serializer.is_valid())


class AbstractModelTest:
    """
    Base class for testing models. It provides methods for testing fields and
    default values of the model. It also provides a method for creating an
    instance of the model and checking if it was saved correctly.

    Attributes:
        model: Model class to be tested.
        base_ok_data: Dictionary with valid data for creating an instance of
            the model. It should be used as a base for creating an instance
            with different values for fields.
        datetime_max_diff: Maximum difference in seconds between the current
            time and the time of the instance creation. Used for checking if
            the default value of a datetime field is set correctly. See the
            `is_equal_with_date` method.
    """

    model = None
    base_ok_data = {}
    datetime_max_diff = 3  # seconds

    def create_instance(
        self, field: str, value: Any
    ) -> tuple[Any, dict, Any, bool, Exception | None]:
        """
        Create an instance of the model with the given value for the field.

        :param field: Field to be tested.
        :type field: str
        :param value: Value to be set for the field. If the value is None, the
            field will be removed from the data.
        :type value: Any
        :return: Tuple with the instance, data, value, if the data is valid and
            saved correctly and the exception if the data is not valid.
        :rtype: tuple
        """
        data = self.base_ok_data.copy()
        data[field] = value
        if value is None:
            data.pop(field)

        instance = self.model(**data)
        valid_and_saved = True
        exc = None
        try:
            instance.full_clean()
            instance.save()
        except Exception as ex:
            valid_and_saved = False
            exc = ex

        if valid_and_saved:
            instance.refresh_from_db()

        return instance, data, value, valid_and_saved, exc

    def iterate_values(
        self, field: str, values: list
    ) -> Iterator[tuple[Any, dict, Any, bool, Exception | None]]:
        """
        Iterate over the values and create an instance of the model with each
        value for the field.

        :param field: Field to be tested.
        :type field: str
        :param values: List of values to be tested.
        :type values: list
        :return: Iterator with tuples with the instance, data, value, if the
            data is valid and saved correctly and the exception if the data is
            not valid.
        :rtype: Iterator
        """
        for value in values:
            yield self.create_instance(field, value)

    @pytest.mark.parametrize('should_be_ok, field, values', [])
    @pytest.mark.django_db(transaction=True)
    def fields_test(
        self, db_data: Any, should_be_ok: bool, field: str, values: list
    ) -> None:
        """
        Test the field with different values. Check if the data is valid and
        if the instance was saved correctly. If the data is valid, check if
        all fields of the instance are equal to the data.

        :param db_data: Fixture with data for the database.
        :type db_data: Any
        :param should_be_ok: If the data should be valid and saved.
        :type should_be_ok: bool
        :param field: Field to be tested.
        :type field: str
        :param values: List of values to be tested.
        :type values: list
        :return: None
        """
        if not self.model:
            pytest.skip('No model set for testing')

        for instance, data, value, valid_and_saved, exc in self.iterate_values(
            field, values
        ):
            if not valid_and_saved:
                if should_be_ok:
                    msg = 'Data should be valid for {}={}, exc={}'.format(
                        field, value, exc
                    )
                    pytest.fail(msg)
                else:
                    pass
            elif valid_and_saved:
                if should_be_ok:
                    not_equal_fields = get_not_equal_values(instance, data)
                    msg = 'All fields should be equal for {}={}. Not equal: {}'
                    assert all(
                        data[k] == getattr(instance, k) for k in data
                    ), msg.format(field, value, not_equal_fields)
                if not should_be_ok:
                    assert not all(
                        data[k] == getattr(instance, k) for k in data
                    ), 'Not all fields should be equal for {}={}'.format(
                        field, value
                    )
                instance.delete()

    @pytest.mark.parametrize('default, field, values', [])
    @pytest.mark.django_db(transaction=True)
    def field_defaults_test(
        self, db_data: Any, default: Any, field: str, values: list
    ) -> None:
        """
        Test the default value of the field with different values. Check if the
        data is valid and if the instance was saved correctly. If the data is
        valid, check if all fields of the instance are equal to the data.

        :param db_data: Fixture with data for the database.
        :type db_data: Any
        :param default: Default value to be set for the field. If the default
            is 'now' and the field is a datetime field, the default will be set
            to the current time.
        :type default: Any
        :param field: Field to be tested.
        :type field: str
        :param values: List of values to be tested.
        :type values: list
        :return: None
        """
        if not self.model:
            pytest.skip('No model set for testing')

        for instance, data, value, valid_and_saved, exc in self.iterate_values(
            field, values
        ):
            if not valid_and_saved:
                msg = 'Data should be valid for {}={}, exc={}'.format(
                    field, value, exc
                )
                pytest.fail(msg)
            elif valid_and_saved:
                instance.refresh_from_db()
                if default == 'now' and isinstance(
                    getattr(instance, field), datetime
                ):
                    data[field] = timezone.now
                    msg = 'All fields should be equal for {}={}'
                    assert self.is_equal_with_date(
                        instance, data, field
                    ), msg.format(field, value)
                else:
                    data[field] = default
                    msg = 'All fields should be equal for {}={}'
                    assert all(
                        data[k] == getattr(instance, k) for k in data
                    ), msg.format(field, value)
                instance.delete()

    def is_equal_with_date(
        self, instance: Any, data: dict, date_field: str
    ) -> bool:
        """
        Check if all fields of the instance are equal to the data and if the
        date field is within the `datetime_max_diff` in seconds from the
        current time.

        :param instance: Instance of the model.
        :type instance: Any
        :param data: Dictionary with data for the instance.
        :type data: dict
        :param date_field: Name of the datetime field.
        :type date_field: str
        :return: If all fields are equal to the data and the date field is
            within the `datetime_max_diff` in seconds from the current time.
        :rtype: bool
        """
        keys = set(data.keys())
        keys.remove(date_field)
        almost_equal = all(data[k] == getattr(instance, k) for k in keys)
        dates_almost_equal = getattr(
            instance, date_field
        ) - timezone.now() <= timedelta(seconds=self.datetime_max_diff)
        return almost_equal and dates_almost_equal


def product_img_path(id, file_name):
    return f'/media/products/product{id}/images/{file_name}'


def category_img_path(id, file_name):
    return f'/media/categories/category{id}/image/{file_name}'


def assert_dict_equal_exclude(dict1, dict2, exclude_keys):
    dict1 = dict1.copy()
    dict2 = dict2.copy()
    for key in exclude_keys:
        dict1.pop(key, None)
        dict2.pop(key, None)
    assert dict1 == dict2


@contextmanager
def assert_not_raises(exception_class):
    try:
        yield
    except exception_class:
        pytest.fail('Did raise {}'.format(exception_class))


def get_ids(data: Iterable[dict]) -> list:
    return [item['id'] for item in data]


def get_obj_ids(data: Iterable[object]) -> list:
    return [item.id for item in data]


def get_keys(data: Iterable[dict], keys: Iterable) -> list[dict]:
    result = []
    for item in data:
        elem = {}
        for key in keys:
            elem[key] = item.get(key)
        result.append(elem)
    return result


def slice_to_dict(
    data: Iterable[dict], keys: Iterable, unique_key
) -> list[dict]:
    result = {}
    for item in data:
        elem = {}
        for key in keys:
            elem[key] = item.get(key)
        result[elem[unique_key]] = elem
    return result


def get_attrs(data: Iterable[object], attrs: Iterable) -> list[dict]:
    result = []
    for item in data:
        elem = {}
        for key in attrs:
            elem[key] = getattr(item, key, None)
        result.append(elem)
    return result


def camelcase_keys_to_underscore(d: dict[str, Any]):
    result = {}
    for key, value in d.items():
        key2 = re.sub(r'([A-Z])', r'_\1', key).lower()
        result[key2] = value
    return result


def is_date_almost_equal(date1: datetime, date2: datetime, max_delta=1):
    delta: timedelta = date1 - date2
    return delta.seconds <= max_delta


def get_not_equal_values(instance, data, with_values=False):
    fields = list(filter(lambda k: data[k] != getattr(instance, k), data))
    if not with_values:
        return fields
    values = [getattr(instance, k) for k in fields]
    return dict(zip(fields, values))

import io
import re
from contextlib import contextmanager
from datetime import datetime, timedelta
from random import randint
from typing import Any, Iterable, Iterator, Type

import pytest
from django.db.models import Model
from django.utils import timezone
from PIL import Image
from rest_framework.serializers import Serializer
from rest_framework.test import APITestCase


class RandomImage:
    """
    Class to generate random images. It creates a list of random pixels and
    generates an image of specified size using these pixels.

    Args:
        size (int): Number of random pixels to be generated.

    Attributes:
        rand_pixels (list): List of random pixels in the format (R, G, B).
    """

    def __init__(self, size: int) -> None:
        """Create a list of random pixels."""
        self.rand_pixels = self._create_random_pixels(size)

    def _create_random_pixels(self, n: int) -> list[tuple[int, int, int]]:
        """
        Create a list of random pixels in the format (R, G, B).

        :param n: Number of random pixels to be generated.
        :type n: int
        :return: List of random pixels.
        :rtype: list[tuple[int, int, int]]
        """
        return [
            (
                randint(0, 255),
                randint(0, 255),
                randint(0, 255),
            )
            for i in range(n)
        ]

    def get_bytes(
        self,
        size: tuple[int, int] = (100, 100),
        filename: str = 'test',
        format: str = 'png',
    ) -> io.BytesIO:
        """
        Generate an image with the specified size using the random pixels. The
        image is saved in the specified format and the file is returned as a
        BytesIO object.

        :param size: Size of the image in pixels.
        :type size: tuple[int, int]
        :param filename: Name of the file.
        :type filename: str
        :param format: Format of the image.
        :type format: str
        :return: BytesIO object with the image file.
        :rtype: io.BytesIO
        """
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
    """Base class for testing serializers with Django testing tools."""

    def assert_all_invalid(
        self,
        serializer_class: Type[Serializer],
        ok_data: dict,
        field_name: str,
        values: list,
    ) -> None:
        """
        Assert that all values of the specified field are invalid. None
        in values means the field is missing.

        :param serializer_class: Serializer class
        :type serializer_class: Type[Serializer]
        :param ok_data: Dictionary with valid data for the serializer.
        :type ok_data: dict
        :param field_name: Name of the field to be tested.
        :type field_name: str
        :param values: List of values to be tested.
        :type values: list
        :return: None
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
        self,
        serializer_class: Type[Serializer],
        ok_data: dict,
        field_name: str,
        values: list,
    ) -> None:
        """
        Assert that all values of the specified field are valid. None
        in values means the field is missing.

        :param serializer_class: Serializer class
        :type serializer_class: Type[Serializer]
        :param ok_data: Dictionary with valid data for the serializer.
        :type ok_data: dict
        :param field_name: Name of the field to be tested.
        :type field_name: str
        :param values: List of values to be tested.
        :type values: list
        :return: None
        """
        for value in values:
            data = ok_data.copy()
            if value is None:
                data.pop(field_name)
            else:
                data[field_name] = value
            serializer = serializer_class(data=data)
            self.assertTrue(serializer.is_valid())


class SerializerTestPytest:
    """Base class for testing serializers with pytest."""

    serializer_class: Type[Serializer] = None
    base_ok_data: dict[str, Any] = {}

    @pytest.mark.parametrize('should_be_ok, field, values', [])
    def test_fields(
        self, should_be_ok: bool, field: str, values: list
    ) -> None:
        """
        Test the field with different values. Check if the data is valid.

        :param should_be_ok: If the data should be valid.
        :type should_be_ok: bool
        :param field: Field to be tested.
        :type field: str
        :param values: List of values to be tested.
        :type values: list
        :raises AssertionError: If the any assertion fails.
        :return: None
        """
        for value in values:
            data = self.base_ok_data.copy()
            data[field] = value
            if value is None:
                data.pop(field, None)
            serializer = self.serializer_class(data=data)
            valid_str = 'valid' if should_be_ok else 'invalid'
            assert (
                serializer.is_valid() == should_be_ok
            ), 'Data should be {} for field {} = {}, errors: {}'.format(
                valid_str, field, value, serializer.errors
            )


class AbstractModelTest:
    """
    Base class for testing models. It provides methods for testing fields and
    default values of the model. It also provides a method for creating an
    instance of the model and checking if it was saved correctly.

    Attributes:
        model (Type[Model]): Model class to be tested.
        base_ok_data (dict): Dictionary with valid data for creating an
            instance of the model. It should be used as a base for creating an
            instance with different values for fields.
        datetime_max_diff (int): Maximum difference in seconds between the
            current time and the time of the instance creation. Used for
            checking if the default value of a datetime field is set correctly.
            See the `is_equal_with_date` method.
    """

    model: Type[Model] = None
    base_ok_data: dict[str, Any] = {}
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
        :rtype: tuple[Any, dict, Any, bool, Exception | None]
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
        :yields: Tuple with the instance, data, value, if the data is valid and
            saved correctly and the exception if the data is not valid.
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
        :raises AssertionError: If the any assertion fails.
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

    @pytest.mark.parametrize('expected, field, values', [])
    @pytest.mark.django_db(transaction=True)
    def field_defaults_test(
        self, db_data: Any, expected: Any, field: str, values: list
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
        :raises AssertionError: If the any assertion fails.
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
                if expected == 'now' and isinstance(
                    getattr(instance, field), datetime
                ):
                    data[field] = timezone.now
                    msg = 'All fields should be equal for {}={}'
                    assert self.is_equal_with_date(
                        instance, data, field
                    ), msg.format(field, value)
                else:
                    data[field] = expected
                    msg = 'All fields should be equal for {}={}'
                    assert all(
                        data[k] == getattr(instance, k) for k in data
                    ), msg.format(field, value)
                instance.delete()

    def is_equal_with_date(
        self, instance: Any, data: dict[str, Any], date_field: str
    ) -> bool:
        """
        Check if all fields of the instance are equal to the data and if the
        date field is within the `datetime_max_diff` in seconds from the
        current time.

        :param instance: Instance of the model.
        :type instance: Any
        :param data: Dictionary with data for the instance.
        :type data: dict[str, Any]
        :param date_field: Name of the datetime field.
        :type date_field: str
        :return: If all fields are equal to the data and the date field is
            within the `datetime_max_diff` in seconds from the current time.
        :rtype: bool
        """
        keys = set(data.keys())
        keys.remove(date_field)
        almost_equal = all(data[k] == getattr(instance, k) for k in keys)
        dates_almost_equal = is_date_almost_equal(
            getattr(instance, date_field),
            timezone.now(),
            self.datetime_max_diff,
        )
        return almost_equal and dates_almost_equal


def product_img_path(id: str, file_name: str) -> str:
    """
    Return the path for a product image.

    :param id: Product ID.
    :type id: int
    :param file_name: Name of the file.
    :type file_name: str
    :return: Path for the product image.
    :rtype: str
    """
    return f'/media/products/product{id}/images/{file_name}'


def category_img_path(id: str, file_name: str) -> str:
    """
    Return the path for a category image.

    :param id: Category ID.
    :type id: int
    :param file_name: Name of the file.
    :type file_name: str
    :return: Path for the category image.
    :rtype: str
    """
    return f'/media/categories/category{id}/image/{file_name}'


def assert_dict_equal_exclude(
    dict1: dict, dict2: dict, exclude_keys: list
) -> None:
    """
    Assert that two dictionaries are equal excluding the specified keys.

    :param dict1: First dictionary.
    :type dict1: dict
    :param dict2: Second dictionary.
    :type dict2: dict
    :param exclude_keys: List of keys to be excluded.
    :type exclude_keys: list
    :return: None
    """
    dict1 = dict1.copy()
    dict2 = dict2.copy()
    for key in exclude_keys:
        dict1.pop(key, None)
        dict2.pop(key, None)
    assert dict1 == dict2


@contextmanager
def assert_not_raises(exception_class: Type[BaseException]) -> Iterator[None]:
    """
    Context manager to assert that an exception was not raised.

    :param exception_class: Exception class to be checked.
    :type exception_class: Type[BaseException]
    :raises AssertionError: If the `exception_class` is raised within the
        context block.
    :yields: None
    """
    try:
        yield
    except exception_class:
        pytest.fail('Did raise {}'.format(exception_class))


def get_ids(data: Iterable[dict]) -> list:
    """
    Get a list of IDs from a list of dictionaries.

    :param data: List of dictionaries.
    :type data: Iterable[dict]
    :return: List of IDs.
    :rtype: list
    """
    return [item['id'] for item in data]


def get_obj_ids(data: Iterable[object]) -> list:
    """
    Get a list of IDs from a list of objects.

    :param data: List of objects.
    :type data: Iterable[object]
    :return: List of IDs.
    :rtype: list
    """
    return [item.id for item in data]


def get_keys(data: Iterable[dict], keys: Iterable) -> list[dict]:
    """
    Get only the specified keys from a list of dictionaries.

    :param data: List of dictionaries.
    :type data: Iterable[dict]
    :param keys: List of keys to be selected.
    :type keys: Iterable
    :return: List of dictionaries with only the specified keys.
    :rtype: list[dict]
    """
    result = []
    for item in data:
        elem = {}
        for key in keys:
            elem[key] = item.get(key)
        result.append(elem)
    return result


def slice_to_dict(
    data: Iterable[dict], keys: Iterable, unique_key: str
) -> list[dict]:
    """
    Convert a list of dictionaries to a dictionary with a unique key (e.g. ID).

    :param data: List of dictionaries.
    :type data: Iterable[dict]
    :param keys: List of keys to be selected.
    :type keys: Iterable
    :param unique_key: Unique key present in all dictionaries to be used as the
        key in the resulting dictionary.
    :type unique_key: str
    :return: Dictionary with the unique key as the key and the selected keys as
        the values.
    :rtype: list[dict]
    """
    result = {}
    for item in data:
        elem = {}
        for key in keys:
            elem[key] = item.get(key)
        result[elem[unique_key]] = elem
    return result


def get_attrs(data: Iterable[object], attrs: Iterable) -> list[dict]:
    """
    Get only the specified attributes from a list of objects.

    :param data: List of objects.
    :type data: Iterable[object]
    :param attrs: List of attributes to be selected.
    :type attrs: Iterable
    :return: List of dictionaries with only the specified attributes.
    :rtype: list[dict]
    """
    result = []
    for item in data:
        elem = {}
        for key in attrs:
            elem[key] = getattr(item, key, None)
        result.append(elem)
    return result


def camelcase_keys_to_underscore(d: dict[str, Any]) -> dict[str, Any]:
    """
    Convert camelCase keys to snake_case.

    :param d: Dictionary with camelCase keys.
    :type d: dict[str, Any]
    :return: Dictionary with snake_case keys.
    :rtype: dict[str, Any]
    """
    result = {}
    for key, value in d.items():
        key2 = re.sub(r'([A-Z])', r'_\1', key).lower()
        result[key2] = value
    return result


def is_date_almost_equal(
    date1: datetime, date2: datetime, max_delta: int = 1
) -> bool:
    """
    Check if two dates are almost equal. The difference between the dates
    should be less than or equal to the specified delta in seconds.

    :param date1: First date.
    :type date1: datetime
    :param date2: Second date.
    :type date2: datetime
    :param max_delta: Maximum difference in seconds between the dates.
    :type max_delta: int
    :return: If the dates are almost equal.
    :rtype: bool
    """
    delta: timedelta = date1 - date2
    return abs(delta.total_seconds()) <= max_delta


def get_not_equal_values(
    instance: Any, data: dict[str, Any], with_values: bool = False
) -> dict[str, Any]:
    """
    Get the fields that are not equal between the instance and the data.

    :param instance: Instance of a model or any object.
    :type instance: Any
    :param data: Dictionary with data for the instance.
    :type data: dict[str, Any]
    :param with_values: If the values of the fields should be returned.
    :type with_values: bool
    :return: Fields that are not equal between the instance and the data.
    :rtype: dict[str, Any]
    """
    fields = list(filter(lambda k: data[k] != getattr(instance, k), data))
    if not with_values:
        return fields
    values = [getattr(instance, k) for k in fields]
    return dict(zip(fields, values))

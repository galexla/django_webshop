from typing import Iterable

from rest_framework.test import APITestCase


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


def get_attrs(data: Iterable[object], attrs: Iterable) -> list[dict]:
    result = []
    for item in data:
        elem = {}
        for key in attrs:
            elem[key] = getattr(item, key, None)
        result.append(elem)
    return result

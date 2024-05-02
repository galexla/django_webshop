import io
import re
from random import randint
from typing import Any, Iterable

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

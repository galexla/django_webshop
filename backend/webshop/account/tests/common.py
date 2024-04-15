import io
from random import randint

from django.test import TestCase
from PIL import Image


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


class BaseTestCase(TestCase):
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

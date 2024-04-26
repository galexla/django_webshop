from django.test import TestCase


class SerializerTestCase(TestCase):
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

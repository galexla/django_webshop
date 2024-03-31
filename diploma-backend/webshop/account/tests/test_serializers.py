from django.test import TestCase

from ..models import User
from ..serializers import SignUpSerializer


class SignUpSerializerTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.user = User.objects.create(username='test2', password='test')

    @classmethod
    def tearDownClass(cls) -> None:
        cls.user.delete()

    def test_validate(self):
        serializer = SignUpSerializer(
            data={'name': '', 'username': '', 'password': ''}
        )
        self.assertFalse(serializer.is_valid())

        serializer = SignUpSerializer(
            data={'name': 'test', 'username': 'test', 'password': ''}
        )
        self.assertFalse(serializer.is_valid())

        serializer = SignUpSerializer(
            data={'name': 'test', 'username': 'test', 'password': 'dfskdfd'}
        )
        self.assertFalse(serializer.is_valid())

        serializer = SignUpSerializer(
            data={
                'name': 'a' * 160,
                'username': 'test',
                'password': 'dfskdfdd',
            }
        )
        self.assertFalse(serializer.is_valid())

        serializer = SignUpSerializer(
            data={'name': 'test', 'username': 'test', 'password': 'dfskdfdd'}
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {
                'first_name': 'test',
                'username': 'test',
                'password': 'dfskdfdd',
            },
        )

    def test_write_only(self):
        serializer = SignUpSerializer(instance=self.user)
        self.assertIsNone(serializer.data.get('password'))
        self.assertIsNotNone(serializer.data.get('username'))

    def test_create(self):
        serializer = SignUpSerializer()
        with self.assertRaises(KeyError):
            serializer.create({'username': '123', 'password': 'dfskdfdd'})

        serializer = SignUpSerializer()
        user = serializer.create(
            {'first_name': '123', 'username': '123', 'password': 'dfskdfdd'}
        )
        db_user = User.objects.get(username='123')
        self.assertEqual(user, db_user)

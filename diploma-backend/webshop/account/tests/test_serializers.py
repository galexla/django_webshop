from django.test import TestCase

from ..models import User
from ..serializers import (
    AvatarUpdateSerializer,
    ProfileSerializer,
    SetPasswordSerializer,
    SignInSerializer,
    SignUpSerializer,
)
from .common import RandomImage


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
            data={'name': 'test', 'username': 'test', 'password': 'a' * 130}
        )
        self.assertFalse(serializer.is_valid())

        serializer = SignUpSerializer(
            data={'name': 'test', 'username': '#test', 'password': 'dfskdfdd'}
        )
        self.assertFalse(serializer.is_valid())

        serializer = SignUpSerializer(
            data={
                'name': 'test',
                'username': '@.+-_test',
                'password': 'dfskdfdd',
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {
                'first_name': 'test',
                'username': '@.+-_test',
                'password': 'dfskdfdd',
            },
        )

    def test_passw_write_only(self):
        serializer = SignUpSerializer(instance=self.user)
        self.assertIsNotNone(serializer.data.get('username'))
        self.assertIsNone(serializer.data.get('password'))

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


class SignInSerializerTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.user = User.objects.create(username='test2', password='test')

    @classmethod
    def tearDownClass(cls) -> None:
        cls.user.delete()

    def test_fields(self):
        serializer = SignInSerializer(data={'username': '', 'password': ''})
        self.assertFalse(serializer.is_valid())

        serializer = SignInSerializer(
            data={'username': 'a' * 160, 'password': 'asggdfsx'}
        )
        self.assertFalse(serializer.is_valid())

        serializer = SignInSerializer(
            data={'username': 'test', 'password': 'a' * 130}
        )
        self.assertFalse(serializer.is_valid())

        serializer = SignInSerializer(
            data={'username': 'test', 'password': 'asggdfsx'}
        )
        self.assertTrue(serializer.is_valid())
        self.assertEqual(
            serializer.validated_data,
            {'username': 'test', 'password': 'asggdfsx'},
        )

        serializer = SignInSerializer(data={'password': 'asggdfsx'})
        self.assertFalse(serializer.is_valid())

    def test_passw_write_only(self):
        serializer = SignInSerializer(instance=self.user)
        self.assertIsNotNone(serializer.data.get('username'))
        self.assertIsNone(serializer.data.get('password'))


class SetPasswordSerializerTest(TestCase):
    def test_fields(self):
        serializer = SetPasswordSerializer(data={})
        self.assertFalse(serializer.is_valid())

        serializer = SetPasswordSerializer(
            data={'currentPassword': '', 'newPassword': ''}
        )
        self.assertFalse(serializer.is_valid())

        serializer = SetPasswordSerializer(
            data={'currentPassword': 'a' * 130, 'newPassword': 'dfdskfjdfa'}
        )
        self.assertFalse(serializer.is_valid())

        serializer = SetPasswordSerializer(
            data={'currentPassword': 'gedfkjdhf', 'newPassword': 'gedfkjdhf'}
        )
        self.assertFalse(serializer.is_valid())

        serializer = SetPasswordSerializer(
            data={'currentPassword': 'gedfkjdhf', 'newPassword': 'dfkjdhf'}
        )
        self.assertFalse(serializer.is_valid())

        serializer = SetPasswordSerializer(
            data={'currentPassword': 'gedfkjdhf', 'newPassword': 'dfdskfjdfa'}
        )
        self.assertTrue(serializer.is_valid())


class AvatarUpdateSerializerTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rand_image = RandomImage(500 * 500)
        cls.user = User.objects.create(username='test', password='fwfsiuefds')

    @classmethod
    def tearDownClass(cls) -> None:
        cls.user.delete()

    def test_validate_avatar(self):
        serializer = AvatarUpdateSerializer(data={'avatar': b'dsfrgk'})
        self.assertFalse(serializer.is_valid())

    def test_avatar_write_only(self):
        serializer = AvatarUpdateSerializer(instance=self.user.profile)
        self.assertIsNone(serializer.data.get('avatar'))


class ProfileSerializerTest(TestCase):
    def test_fields(self):
        ok_data = {
            'fullName': 'test',
            'email': 'test@test.com',
            'phone': '+24437',
        }

        self._assert_invalid_values(ok_data, 'fullName', [None, '', 'a' * 160])

        self._assert_invalid_values(
            ok_data,
            'email',
            [
                None,
                '',
                'a@' + 'a' * 260 + '.com',
                'test',
                'test@test',
                '.test@test.com',
            ],
        )

        self._assert_invalid_values(
            ok_data,
            'phone',
            [None, '', '+' + '1' * 35, '+1234', '1234567'],
        )

        serializer = ProfileSerializer(data=ok_data)
        self.assertTrue(serializer.is_valid())

    def _assert_invalid_values(
        self, valid_data: dict, field_name: str, invalid_values: list[str]
    ):
        """
        Ensure that valid_data[field_name] replaced by any value from
        invalid_values leads to serializer.is_valid() = False. None in
        invalid_values list means the field is removed.
        """
        for value in invalid_values:
            data = valid_data.copy()
            if value is None:
                data.pop(field_name)
            else:
                data[field_name] = value
            serializer = ProfileSerializer(data=data)
            self.assertFalse(serializer.is_valid())

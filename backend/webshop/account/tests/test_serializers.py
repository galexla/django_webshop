from django.test import TestCase
from tests.common import RandomImage, SerializerTestCase

from ..models import User
from ..serializers import (
    AvatarUpdateSerializer,
    ProfileSerializer,
    SetPasswordSerializer,
    SignInSerializer,
    SignUpSerializer,
)


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


class SetPasswordSerializerTest(SerializerTestCase):
    def test_fields(self):
        ok_data = {'currentPassword': 'gedfkjdhf', 'newPassword': 'dfdskfjdfa'}

        serializer = SetPasswordSerializer(data={})
        self.assertFalse(serializer.is_valid())

        self.assert_all_invalid(
            ProfileSerializer,
            ok_data,
            'currentPassword',
            [None, '', 'a' * 130],
        )

        self.assert_all_invalid(
            ProfileSerializer,
            ok_data,
            'newPassword',
            [None, '', 'gedfkjdhf', 'dfkjdhf'],
        )

        serializer = SetPasswordSerializer(data=ok_data)
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


class ProfileSerializerTest(SerializerTestCase):
    def test_fields(self):
        ok_data = {
            'fullName': 'test',
            'email': 'test@test.com',
            'phone': '+24437',
        }

        self.assert_all_invalid(
            ProfileSerializer, ok_data, 'fullName', [None, '', 'a' * 160]
        )

        self.assert_all_invalid(
            ProfileSerializer,
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

        self.assert_all_invalid(
            ProfileSerializer,
            ok_data,
            'phone',
            [None, '', '+' + '1' * 35, '+1234', '1234567'],
        )

        serializer = ProfileSerializer(data=ok_data)
        self.assertTrue(serializer.is_valid())

    def test_update(self):
        data = {
            'fullName': 'Test',
            'email': 'test@test.com',
            'phone': '+5457636514',
        }
        serializer = ProfileSerializer()
        with self.assertRaises(TypeError):
            serializer.update('a', data)

        user = User.objects.create(username='a', password='a')
        serializer = ProfileSerializer()
        serializer.update(user, data)
        user.refresh_from_db(fields=['first_name', 'email'])
        self.assertEqual(user.first_name, data['fullName'])
        self.assertEqual(user.email, data['email'])
        self.assertEqual(user.profile.phone, data['phone'])

        user.delete()

    def test_to_representation(self):
        data = {
            'fullName': 'Test',
            'email': 'test@test.com',
            'phone': '+5457636514',
        }
        serializer = ProfileSerializer()
        with self.assertRaises(TypeError):
            serializer.update('a', data)

        user = User.objects.create(
            username='a', password='a', first_name='b', email='test@test.com'
        )
        user.profile.phone = '+5457636514'
        expected_repr = {
            'fullName': 'b',
            'email': 'test@test.com',
            'phone': '+5457636514',
            'avatar': {'src': '', 'alt': ''},
        }
        serializer = ProfileSerializer()
        representation = serializer.to_representation(user)
        self.assertEqual(representation, expected_repr)

        user.delete()

from django.core.files.storage import default_storage
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from tests.common import RandomImage

from ..models import Profile, User


class SignInViewTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.user1 = User.objects.create_user(
            username='user1', password='secret', email='user1@user.com'
        )
        cls.user1.profile = Profile.objects.create(user=cls.user1)
        cls.user2 = User.objects.create_user(
            username='user2',
            password='secret',
            email='user2@user.com',
            is_active=False,
        )
        cls.user2.profile = Profile.objects.create(user=cls.user2)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.user1.profile.delete()
        cls.user1.delete()
        cls.user2.profile.delete()
        cls.user2.delete()

    def test_post(self):
        url = reverse('account:sign-in')

        response = self.client.post(
            url, {'username': 'user1', 'password': 'secret'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data)

        response = self.client.get(reverse('account:profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            url, {'username': 'user2', 'password': 'secret'}
        )
        self.assertEqual(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        response = self.client.post(
            url, {'username': 'user3', 'password': 'secret'}
        )
        self.assertEqual(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        response = self.client.post(
            url, {'username': 'user1', 'password12345': 'secret'}
        )
        self.assertEqual(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        response = self.client.post(
            url, {'username12345': 'user1', 'password': 'secret'}
        )
        self.assertEqual(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class SignOutViewTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.user1 = User.objects.create_user(
            username='user1', password='secret', email='user1@user.com'
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.user1.delete()

    def test_post(self):
        url = reverse('account:sign-out')

        response: Response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.user1)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data)
        basket_id_cookie = response.cookies.get('basket_id', None)
        basket_id_cookie = basket_id_cookie.value if basket_id_cookie else ''
        self.assertEqual(basket_id_cookie, '')
        response = self.client.get(reverse('account:profile'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SignUpViewTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.user1 = User.objects.create_user(
            username='user1', password='secret', email='user1@user.com'
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.user1.delete()
        Profile.objects.filter(user__username='user2').delete()
        User.objects.filter(username='user2').delete()

    def test_post(self):
        url = reverse('account:sign-up')

        response = self.client.post(
            url,
            {'username': 'user1', 'password': 'secret', 'name': 'user'},
        )
        self.assertEqual(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        post_data = {
            'username': 'user2',
            'password': '123qazxsw',
            'name': 'user',
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data)
        user = User.objects.filter(username='user2').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, post_data['username'])
        self.assertEqual(user.first_name, post_data['name'])
        response = self.client.get(reverse('account:profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            url,
            {'username': 'user1', 'password': 'secret', 'name12345': 'user'},
        )
        self.assertEqual(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        response = self.client.post(
            url,
            {'username': 'user3', 'password': 'secret', 'name1': 'user'},
        )
        self.assertEqual(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        response = self.client.post(url, {})
        self.assertEqual(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class SetPasswordViewTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.user1 = User.objects.create_user(
            username='user1', password='secret', email='user1@user.com'
        )
        cls.user1.profile = Profile.objects.create(user=cls.user1)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.user1.profile.delete()
        cls.user1.delete()

    def test_post(self):
        url = reverse('account:password')

        response = self.client.post(
            url,
            {'currentPassword': 'secret', 'newPassword': 'newPass321'},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.user1)

        response = self.client.post(
            url,
            {'currentPassword': 'secret1', 'newPassword': 'newPass321'},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            url,
            {'currentPassword': 'secret', 'newPassword': 'newPass'},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            url,
            {'currentPassword': 'secret', 'newPassword': 'newPass321'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(
            reverse('account:sign-in'),
            {'username': 'user1', 'password': 'newPass321'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data)
        response = self.client.get(reverse('account:profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.logout()


class ProfileViewTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.user1 = User.objects.create_user(
            username='user1',
            first_name='123',
            password='secret',
            email='user1@user.com',
        )
        cls.user1.profile = Profile.objects.create(
            user=cls.user1, phone='12345678'
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.user1.profile.delete()
        cls.user1.delete()

    def test_get(self):
        url = reverse('account:profile')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.user1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                'fullName': '123',
                'email': 'user1@user.com',
                'phone': '12345678',
                'avatar': {'src': '', 'alt': ''},
            },
        )

    def test_post(self):
        url = reverse('account:profile')
        post_data = {
            'fullName': 'Annoying Orange',
            'email': 'no-reply@mail.ru',
            'phone': '+78002000600',
            'avatar': {'src': '', 'alt': ''},
        }

        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.user1)
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, post_data)

        user = User.objects.filter(
            username='user1',
            first_name=post_data['fullName'],
            email=post_data['email'],
        )
        self.assertIsNotNone(user)
        profile = Profile.objects.filter(
            user=self.user1,
            phone=post_data['phone'],
            avatar=post_data['avatar']['src'],
            avatar_alt=post_data['avatar']['alt'],
        )
        self.assertIsNotNone(profile)


class AvatarUpdateViewTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.user = User.objects.create(
            username='user1', password='secret', email='user1@user.com'
        )
        cls.rand_image = RandomImage(500 * 500)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.user.delete()

    def test_post(self):
        url = reverse('account:avatar')

        photo_bytes = self.rand_image.get_bytes(size=(100, 100), format='png')
        data = {'avatar': photo_bytes}
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.user)
        photo_bytes = self.rand_image.get_bytes(size=(100, 100), format='png')
        data = {'avatar': photo_bytes}
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile = Profile.objects.get(user_id=self.user.id)
        file_data = default_storage.open(profile.avatar.path).read()
        self.assertEqual(file_data, photo_bytes.getvalue())

        photo_bytes = self.rand_image.get_bytes(
            size=(1000, 1000), format='png'
        )
        data = {'avatar': photo_bytes}
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {'avatar': b'dsfvks'}
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        photo_bytes = self.rand_image.get_bytes(size=(100, 100), format='gif')
        data = {'avatar': photo_bytes}
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        photo_bytes = self.rand_image.get_bytes(size=(100, 100), format='jpeg')
        data = {'avatar': photo_bytes}
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

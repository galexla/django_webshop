from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from .models import Profile, User


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
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        response = self.client.get(reverse('account:profile'))
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            url, {'username': 'user2', 'password': 'secret'}
        )
        self.assertEquals(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        response = self.client.post(
            url, {'username': 'user3', 'password': 'secret'}
        )
        self.assertEquals(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        response = self.client.post(
            url, {'username': 'user1', 'password12345': 'secret'}
        )
        self.assertEquals(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        response = self.client.post(
            url, {'username12345': 'user1', 'password': 'secret'}
        )
        self.assertEquals(
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

        response = self.client.post(url)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.user1)
        response = self.client.post(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('account:profile'))
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)


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
        self.assertEquals(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        post_data = {
            'username': 'user2',
            'password': '123qazxsw',
            'name': 'user',
        }
        response = self.client.post(url, post_data)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        user = User.objects.filter(username='user2').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, post_data['username'])
        self.assertEqual(user.first_name, post_data['name'])
        response = self.client.get(reverse('account:profile'))
        self.assertEquals(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            url,
            {'username': 'user1', 'password': 'secret', 'name12345': 'user'},
        )
        self.assertEquals(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        response = self.client.post(
            url,
            {'username': 'user3', 'password': 'secret', 'name1': 'user'},
        )
        self.assertEquals(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        response = self.client.post(url, {})
        self.assertEquals(
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
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.user1)

        response = self.client.post(
            url,
            {'currentPassword': 'secret1', 'newPassword': 'newPass321'},
        )
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            url,
            {'currentPassword': 'secret', 'newPassword': 'newPass'},
        )
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)

        response = self.client.post(
            url,
            {'currentPassword': 'secret', 'newPassword': 'newPass321'},
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        response = self.client.post(
            reverse('account:sign-in'),
            {'username': 'user1', 'password': 'newPass321'},
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('account:profile'))
        self.assertEquals(response.status_code, status.HTTP_200_OK)

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
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.user1)
        response = self.client.get(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(
            response.data,
            {
                'fullName': '123',
                'email': 'user1@user.com',
                'phone': '12345678',
                'avatar': {'src': '', 'alt': ''},
            },
        )

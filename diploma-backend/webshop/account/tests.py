from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response

from .models import User


class SignInViewTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.user1 = User.objects.create_user(
            username='user1', password='secret', email='user1@user.com'
        )
        cls.user2 = User.objects.create_user(
            username='user2',
            password='secret',
            email='user2@user.com',
            is_active=False,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.user1.delete()
        cls.user2.delete()

    def test_signin(self):
        url = reverse('account:sign-in')
        response = self.client.post(
            url, {'username': 'user1', 'password': 'secret'}
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user1.is_authenticated)

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

    def test_signin(self):
        url = reverse('account:sign-out')

        response = self.client.post(url)
        self.assertEquals(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_login(self.user1)
        response = self.client.post(url)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.user1.is_authenticated)


class SignUpViewTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.user1 = User.objects.create_user(
            username='user1', password='secret', email='user1@user.com'
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.user1.delete()
        User.objects.filter(username='user2').delete()

    def test_signin(self):
        url = reverse('account:sign-up')

        response: Response = self.client.post(
            url,
            {'username': 'user1', 'password': 'secret', 'name': 'user'},
        )
        self.assertEquals(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        response: Response = self.client.post(
            url,
            {'username': 'user2', 'password': '123qazxsw', 'name': 'user'},
        )
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.filter(username='user2').exists())
        self.assertTrue(User.objects.get(username='user2').is_authenticated)

        response: Response = self.client.post(
            url,
            {'username': 'user1', 'password': 'secret', 'name12345': 'user'},
        )
        self.assertEquals(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        response: Response = self.client.post(
            url,
            {'username': 'user3', 'password': 'secret', 'name1': 'user'},
        )
        self.assertEquals(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

        response: Response = self.client.post(url, {})
        self.assertEquals(
            response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

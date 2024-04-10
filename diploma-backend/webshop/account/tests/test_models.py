from django.db import IntegrityError
from django.test import TestCase

from ..models import Profile, User, get_avatar_upload_path
from .common import BaseTestCase, RandomImage


class TestTopLevel(TestCase):
    def test_get_avatar_upload_path(self):
        user = User.objects.create(username='a', password='a')
        expected = f'users/user{user.pk}/avatar/test.jpeg'
        path = get_avatar_upload_path(user.profile, 'test.jpeg')
        self.assertEqual(path, expected)
        user.delete()


class TestUser(TestCase):
    def test_fields(self):
        user = User.objects.create(username='a', password='a', email='a@a.com')
        with self.assertRaises(IntegrityError):
            User.objects.create(username='b', password='b', email='a@a.com')
        user.delete()


class TestCustomUserManager(TestCase):
    def test_create(self):
        user = User.objects.create(username='a', password='a')
        profile = Profile.objects.get(user_id=user.id)
        self.assertIsNotNone(profile)
        user.delete()

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            username='a', password='a', email='a@a.com'
        )
        profile = Profile.objects.get(user_id=user.id)
        self.assertIsNotNone(profile)
        user.delete()


class TestProfile(TestCase):
    def test_fields(self):
        user = User.objects.create(username='a', password='a')
        user.profile.delete()

        profile = Profile.objects.create(
            user_id=user.id, phone='+1646465465', avatar_alt='abc'
        )
        self.assertIsNotNone(profile)
        self.assertEqual(profile.phone, '+1646465465')
        self.assertEqual(profile.avatar_alt, 'abc')

        user.delete()

from django.conf import settings
from django.test.runner import DiscoverRunner


class FastTestRunner(DiscoverRunner):
    def setup_test_environment(self):
        super(FastTestRunner, self).setup_test_environment()
        settings.STORAGES = {
            'default': {
                'BACKEND': 'django.core.files.storage.memory.InMemoryStorage',
            },
            'staticfiles': {
                'BACKEND': 'django.core.files.storage.memory.InMemoryStorage',
            },
        }
        settings.DEFAULT_FILE_STORAGE = (
            'django.core.files.storage.memory.InMemoryStorage'
        )
        settings.DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        }
        settings.PASSWORD_HASHERS = (
            'django.contrib.auth.hashers.MD5PasswordHasher',
        )

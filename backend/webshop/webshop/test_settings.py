from .settings import *

ALLOWED_HOSTS += ['testserver']
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.memory.InMemoryStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.core.files.storage.memory.InMemoryStorage',
    },
}
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher',)
INSTALLED_APPS.insert(0, 'pytest_django')

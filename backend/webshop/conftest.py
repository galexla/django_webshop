import pytest
from django.core.management import call_command


@pytest.fixture(scope='function')
def db_data(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command('loaddata', 'fixtures/sample_data.json')
        yield

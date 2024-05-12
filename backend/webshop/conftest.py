import pytest
from django.core.management import call_command


@pytest.fixture(scope='function')
def db_data(django_db_setup, django_db_blocker):
    """
    A fixture with sample data for the database.

    :param django_db_setup: Django database setup fixture
    :param django_db_blocker: Django database blocker fixture
    """
    with django_db_blocker.unblock():
        call_command('loaddata', 'fixtures/sample_data.json')
        yield

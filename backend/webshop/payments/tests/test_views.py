import pytest
from account.models import User
from django.urls import reverse
from payments.views import PaymentView
from rest_framework import status
from rest_framework.test import APIClient


class TestPaymentView:
    base_ok_data = {
        'number': 142384,
        'name': 'JOHN SMITH',
        'month': '01',
        'year': 2345,
        'code': 123,
    }

    @classmethod
    def setup_class(cls):
        cls.client = APIClient()

    @pytest.mark.django_db(transaction=True)
    def test_all(self, db_data):
        url = reverse('payments:payment', kwargs={'pk': 3})

        response = self.client.post(url, self.base_ok_data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        self.client.force_login(User.objects.get(id=2))
        response = self.client.post(url, self.base_ok_data)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        self.client.force_login(User.objects.get(id=1))

        response = self.client.post(
            reverse('payments:payment', kwargs={'pk': 2}), self.base_ok_data
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        data = self.base_ok_data.copy()
        data['number'] = 999_999_992
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        data = self.base_ok_data.copy()
        data['year'] = 13
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        for number in (12345, 12340):
            data['number'] = number
            response = self.client.post(url, data)
            assert response.status_code in (
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        response = self.client.post(url, self.base_ok_data)
        assert response.status_code == status.HTTP_200_OK

    def test_get_random_error(self):
        view = PaymentView()
        for _ in range(10):
            error_str, status_code = view._get_random_error()
            assert 15 <= len(error_str) <= 34
            assert 'a' in error_str
            assert 'i' in error_str
            assert status_code in (
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

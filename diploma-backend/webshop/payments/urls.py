from django.urls import path

from .views import PaymentView

app_name = 'payments'

urlpatterns = [
    path('payment/<int:pk>', PaymentView.as_view(), name='payment'),
]

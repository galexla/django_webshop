from django.urls import path

from .views import LoginView, RegistrationView

app_name = 'account'

urlpatterns = [
    path('sign-in', LoginView.as_view(), name='sign-in'),
    path('sign-up', RegistrationView.as_view(), name='sign-up'),
]

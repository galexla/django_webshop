from django.urls import path

from .views import LoginView, LogoutView, RegistrationView

app_name = 'account'

urlpatterns = [
    path('sign-in', LoginView.as_view(), name='sign-in'),
    path('sign-up', RegistrationView.as_view(), name='sign-up'),
    path('sign-out', LogoutView.as_view(), name='sign-out'),
]

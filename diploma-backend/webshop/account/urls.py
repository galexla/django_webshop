from django.urls import path

from .views import (
    AvatarUpdateView,
    LoginView,
    LogoutView,
    ProfileView,
    RegistrationView,
)

app_name = 'account'

urlpatterns = [
    path('sign-in', LoginView.as_view(), name='sign-in'),
    path('sign-up', RegistrationView.as_view(), name='sign-up'),
    path('sign-out', LogoutView.as_view(), name='sign-out'),
    path('profile', ProfileView.as_view(), name='profile'),
    path('profile/avatar', AvatarUpdateView.as_view(), name='avatar'),
]

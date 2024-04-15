from django.urls import path

from .views import (
    AvatarUpdateView,
    ProfileView,
    SetPasswordView,
    SignInView,
    SignOutView,
    SignUpView,
)

app_name = 'account'

urlpatterns = [
    path('sign-in/', SignInView.as_view(), name='sign-in'),
    path('sign-up/', SignUpView.as_view(), name='sign-up'),
    path('sign-out/', SignOutView.as_view(), name='sign-out'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/avatar/', AvatarUpdateView.as_view(), name='avatar'),
    path('profile/password/', SetPasswordView.as_view(), name='password'),
]

from django.urls import path

from .views import LoginView

app_name = 'account'

urlpatterns = [
    path('sign-in', LoginView.as_view(), name='sign-in'),
]

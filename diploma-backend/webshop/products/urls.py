from django.urls import path

from .views import TopLevelCategoryListView

app_name = 'products'

urlpatterns = [
    path('categories/', TopLevelCategoryListView.as_view(), name='categories'),
]

from django.urls import path

from .views import TagListView, TopLevelCategoryListView

app_name = 'products'

urlpatterns = [
    path('categories/', TopLevelCategoryListView.as_view(), name='categories'),
    path('tags/', TagListView.as_view(), name='tags'),
]

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CatalogViewSet, TagListView, TopLevelCategoryListView

app_name = 'products'

routers = DefaultRouter()
routers.register('catalog', CatalogViewSet)

urlpatterns = [
    path('categories/', TopLevelCategoryListView.as_view(), name='categories'),
    path('tags/', TagListView.as_view(), name='tags'),
    path('', include(routers.urls)),
]

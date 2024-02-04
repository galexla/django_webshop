from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BasketStubViewSet,
    CatalogViewSet,
    TagListViewSet,
    TopLevelCategoryListView,
)

app_name = 'products'

routers = DefaultRouter()
routers.register('catalog', CatalogViewSet)
routers.register('tags', TagListViewSet)

urlpatterns = [
    path('', include(routers.urls)),
    path('categories/', TopLevelCategoryListView.as_view(), name='categories'),
    # path('tags/', TagListView.as_view(), name='tags'),
    path('basket/', BasketStubViewSet.as_view(), name='basket'),
]

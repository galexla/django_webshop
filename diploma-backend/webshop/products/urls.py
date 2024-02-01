from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BasketStubViewSet,
    CatalogViewSet,
    TagListView,
    TopLevelCategoryListView,
)

app_name = 'products'

routers = DefaultRouter()
routers.register('catalog', CatalogViewSet)
# routers.register('basket', BasketStubViewSet)

urlpatterns = [
    path('categories/', TopLevelCategoryListView.as_view(), name='categories'),
    path('tags/', TagListView.as_view(), name='tags'),
    path('', include(routers.urls)),
    # path('catalog/', CatalogViewSet.as_view(), name='catalog'),
    path('basket/', BasketStubViewSet.as_view(), name='basket'),
]

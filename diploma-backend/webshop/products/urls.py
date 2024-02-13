from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BannerProductsListView,
    BasketStubViewSet,
    CatalogViewSet,
    LimitedProductsListView,
    PopularProductsListView,
    ProductDetailView,
    ReviewCreateView,
    TagListViewSet,
    TopLevelCategoryListView,
)

app_name = 'products'

routers = DefaultRouter()
routers.register('catalog', CatalogViewSet)
routers.register('tags', TagListViewSet)

urlpatterns = [
    path('', include(routers.urls)),
    path(
        'product/<int:pk>/',
        ProductDetailView.as_view(),
        name='product-details',
    ),
    path(
        'product/<int:pk>/reviews',
        ReviewCreateView.as_view(),
        name='create-review',
    ),
    path('banners/', BannerProductsListView.as_view(), name='banners'),
    path(
        'products/popular/',
        PopularProductsListView.as_view(),
        name='popular-products',
    ),
    path(
        'products/limited/',
        LimitedProductsListView.as_view(),
        name='limited-products',
    ),
    path('categories/', TopLevelCategoryListView.as_view(), name='categories'),
    # path('tags/', TagListView.as_view(), name='tags'),
    path('basket/', BasketStubViewSet.as_view(), name='basket'),
]

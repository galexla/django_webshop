from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BannerProductsListView,
    BasketView,
    CatalogViewSet,
    LimitedProductsListView,
    OrdersView,
    OrderView,
    PopularProductsListView,
    ProductDetailView,
    ReviewCreateView,
    SalesView,
    TagListViewSet,
    TopLevelCategoryListView,
)

app_name = 'products'

routers = DefaultRouter()
routers.register('catalog', CatalogViewSet)
routers.register('tags', TagListViewSet, basename='tags')

urlpatterns = [
    path('', include(routers.urls)),
    path(
        'product/<int:pk>/',
        ProductDetailView.as_view(),
        name='product-details',
    ),
    path(
        'product/<int:pk>/reviews/',
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
    path('sales/', SalesView.as_view(), name='sales'),
    path('categories/', TopLevelCategoryListView.as_view(), name='categories'),
    path('basket/', BasketView.as_view(), name='basket'),
    path('orders/', OrdersView.as_view(), name='orders'),
    path('order/<int:pk>/', OrderView.as_view(), name='order'),
]

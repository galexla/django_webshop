from rest_framework import generics

from .models import Category
from .serializers import TopLevelCategorySerializer


class TopLevelCategoryListView(generics.ListAPIView):
    serializer_class = TopLevelCategorySerializer

    def get_queryset(self):
        return Category.objects.filter(parent=None).prefetch_related(
            'subcategories'
        )

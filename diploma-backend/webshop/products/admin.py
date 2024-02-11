from typing import Any

from django.contrib import admin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.utils.translation import gettext_lazy as _

from .forms import CategoryAdminForm, ProductAdminForm
from .models import Category, Product, ProductImage, Specification, Tag


class SubcategoryInline(admin.TabularInline):
    model = Category
    verbose_name = _('Subcategory')
    verbose_name_plural = _('Subcategories')


class ParentCategoryListFilter(admin.SimpleListFilter):
    title = _('parent category')
    parameter_name = 'parent__title'

    def lookups(self, request, model_admin):
        queryset = Category.objects.filter(parent=None)
        result = [(category.pk, category.title) for category in queryset]
        return result

    def queryset(
        self, request: Any, queryset: QuerySet[Any]
    ) -> QuerySet[Any] | None:
        if self.value() is None:
            return queryset
        return queryset.filter(parent=self.value())


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = 'title', 'get_parent_title'
    search_fields = 'title', 'parent__title'
    list_filter = (ParentCategoryListFilter,)
    sortable_by = ()
    form = CategoryAdminForm
    inlines = [SubcategoryInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('parent').order_by(
            'parent__title', 'title'
        )

    def get_parent_title(self, obj):
        return obj.parent.title if obj.parent else None

    get_parent_title.short_description = _('Parent')


class ProductImagesInline(admin.TabularInline):
    model = ProductImage
    verbose_name = _('Image')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'price',
        'category',
        'count',
        'date',
        'short_description',
        'free_delivery',
        'purchases',
        'is_limited_edition',
        'is_banner',
        'rating',
        'archived',
    )
    form = ProductAdminForm
    inlines = [ProductImagesInline]

    def short_description(self, obj):
        return obj.description[:20] + '...'

    short_description.short_description = _('Description')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Specification)
class SpecificationAdmin(admin.ModelAdmin):
    list_display = 'name', 'value'

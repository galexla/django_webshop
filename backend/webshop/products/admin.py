from typing import Any

from django import forms
from django.contrib import admin
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.utils.translation import gettext_lazy as _

from .forms import CategoryAdminForm, ProductAdminForm
from .models import (
    Category,
    Order,
    OrderProduct,
    Product,
    ProductImage,
    Sale,
    Specification,
    Tag,
)


@admin.action(description='Archive items')
def mark_archived(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
):
    """
    Mark selected items as archived.

    :param modeladmin: ModelAdmin instance
    :type modeladmin: admin.ModelAdmin
    :param request: Http request
    :type request: HttpRequest
    :param queryset: QuerySet of selected items
    :type queryset: QuerySet
    :return: None
    """
    queryset.update(archived=True)


@admin.action(description='Unarchive items')
def mark_unarchived(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
):
    """
    Mark selected items as not archived.

    :param modeladmin: ModelAdmin instance
    :type modeladmin: admin.ModelAdmin
    :param request: Http request
    :type request: HttpRequest
    :param queryset: QuerySet of selected items
    :type queryset: QuerySet
    :return: None
    """
    queryset.update(archived=False)


class SubcategoryInline(admin.TabularInline):
    """Inline representation of Subcategory model in CategoryAdmin panel."""

    model = Category
    verbose_name = _('Subcategory')
    verbose_name_plural = _('Subcategories')


class ParentCategoryListFilter(admin.SimpleListFilter):
    """Custom filter for Category model in admin panel."""

    title = _('parent category')
    parameter_name = 'parent__title'

    def lookups(
        self, request: HttpRequest, model_admin: admin.ModelAdmin
    ) -> list[tuple[str, str]]:
        """
        Return list of top-level categories (id, title).

        :param request: Http request
        :type request: HttpRequest
        :param model_admin: ModelAdmin instance
        :type model_admin: admin.ModelAdmin
        :return: List of tuples with top-level categories (id, title)
        :rtype: list[tuple[str, str]]
        """
        queryset = Category.objects.filter(parent=None)
        result = [(category.pk, category.title) for category in queryset]
        return result

    def queryset(
        self, request: Any, queryset: QuerySet[Any]
    ) -> QuerySet[Any] | None:
        """
        Filter queryset by parent category.

        :param request: Http request
        :type request: HttpRequest
        :param queryset: QuerySet of Category admin panel
        :type queryset: QuerySet
        :return: Filtered queryset
        :rtype: QuerySet
        """
        if self.value() is None:
            return queryset
        return queryset.filter(parent=self.value())


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin panel for Category model."""

    actions = [
        mark_archived,
        mark_unarchived,
    ]
    list_display = ['pk', 'title', 'get_parent_title', 'archived']
    list_display_links = ['pk', 'title']
    search_fields = ['title', 'parent__title']
    list_filter = [ParentCategoryListFilter, 'archived']
    ordering = ['parent__title', 'title', 'pk']
    sortable_by = []
    form = CategoryAdminForm
    inlines = [SubcategoryInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Any]:
        """
        Return queryset for Category admin panel.

        :param request: Http request
        :type request: HttpRequest
        :return: Queryset
        :rtype: QuerySet
        """
        queryset = super().get_queryset(request)
        return queryset.prefetch_related('parent').order_by(
            'parent__title', 'title'
        )

    def get_parent_title(self, obj: Category) -> str:
        """
        Return parent category title.

        :param obj: Category instance
        :type obj: Category
        :return: Parent category title
        :rtype: str
        """
        return obj.parent.title if obj.parent else None

    get_parent_title.short_description = _('Parent')

    def has_delete_permission(
        self, request: HttpRequest, obj: Category = None
    ) -> bool:
        """
        Disable delete permission in Category admin panel.

        :param request: Http request
        :type request: HttpRequest
        :param obj: Category instance
        :type obj: Category
        :return: False
        :rtype: bool
        """
        return False


class ProductImagesInline(admin.TabularInline):
    """Inline representation of ProductImage model in ProductAdmin panel."""

    model = ProductImage
    verbose_name = _('Image')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin panel for Product model."""

    actions = [
        mark_archived,
        mark_unarchived,
    ]
    list_display = [
        'pk',
        'title',
        'price',
        'category',
        'count',
        'short_description',
        'free_dlvr',
        'sold',
        'limited',
        'banner',
        'rating',
        'archived',
    ]
    list_display_links = ['pk', 'title']
    ordering = ['title', 'pk']
    search_fields = ['title', 'description', 'full_description', 'price']
    list_filter = ['is_limited_edition', 'is_banner', 'archived']
    form = ProductAdminForm
    readonly_fields = ['created_at', 'sold_count']
    inlines = [ProductImagesInline]
    fieldsets = [
        (
            None,
            {
                'fields': (
                    'title',
                    'category',
                    'price',
                    'count',
                    'sold_count',
                    'free_delivery',
                    'description',
                    'full_description',
                    'created_at',
                ),
            },
        ),
        (
            _('Marketing options'),
            {
                'fields': (
                    'rating',
                    'is_limited_edition',
                    'is_banner',
                ),
            },
        ),
        (
            _('Tags & specifications'),
            {
                'fields': ('tags', 'specifications'),
                'classes': ('collapse',),
            },
        ),
        (
            _('Soft deletion'),
            {
                'fields': ('archived',),
                'classes': ('collapse',),
                'description': _('Field "archived" is for soft delete'),
            },
        ),
    ]

    def short_description(self, obj: Product) -> str:
        """
        Return short description of product.

        :param obj: Product instance
        :type obj: Product
        :return: Short description of product
        :rtype: str
        """
        return obj.description[:20] + '...'

    short_description.short_description = _('Description')

    def limited(self, obj: Product) -> bool:
        """
        Return True if product is limited edition, False otherwise.

        :param obj: Product instance
        :type obj: Product
        :return: True if product is limited edition, False otherwise
        :rtype: bool
        """
        return obj.is_limited_edition

    limited.short_description = _('Limited')

    def banner(self, obj: Product) -> bool:
        """
        Return True if product is banner edition, False otherwise.

        :param obj: Product instance
        :type obj: Product
        :return: True if product is banner edition, False otherwise
        :rtype: bool
        """
        return obj.is_banner

    banner.short_description = _('Banner')

    def sold(self, obj: Product) -> int:
        """
        Return number of sold products.

        :param obj: Product instance
        :type obj: Product
        :return: Number of sold products
        :rtype: int
        """
        return obj.sold_count

    sold.short_description = _('Sold')

    def free_dlvr(self, obj: Product) -> bool:
        """
        Return True if product has free delivery, False otherwise.

        :param obj: Product instance
        :type obj: Product
        :return: True if product has free delivery, False otherwise
        :rtype: bool
        """
        return obj.free_delivery

    free_dlvr.short_description = _('Free dlvr')

    def has_delete_permission(
        self, request: HttpRequest, obj: Product = None
    ) -> bool:
        """
        Disable delete permission In Product admin panel.

        :param request: Http request
        :type request: HttpRequest
        :param obj: Product instance
        :type obj: Product
        :return: False
        :rtype: bool
        """
        return False


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin panel for Tag model."""

    list_display = ['name']


@admin.register(Specification)
class SpecificationAdmin(admin.ModelAdmin):
    """Admin panel for Specification model."""

    list_display = ['name', 'value']


class ProductChoiceField(forms.ModelChoiceField):
    """Custom ModelChoiceField for SaleAdmin form."""

    def label_from_instance(self, obj: Product) -> str:
        """
        Return label for Product instance in format "title - price".

        :param obj: Product instance
        :type obj: Product
        :return: Formatted label
        :rtype: str
        """
        return f"{obj.title} - ${obj.price}"


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    """Admin panel for Sale model."""

    list_display = [
        'product',
        'date_from',
        'date_to',
        'sale_price',
    ]
    search_fields = ['product__title', 'date_from', 'date_to', 'sale_price']
    ordering = ['product', 'date_from', 'date_to']
    sortable_by = []

    def formfield_for_foreignkey(
        self, db_field, request: HttpRequest, **kwargs
    ) -> forms.ModelChoiceField | None:
        """
        Return ProductChoiceField for product field in SaleAdmin form.

        :param db_field: Field of Sale model
        :type db_field: Any
        :param request: Http request
        :type request: HttpRequest
        :return: ModelChoiceField | None
        :rtype: Any
        """
        if db_field.name == "product":
            return ProductChoiceField(queryset=Product.objects.all())
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class OrderProductsInline(admin.TabularInline):
    """Inline representation of OrderProduct model in OrderAdmin panel."""

    model = OrderProduct
    verbose_name = _('Order product')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin panel for Order model."""

    actions = [
        mark_archived,
        mark_unarchived,
    ]
    list_display = [
        'pk',
        'created_at',
        'user',
        'total_cost',
        'full_name',
        'status',
        'delivery_type',
        'archived',
    ]
    list_display_links = ['pk', 'created_at']
    ordering = ['-created_at', 'pk']
    search_fields = [
        'full_name',
        'city',
        'address',
        'email',
        'phone',
        'user__username',
        'total_cost',
        'created_at',
    ]
    list_filter = [
        'status',
        'delivery_type',
        'payment_type',
        'archived',
    ]
    readonly_fields = ['created_at', 'user']
    inlines = [OrderProductsInline]

    def has_delete_permission(
        self, request: HttpRequest, obj: Order = None
    ) -> bool:
        """
        Disable delete permission in Order admin panel.

        :param request: Http request
        :type request: HttpRequest
        :param obj: Order instance
        :type obj: Order
        :return: False
        :rtype: bool
        """
        return False

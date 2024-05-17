from django import forms

from .models import Category, Product


class CategoryAdminForm(forms.ModelForm):
    """Form for Category model in admin panel."""

    class Meta:
        model = Category
        fields = '__all__'

    image_alt = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.Textarea,
    )

    def __init__(self, *args, **kwargs) -> None:
        """Initialize form."""
        super(CategoryAdminForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance and instance.subcategories.all():
            self.fields['parent'].queryset = Category.objects.none()
        else:
            queryset = Category.objects.filter(parent__isnull=True)
            if instance:
                queryset = queryset.exclude(id=instance.id)
            self.fields['parent'].queryset = queryset

    def has_child_categories(self, instance: Category) -> bool:
        """
        Check if category has child categories.

        :param instance: Category instance
        :type instance: Category
        :return: True if category has child categories, False otherwise
        :rtype: bool
        """
        child = Category.objects.filter(parent__id=instance.id).first()
        return True if child else False


class ProductAdminForm(forms.ModelForm):
    """Form for Product model in admin panel."""

    class Meta:
        model = Product
        fields = [
            'title',
            'price',
            'category',
            'count',
            'description',
            'full_description',
            'free_delivery',
            'is_limited_edition',
            'is_banner',
            'tags',
            'specifications',
            'rating',
            'archived',
        ]

    description = forms.CharField(
        required=False,
        max_length=3000,
        widget=forms.Textarea,
    )
    full_description = forms.CharField(
        required=False,
        max_length=20000,
        widget=forms.Textarea,
    )

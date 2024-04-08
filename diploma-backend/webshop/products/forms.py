from django import forms

from .models import Category, Product


class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'

    image_alt = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.Textarea,
    )

    def __init__(self, *args, **kwargs):
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
        child = Category.objects.filter(parent__id=instance.id).first()
        return True if child else False


class ProductAdminForm(forms.ModelForm):
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

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
        if instance and instance.parent:
            self.fields['parent'].queryset = Category.objects.none()
        else:
            queryset = Category.objects.filter(parent__isnull=True)
            if instance:
                queryset = queryset.exclude(pk=instance.pk)
            self.fields['parent'].queryset = queryset


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

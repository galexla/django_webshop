from django import forms

from .models import Category


class CategoryAdminForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(CategoryAdminForm, self).__init__(*args, **kwargs)
        self.fields['parent'].queryset = Category.objects.filter(
            parent__isnull=True
        ).exclude(pk=kwargs['instance'].pk)

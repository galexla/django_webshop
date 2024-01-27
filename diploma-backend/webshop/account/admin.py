from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Category, User

admin.site.register(User, UserAdmin)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'parent')
    search_fields = ('title', 'parent__title')
    list_filter = ('parent',)
    ordering = ('parent', 'title')

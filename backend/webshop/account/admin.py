from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CategoryAdmin(UserAdmin):
    list_display = [
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_active',
    ]

    def has_delete_permission(self, request, obj=None):
        return False

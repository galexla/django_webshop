from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import User


@admin.action(description='Activate users')
def mark_active(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
):
    queryset.update(is_active=True)


@admin.action(description='Deactivate users')
def mark_inactive(
    modeladmin: admin.ModelAdmin, request: HttpRequest, queryset: QuerySet
):
    queryset.update(is_active=False)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    User admin.
    """

    actions = [
        mark_active,
        mark_inactive,
    ]
    list_display = [
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'is_active',
    ]

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        """
        Check if user can delete object.

        :param request: Request
        :type request: Any
        :param obj: Object
        :type obj: Any
        :return: True if user can delete object, False otherwise
        :rtype: bool
        """
        return False

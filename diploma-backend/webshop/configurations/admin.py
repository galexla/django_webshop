from django.contrib import admin
from django.core.exceptions import PermissionDenied

from .models import ShopConfiguration


@admin.register(ShopConfiguration)
class ShopConfigurationAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'description')

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.key in ShopConfiguration.protected_keys:
            return ('key',)
        return ()

    def delete_model(self, request, obj):
        if obj.key in ShopConfiguration.protected_keys:
            raise PermissionDenied(
                f'The "{obj.key}" configuration is protected and cannot be deleted'
            )
        super().delete_model(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.key in ShopConfiguration.protected_keys:
            return False
        return super().has_delete_permission(request, obj=obj)

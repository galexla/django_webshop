from django.contrib import admin

from .models import ShopConfiguration


@admin.register(ShopConfiguration)
class ShopConfigurationAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'description')

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.key in ShopConfiguration.protected_keys:
            return ('key', 'description')
        return ()

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

from django.contrib import admin
from django.http import HttpRequest

from .models import ShopConfiguration


@admin.register(ShopConfiguration)
class ShopConfigurationAdmin(admin.ModelAdmin):
    """Shop configuration admin panel."""

    list_display = ('key', 'value', 'description')

    def get_readonly_fields(
        self, request: HttpRequest, obj: ShopConfiguration = None
    ) -> tuple[str, str]:
        """
        Disable editing of protected keys in admin panel.

        :param request: Request
        :type request: HttpRequest
        :param obj: Object
        :type obj: ShopConfiguration | None
        :return: False
        :rtype: bool
        """
        if obj and obj.key in ShopConfiguration.protected_keys:
            return ('key', 'description')
        return ()

    def has_delete_permission(
        self, request: HttpRequest, obj: ShopConfiguration | None = None
    ) -> bool:
        """
        Disable delete permission in admin panel.

        :param request: Request
        :type request: HttpRequest
        :param obj: Object
        :type obj: ShopConfiguration | None
        :return: False
        :rtype: bool
        """
        return False

    def has_add_permission(
        self, request: HttpRequest, obj: ShopConfiguration | None = None
    ) -> bool:
        """
        Disable add permission in admin panel.

        :param request: Request
        :type request: HttpRequest
        :param obj: Object
        :type obj: ShopConfiguration | None
        :return: False
        :rtype: bool
        """
        return False
